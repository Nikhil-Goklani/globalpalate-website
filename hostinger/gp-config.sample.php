<?php
// Copy this file to gp-config.php in the folder ABOVE public_html and fill in your values.
// (Hostinger File Manager > the folder that contains "public_html".) Never put it in GitHub.
return [
    // ---- Admin panel ----
    'ADMIN_PASSWORD' => '',          // your admin login: 16+ characters
    'BUILD_TOKEN'    => '',          // random 32+ characters; the same value goes into GitHub secret BUILD_TOKEN
    // Publish button -> starts the GitHub build. Create a fine-grained token (see HOSTINGER-SETUP.md Part 5)
    'GITHUB_TOKEN' => '',
    'GITHUB_REPO'  => 'Nikhil-Goklani/globalpalate-website',
    'GITHUB_WORKFLOW' => 'hostinger.yml',
    'GITHUB_REF'   => 'main',

    // ---- Forms ----
    // Zoho CRM Web-to-Lead: the three hidden fields
    'ZOHO_XNQSJSDP'  => '',
    'ZOHO_XMIWTLD'   => '',
    'ZOHO_ACTIONTYPE' => 'TGVhZHM=',
    // Email copy of every lead (optional). NOTIFY_FROM must be an address at globalpalate.co
    'NOTIFY_TO'   => '',
    'NOTIFY_FROM' => '',
    // Optional spam check (Cloudflare Turnstile secret)
    'TURNSTILE_SECRET' => '',
];
