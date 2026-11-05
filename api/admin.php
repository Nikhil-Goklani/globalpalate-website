<?php
// Admin API (PHP port of functions/api/admin/[[path]].js). Routed from /api/admin/<path> by .htaccess.
require __DIR__ . '/_core.php';
const MAX_IMG = 4 * 1024 * 1024, MAX_JSON = 1500000;
function image_type($b) {
    if (strlen($b) < 12) return '';
    if (substr($b, 0, 3) === "\xFF\xD8\xFF") return 'image/jpeg';
    if (substr($b, 0, 4) === "\x89PNG") return 'image/png';
    if (substr($b, 0, 4) === 'RIFF' && substr($b, 8, 4) === 'WEBP') return 'image/webp';
    return '';
}
function summarize($prev, $next) {
    $bits = []; $pk = []; $nk = [];
    foreach ((is_array($prev) ? ($prev['products'] ?? []) : []) as $p) $pk[$p['key'] ?? ''] = $p;
    foreach ($next['products'] as $p) $nk[$p['key']] = $p;
    foreach ($nk as $k => $p) { if (!isset($pk[$k])) $bits[] = 'added ' . $k; elseif (enc($pk[$k]) !== enc($p)) $bits[] = 'edited ' . $k; }
    foreach ($pk as $k => $p) if (!isset($nk[$k])) $bits[] = 'deleted ' . $k;
    foreach (['settings', 'company', 'certs', 'transit', 'pages', 'redirects'] as $s) if (is_array($prev) && enc($prev[$s] ?? null) !== enc($next[$s])) $bits[] = 'changed ' . $s;
    return implode(', ', array_slice($bits, 0, 8)) ?: 'saved';
}
$now = (int)round(microtime(true) * 1000); $method = $_SERVER['REQUEST_METHOD'];
$path = trim((string)($_GET['path'] ?? ''), '/'); $cfg = gp_cfg();
if (empty($cfg['ADMIN_PASSWORD'])) jout(['ok' => false, 'error' => 'ADMIN_PASSWORD is not set. Create gp-config.php above public_html (see HOSTINGER-SETUP.md).'], 503);
gp_dir();
if ($method !== 'GET') {   // CSRF: same-origin + custom header
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    if ($origin !== '' && parse_url($origin, PHP_URL_HOST) !== parse_url('//' . ($_SERVER['HTTP_HOST'] ?? ''), PHP_URL_HOST)) jout(['ok' => false, 'error' => 'Origin not allowed.'], 403);
    if (($_SERVER['HTTP_X_GP_ADMIN'] ?? '') !== '1') jout(['ok' => false, 'error' => 'Missing admin header.'], 403);
}
$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
if ($path === 'login' && $method === 'POST') {
    if (!gp_rate('login:' . $ip, 8, 900)) jout(['ok' => false, 'error' => 'Too many attempts. Try again in 15 minutes.'], 429);
    $b = json_decode(file_get_contents('php://input'), true); if (!is_array($b)) jout(['ok' => false, 'error' => 'Invalid request.'], 400);
    if (!hash_equals((string)$cfg['ADMIN_PASSWORD'], S($b['password'] ?? '', 200))) jout(['ok' => false, 'error' => 'Wrong password.'], 401);
    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') || ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https' ? ' Secure;' : '';
    jout(['ok' => true], 200, ['Set-Cookie: gp_admin=' . gp_make_session($now) . '; HttpOnly;' . $secure . ' SameSite=Strict; Path=/; Max-Age=28800']);
}
if ($path === 'logout' && $method === 'POST') jout(['ok' => true], 200, ['Set-Cookie: gp_admin=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0']);
$authed = gp_check_session($now);
if ($path === 'me') jout(['ok' => true, 'authed' => $authed]);
if (!$authed) jout(['ok' => false, 'error' => 'Please sign in.'], 401);

