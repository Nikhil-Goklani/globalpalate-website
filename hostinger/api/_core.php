<?php
// Shared helpers for the PHP admin API (port of functions/_shared/core.js). Not reachable from the web (see .htaccess).
function gp_cfg() {
    static $c = null; if ($c !== null) return $c; $c = [];
    foreach ([dirname($_SERVER['DOCUMENT_ROOT']) . '/gp-config.php', __DIR__ . '/config.php'] as $p) {
        if (is_file($p)) { $x = include $p; if (is_array($x)) { $c = $x; break; } }
    }
    return $c;
}
function gp_jflags() { return JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_INVALID_UTF8_SUBSTITUTE; }
function jout($o, $status = 200, $headers = []) {
    http_response_code($status); header('Content-Type: application/json; charset=utf-8'); header('Cache-Control: no-store');
    foreach ($headers as $h) header($h, false);
    echo is_string($o) ? $o : json_encode($o, gp_jflags()); exit;
}
function gp_dir() {
    static $d = null; if ($d !== null) return $d;
    $cfg = gp_cfg(); $d = rtrim($cfg['DATA_DIR'] ?? (dirname($_SERVER['DOCUMENT_ROOT']) . '/gp-data'), '/');
    foreach (['', '/hist', '/img', '/rl'] as $s) { if (!is_dir($d . $s) && !@mkdir($d . $s, 0750, true)) jout(['ok' => false, 'error' => 'Cannot create the data folder next to public_html. Check folder permissions or set DATA_DIR in gp-config.php.'], 503); }
    return $d;
}
function gp_read($f) { $p = gp_dir() . '/' . $f; return is_file($p) ? file_get_contents($p) : null; }
function gp_write($f, $s) { return file_put_contents(gp_dir() . '/' . $f, $s, LOCK_EX) !== false; }

// ---- sessions, CSRF, rate limit ----
function gp_secret() { $c = gp_cfg(); return (string)($c['ADMIN_SESSION_SECRET'] ?? $c['ADMIN_PASSWORD'] ?? ''); }
function gp_make_session($now) { $exp = $now + 8 * 3600 * 1000; return $exp . '.' . hash_hmac('sha256', 's.' . $exp, gp_secret()); }
function gp_check_session($now) {
    if (gp_secret() === '' || empty($_COOKIE['gp_admin'])) return false;
    $parts = explode('.', (string)$_COOKIE['gp_admin']); if (count($parts) !== 2 || !ctype_digit($parts[0]) || (float)$parts[0] < $now) return false;
    return hash_equals(hash_hmac('sha256', 's.' . $parts[0], gp_secret()), $parts[1]);
}
function gp_rate($key, $max, $windowSec) {
    $f = gp_dir() . '/rl/' . md5($key); $now = time();
    $hits = is_file($f) ? array_filter(array_map('intval', explode(',', (string)file_get_contents($f))), function ($t) use ($now, $windowSec) { return $t > $now - $windowSec; }) : [];
    if (count($hits) >= $max) return false; $hits[] = $now; file_put_contents($f, implode(',', $hits), LOCK_EX); return true;
}

// ---- sanitising (port of core.js: S, list, pairs, cleanProduct, cleanData) ----
function truthy($v) { return !($v === null || $v === false || $v === 0 || $v === 0.0 || $v === ''); }
function S($v, $max = 2000) {
    if (is_bool($v)) $v = $v ? 'true' : 'false'; elseif (is_int($v) || is_float($v)) $v = (string)$v; elseif (!is_string($v)) $v = '';
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', '', $v);
    $t = @preg_replace('/^[\p{Z}\s]+|[\p{Z}\s]+$/u', '', $v); if ($t !== null) $v = $t; else $v = trim($v);
    return mb_substr($v, 0, $max);
}
function is_list_arr($v) { return is_array($v) && ($v === [] || array_keys($v) === range(0, count($v) - 1)); }
function lst($v, $max) { return is_list_arr($v) ? array_slice($v, 0, $max) : []; }
function at($v, $k) { return is_array($v) && array_key_exists($k, $v) ? $v[$k] : null; }
function nonempty($arr) { return array_values(array_filter($arr, function ($x) { return $x !== ''; })); }
function pairs($v, $max, $a = 300, $b = 1500) {
    $o = []; foreach (lst($v, $max) as $x) { $p = [S(at($x, 0), $a), S(at($x, 1), $b)]; if ($p[0] !== '' || $p[1] !== '') $o[] = $p; } return $o;
}
function is_url($u) { return $u === '' || preg_match('#^https?://\S+$#i', $u) === 1; }
const GP_COMM = ['price_from', 'price_to', 'price_unit', 'price_basis', 'tiers', 'price_valid', 'in_stock', 'qty', 'ships_within', 'lot', 'pack_format', 'net_weight', 'packs_per_pallet', 'pallet_net', 'origin_region', 'supplier', 'last_audit'];

