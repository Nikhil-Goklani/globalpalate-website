// Admin API: /api/admin/*  (login, data, upload, publish, history)
import { json, S, safeEq, makeSession, checkSession, rateLimit, cleanData, getMeta, getDraft, saveDraft, pad } from '../../_shared/core.js';

const MAX_IMG = 4 * 1024 * 1024, MAX_JSON = 1_500_000;
function imageType(b) {
  const u = new Uint8Array(b.slice(0, 12));
  if (u[0] === 0xFF && u[1] === 0xD8 && u[2] === 0xFF) return 'image/jpeg';
  if (u[0] === 0x89 && u[1] === 0x50 && u[2] === 0x4E && u[3] === 0x47) return 'image/png';
  if (u[0] === 0x52 && u[1] === 0x49 && u[2] === 0x46 && u[3] === 0x46 && u[8] === 0x57 && u[9] === 0x45 && u[10] === 0x42 && u[11] === 0x50) return 'image/webp';
  return '';
}
function summarize(prev, next) {
  const bits = []; const pk = Object.fromEntries((prev && prev.products || []).map(p => [p.key, p]));
  const nk = Object.fromEntries(next.products.map(p => [p.key, p]));
  for (const k in nk) if (!pk[k]) bits.push('added ' + k); else if (JSON.stringify(pk[k]) !== JSON.stringify(nk[k])) bits.push('edited ' + k);
  for (const k in pk) if (!nk[k]) bits.push('deleted ' + k);
  for (const s of ['settings', 'company', 'certs', 'transit', 'pages', 'redirects']) if (prev && JSON.stringify(prev[s]) !== JSON.stringify(next[s])) bits.push('changed ' + s);
  return bits.slice(0, 8).join(', ') || 'saved';
}

