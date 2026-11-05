import assert from 'node:assert/strict';
import fs from 'node:fs';
import { handleAdmin } from '../functions/api/admin/[[path]].js';
import { handleExport } from '../functions/api/export.js';
import { handleImg } from '../functions/api/img/[id].js';
import { cleanData } from '../functions/_shared/core.js';

class KV { constructor() { this.m = new Map(); }
  async get(k, t) { const v = this.m.get(k); if (!v) return null; return t === 'arrayBuffer' ? v.v : (typeof v.v === 'string' ? v.v : null); }
  async getWithMetadata(k, t) { const v = this.m.get(k); return v ? { value: v.v, metadata: v.meta } : { value: null }; }
  async put(k, v, o = {}) { this.m.set(k, { v, meta: o.metadata }); } async delete(k) { this.m.delete(k); }
  async list({ prefix = '' } = {}) { return { keys: [...this.m.keys()].filter(k => k.startsWith(prefix)).map(name => ({ name })) }; } }
const seed = JSON.parse(fs.readFileSync(new URL('../data/site-data.json', import.meta.url)));
const ASSETS = { fetch: async () => new Response(JSON.stringify(seed), { status: 200 }) };
const env = { GP_KV: new KV(), ADMIN_PASSWORD: 'correct horse battery', BUILD_TOKEN: 'tok-123', ASSETS, DEPLOY_HOOK_URL: 'https://hook.example/deploy' };
let ipn = 0, NOW = 1_800_000_000_000;
const req = (path, { method = 'GET', body, headers = {}, cookie, raw } = {}) => new Request('https://globalpalate.co/api/admin/' + path, { method, headers: { 'CF-Connecting-IP': '5.5.5.' + (++ipn), ...(method !== 'GET' ? { 'X-GP-Admin': '1' } : {}), ...(cookie ? { Cookie: cookie } : {}), ...headers }, body: raw !== undefined ? raw : (body ? JSON.stringify(body) : undefined) });
const call = (r, now = NOW, f) => handleAdmin(r, env, now, f);

// unauthenticated
let r = await call(req('data')); assert.equal(r.status, 401, 'data needs login');
r = await call(req('me')); assert.equal((await r.json()).authed, false);
// csrf
r = await call(new Request('https://globalpalate.co/api/admin/login', { method: 'POST', body: '{"password":"x"}' })); assert.equal(r.status, 403, 'missing X-GP-Admin header refused');
r = await call(req('login', { method: 'POST', body: { password: 'x' }, headers: { Origin: 'https://evil.example' } })); assert.equal(r.status, 403, 'cross-origin refused');
// wrong password, then right
r = await call(req('login', { method: 'POST', body: { password: 'nope' } })); assert.equal(r.status, 401);
r = await call(req('login', { method: 'POST', body: { password: env.ADMIN_PASSWORD } })); assert.equal(r.status, 200);
const sc = r.headers.get('Set-Cookie'); assert.match(sc, /HttpOnly/); assert.match(sc, /SameSite=Strict/); assert.match(sc, /Secure/);
const cookie = sc.split(';')[0];
r = await call(req('me', { cookie })); assert.equal((await r.json()).authed, true);
// tampered / expired cookie
r = await call(req('data', { cookie: cookie.slice(0, -2) + 'aa' })); assert.equal(r.status, 401, 'tampered cookie');
r = await call(req('data', { cookie }), NOW + 9 * 3600 * 1000); assert.equal(r.status, 401, 'expired cookie');
// login rate limit (same ip)
const sameIp = () => new Request('https://globalpalate.co/api/admin/login', { method: 'POST', headers: { 'X-GP-Admin': '1', 'CF-Connecting-IP': '7.7.7.7' }, body: '{"password":"bad"}' });
let last; for (let i = 0; i < 9; i++) last = await call(sameIp()); assert.equal(last.status, 429, 'login rate limited');