function clean_product($p, &$errors, $i) {
    $p = is_array($p) ? $p : [];
    $at = 'Product ' . ($i + 1) . (S(at($p, 'name'), 60) !== '' ? ' (' . S(at($p, 'name'), 60) . ')' : '');
    $seo = at($p, 'seo'); $img = at($p, 'image'); $com = at($p, 'commercial');
    $o = [
        'key' => mb_strtolower(S(at($p, 'key'), 40)), 'slug' => mb_strtolower(S(at($p, 'slug'), 90)), 'status' => at($p, 'status') === 'draft' ? 'draft' : 'published', 'updated' => S(at($p, 'updated'), 30),
        'name' => S(at($p, 'name'), 120), 'short' => S(at($p, 'short'), 60), 'common' => S(at($p, 'common'), 40), 'botanical' => S(at($p, 'botanical'), 120), 'part' => S(at($p, 'part'), 60), 'tag' => S(at($p, 'tag'), 60),
        'unit_mode' => at($p, 'unit_mode') === 'drum' ? 'drum' : 'kg', 'box' => S(at($p, 'box'), 60), 'title' => S(at($p, 'title'), 120), 'meta' => S(at($p, 'meta'), 320), 'h1' => S(at($p, 'h1'), 160), 'lead' => S(at($p, 'lead'), 700), 'card' => S(at($p, 'card'), 300),
        'desc' => nonempty(array_map(function ($x) { return S($x, 2500); }, lst(at($p, 'desc'), 12))), 'specs' => pairs(at($p, 'specs'), 40),
        'purity' => nonempty(array_map(function ($x) { return S($x, 200); }, lst(at($p, 'purity'), 20))),
        'ttk_sub' => S(at($p, 'ttk_sub'), 300), 'ttk' => pairs(at($p, 'ttk'), 12), 'faq' => pairs(at($p, 'faq'), 30, 300, 2000), 'plant' => S(at($p, 'plant'), 200), 'look' => S(at($p, 'look'), 200), 'alt' => S(at($p, 'alt'), 200),
        'image' => ['src' => at($img, 'src') === 'kv' ? 'kv' : 'static', 'id' => preg_replace('/[^a-f0-9]/', '', S(at($img, 'id'), 40))],
        'seo' => ['canonical' => S(at($seo, 'canonical'), 300), 'noindex' => truthy(at($seo, 'noindex')), 'og_title' => S(at($seo, 'og_title'), 120), 'og_desc' => S(at($seo, 'og_desc'), 300), 'focus_keyword' => S(at($seo, 'focus_keyword'), 80)],
    ];
    $commercial = []; foreach (GP_COMM as $k) $commercial[$k] = S(at($com, $k), $k === 'tiers' ? 800 : 200);
    $o['commercial'] = (object)$commercial;
    $tests = [];
    foreach (lst(at($p, 'tests'), 60) as $t) { $r = ['param' => S(at($t, 'param'), 150), 'limit' => S(at($t, 'limit'), 200), 'method' => S(at($t, 'method'), 200), 'result' => S(at($t, 'result'), 200)]; if ($r['param'] !== '' || $r['limit'] !== '' || $r['result'] !== '') $tests[] = $r; }
    $o['tests'] = $tests;
    if (!preg_match('/^[a-z0-9]+(?:-[a-z0-9]+)*$/', $o['key']) || mb_strlen($o['key']) < 2) $errors[] = "$at: the internal key must be lowercase letters, numbers and hyphens (2+ characters).";
    if (!preg_match('/^[a-z0-9]+(?:-[a-z0-9]+)*$/', $o['slug']) || mb_strlen($o['slug']) < 3) $errors[] = "$at: the URL slug must be lowercase letters, numbers and hyphens (3+ characters).";
    if ($o['name'] === '') $errors[] = "$at: a product name is required.";
    if ($o['short'] === '') $o['short'] = mb_substr($o['name'], 0, 60);
    if ($o['common'] === '') $o['common'] = mb_strtolower(explode(' ', $o['short'])[0]);
    if ($o['seo']['canonical'] !== '' && !is_url($o['seo']['canonical'])) $errors[] = "$at: canonical URL must start with https://";
    return $o;
}
function clean_addr($a) { return ['name' => S(at($a, 'name'), 80), 'street' => S(at($a, 'street'), 120), 'city' => S(at($a, 'city'), 80), 'state' => S(at($a, 'state'), 40), 'zip' => S(at($a, 'zip'), 20)]; }
function clean_data($d) {
    $errors = []; $d = is_array($d) ? $d : []; $st = at($d, 'settings');
    $settings = ['phone' => S(at($st, 'phone'), 40), 'phone2' => S(at($st, 'phone2'), 40), 'email' => mb_strtolower(S(at($st, 'email'), 120)), 'hours' => S(at($st, 'hours'), 120), 'response' => S(at($st, 'response'), 80), 'moq' => S(at($st, 'moq'), 40), 'lead_time' => S(at($st, 'lead_time'), 200),
        'parent' => S(at($st, 'parent'), 120), 'booking_url' => S(at($st, 'booking_url'), 300), 'show' => S(at($st, 'show'), 400), 'ga4' => S(at($st, 'ga4'), 30), 'turnstile' => S(at($st, 'turnstile'), 80), 'gsc_verification' => S(at($st, 'gsc_verification'), 120),
        'warehouse' => clean_addr(at($st, 'warehouse')), 'office' => clean_addr(at($st, 'office')), 'same_as' => nonempty(array_map(function ($x) { return S($x, 300); }, lst(at($st, 'same_as'), 10))), 'robots_extra' => S(at($st, 'robots_extra'), 800)];
    if ($settings['email'] !== '' && !preg_match('/^[^\s@]+@[^\s@]+\.[^\s@]+$/', $settings['email'])) $errors[] = 'Settings: the sales email is not a valid address.';
    if ($settings['ga4'] !== '' && !preg_match('/^G-[A-Z0-9]{4,14}$/', $settings['ga4'])) $errors[] = 'Settings: Google Analytics ID looks like G-XXXXXXXXXX.';
    if (!is_url($settings['booking_url'])) $errors[] = 'Settings: booking link must start with https://';
    foreach ($settings['same_as'] as $u) if (!is_url($u)) $errors[] = 'Settings: social profile links must start with https://';
    $products = []; foreach (lst(at($d, 'products'), 200) as $i => $p) $products[] = clean_product($p, $errors, $i);
    $keys = []; $slugs = [];
    foreach ($products as $p) {
        if (isset($keys[$p['key']])) $errors[] = "Two products share the key \"{$p['key']}\"."; $keys[$p['key']] = 1;
        if (isset($slugs[$p['slug']])) $errors[] = "Two products share the URL slug \"{$p['slug']}\"."; $slugs[$p['slug']] = 1;
    }
    $company = []; $c = at($d, 'company');
    if (is_array($c)) foreach (array_slice($c, 0, 80, true) as $k => $v) { $val = S($v, 3000); $kk = S((string)$k, 100); if ($kk !== '' && $val !== '') $company[$kk] = $val; }
    $certs = [];
    foreach (lst(at($d, 'certs'), 40) as $x) { $r = ['name' => S(at($x, 'name'), 100), 'applies' => S(at($x, 'applies'), 200), 'holder' => S(at($x, 'holder'), 120), 'htype' => S(at($x, 'htype'), 60), 'certifier' => S(at($x, 'certifier'), 160), 'number' => S(at($x, 'number'), 80), 'expiry' => S(at($x, 'expiry'), 30), 'url' => S(at($x, 'url'), 400)]; if ($r['name'] !== '') $certs[] = $r; }
    foreach ($certs as $r) if (!is_url($r['url'])) $errors[] = "Certificate \"{$r['name']}\": verification link must start with https://";
    $transit = [];
    foreach (lst(at($d, 'transit'), 80) as $x) { $r = ['state' => S(at($x, 'state'), 60), 'region' => S(at($x, 'region'), 30), 'ltl' => S(at($x, 'ltl'), 30), 'ftl' => S(at($x, 'ftl'), 30), 'note' => S(at($x, 'note'), 200)]; if ($r['state'] !== '') $transit[] = $r; }
    $pages = []; $pg = at($d, 'pages');
    if (is_array($pg)) foreach (array_slice($pg, 0, 60, true) as $path => $v) {
        $path = (string)$path; if (!preg_match('#^/([a-z0-9-]+/)*$#', $path)) continue;
        $o = ['title' => S(at($v, 'title'), 120), 'description' => S(at($v, 'description'), 320), 'og_title' => S(at($v, 'og_title'), 120), 'og_desc' => S(at($v, 'og_desc'), 300), 'canonical' => S(at($v, 'canonical'), 300), 'noindex' => truthy(at($v, 'noindex'))];
        if (!is_url($o['canonical'])) $errors[] = "Page $path: canonical must start with https://";
        if ($o['title'] !== '' || $o['description'] !== '' || $o['og_title'] !== '' || $o['og_desc'] !== '' || $o['canonical'] !== '' || $o['noindex']) $pages[$path] = $o;
    }
    $redirects = [];
    foreach (lst(at($d, 'redirects'), 300) as $x) { $r = ['from' => S(at($x, 'from'), 300), 'to' => S(at($x, 'to'), 400)]; if ($r['from'] !== '' && $r['to'] !== '') $redirects[] = $r; }
    foreach ($redirects as $r) {
        if ($r['from'][0] !== '/' || preg_match('/\s/', $r['from'])) $errors[] = "Redirect \"{$r['from']}\": the old URL must start with / and have no spaces.";
        if (!($r['to'][0] === '/' || preg_match('#^https?://#', $r['to'])) || preg_match('/\s/', $r['to'])) $errors[] = "Redirect to \"{$r['to']}\": must start with / or https://";
    }
    return ['ok' => !$errors, 'errors' => $errors, 'data' => ['version' => 1, 'updated' => S(at($d, 'updated'), 30), 'settings' => $settings, 'company' => (object)$company, 'certs' => $certs, 'transit' => $transit, 'pages' => (object)$pages, 'redirects' => $redirects, 'products' => $products]];
}
function enc($v) { return json_encode($v, gp_jflags()); }