export async function handleAdmin(request, env, now = Date.now(), fetchImpl = fetch) {
  const url = new URL(request.url);
  const path = url.pathname.replace(/^\/api\/admin\/?/, '').replace(/\/$/, '');
  const method = request.method;
  if (!env.GP_KV) return json({ ok: false, error: 'Storage is not configured. Bind a KV namespace named GP_KV.' }, 503);
  if (!(env.ADMIN_PASSWORD || '').length) return json({ ok: false, error: 'ADMIN_PASSWORD is not set.' }, 503);
  if (method !== 'GET') {   // CSRF: same-origin + custom header
    const origin = request.headers.get('Origin');
    if (origin && new URL(origin).host !== url.host) return json({ ok: false, error: 'Origin not allowed.' }, 403);
    if (request.headers.get('X-GP-Admin') !== '1') return json({ ok: false, error: 'Missing admin header.' }, 403);
  }
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  if (path === 'login' && method === 'POST') {
    if (!(await rateLimit(env, 'login:' + ip, 8, 900, now))) return json({ ok: false, error: 'Too many attempts. Try again in 15 minutes.' }, 429);
    let b; try { b = await request.json(); } catch { return json({ ok: false, error: 'Invalid request.' }, 400); }
    if (!safeEq(S(b.password, 200), env.ADMIN_PASSWORD)) return json({ ok: false, error: 'Wrong password.' }, 401);
    const tok = await makeSession(env, now); const secure = url.protocol === 'https:' ? ' Secure;' : '';
    return json({ ok: true }, 200, { 'Set-Cookie': `gp_admin=${tok}; HttpOnly;${secure} SameSite=Strict; Path=/; Max-Age=28800` });
  }
  if (path === 'logout' && method === 'POST') return json({ ok: true }, 200, { 'Set-Cookie': 'gp_admin=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0' });
  const authed = await checkSession(env, request, now);
  if (path === 'me') return json({ ok: true, authed });
  if (!authed) return json({ ok: false, error: 'Please sign in.' }, 401);

  if (path === 'data' && method === 'GET') {
    const data = await getDraft(env); const meta = await getMeta(env);
    if (!data) return json({ ok: false, error: 'No data found. Deploy with admin/seed.json or restore from history.' }, 404);
    const pub = await env.GP_KV.get('published');
    return json({ ok: true, data, rev: meta.rev, published: { rev: meta.publishedRev, at: meta.publishedAt, same: pub ? JSON.stringify(JSON.parse(pub)) === JSON.stringify(data) : false }, hook: !!env.DEPLOY_HOOK_URL });
  }
  if (path === 'data' && method === 'PUT') {
    const text = await request.text(); if (text.length > MAX_JSON) return json({ ok: false, error: 'Data too large.' }, 413);
    let b; try { b = JSON.parse(text); } catch { return json({ ok: false, error: 'Invalid JSON.' }, 400); }
    const meta = await getMeta(env);
    if (Number(b.baseRev) !== meta.rev) return json({ ok: false, error: 'Someone else saved newer changes. Reload the admin to get them before saving.', conflict: true, rev: meta.rev }, 409);
    const c = cleanData(b.data);
    if (!c.ok) return json({ ok: false, error: c.errors[0], errors: c.errors }, 400);
    const prev = await getDraft(env);
    const m = await saveDraft(env, c.data, meta, summarize(prev, c.data), new Date(now).toISOString());
    return json({ ok: true, rev: m.rev, data: c.data });
  }
  if (path === 'upload' && method === 'POST') {
    const buf = await request.arrayBuffer();
    if (!buf.byteLength || buf.byteLength > MAX_IMG) return json({ ok: false, error: 'Image must be under 4 MB.' }, 413);
    const type = imageType(buf); if (!type) return json({ ok: false, error: 'Only JPEG, PNG or WebP images are accepted.' }, 400);
    const id = [...crypto.getRandomValues(new Uint8Array(12))].map(x => x.toString(16).padStart(2, '0')).join('');
    await env.GP_KV.put('img:' + id, buf, { metadata: { type } });
    return json({ ok: true, id, url: '/api/img/' + id });
  }
  if (path === 'publish' && method === 'POST') {
    const draft = await env.GP_KV.get('draft'); if (!draft) return json({ ok: false, error: 'Nothing to publish.' }, 400);
    const c = cleanData(JSON.parse(draft)); if (!c.ok) return json({ ok: false, error: 'Fix this before publishing: ' + c.errors[0] }, 400);
    const meta = await getMeta(env);
    await env.GP_KV.put('published', JSON.stringify(c.data));
    meta.publishedRev = meta.rev; meta.publishedAt = new Date(now).toISOString(); await env.GP_KV.put('meta', JSON.stringify(meta));
    let triggered = false, hookError = '';
    if (env.DEPLOY_HOOK_URL) { try { const r = await fetchImpl(env.DEPLOY_HOOK_URL, { method: 'POST' }); triggered = r.ok; if (!r.ok) hookError = 'The deploy hook returned ' + r.status; } catch { hookError = 'Could not reach the deploy hook.'; } }
    return json({ ok: true, published: true, triggered, hookError, note: triggered ? 'Build started. Changes go live in about 1-2 minutes.' : (env.DEPLOY_HOOK_URL ? hookError : 'Saved as the published version, but no DEPLOY_HOOK_URL is set, so the site was not rebuilt automatically.') });
  }
  if (path === 'history' && method === 'GET') {
    const l = await env.GP_KV.list({ prefix: 'hist:' }); const out = [];
    for (const k of (l.keys || []).map(k => k.name).sort().reverse()) { const r = JSON.parse(await env.GP_KV.get(k)); out.push({ id: k.slice(5), rev: r.rev, at: r.at, summary: r.summary }); }
    return json({ ok: true, items: out });
  }
  if (path === 'history/restore' && method === 'POST') {
    let b; try { b = await request.json(); } catch { return json({ ok: false, error: 'Invalid request.' }, 400); }
    const raw = await env.GP_KV.get('hist:' + S(b.id, 20).replace(/[^0-9]/g, '')); if (!raw) return json({ ok: false, error: 'Version not found.' }, 404);
    const meta = await getMeta(env); const c = cleanData(JSON.parse(raw).data);
    const m = await saveDraft(env, c.data, meta, 'restored version ' + S(b.id, 20), new Date(now).toISOString());
    return json({ ok: true, rev: m.rev });
  }
  return json({ ok: false, error: 'Not found.' }, 404);
}
export const onRequest = ({ request, env }) => handleAdmin(request, env);
