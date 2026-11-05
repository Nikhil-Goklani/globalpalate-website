// Cloudflare Pages Function: POST /api/lead
// Validates, spam-checks and forwards leads to Zoho CRM (Web-to-Lead) and/or email (Resend).
// Required env: at least one channel: ZOHO_XNQSJSDP + ZOHO_XMIWTLD (+ ZOHO_ACTIONTYPE) OR RESEND_API_KEY + NOTIFY_TO + NOTIFY_FROM
// Optional env: TURNSTILE_SECRET, ALLOWED_ORIGINS (comma list), ZOHO_WTL_URL, RATE_KV (KV namespace binding)
const TYPES = ['quote', 'sample', 'inquiry', 'documents', 'credit'];
const MEM = new Map();
const json = (obj, status = 200) => new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
const clean = (v, max = 500) => String(v == null ? '' : v).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '').trim().slice(0, max);
const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,}$/;

export async function handleLead(request, env, fetchImpl = fetch, now = Date.now()) {
  if (request.method !== 'POST') return json({ ok: false, error: 'Method not allowed.' }, 405);
  const url = new URL(request.url);
  const origin = request.headers.get('Origin');
  if (origin) {
    const allowed = (env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
    if (new URL(origin).host !== url.host && !allowed.includes(origin)) return json({ ok: false, error: 'Origin not allowed.' }, 403);
  }
  const raw = await request.text();
  if (raw.length > 20000) return json({ ok: false, error: 'Request too large.' }, 413);
  let d; try { d = JSON.parse(raw); } catch { return json({ ok: false, error: 'Invalid request.' }, 400); }
  if (!d || typeof d !== 'object') return json({ ok: false, error: 'Invalid request.' }, 400);

  // spam: honeypot and minimum fill time (silently accepted, nothing stored)
  if (clean(d.website)) return json({ ok: true });
  const rendered = Number(d.rendered);
  if (!rendered || now - rendered < 3000) return json({ ok: true });

  // rate limit per IP: 5 per 10 minutes
  const ip = request.headers.get('CF-Connecting-IP') || request.headers.get('X-Forwarded-For') || 'unknown';
  const key = 'rl:' + ip, windowMs = 600000;
  if (env.RATE_KV) {
    const n = Number(await env.RATE_KV.get(key)) || 0;
    if (n >= 5) return json({ ok: false, error: 'Too many requests. Please try again later.' }, 429);
    await env.RATE_KV.put(key, String(n + 1), { expirationTtl: 600 });
  } else {
    const hits = (MEM.get(key) || []).filter(t => now - t < windowMs);
    if (hits.length >= 5) return json({ ok: false, error: 'Too many requests. Please try again later.' }, 429);
    hits.push(now); MEM.set(key, hits);
  }

  // Turnstile
  if (env.TURNSTILE_SECRET) {
    const token = clean(d['cf-turnstile-response'], 2048);
    if (!token) return json({ ok: false, error: 'Please complete the spam check and try again.' }, 400);
    const body = new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: token, remoteip: ip });
    let r; try { r = await (await fetchImpl('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body })).json(); } catch { r = null; }
    if (!r || !r.success) return json({ ok: false, error: 'Spam check failed. Please try again.' }, 400);
  }

  // validate
  const type = clean(d.type, 20);
  if (!TYPES.includes(type)) return json({ ok: false, error: 'Invalid request type.' }, 400);
  const f = {
    first: clean(d.first_name, 80), last: clean(d.last_name, 80), email: clean(d.email, 254).toLowerCase(), phone: clean(d.phone, 40),
    company: clean(d.company, 120), url: clean(d.company_url, 200), qty: clean(d.quantity, 20), unit: clean(d.unit, 10) === 'drum' ? 'drums' : 'kg',
    zip: clean(d.zip, 20), needed: clean(d.needed_by, 20), use: clean(d.intended_use, 80), msg: clean(d.message, 2000), page: clean(d.page, 200),
    products: (Array.isArray(d.products) ? d.products : [d.products]).filter(Boolean).map(p => clean(p, 40)).slice(0, 10),
  };
  const err = [];
  if (!f.first) err.push('your name');
  if (!EMAIL.test(f.email)) err.push('a valid email');
  if (type !== 'inquiry' && !f.company) err.push('your company');
  if (type === 'inquiry' && !f.msg) err.push('a message');
  if ((type === 'quote' || type === 'sample') && !f.qty) err.push('the quantity you need');
  if ((type === 'quote' || type === 'sample') && !f.zip) err.push('a delivery ZIP / postal code');
  if (err.length) return json({ ok: false, error: 'Please provide ' + err.join(', ') + '.' }, 400);

  const label = { quote: 'Quote request', sample: 'Sample request', inquiry: 'General inquiry', documents: 'Documentation request', credit: 'Credit application' }[type];
  const lines = [`Type: ${label}`, f.products.length && `Products: ${f.products.join(', ')}`, f.qty && `Quantity: ${f.qty} ${f.unit}`, f.zip && `Delivery ZIP: ${f.zip}`,
    f.needed && `Needed by: ${f.needed}`, f.use && `Intended use: ${f.use}`, f.url && `Company website: ${f.url}`, f.msg && `Message: ${f.msg}`, `Submitted from: ${f.page}`].filter(Boolean);
  const description = lines.join('\n');

  const results = [];
  if (env.ZOHO_XNQSJSDP && env.ZOHO_XMIWTLD) {
    const p = new URLSearchParams({ xnQsjsdp: env.ZOHO_XNQSJSDP, xmIwtLD: env.ZOHO_XMIWTLD, actionType: env.ZOHO_ACTIONTYPE || 'TGVhZHM=', returnURL: 'null',
      'First Name': f.first, 'Last Name': f.last || f.first, Email: f.email, Phone: f.phone, Company: f.company || 'Not provided', Website: f.url,
      'Lead Source': 'Website - ' + label, Description: description });
    try {
      const r = await fetchImpl(env.ZOHO_WTL_URL || 'https://crm.zoho.com/crm/WebToLeadForm', { method: 'POST', body: p, redirect: 'manual' });
      results.push(r.status < 400 || r.type === 'opaqueredirect');
    } catch { results.push(false); }
  }
  if (env.RESEND_API_KEY && env.NOTIFY_TO && env.NOTIFY_FROM) {
    try {
      const r = await fetchImpl('https://api.resend.com/emails', { method: 'POST', headers: { Authorization: 'Bearer ' + env.RESEND_API_KEY, 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: env.NOTIFY_FROM, to: env.NOTIFY_TO.split(',').map(s => s.trim()), reply_to: f.email, subject: `[Website] ${label}: ${f.first} ${f.last} (${f.company || 'no company'})`,
          text: `${f.first} ${f.last}\n${f.email}\n${f.phone}\n${f.company}\n\n${description}` }) });
      results.push(r.ok);
    } catch { results.push(false); }
  }
  if (!results.length) return json({ ok: false, error: 'The form is not configured yet.' }, 503);
  if (!results.some(Boolean)) return json({ ok: false, error: 'We could not record your request.' }, 502);
  return json({ ok: true });
}
export const onRequestPost = ({ request, env }) => handleLead(request, env);
export const onRequest = ({ request, env }) => handleLead(request, env);