// ---- storage ----
function get_meta() { $m = gp_read('meta.json'); $a = $m ? json_decode($m, true) : null; return is_array($a) ? $a + ['rev' => 0, 'publishedRev' => 0, 'publishedAt' => ''] : ['rev' => 0, 'publishedRev' => 0, 'publishedAt' => '']; }
function get_draft_raw() {   // returns the raw JSON string of the draft (seeds from admin/seed.json on first run)
    $raw = gp_read('draft.json'); if ($raw !== null) return $raw;
    $sp = $_SERVER['DOCUMENT_ROOT'] . '/admin/seed.json';
    if (is_file($sp)) { $seed = json_decode(file_get_contents($sp), true); if (is_array($seed)) { $c = clean_data($seed); $s = enc($c['data']); gp_write('draft.json', $s); gp_write('published.json', $s); return $s; } }
    return null;
}
function save_draft($data, $meta, $summary, $nowIso) {
    $prev = gp_read('draft.json');
    if ($prev !== null) gp_write('hist/' . str_pad((string)$meta['rev'], 8, '0', STR_PAD_LEFT) . '.json', '{"rev":' . (int)$meta['rev'] . ',"at":' . enc($meta['savedAt'] ?? $nowIso) . ',"summary":' . enc($meta['summary'] ?? '') . ',"data":' . $prev . '}');
    $meta['rev'] = (int)$meta['rev'] + 1; $meta['savedAt'] = $nowIso; $meta['summary'] = $summary ?: '';
    $data['updated'] = substr($nowIso, 0, 10);
    gp_write('draft.json', enc($data)); gp_write('meta.json', enc($meta));
    $files = glob(gp_dir() . '/hist/*.json') ?: []; sort($files);
    foreach (array_slice($files, 0, max(0, count($files) - 30)) as $f) @unlink($f);
    return $meta;
}
function gh_dispatch(&$err) {
    $c = gp_cfg(); $repo = $c['GITHUB_REPO'] ?? ''; $tok = $c['GITHUB_TOKEN'] ?? '';
    if ($repo === '' || $tok === '') { $err = 'GITHUB_TOKEN / GITHUB_REPO are not set in gp-config.php.'; return false; }
    $ch = curl_init(rtrim($c['GITHUB_API'] ?? 'https://api.github.com', '/') . '/repos/' . $repo . '/actions/workflows/' . rawurlencode($c['GITHUB_WORKFLOW'] ?? 'hostinger.yml') . '/dispatches');
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 15, CURLOPT_POSTFIELDS => json_encode(['ref' => $c['GITHUB_REF'] ?? 'main']),
        CURLOPT_HTTPHEADER => ['Authorization: Bearer ' . $tok, 'Accept: application/vnd.github+json', 'X-GitHub-Api-Version: 2022-11-28', 'User-Agent: gp-admin', 'Content-Type: application/json']]);
    curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    if ($code === 204) return true;
    $err = $code === 0 ? 'Could not reach GitHub.' : ($code === 401 || $code === 403 || $code === 404 ? 'GitHub refused the token (HTTP ' . $code . '). Check the token, its permissions and GITHUB_REPO.' : 'GitHub returned HTTP ' . $code . '.');
    return false;
}