// data: first load seeds from ASSETS
r = await call(req('data', { cookie })); let j = await r.json(); assert.equal(j.ok, true); assert.equal(j.data.products.length, seed.products.length); assert.equal(j.rev, 0);
assert.equal(j.hook, true);
// edit a product
const d = structuredClone(j.data); d.products[0].title = 'New SEO title for turmeric'; d.products[0].commercial.price_from = '5.5';
r = await call(req('data', { method: 'PUT', cookie, body: { data: d, baseRev: 0 } })); j = await r.json(); assert.equal(r.status, 200, JSON.stringify(j)); assert.equal(j.rev, 1);
assert.equal(j.data.products[0].title, 'New SEO title for turmeric');
// conflict
r = await call(req('data', { method: 'PUT', cookie, body: { data: d, baseRev: 0 } })); assert.equal(r.status, 409, 'stale baseRev -> conflict');
// validation: duplicate slug, bad slug, bad url, missing name
const bad = structuredClone(d); bad.products[1].slug = bad.products[0].slug;
r = await call(req('data', { method: 'PUT', cookie, body: { data: bad, baseRev: 1 } })); j = await r.json(); assert.equal(r.status, 400); assert.match(j.error, /share the URL slug/);
const bad2 = structuredClone(d); bad2.products[0].slug = 'Bad Slug!'; r = await call(req('data', { method: 'PUT', cookie, body: { data: bad2, baseRev: 1 } })); assert.equal(r.status, 400);
const bad3 = structuredClone(d); bad3.certs[0].url = 'javascript:alert(1)'; r = await call(req('data', { method: 'PUT', cookie, body: { data: bad3, baseRev: 1 } })); j = await r.json(); assert.equal(r.status, 400); assert.match(j.error, /https/);
const bad4 = structuredClone(d); bad4.products[0].name = ''; r = await call(req('data', { method: 'PUT', cookie, body: { data: bad4, baseRev: 1 } })); assert.equal(r.status, 400);
const bad5 = structuredClone(d); bad5.settings.ga4 = 'UA-12'; r = await call(req('data', { method: 'PUT', cookie, body: { data: bad5, baseRev: 1 } })); assert.equal(r.status, 400);
// add + delete a product
const d2 = structuredClone(d); d2.products.push({ key: 'black-pepper', slug: 'organic-black-pepper', name: 'Organic Black Pepper', short: 'Black Pepper', status: 'draft' }); d2.products = d2.products.filter(p => p.key !== 'arrowroot');
r = await call(req('data', { method: 'PUT', cookie, body: { data: d2, baseRev: 1 } })); j = await r.json(); assert.equal(r.status, 200, JSON.stringify(j)); assert.equal(j.data.products.at(-1).common, 'black');
assert.equal(j.data.products.find(p => p.key === 'arrowroot'), undefined);
// html in text is stored as text (escaped at build time), control chars stripped
const d3 = structuredClone(j.data); d3.products[0].lead = 'Hello\u0000 <b>bold</b>'; r = await call(req('data', { method: 'PUT', cookie, body: { data: d3, baseRev: j.rev } })); j = await r.json(); assert.equal(j.data.products[0].lead, 'Hello <b>bold</b>');
// history + restore
r = await call(req('history', { cookie })); let h = await r.json(); assert.ok(h.items.length >= 3); assert.match(h.items.map(i => i.summary).join('|'), /edited turmeric|added black-pepper|deleted arrowroot/);
const oldest = h.items.at(-1); r = await call(req('history/restore', { method: 'POST', cookie, body: { id: oldest.id } })); j = await r.json(); assert.equal(r.status, 200);
r = await call(req('data', { cookie })); j = await r.json(); assert.ok(j.data.products.find(p => p.key === 'arrowroot'), 'restore brings arrowroot back');
// upload
const png = new Uint8Array([0x89, 0x50, 0x4E, 0x47, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3]);
r = await call(req('upload', { method: 'POST', cookie, raw: png })); j = await r.json(); assert.equal(r.status, 200); assert.match(j.id, /^[a-f0-9]{24}$/);
let ir = await handleImg(j.id, env); assert.equal(ir.status, 200); assert.equal(ir.headers.get('Content-Type'), 'image/png');
r = await call(req('upload', { method: 'POST', cookie, raw: new TextEncoder().encode('<script>alert(1)</script>') })); assert.equal(r.status, 400, 'non-image rejected');
r = await call(req('upload', { method: 'POST', cookie, raw: new Uint8Array(5 * 1024 * 1024) })); assert.equal(r.status, 413, 'too big');
assert.equal((await handleImg('../etc/passwd', env)).status, 404);
// export before publish uses seed-published, with token
let er = await handleExport(new Request('https://x/api/export'), env); assert.equal(er.status, 401);
er = await handleExport(new Request('https://x/api/export', { headers: { Authorization: 'Bearer wrong' } }), env); assert.equal(er.status, 401);
// publish: only draft changes after publish appear in export
r = await call(req('data', { cookie })); j = await r.json(); const d4 = structuredClone(j.data); d4.products[0].title = 'Published title v1';
r = await call(req('data', { method: 'PUT', cookie, body: { data: d4, baseRev: j.rev } })); j = await r.json();
let hookCalled = 0; const fakeFetch = async (u, o) => { hookCalled++; assert.equal(u, env.DEPLOY_HOOK_URL); assert.equal(o.method, 'POST'); return new Response('{}', { status: 200 }); };
r = await call(req('publish', { method: 'POST', cookie, body: {} }), NOW, fakeFetch); j = await r.json(); assert.equal(j.ok, true); assert.equal(j.triggered, true); assert.equal(hookCalled, 1);
const d5 = structuredClone(d4); d5.products[0].title = 'Draft only title v2';
r = await call(req('data', { cookie })); j = await r.json(); r = await call(req('data', { method: 'PUT', cookie, body: { data: d5, baseRev: j.rev } }));
er = await handleExport(new Request('https://x/api/export', { headers: { Authorization: 'Bearer tok-123' } }), env); const exp = await er.json();
assert.equal(exp.products[0].title, 'Published title v1', 'export returns published snapshot, not the draft');
r = await call(req('data', { cookie })); j = await r.json(); assert.equal(j.published.same, false);
// hook failure is reported, not hidden
r = await call(req('publish', { method: 'POST', cookie, body: {} }), NOW, async () => new Response('', { status: 500 })); j = await r.json(); assert.equal(j.ok, true); assert.equal(j.triggered, false); assert.match(j.hookError, /500/);
// cleanData unit
assert.equal(cleanData({ products: [{ key: 'a', slug: 'bb', name: 'x' }] }).ok, false);
// no password configured -> locked
r = await handleAdmin(req('me'), { GP_KV: new KV() }, NOW); assert.equal(r.status, 503);
console.log('ALL ADMIN API TESTS PASSED');
