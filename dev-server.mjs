// Local preview: serves ./out and runs the same Functions code as Cloudflare, with a JSON file as the KV store.
//   python3 build/build.py && node dev-server.mjs         ->  http://localhost:8788   (admin password: "admin", or set ADMIN_PASSWORD)
// "Publish" in the admin runs a real local rebuild using the published data, exactly like the Cloudflare build does.
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import { spawn } from 'node:child_process'; import { fileURLToPath } from 'node:url';
import { handleAdmin } from './functions/api/admin/[[path]].js'; import { handleExport } from './functions/api/export.js'; import { handleImg } from './functions/api/img/[id].js'; import { handleLead } from './functions/api/lead.js';
const ROOT = path.dirname(fileURLToPath(import.meta.url)), OUT = path.join(ROOT, 'out'), PORT = Number(process.env.PORT || 8788);
const STORE = process.env.DEV_KV_FILE || path.join(ROOT, '.dev-kv.json');
const mem = new Map(); try { for (const [k, v] of Object.entries(JSON.parse(fs.readFileSync(STORE)))) mem.set(k, v.bin ? { v: Buffer.from(v.v, 'base64').buffer.slice(0), meta: v.meta } : v); } catch {}
const persist = () => { const o = {}; for (const [k, v] of mem) o[k] = v.v instanceof ArrayBuffer ? { bin: 1, v: Buffer.from(v.v).toString('base64'), meta: v.meta } : v; fs.writeFileSync(STORE, JSON.stringify(o)); };
const KV = { async get(k, t) { const v = mem.get(k); if (!v) return null; return t === 'arrayBuffer' ? v.v : (typeof v.v === 'string' ? v.v : null); }, async getWithMetadata(k) { const v = mem.get(k); return v ? { value: v.v, metadata: v.meta } : { value: null }; },
  async put(k, v, o = {}) { mem.set(k, { v, meta: o.metadata }); persist(); }, async delete(k) { mem.delete(k); persist(); }, async list({ prefix = '' } = {}) { return { keys: [...mem.keys()].filter(k => k.startsWith(prefix)).map(name => ({ name })) }; } };
const env = { GP_KV: KV, ADMIN_PASSWORD: process.env.ADMIN_PASSWORD || 'admin', BUILD_TOKEN: process.env.BUILD_TOKEN || 'dev-build-token', DEPLOY_HOOK_URL: 'local://build',
  ASSETS: { fetch: async () => new Response(fs.readFileSync(path.join(OUT, 'admin', 'seed.json')), { status: 200 }) } };
let building = false, lastBuild = '';
function localBuild() {
  if (building) return; building = true;
  const p = spawn('python3', [path.join(ROOT, 'build', 'build.py')], { cwd: ROOT, env: { ...process.env, EXPORT_URL: `http://localhost:${PORT}/api/export`, BUILD_TOKEN: env.BUILD_TOKEN } });
  let log = ''; p.stdout.on('data', d => log += d); p.stderr.on('data', d => log += d); p.on('close', c => { building = false; lastBuild = `exit ${c}\n` + log; console.log('[build]', lastBuild.split('\n').slice(0, 6).join(' | ')); });
}
const hookFetch = async (url) => { if (url === 'local://build') { setTimeout(localBuild, 50); return new Response('{}', { status: 200 }); } return new Response('', { status: 500 }); };
const MIME = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.xml': 'application/xml', '.txt': 'text/plain', '.pdf': 'application/pdf' };
http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const chunks = []; for await (const c of req) chunks.push(c); const body = Buffer.concat(chunks);
    const mk = () => new Request(url, { method: req.method, headers: req.headers, body: ['GET', 'HEAD'].includes(req.method) ? undefined : body });
    let r = null;
    if (url.pathname.startsWith('/api/admin')) r = await handleAdmin(mk(), env, Date.now(), hookFetch);
    else if (url.pathname === '/api/export') r = await handleExport(mk(), env);
    else if (url.pathname.startsWith('/api/img/')) r = await handleImg(url.pathname.split('/').pop(), env);
    else if (url.pathname === '/api/lead') r = await handleLead(mk(), {});
    else if (url.pathname === '/__build-status') r = new Response(JSON.stringify({ building, lastBuild }), { headers: { 'Content-Type': 'application/json' } });
    if (r) { res.writeHead(r.status, Object.fromEntries(r.headers)); return res.end(Buffer.from(await r.arrayBuffer())); }
    let f = path.normalize(path.join(OUT, decodeURIComponent(url.pathname))); if (!f.startsWith(OUT)) { res.writeHead(403); return res.end(); }
    if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
    if (!fs.existsSync(f)) { res.writeHead(404, { 'Content-Type': 'text/html' }); return res.end(fs.existsSync(path.join(OUT, '404.html')) ? fs.readFileSync(path.join(OUT, '404.html')) : 'Not found'); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); res.end(fs.readFileSync(f));
  } catch (e) { console.error(e); res.writeHead(500); res.end('Server error'); }
}).listen(PORT, () => console.log(`Preview: http://localhost:${PORT}   Admin: http://localhost:${PORT}/admin/   (password: ${env.ADMIN_PASSWORD})`));