if ($path === 'data' && $method === 'GET') {
    $draft = get_draft_raw(); $meta = get_meta();
    if ($draft === null) jout(['ok' => false, 'error' => 'No data found. Make sure admin/seed.json was deployed, or restore from history.'], 404);
    $pub = gp_read('published.json');
    jout('{"ok":true,"data":' . $draft . ',"rev":' . (int)$meta['rev'] . ',"published":{"rev":' . (int)$meta['publishedRev'] . ',"at":' . enc($meta['publishedAt']) . ',"same":' . ($pub !== null && $pub === $draft ? 'true' : 'false') . '},"hook":' . (!empty($cfg['GITHUB_TOKEN']) ? 'true' : 'false') . '}');
}
if ($path === 'data' && $method === 'PUT') {
    $text = file_get_contents('php://input'); if (strlen($text) > MAX_JSON) jout(['ok' => false, 'error' => 'Data too large.'], 413);
    $b = json_decode($text, true); if (!is_array($b)) jout(['ok' => false, 'error' => 'Invalid JSON.'], 400);
    $meta = get_meta();
    if ((float)($b['baseRev'] ?? -1) !== (float)$meta['rev']) jout(['ok' => false, 'error' => 'Someone else saved newer changes. Reload the admin to get them before saving.', 'conflict' => true, 'rev' => $meta['rev']], 409);
    $c = clean_data($b['data'] ?? null);
    if (!$c['ok']) jout(['ok' => false, 'error' => $c['errors'][0], 'errors' => $c['errors']], 400);
    $prevRaw = get_draft_raw(); $prev = $prevRaw ? json_decode($prevRaw, true) : null;
    $m = save_draft($c['data'], $meta, summarize($prev, json_decode(enc($c['data']), true)), gmdate('Y-m-d\TH:i:s') . '.000Z');
    jout('{"ok":true,"rev":' . (int)$m['rev'] . ',"data":' . gp_read('draft.json') . '}');
}
if ($path === 'upload' && $method === 'POST') {
    $buf = file_get_contents('php://input', false, null, 0, MAX_IMG + 1);
    if ($buf === '' || strlen($buf) > MAX_IMG) jout(['ok' => false, 'error' => 'Image must be under 4 MB.'], 413);
    $type = image_type($buf); if ($type === '') jout(['ok' => false, 'error' => 'Only JPEG, PNG or WebP images are accepted.'], 400);
    $id = bin2hex(random_bytes(12));
    gp_write('img/' . $id . '.bin', $buf); gp_write('img/' . $id . '.type', $type);
    jout(['ok' => true, 'id' => $id, 'url' => '/api/img/' . $id]);
}
if ($path === 'publish' && $method === 'POST') {
    $draft = gp_read('draft.json'); if ($draft === null) jout(['ok' => false, 'error' => 'Nothing to publish.'], 400);
    $c = clean_data(json_decode($draft, true)); if (!$c['ok']) jout(['ok' => false, 'error' => 'Fix this before publishing: ' . $c['errors'][0]], 400);
    $meta = get_meta();
    gp_write('published.json', $draft);   // draft is already cleaned data; byte-identical so "same" stays accurate
    $meta['publishedRev'] = $meta['rev']; $meta['publishedAt'] = gmdate('Y-m-d\TH:i:s') . '.000Z'; gp_write('meta.json', enc($meta));
    $err = ''; $triggered = !empty($cfg['GITHUB_TOKEN']) ? gh_dispatch($err) : false;
    jout(['ok' => true, 'published' => true, 'triggered' => $triggered, 'hookError' => $err,
        'note' => $triggered ? 'Build started. Changes go live in about 3-4 minutes.' : ($err ?: 'Saved as the published version, but the site was not rebuilt automatically.')]);
}
if ($path === 'history' && $method === 'GET') {
    $files = glob(gp_dir() . '/hist/*.json') ?: []; rsort($files); $out = [];
    foreach ($files as $f) { $r = json_decode(file_get_contents($f), true); if (is_array($r)) $out[] = ['id' => basename($f, '.json'), 'rev' => $r['rev'], 'at' => $r['at'], 'summary' => $r['summary']]; }
    jout(['ok' => true, 'items' => $out]);
}
if ($path === 'history/restore' && $method === 'POST') {
    $b = json_decode(file_get_contents('php://input'), true); if (!is_array($b)) jout(['ok' => false, 'error' => 'Invalid request.'], 400);
    $id = preg_replace('/[^0-9]/', '', S($b['id'] ?? '', 20)); $raw = $id !== '' ? gp_read('hist/' . $id . '.json') : null;
    if ($raw === null) jout(['ok' => false, 'error' => 'Version not found.'], 404);
    $meta = get_meta(); $r = json_decode($raw, true); $c = clean_data($r['data'] ?? null);
    $m = save_draft($c['data'], $meta, 'restored version ' . S($b['id'] ?? '', 20), gmdate('Y-m-d\TH:i:s') . '.000Z');
    jout(['ok' => true, 'rev' => $m['rev']]);
}
jout(['ok' => false, 'error' => 'Not found.'], 404);
