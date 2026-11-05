<?php
// GET /api/img/<id> - uploaded product images (public).
require __DIR__ . '/_core.php';
$id = (string)($_GET['id'] ?? '');
if (!preg_match('/^[a-f0-9]{24}$/', $id)) { http_response_code(404); exit('Not found'); }
$bin = gp_read('img/' . $id . '.bin'); $type = trim((string)gp_read('img/' . $id . '.type'));
if ($bin === null || !in_array($type, ['image/jpeg', 'image/png', 'image/webp'], true)) { http_response_code(404); exit('Not found'); }
header('Content-Type: ' . $type); header('Cache-Control: public, max-age=31536000, immutable'); header('X-Content-Type-Options: nosniff'); header('Content-Length: ' . strlen($bin));
echo $bin;
