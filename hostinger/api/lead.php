<?php
// Hostinger replacement for the Cloudflare form endpoint: POST /api/lead
// Secrets live OUTSIDE public_html in gp-config.php (see HOSTINGER-SETUP.md), never in GitHub.
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
function out($ok, $err = null, $code = 200) { http_response_code($code); echo json_encode($ok ? ['ok' => true] : ['ok' => false, 'error' => $err]); exit; }
function clean($v, $max = 500) { $v = is_scalar($v) ? (string)$v : ''; $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', '', $v); return mb_substr(trim($v), 0, $max); }

if ($_SERVER['REQUEST_METHOD'] !== 'POST') out(false, 'Method not allowed.', 405);

$cfg = [];
foreach ([dirname($_SERVER['DOCUMENT_ROOT']) . '/gp-config.php', __DIR__ . '/config.php'] as $p) { if (is_file($p)) { $cfg = include $p; break; } }
if (!is_array($cfg)) $cfg = [];

$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '' && parse_url($origin, PHP_URL_HOST) !== ($_SERVER['HTTP_HOST'] ?? '')) out(false, 'Origin not allowed.', 403);

$raw = file_get_contents('php://input', false, null, 0, 20001);
if (strlen($raw) > 20000) out(false, 'Request too large.', 413);
$d = json_decode($raw, true);
if (!is_array($d)) out(false, 'Invalid request.', 400);

// spam: honeypot + minimum fill time (silently accepted, nothing sent)
if (clean($d['website'] ?? '') !== '') out(true);
$rendered = (float)($d['rendered'] ?? 0);
if (!$rendered || (microtime(true) * 1000 - $rendered) < 3000) out(true);

// rate limit: 5 per 10 minutes per IP (file based)
$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$rl = sys_get_temp_dir() . '/gp_rl_' . md5($ip);
$hits = is_file($rl) ? array_filter(array_map('intval', explode(',', (string)@file_get_contents($rl))), function ($t) { return $t > time() - 600; }) : [];
if (count($hits) >= 5) out(false, 'Too many requests. Please try again later.', 429);
$hits[] = time(); @file_put_contents($rl, implode(',', $hits));

// Cloudflare Turnstile (optional)
if (!empty($cfg['TURNSTILE_SECRET'])) {
    $tok = clean($d['cf-turnstile-response'] ?? '', 2048);
    if ($tok === '') out(false, 'Please complete the spam check and try again.', 400);
    $ch = curl_init('https://challenges.cloudflare.com/turnstile/v0/siteverify');
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 10,
        CURLOPT_POSTFIELDS => http_build_query(['secret' => $cfg['TURNSTILE_SECRET'], 'response' => $tok, 'remoteip' => $ip])]);
    $r = json_decode((string)curl_exec($ch), true); curl_close($ch);
    if (empty($r['success'])) out(false, 'Spam check failed. Please try again.', 400);
}

$types = ['quote', 'sample', 'inquiry', 'documents', 'credit'];
$type = clean($d['type'] ?? '', 20);
if (!in_array($type, $types, true)) out(false, 'Invalid request type.', 400);
$prod = $d['products'] ?? [];
if (!is_array($prod)) $prod = [$prod];
$f = [
    'first' => clean($d['first_name'] ?? '', 80), 'last' => clean($d['last_name'] ?? '', 80),
    'email' => strtolower(clean($d['email'] ?? '', 254)), 'phone' => clean($d['phone'] ?? '', 40),
    'company' => clean($d['company'] ?? '', 120), 'url' => clean($d['company_url'] ?? '', 200),
    'qty' => clean($d['quantity'] ?? '', 20), 'unit' => clean($d['unit'] ?? '', 10) === 'drum' ? 'drums' : 'kg',
    'zip' => clean($d['zip'] ?? '', 20), 'needed' => clean($d['needed_by'] ?? '', 20), 'use' => clean($d['intended_use'] ?? '', 80),
    'msg' => clean($d['message'] ?? '', 2000), 'page' => clean($d['page'] ?? '', 200),
    'products' => array_slice(array_map(function ($p) { return clean($p, 40); }, array_filter($prod)), 0, 10),
];
$err = [];
if ($f['first'] === '') $err[] = 'your name';
if (!filter_var($f['email'], FILTER_VALIDATE_EMAIL)) $err[] = 'a valid email';
if ($type !== 'inquiry' && $f['company'] === '') $err[] = 'your company';
if ($type === 'inquiry' && $f['msg'] === '') $err[] = 'a message';
if (in_array($type, ['quote', 'sample'], true) && $f['qty'] === '') $err[] = 'the quantity you need';
if (in_array($type, ['quote', 'sample'], true) && $f['zip'] === '') $err[] = 'a delivery ZIP / postal code';
if ($err) out(false, 'Please provide ' . implode(', ', $err) . '.', 400);

