<?php
// GET /api/export - the published data for the site build. Needs "Authorization: Bearer <BUILD_TOKEN>".
require __DIR__ . '/_core.php';
$cfg = gp_cfg(); $want = (string)($cfg['BUILD_TOKEN'] ?? '');
if ($want === '') jout(['ok' => false, 'error' => 'Not configured.'], 503);
$h = $_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? '';
if ($h === '' && function_exists('getallheaders')) foreach (getallheaders() as $k => $v) if (strtolower($k) === 'authorization') $h = $v;
$tok = trim(preg_replace('/^Bearer\s+/i', '', $h));
if (!hash_equals($want, $tok)) jout(['ok' => false, 'error' => 'Unauthorized.'], 401);
gp_dir(); get_draft_raw();   // makes sure the seed exists on first run
$pub = gp_read('published.json');
if ($pub === null) jout(['ok' => false, 'error' => 'Nothing published yet.'], 404);
jout($pub);
