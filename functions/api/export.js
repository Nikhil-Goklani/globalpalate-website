// GET /api/export  - the published data, for the site build. Requires "Authorization: Bearer <BUILD_TOKEN>".
import { json, safeEq } from '../_shared/core.js';
export async function handleExport(request, env) {
  if (!env.GP_KV || !env.BUILD_TOKEN) return json({ ok: false, error: 'Not configured.' }, 503);
  const tok = (request.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
  if (!safeEq(tok, env.BUILD_TOKEN)) return json({ ok: false, error: 'Unauthorized.' }, 401);
  const pub = await env.GP_KV.get('published');
  if (!pub) return json({ ok: false, error: 'Nothing published yet.' }, 404);
  return new Response(pub, { headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
}
export const onRequestGet = ({ request, env }) => handleExport(request, env);
