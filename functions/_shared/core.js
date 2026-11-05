// Shared helpers for the admin API (Cloudflare Pages Functions).
export const enc = new TextEncoder();
export const json = (o, status = 200, headers = {}) => new Response(JSON.stringify(o), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...headers } });
const MEM = new Map();
const S = (v, max = 2000) => String(v == null ? '' : v).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '').trim().slice(0, max);
const hex = buf => [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
async function hmac(secret, msg) {
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return hex(await crypto.subtle.sign('HMAC', key, enc.encode(msg)));
}
export function safeEq(a, b) {
  a = String(a); b = String(b); let d = a.length ^ b.length;
  for (let i = 0; i < Math.max(a.length, b.length); i++) d |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
  return d === 0;
}
const secretOf = env => env.ADMIN_SESSION_SECRET || env.ADMIN_PASSWORD || '';
export async function makeSession(env, now) { const exp = now + 8 * 3600 * 1000; return `${exp}.${await hmac(secretOf(env), 's.' + exp)}`; }
export async function checkSession(env, request, now) {
  if (!secretOf(env)) return false;
  const m = /(?:^|;\s*)gp_admin=([^;]+)/.exec(request.headers.get('Cookie') || '');
  if (!m) return false;
  const [exp, sig] = m[1].split('.');
  if (!exp || !sig || Number(exp) < now) return false;
  return safeEq(sig, await hmac(secretOf(env), 's.' + exp));
}
export async function rateLimit(env, key, max, windowSec, now) {
  if (env.GP_KV) {
    const raw = await env.GP_KV.get('rl:' + key); const n = Number(raw) || 0;
    if (n >= max) return false;
    await env.GP_KV.put('rl:' + key, String(n + 1), { expirationTtl: Math.max(60, windowSec) }); return true;
  }
  const hits = (MEM.get(key) || []).filter(t => now - t < windowSec * 1000);
  if (hits.length >= max) return false; hits.push(now); MEM.set(key, hits); return true;
}

// ---------- validation / sanitising of the whole data document ----------
const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const KEY = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const isUrl = u => !u || /^https?:\/\/[^\s]+$/i.test(u);
const list = (v, max) => (Array.isArray(v) ? v : []).slice(0, max);
const pairs = (v, max, a = 300, b = 1500) => list(v, max).map(x => [S(x && x[0], a), S(x && x[1], b)]).filter(x => x[0] || x[1]);
const COMM = ['price_from', 'price_to', 'price_unit', 'price_basis', 'tiers', 'price_valid', 'in_stock', 'qty', 'ships_within', 'lot', 'pack_format', 'net_weight', 'packs_per_pallet', 'pallet_net', 'origin_region', 'supplier', 'last_audit'];

export function cleanProduct(p, errors, i) {
  const at = `Product ${i + 1}${p && p.name ? ' (' + S(p.name, 60) + ')' : ''}`;
  p = p || {};
  const o = {
    key: S(p.key, 40).toLowerCase(), slug: S(p.slug, 90).toLowerCase(), status: p.status === 'draft' ? 'draft' : 'published', updated: S(p.updated, 30),
    name: S(p.name, 120), short: S(p.short, 60), common: S(p.common, 40), botanical: S(p.botanical, 120), part: S(p.part, 60), tag: S(p.tag, 60),
    unit_mode: p.unit_mode === 'drum' ? 'drum' : 'kg', box: S(p.box, 60), title: S(p.title, 120), meta: S(p.meta, 320), h1: S(p.h1, 160), lead: S(p.lead, 700), card: S(p.card, 300),
    desc: list(p.desc, 12).map(x => S(x, 2500)).filter(Boolean), specs: pairs(p.specs, 40), purity: list(p.purity, 20).map(x => S(x, 200)).filter(Boolean),
    ttk_sub: S(p.ttk_sub, 300), ttk: pairs(p.ttk, 12), faq: pairs(p.faq, 30, 300, 2000), plant: S(p.plant, 200), look: S(p.look, 200), alt: S(p.alt, 200),
    image: { src: p.image && p.image.src === 'kv' ? 'kv' : 'static', id: S(p.image && p.image.id, 40).replace(/[^a-f0-9]/g, '') },
    seo: { canonical: S(p.seo && p.seo.canonical, 300), noindex: !!(p.seo && p.seo.noindex), og_title: S(p.seo && p.seo.og_title, 120), og_desc: S(p.seo && p.seo.og_desc, 300), focus_keyword: S(p.seo && p.seo.focus_keyword, 80) },
    commercial: {}, tests: list(p.tests, 60).map(t => ({ param: S(t && t.param, 150), limit: S(t && t.limit, 200), method: S(t && t.method, 200), result: S(t && t.result, 200) })).filter(t => t.param || t.limit || t.result),
  };
  for (const k of COMM) o.commercial[k] = S(p.commercial && p.commercial[k], k === 'tiers' ? 800 : 200);
  if (!KEY.test(o.key) || o.key.length < 2) errors.push(`${at}: the internal key must be lowercase letters, numbers and hyphens (2+ characters).`);
  if (!SLUG.test(o.slug) || o.slug.length < 3) errors.push(`${at}: the URL slug must be lowercase letters, numbers and hyphens (3+ characters).`);
  if (!o.name) errors.push(`${at}: a product name is required.`);
  if (!o.short) o.short = o.name.slice(0, 60);
  if (!o.common) o.common = o.short.split(' ')[0].toLowerCase();
  if (o.seo.canonical && !isUrl(o.seo.canonical)) errors.push(`${at}: canonical URL must start with https://`);
  return o;
}

export function cleanData(d) {
  const errors = []; d = d || {};
  const st = d.settings || {}; const addr = a => ({ name: S(a && a.name, 80), street: S(a && a.street, 120), city: S(a && a.city, 80), state: S(a && a.state, 40), zip: S(a && a.zip, 20) });
  const settings = { phone: S(st.phone, 40), phone2: S(st.phone2, 40), email: S(st.email, 120).toLowerCase(), hours: S(st.hours, 120), response: S(st.response, 80), moq: S(st.moq, 40), lead_time: S(st.lead_time, 200),
    parent: S(st.parent, 120), booking_url: S(st.booking_url, 300), show: S(st.show, 400), ga4: S(st.ga4, 30), turnstile: S(st.turnstile, 80), gsc_verification: S(st.gsc_verification, 120),
    warehouse: addr(st.warehouse), office: addr(st.office), same_as: list(st.same_as, 10).map(x => S(x, 300)).filter(Boolean), robots_extra: S(st.robots_extra, 800) };
  if (settings.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(settings.email)) errors.push('Settings: the sales email is not a valid address.');
  if (settings.ga4 && !/^G-[A-Z0-9]{4,14}$/.test(settings.ga4)) errors.push('Settings: Google Analytics ID looks like G-XXXXXXXXXX.');
  if (!isUrl(settings.booking_url)) errors.push('Settings: booking link must start with https://');
  for (const u of settings.same_as) if (!isUrl(u)) errors.push('Settings: social profile links must start with https://');
  const products = list(d.products, 200).map((p, i) => cleanProduct(p, errors, i));
  const keys = new Set(), slugs = new Set();
  for (const p of products) {
    if (keys.has(p.key)) errors.push(`Two products share the key "${p.key}".`); keys.add(p.key);
    if (slugs.has(p.slug)) errors.push(`Two products share the URL slug "${p.slug}".`); slugs.add(p.slug);
  }
  const company = {}; for (const [k, v] of Object.entries(d.company || {}).slice(0, 80)) { const val = S(v, 3000); if (S(k, 100) && val) company[S(k, 100)] = val; }
  const certs = list(d.certs, 40).map(c => ({ name: S(c && c.name, 100), applies: S(c && c.applies, 200), holder: S(c && c.holder, 120), htype: S(c && c.htype, 60), certifier: S(c && c.certifier, 160), number: S(c && c.number, 80), expiry: S(c && c.expiry, 30), url: S(c && c.url, 400) })).filter(c => c.name);
  for (const c of certs) if (!isUrl(c.url)) errors.push(`Certificate "${c.name}": verification link must start with https://`);
  const transit = list(d.transit, 80).map(t => ({ state: S(t && t.state, 60), region: S(t && t.region, 30), ltl: S(t && t.ltl, 30), ftl: S(t && t.ftl, 30), note: S(t && t.note, 200) })).filter(t => t.state);
  const pages = {};
  for (const [path, v] of Object.entries(d.pages || {}).slice(0, 60)) {
    if (!/^\/([a-z0-9-]+\/)*$/.test(path)) continue;
    const o = { title: S(v && v.title, 120), description: S(v && v.description, 320), og_title: S(v && v.og_title, 120), og_desc: S(v && v.og_desc, 300), canonical: S(v && v.canonical, 300), noindex: !!(v && v.noindex) };
    if (!isUrl(o.canonical)) errors.push(`Page ${path}: canonical must start with https://`);
    if (o.title || o.description || o.og_title || o.og_desc || o.canonical || o.noindex) pages[path] = o;
  }
  const redirects = list(d.redirects, 300).map(r => ({ from: S(r && r.from, 300), to: S(r && r.to, 400) })).filter(r => r.from && r.to);
  for (const r of redirects) { if (!r.from.startsWith('/') || /\s/.test(r.from)) errors.push(`Redirect "${r.from}": the old URL must start with / and have no spaces.`); if (!(r.to.startsWith('/') || /^https?:\/\//.test(r.to)) || /\s/.test(r.to)) errors.push(`Redirect to "${r.to}": must start with / or https://`); }
  return { ok: errors.length === 0, errors, data: { version: 1, updated: S(d.updated, 30), settings, company, certs, transit, pages, redirects, products } };
}

// ---------- storage ----------
const pad = n => String(n).padStart(8, '0');
export async function getMeta(env) { const m = await env.GP_KV.get('meta'); return m ? JSON.parse(m) : { rev: 0, publishedRev: 0, publishedAt: '' }; }
export async function getDraft(env) {
  const raw = await env.GP_KV.get('draft'); if (raw) return JSON.parse(raw);
  if (env.ASSETS) {   // first run: start from the seed data shipped with the site
    try { const r = await env.ASSETS.fetch(new Request('https://assets.local/admin/seed.json')); if (r.ok) { const seed = await r.json(); await env.GP_KV.put('draft', JSON.stringify(seed)); await env.GP_KV.put('published', JSON.stringify(seed)); return seed; } } catch {}
  }
  return null;
}
export async function saveDraft(env, data, meta, summary, nowIso) {
  const prev = await env.GP_KV.get('draft');
  if (prev) { await env.GP_KV.put('hist:' + pad(meta.rev), JSON.stringify({ rev: meta.rev, at: meta.savedAt || nowIso, summary: meta.summary || '', data: JSON.parse(prev) })); }
  meta.rev += 1; meta.savedAt = nowIso; meta.summary = summary || '';
  data.updated = nowIso.slice(0, 10);
  await env.GP_KV.put('draft', JSON.stringify(data)); await env.GP_KV.put('meta', JSON.stringify(meta));
  const l = await env.GP_KV.list({ prefix: 'hist:' }); const names = (l.keys || []).map(k => k.name).sort();
  for (const n of names.slice(0, Math.max(0, names.length - 30))) await env.GP_KV.delete(n);
  return meta;
}
export { S, pad };