$labels = ['quote' => 'Quote request', 'sample' => 'Sample request', 'inquiry' => 'General inquiry', 'documents' => 'Documentation request', 'credit' => 'Credit application'];
$label = $labels[$type];
$lines = array_filter([
    "Type: $label", $f['products'] ? 'Products: ' . implode(', ', $f['products']) : '', $f['qty'] ? "Quantity: {$f['qty']} {$f['unit']}" : '',
    $f['zip'] ? "Delivery ZIP: {$f['zip']}" : '', $f['needed'] ? "Needed by: {$f['needed']}" : '', $f['use'] ? "Intended use: {$f['use']}" : '',
    $f['url'] ? "Company website: {$f['url']}" : '', $f['msg'] ? "Message: {$f['msg']}" : '', "Submitted from: {$f['page']}",
]);
$description = implode("\n", $lines);

$results = [];
// Zoho CRM Web-to-Lead
if (!empty($cfg['ZOHO_XNQSJSDP']) && !empty($cfg['ZOHO_XMIWTLD'])) {
    $ch = curl_init($cfg['ZOHO_WTL_URL'] ?? 'https://crm.zoho.com/crm/WebToLeadForm');
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 15, CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_POSTFIELDS => http_build_query([
            'xnQsjsdp' => $cfg['ZOHO_XNQSJSDP'], 'xmIwtLD' => $cfg['ZOHO_XMIWTLD'], 'actionType' => $cfg['ZOHO_ACTIONTYPE'] ?? 'TGVhZHM=', 'returnURL' => 'null',
            'First Name' => $f['first'], 'Last Name' => $f['last'] !== '' ? $f['last'] : $f['first'], 'Email' => $f['email'], 'Phone' => $f['phone'],
            'Company' => $f['company'] !== '' ? $f['company'] : 'Not provided', 'Website' => $f['url'], 'Lead Source' => 'Website - ' . $label, 'Description' => $description,
        ])]);
    curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
    $results[] = $code > 0 && $code < 400;
}
// Email copy (uses the server's mail(); NOTIFY_FROM must be an address at your own domain)
if (!empty($cfg['NOTIFY_TO']) && !empty($cfg['NOTIFY_FROM'])) {
    $subject = "[Website] $label: {$f['first']} {$f['last']} (" . ($f['company'] ?: 'no company') . ')';
    $subject = preg_replace('/[\r\n]+/', ' ', $subject);
    $headers = "From: {$cfg['NOTIFY_FROM']}\r\nReply-To: {$f['email']}\r\nContent-Type: text/plain; charset=UTF-8";
    $results[] = @mail($cfg['NOTIFY_TO'], '=?UTF-8?B?' . base64_encode($subject) . '?=', "{$f['first']} {$f['last']}\n{$f['email']}\n{$f['phone']}\n{$f['company']}\n\n$description", $headers);
}
if (!$results) out(false, 'The form is not configured yet.', 503);
if (!in_array(true, $results, true)) out(false, 'We could not record your request.', 502);
out(true);
