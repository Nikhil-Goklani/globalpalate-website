// GET /api/img/<id>  - uploaded product images (public, immutable).
export async function handleImg(id, env) {
  if (!env.GP_KV || !/^[a-f0-9]{24}$/.test(id)) return new Response('Not found', { status: 404 });
  const r = await env.GP_KV.getWithMetadata('img:' + id, 'arrayBuffer');
  if (!r || !r.value) return new Response('Not found', { status: 404 });
  return new Response(r.value, { headers: { 'Content-Type': (r.metadata && r.metadata.type) || 'image/jpeg', 'Cache-Control': 'public, max-age=31536000, immutable', 'X-Content-Type-Options': 'nosniff' } });
}
export const onRequestGet = ({ params, env }) => handleImg(params.id, env);
