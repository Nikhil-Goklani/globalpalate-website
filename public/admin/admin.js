(function () {
'use strict';
var D = document, $ = function (s, c) { return (c || D).querySelector(s); }, $$ = function (s, c) { return [].slice.call((c || D).querySelectorAll(s)); };
var S = { data: null, rev: 0, origJson: {}, origSlug: {}, dirty: false, view: 'products', pi: -1, tab: 'basics', defaults: {}, pub: {}, hook: false, q: '', pq: '' };
var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
function get(path) { return path.split('.').reduce(function (o, k) { return o == null ? o : o[k]; }, S.data); }
function set(path, v) { var ks = path.split('.'), o = S.data; for (var i = 0; i < ks.length - 1; i++) { if (o[ks[i]] == null) o[ks[i]] = {}; o = o[ks[i]]; } o[ks[ks.length - 1]] = v; }
function num(s) { var n = parseFloat(String(s == null ? '' : s).replace(/[$,]/g, '')); return isNaN(n) ? null : n; }
function P() { return S.data.products[S.pi]; }

var STANDARD = ['Particle size / mesh', 'Loss on drying (moisture)', 'Total ash', 'Marker content (curcumin / withanolides / other)', 'Lead (Pb)', 'Cadmium (Cd)', 'Arsenic (As)', 'Mercury (Hg)', 'Total plate count', 'Yeast & mold', 'E. coli', 'Salmonella', 'Aflatoxin (B1 / total)', 'Ochratoxin A', 'Pesticide residue (program and limits)', 'Adulterant screen (turmeric: lead chromate, synthetic dyes)', 'Steam sterilization / kill step', 'ETO / irradiation status', 'Allergen statement', 'Shelf life'];
var COMPANY = [
 ['Years in business', 'e.g. Operating since 2014', 1], ['Company story', '2-4 sentences: who started it, why, what you stand for', 4],
 ['FDA food facility registration', 'Who is registered (Global Palate or warehouse) and the FEI / registration number', 2], ['FSVP / importer of record', 'Who is importer of record and who runs the FSVP', 2],
 ['GMP statement', 'Which cGMP standard applies (21 CFR 117 / 111) and who is audited', 2], ['Product liability insurance', 'Coverage amount and insurer', 2],
 ['Recall / non-conformance policy', 'How a recall or out-of-spec lot is handled, who to contact, timeline', 3], ['Returns policy', 'When returns/credits are accepted, time limit, who pays freight', 3],
 ['Payment terms', 'e.g. Net 30 on approved credit; prepayment for first order', 1], ['Default price basis', 'e.g. FOB Compton, CA (used when a product does not state its own)', 1],
 ['Credit application', 'Do you offer credit? Any minimum or trade references needed', 2], ['Kill step statement', 'e.g. Steam sterilized at origin, validated 5-log reduction (only if true)', 2],
 ['ETO / irradiation statement', 'e.g. Steam sterilized. Not treated with ethylene oxide or irradiation. (only if true)', 2], ['Heavy metals compliance statement', 'Your limits for lead, cadmium, arsenic and the standard you follow', 2],
 ['Cross-contact statement', 'Does the facility handle allergens? Shared lines? Allergen controls', 2], ['Origin and supplier audit status', 'Regions in India, years with the processor, last audit', 2],
 ['Why Global Palate vs other U.S. distributors', 'One point per line. Only what you can prove', 4], ['Customer references', 'Company names you may publish and/or "References on request"', 2],
 ['Planned products', 'Comma-separated, e.g. black pepper, cinnamon, cardamom', 1], ['Netlify address', 'The netlify.app address to redirect to globalpalate.co', 1]];
var PAGE_NAMES = { '/': 'Home', '/industries/': 'Industries', '/ordering/': 'Ordering & terms', '/about/': 'About', '/contact/': 'Contact', '/quality/': 'Quality & documentation', '/supply-chain/': 'Supply chain', '/privacy/': 'Privacy policy', '/terms/': 'Terms', '/cookie-policy/': 'Cookie policy' };

// ---------- api ----------
function api(path, o) {
  o = o || {}; var h = { 'X-GP-Admin': '1' }; if (o.body && !o.raw) h['Content-Type'] = 'application/json'; if (o.type) h['Content-Type'] = o.type;
  return fetch('/api/admin/' + path, { method: o.method || 'GET', credentials: 'same-origin', headers: h, body: o.body ? (o.raw ? o.body : JSON.stringify(o.body)) : undefined })
    .then(function (r) { return r.json().catch(function () { return { ok: false, error: 'Unexpected response' }; }).then(function (j) { return { status: r.status, j: j }; }); });
}
function toast(msg, bad) { var t = $('#toast'); t.textContent = msg; t.className = 'toast' + (bad ? ' bad' : ''); t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(function () { t.hidden = true; }, bad ? 6000 : 3200); }
function modal(title, bodyHtml, buttons) {
  $('#mt').textContent = title; $('#mb').innerHTML = bodyHtml;
  $('#ma').innerHTML = buttons.map(function (b, i) { return '<button type="button" class="btn ' + (b.cls || '') + '" data-mbtn="' + i + '">' + esc(b.label) + '</button>'; }).join('');
  $('#modal').hidden = false; modal.btns = buttons; var f = $('#ma .btn:last-child') || $('#ma .btn'); if (f) f.focus();
}
function closeModal() { $('#modal').hidden = true; }

// ---------- boot ----------
function boot() {
  api('me').then(function (x) { if (x.j.authed) load(); else if (x.status === 503) showLogin(x.j.error); else showLogin(); });
  fetch('pages.json').then(function (r) { return r.ok ? r.json() : {}; }).then(function (j) { S.defaults = j; }).catch(function () {});
}
function showLogin(msg) { $('#app').hidden = true; $('#login').hidden = false; if (msg) { var e = $('#loginErr'); e.textContent = msg; e.hidden = false; } $('#pw').focus(); }
function load() {
  return api('data').then(function (x) {
    if (x.status === 401) return showLogin();
    if (!x.j.ok) { showLogin(x.j.error); return; }
    S.data = x.j.data; S.rev = x.j.rev; S.pub = x.j.published; S.hook = x.j.hook; S.dirty = false; snapshot();
    $('#login').hidden = true; $('#app').hidden = false; render();
  });
}
function snapshot() {
  S.origJson = {}; S.origSlug = {};
  S.data.products.forEach(function (p) { var c = JSON.parse(JSON.stringify(p)); delete c.updated; S.origJson[p.key] = JSON.stringify(c); S.origSlug[p.key] = p.slug; });
}
function markDirty() { if (!S.dirty) { S.dirty = true; chrome(); } }
function chrome() {
  var c = $('#status');
  if (S.dirty) { c.textContent = 'Unsaved changes'; c.className = 'chip dirty'; }
  else if (S.pub && S.pub.same) { c.textContent = 'Live site matches'; c.className = 'chip ok'; }
  else { c.textContent = 'Saved, not published'; c.className = 'chip'; }
  $$('#nav button').forEach(function (b) { b.setAttribute('aria-current', b.dataset.view === S.view ? 'page' : 'false'); });
}

// ---------- form helpers ----------
function fid(path) { return 'f_' + path.replace(/[^a-z0-9]/gi, '_'); }
function F(label, path, o) {
  o = o || {}; var v = get(path); if (o.lines && Array.isArray(v)) v = v.join('\n'); var id = fid(path), cnt = o.count ? ' data-count="' + o.count.join('-') + '"' : '';
  var ph = o.ph != null ? ' placeholder="' + esc(o.ph) + '"' : '';
  var attrs = ' id="' + id + '" data-bind="' + esc(path) + '"' + cnt + (o.lines ? ' data-lines="1"' : '') + (o.slug ? ' data-slug="1"' : '') + ph;
  var el;
  if (o.type === 'area') el = '<textarea' + attrs + ' rows="' + (o.rows || 3) + '">' + esc(v) + '</textarea>';
  else if (o.type === 'select') el = '<select' + attrs + '>' + o.options.map(function (x) { return '<option value="' + esc(x[0]) + '"' + (String(v == null ? '' : v) === x[0] ? ' selected' : '') + '>' + esc(x[1]) + '</option>'; }).join('') + '</select>';
  else if (o.type === 'check') return '<label style="margin-top:14px"><input type="checkbox"' + attrs + (v ? ' checked' : '') + '>' + esc(label) + '</label>' + (o.hint ? '<p class="hint">' + esc(o.hint) + '</p>' : '');
  else el = '<input type="' + (o.type || 'text') + '"' + attrs + ' value="' + esc(v) + '"' + (o.inputmode ? ' inputmode="' + o.inputmode + '"' : '') + '>';
  return '<div' + (o.cls ? ' class="' + o.cls + '"' : '') + '><label for="' + id + '">' + esc(label) + (o.count ? '<span class="cnt" data-cnt-for="' + id + '"></span>' : '') + '</label>' + el + (o.hint ? '<p class="hint">' + esc(o.hint) + '</p>' : '') + '</div>';
}
function strList(path, ph, area, addLabel) {
  var a = get(path) || [];
  return a.map(function (x, i) { return '<div class="row-edit r1">' + (area ? '<textarea data-bind="' + path + '.' + i + '" placeholder="' + esc(ph) + '" rows="3" aria-label="' + esc(ph) + ' ' + (i + 1) + '">' + esc(x) + '</textarea>' : '<input data-bind="' + path + '.' + i + '" value="' + esc(x) + '" placeholder="' + esc(ph) + '" aria-label="' + esc(ph) + ' ' + (i + 1) + '">') + '<button type="button" class="btn sm danger" data-act="del" data-path="' + path + '" data-idx="' + i + '" aria-label="Remove">&times;</button></div>'; }).join('') +
    '<button type="button" class="btn sm" data-act="add" data-path="' + path + '" data-tpl="&quot;&quot;">+ ' + esc(addLabel || 'Add') + '</button>';
}
function rows(path, cols, addLabel, cls) {
  var a = get(path) || [], isPair = Array.isArray(a[0]) || (a.length === 0 && cols[0].k === 0);
  var html = a.map(function (r, i) {
    return '<div class="row-edit ' + (cls || '') + '">' + cols.map(function (c) {
      var p = path + '.' + i + '.' + c.k, v = r[c.k];
      if (c.sel) return '<select data-bind="' + p + '" aria-label="' + esc(c.ph) + '">' + c.sel.map(function (o) { return '<option' + (o === v ? ' selected' : '') + '>' + esc(o) + '</option>'; }).join('') + '</select>';
      return c.area ? '<textarea data-bind="' + p + '" placeholder="' + esc(c.ph) + '" aria-label="' + esc(c.ph) + '" rows="2">' + esc(v) + '</textarea>' : '<input data-bind="' + p + '" value="' + esc(v) + '" placeholder="' + esc(c.ph) + '" aria-label="' + esc(c.ph) + '">';
    }).join('') + '<button type="button" class="btn sm danger" data-act="del" data-path="' + path + '" data-idx="' + i + '" aria-label="Remove row">&times;</button></div>';
  }).join('');
  var tpl = isPair ? cols.map(function () { return ''; }) : cols.reduce(function (o, c) { o[c.k] = ''; return o; }, {});
  return html + '<button type="button" class="btn sm" data-act="add" data-path="' + path + '" data-tpl="' + esc(JSON.stringify(tpl)) + '">+ ' + esc(addLabel || 'Add row') + '</button>';
}

// ---------- SEO + quality checks ----------
function seoChecks(p) {
  var kw = (p.seo.focus_keyword || '').toLowerCase().trim(), L = [];
  function add(ok, label, hint, lvl) { L.push({ ok: ok, label: label, hint: hint || '', lvl: lvl || 'fail' }); }
  var tl = (p.title || '').length, ml = (p.meta || '').length, words = (p.desc || []).join(' ').split(/\s+/).filter(Boolean).length;
  add(tl >= 30 && tl <= 60, 'SEO title is 30-60 characters (' + tl + ')', 'Search results cut titles at about 60 characters.');
  add(ml >= 140 && ml <= 160, 'Meta description is 140-160 characters (' + ml + ')', 'This is the text shown under your title in Google.');
  add(!!p.h1, 'Page heading (H1) is set');
  if (kw) {
    add((p.title || '').toLowerCase().indexOf(kw) >= 0, 'Focus keyword "' + kw + '" is in the SEO title');
    add((p.meta || '').toLowerCase().indexOf(kw) >= 0, 'Focus keyword is in the meta description');
    add((p.h1 || '').toLowerCase().indexOf(kw) >= 0, 'Focus keyword is in the H1');
    add((p.desc[0] || '').toLowerCase().indexOf(kw) >= 0 || (p.lead || '').toLowerCase().indexOf(kw) >= 0, 'Focus keyword appears in the opening text');
    add((p.slug || '').indexOf(kw.replace(/[^a-z0-9]+/g, '-')) >= 0, 'Focus keyword is in the URL slug', 'Changing a live slug adds a 301 redirect automatically.', 'warn');
  } else add(false, 'Set a focus keyword (SEO tab)', 'The phrase buyers search for, e.g. "organic turmeric powder bulk".', 'warn');
  add(/^[a-z0-9-]+$/.test(p.slug || '') && p.slug.length <= 75, 'URL slug is lowercase, short and clean');
  add(words >= 120, 'Description has 120+ words (' + words + ')', 'Thin pages rank poorly and give buyers too little to go on.', 'warn');
  add(p.image && (p.image.src === 'kv' || !!S.origSlug[p.key]), 'Product photo is uploaded', 'Without one the site shows a plain placeholder.');
  add((p.alt || '').length >= 10, 'Image alt text is descriptive');
  add((p.faq || []).filter(function (q) { return q[0] && q[1]; }).length >= 3, '3+ product-specific FAQs (' + (p.faq || []).length + ')', 'FAQs feed Google rich results and AI answers.', 'warn');
  add(num(p.commercial.price_from) != null, 'Indicative price is published', 'Buyers leave when there is no price at all.', 'warn');
  add(!!p.commercial.in_stock, 'Stock status is set', '', 'warn');
  add((p.specs || []).length >= 4, 'Specification table has 4+ rows (' + (p.specs || []).length + ')');
  add((p.tests || []).filter(function (t) { return t.limit || t.result; }).length >= 8, 'Quality tests filled for 8+ parameters', 'Heavy metals, micro, moisture, ash, allergens.', 'warn');
  add(!!p.botanical, 'Botanical (Latin) name is set');
  var dupT = S.data.products.some(function (o) { return o !== p && o.title && o.title === p.title; }), dupM = S.data.products.some(function (o) { return o !== p && o.meta && o.meta === p.meta; });
  add(!dupT && !dupM, 'Title and meta description are unique on the site');
  add(!p.seo.noindex, 'Page is indexable by search engines', 'Tick "noindex" only for pages you want hidden.', 'warn');
  return L;
}
function score(p) { var c = seoChecks(p), ok = c.filter(function (x) { return x.ok; }).length; return { n: ok, t: c.length, pct: Math.round(ok * 100 / c.length) }; }
function scoreHtml(p) { var s = score(p); return '<span class="score ' + (s.pct >= 85 ? 'a' : s.pct >= 65 ? 'b' : 'c') + '">' + s.pct + '%</span> <small>(' + s.n + '/' + s.t + ')</small>'; }
function commWarnings(p) {
  var c = p.commercial, w = [], lo = num(c.price_from), hi = num(c.price_to);
  if (lo != null && hi != null && lo > hi) w.push('"Price from" is higher than "price to".');
  var tiers = (c.tiers || '').split('\n').map(function (l) { var m = l.match(/\$\s*([\d.]+)/); return m ? parseFloat(m[1]) : null; }).filter(function (x) { return x != null; });
  tiers.forEach(function (t) { if (lo != null && t < lo - 1e-9) w.push('A tier price ($' + t + ') is below "price from".'); if (hi != null && t > hi + 1e-9) w.push('A tier price ($' + t + ') is above "price to".'); });
  var m = (c.pack_format || '').match(/(\d+(?:\.\d+)?)\s*kg/i), pw = m ? parseFloat(m[1]) : null, nw = num(c.net_weight);
  if (pw && nw && pw !== nw) w.push('Pack format says ' + pw + ' kg but net weight per pack is ' + nw + '. Pack and pallet rows are hidden on the site until they agree.');
  else { var packs = num(c.packs_per_pallet), pal = (c.pallet_net || '').match(/([\d.]+)\s*(kg|mt)?/i), wt = nw || pw; if (packs && wt && pal) { var tot = parseFloat(pal[1]) * ((pal[2] || '').toLowerCase() === 'mt' ? 1000 : 1); if (Math.abs(packs * wt - tot) >= 1) w.push(packs + ' packs x ' + wt + ' kg = ' + packs * wt + ' kg, but the pallet says ' + c.pallet_net + '.'); } }
  if (c.in_stock === 'Yes' && !c.ships_within) w.push('In stock is Yes but "ships within" is empty.');
  return w;
}
function testWarnings(p) {
  var w = [];
  (p.tests || []).forEach(function (t) { var mx = String(t.limit || '').match(/^\s*(?:max\.?|nmt|not more than)\s*([\d.]+)/i); if (mx && /^\s*[\d.]+\s*(%|ppm)/.test(t.result || '') && parseFloat(t.result) > parseFloat(mx[1])) w.push(t.param + ': result ' + t.result + ' is above the limit (' + t.limit + '). This row is hidden on the site.'); });
  return w;
}
function warnBox(list) { return list.length ? '<div class="warnbox"><strong>Check this</strong><ul>' + list.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></div>' : ''; }

// ---------- views ----------
function render() {
  var items = [['products', 'Products'], ['pages', 'Page SEO'], ['settings', 'Site settings'], ['certs', 'Certificates'], ['company', 'Company facts'], ['transit', 'Transit times'], ['redirects', 'Redirects'], ['history', 'History']];
  $('#nav').innerHTML = items.map(function (x) { return '<button type="button" data-act="nav" data-view="' + x[0] + '">' + x[1] + '</button>'; }).join('');
  var y = window.scrollY; var m = $('#main');
  var v = S.view; m.innerHTML = v === 'product' ? viewProduct() : v === 'pages' ? viewPages() : v === 'settings' ? viewSettings() : v === 'certs' ? viewCerts() : v === 'company' ? viewCompany() : v === 'transit' ? viewTransit() : v === 'redirects' ? viewRedirects() : v === 'history' ? viewHistory() : viewProducts();
  chrome(); counters(); if (v === 'product') live(); window.scrollTo(0, y);
  if (v === 'history') loadHistory();
}
function viewProducts() {
  var q = S.q.toLowerCase();
  var rowsH = S.data.products.map(function (p, i) { return { p: p, i: i }; }).filter(function (x) { return !q || (x.p.name + ' ' + x.p.slug + ' ' + x.p.botanical).toLowerCase().indexOf(q) >= 0; }).map(function (x) {
    var p = x.p, i = x.i, c = p.commercial, pr = num(c.price_from) != null ? '$' + num(c.price_from) + (num(c.price_to) != null && c.price_to !== c.price_from ? '–$' + num(c.price_to) : '') + '/' + (c.price_unit || 'kg') : '—';
    var st = c.in_stock === 'Yes' ? 'In stock' + (c.qty ? ' (' + esc(c.qty) + ')' : '') : c.in_stock === 'No' ? 'Out of stock' : '—';
    var im = p.image && p.image.src === 'kv' ? '/api/img/' + p.image.id : '../images/' + p.key + '-320.webp';
    return '<tr><td><img src="' + im + '" alt="" loading="lazy" onerror="this.style.visibility=\'hidden\'"></td><td><strong>' + esc(p.name) + '</strong><br><small>/product/' + esc(p.slug) + '/</small></td><td><span class="badge ' + (p.status === 'draft' ? 'draft' : 'pub') + '">' + (p.status === 'draft' ? 'Draft' : 'Published') + '</span></td><td>' + pr + '</td><td>' + st + '</td><td>' + scoreHtml(p) + '</td><td style="white-space:nowrap"><button class="btn sm" data-act="edit" data-i="' + i + '">Edit</button> <button class="btn sm" data-act="up" data-i="' + i + '" aria-label="Move up">↑</button> <button class="btn sm" data-act="down" data-i="' + i + '" aria-label="Move down">↓</button> <button class="btn sm" data-act="dup" data-i="' + i + '">Duplicate</button> <button class="btn sm danger" data-act="delp" data-i="' + i + '">Delete</button></td></tr>';
  }).join('');
  return '<h1>Products</h1><div class="bar2"><button class="btn primary" data-act="newp">+ Add product</button><input type="search" id="q" placeholder="Search products" value="' + esc(S.q) + '" aria-label="Search products"><span class="hint">Drafts are saved but never appear on the live site. Order here is the order on the site.</span></div><table class="list"><thead><tr><th></th><th>Product</th><th>Status</th><th>Price</th><th>Stock</th><th>SEO</th><th>Actions</th></tr></thead><tbody>' + (rowsH || '<tr><td colspan="7">No products yet.</td></tr>') + '</tbody></table>';
}
var TABS = [['basics', 'Basics'], ['content', 'Content'], ['pricing', 'Pricing & stock'], ['tests', 'Quality tests'], ['image', 'Photo'], ['seo', 'SEO']];
function viewProduct() {
  var p = P(); if (!p) { S.view = 'products'; return viewProducts(); }
  var i = S.pi, b = 'products.' + i + '.';
  var tabs = '<div class="tabs" role="tablist">' + TABS.map(function (t) { return '<button type="button" role="tab" data-act="tab" data-tab="' + t[0] + '" aria-selected="' + (S.tab === t[0]) + '">' + t[1] + '</button>'; }).join('') + '</div>';
  var body = '';
  if (S.tab === 'basics') body = '<div class="g2">' + F('Product name', b + 'name', { hint: 'Shown as the page name and in menus.' }) + F('Short name', b + 'short', { hint: 'Used in cards and footer, e.g. "Turmeric Powder".' }) +
    F('Common name', b + 'common', { hint: 'One word used in sentences, e.g. "turmeric".' }) + F('Botanical (Latin) name', b + 'botanical') + F('Plant part', b + 'part', { ph: 'Rhizome, Root, Leaves…' }) + F('Category tag', b + 'tag', { ph: 'Spice · Root' }) +
    F('Status', b + 'status', { type: 'select', options: [['published', 'Published (live after Publish)'], ['draft', 'Draft (hidden)']] }) + F('Sold by', b + 'unit_mode', { type: 'select', options: [['kg', 'Kilogram (powders)'], ['drum', 'Drum']] }) + F('Standard order size text', b + 'box', { ph: '100 kg' }) +
    F('Internal key', b + 'key', { hint: 'Cannot be changed after creation.' }).replace('<input ', '<input readonly ') + '</div>' +
    F('URL slug', b + 'slug', { slug: 1, hint: 'Page address: https://globalpalate.co/product/<slug>/' }) + '<p class="hint" id="slugPrev"></p>';
  else if (S.tab === 'content') body = F('Page heading (H1)', b + 'h1', { hint: 'The main headline on the page.' }) + F('Intro paragraph', b + 'lead', { type: 'area', rows: 3, hint: 'Shown under the headline.' }) + F('Card blurb', b + 'card', { type: 'area', rows: 2, hint: 'One line used on product cards and in llms.txt.' }) +
    '<h3 style="margin-top:20px">Description paragraphs</h3>' + strList(b + 'desc', 'Paragraph', true, 'Add paragraph') +
    '<h3 style="margin-top:20px">Specification table</h3>' + rows(b + 'specs', [{ k: 0, ph: 'Label' }, { k: 1, ph: 'Value' }], 'Add spec row') +
    '<h3 style="margin-top:20px">Purity statements</h3>' + strList(b + 'purity', 'e.g. Gluten free', false, 'Add statement') +
    '<h3 style="margin-top:20px">"Things to know" card</h3>' + F('Card subtitle', b + 'ttk_sub') + rows(b + 'ttk', [{ k: 0, ph: 'Heading' }, { k: 1, ph: 'Text' }], 'Add point') +
    '<h3 style="margin-top:20px">Product-specific FAQs</h3><p class="hint">Standard FAQs (price, minimum order, stock, testing, shelf life) are added automatically.</p>' + rows(b + 'faq', [{ k: 0, ph: 'Question' }, { k: 1, ph: 'Answer', area: 1 }], 'Add FAQ') +
    '<div class="g2"><div>' + F('Plant description (used in FAQ)', b + 'plant', { ph: 'rhizome (root) of the Curcuma longa plant' }) + '</div><div>' + F('Appearance (used in FAQ)', b + 'look', { ph: 'a fine golden-yellow powder' }) + '</div></div>';
  else if (S.tab === 'pricing') { var c = b + 'commercial.';
    body = '<p class="hint">Only filled fields are published. Prices are shown as indicative and confirmed by quote.</p><div id="commWarn"></div><h3>Price</h3><div class="g3">' + F('Price from (USD)', c + 'price_from', { inputmode: 'decimal' }) + F('Price to (USD)', c + 'price_to', { inputmode: 'decimal' }) + F('Per', c + 'price_unit', { type: 'select', options: [['', 'kg (default)'], ['kg', 'kg'], ['drum', 'drum']] }) + '</div>' +
      '<div class="g2">' + F('Price basis', c + 'price_basis', { ph: 'FOB Compton, CA' }) + F('Price valid as of', c + 'price_valid', { type: 'date' }) + '</div>' + F('Volume tiers (one per line)', c + 'tiers', { type: 'area', rows: 5, ph: '100 kg: $7.50\n500 kg: $7.20' }) +
      '<h3 style="margin-top:20px">Availability</h3><div class="g3">' + F('In stock?', c + 'in_stock', { type: 'select', options: [['', 'Not stated'], ['Yes', 'Yes'], ['No', 'No']] }) + F('Quantity on hand', c + 'qty', { ph: '5000 (kg)' }) + F('Ships within', c + 'ships_within', { ph: '2-3 business days' }) + '</div>' + F('Lot / crop year', c + 'lot', { ph: '2026' }) +
      '<h3 style="margin-top:20px">Packing</h3><div class="g2">' + F('Pack format', c + 'pack_format', { ph: '25 kg kraft paper bags' }) + F('Net weight per pack (kg)', c + 'net_weight', { inputmode: 'decimal' }) + F('Packs per pallet', c + 'packs_per_pallet', { inputmode: 'numeric' }) + F('Pallet net weight', c + 'pallet_net', { ph: '1000 kg or 1 MT' }) + '</div>' +
      '<h3 style="margin-top:20px">Origin</h3><div class="g2">' + F('Origin region', c + 'origin_region', { ph: 'Maharashtra, India' }) + F('Supplier / processor', c + 'supplier') + '</div>' + F('Last audit (who, when, result)', c + 'last_audit'); }
  else if (S.tab === 'tests') body = '<p class="hint">Test limits, methods and typical results. Rows with a limit or result appear on the product page.</p><div id="testWarn"></div>' + '<div class="row-edit r4" aria-hidden="true"><strong>Parameter</strong><strong>Limit</strong><strong>Method</strong><strong>Typical result</strong></div>' +
    rows(b + 'tests', [{ k: 'param', ph: 'Parameter' }, { k: 'limit', ph: 'Limit' }, { k: 'method', ph: 'Method' }, { k: 'result', ph: 'Result' }], 'Add test', 'r4') + '<p style="margin-top:12px"><button class="btn sm" data-act="stdtests">Add the 20 standard parameters</button></p>';
  else if (S.tab === 'image') { var im = p.image && p.image.src === 'kv' ? '/api/img/' + p.image.id : '../images/' + p.key + '-640.webp';
    body = '<div class="imgbox"><img id="imgPrev" src="' + im + '" alt="Current product photo" onerror="this.style.visibility=\'hidden\'"><div><p>Upload a square-ish photo of the product (JPEG, PNG or WebP, up to 4 MB). It is cropped to a square and converted to fast WebP when the site is built.</p><input type="file" id="imgFile" accept="image/jpeg,image/png,image/webp"><p class="hint" id="imgMsg"></p></div></div>' + F('Alt text', b + 'alt', { hint: 'Describe the photo for screen readers and image search, e.g. "Ceramic bowl of organic turmeric powder".' }); }
  else if (S.tab === 'seo') { var s = b + 'seo.';
    body = '<div class="split"><div>' + F('Focus keyword', s + 'focus_keyword', { hint: 'The phrase buyers search for. Used for the checklist only; it is not published.' }) + F('SEO title', b + 'title', { count: [30, 60], hint: 'The clickable headline in search results. Include "| Global Palate" at the end.' }) +
      F('Meta description', b + 'meta', { type: 'area', rows: 3, count: [140, 160], hint: 'The text under the title in search results.' }) + '<h3 style="margin-top:20px">Advanced</h3>' + F('Canonical URL (leave empty for the default)', s + 'canonical', { type: 'url', ph: 'https://globalpalate.co/product/' + p.slug + '/' }) +
      F('Hide from search engines (noindex)', s + 'noindex', { type: 'check', hint: 'The page still works but is left out of Google and the sitemap.' }) + F('Social share title (optional)', s + 'og_title', { hint: 'Defaults to the SEO title.' }) + F('Social share description (optional)', s + 'og_desc', { type: 'area', rows: 2 }) +
      '<p class="hint">The social share image is generated automatically from the product photo.</p></div><div id="seoBox"></div></div>'; }
  return '<p><button class="btn ghost" data-act="nav" data-view="products">← All products</button></p><h1>' + esc(p.name || 'New product') + ' <span class="badge ' + (p.status === 'draft' ? 'draft' : 'pub') + '">' + (p.status === 'draft' ? 'Draft' : 'Published') + '</span></h1><p class="hint">https://globalpalate.co/product/' + esc(p.slug) + '/ · SEO score ' + scoreHtml(p).replace(/<[^>]+>/g, '') + '</p>' + tabs + '<div class="card">' + body + '</div>';
}
function jsonLd(p) {
  var o = { '@type': 'Product', name: p.name, description: p.meta, sku: p.key, brand: { '@type': 'Brand', name: 'Global Palate' }, additionalProperty: [{ name: 'Botanical name', value: p.botanical }, { name: 'Plant part', value: p.part }] };
  var lo = num(p.commercial.price_from), hi = num(p.commercial.price_to); if (lo != null && (p.commercial.price_unit || 'kg') === 'kg') { o.offers = { '@type': 'AggregateOffer', priceCurrency: 'USD', lowPrice: lo.toFixed(2), highPrice: (hi != null ? hi : lo).toFixed(2) }; if (p.commercial.in_stock === 'Yes') o.offers.availability = 'https://schema.org/InStock'; }
  return JSON.stringify(o, null, 1);
}
function live() {
  var p = P(); if (!p) return;
  var sb = $('#seoBox');
  if (sb) {
    var t = p.title || ''; if (t.length > 60) t = t.slice(0, 58) + '…'; var d = p.meta || ''; if (d.length > 160) d = d.slice(0, 157) + '…';
    var ch = seoChecks(p);
    sb.innerHTML = '<h3>Google preview</h3><div class="serp"><div class="u">globalpalate.co › product › ' + esc(p.slug) + '</div><div class="t">' + esc(t) + '</div><div class="d">' + esc(d || 'Add a meta description…') + '</div></div>' +
      '<h3 style="margin-top:18px">SEO checklist <span style="float:right">' + scoreHtml(p) + '</span></h3><ul class="checks">' + ch.map(function (x) { return '<li class="' + (x.ok ? 'pass' : x.lvl) + '"><span class="i">' + (x.ok ? '✓' : x.lvl === 'warn' ? '!' : '✗') + '</span><span>' + esc(x.label) + (!x.ok && x.hint ? '<small>' + esc(x.hint) + '</small>' : '') + '</span></li>'; }).join('') + '</ul>' +
      '<details class="k"><summary>Structured data (generated automatically)</summary><div><pre style="white-space:pre-wrap;font-size:12px">' + esc(jsonLd(p)) + '</pre></div></details>';
  }
  var cw = $('#commWarn'); if (cw) cw.innerHTML = warnBox(commWarnings(p));
  var tw = $('#testWarn'); if (tw) tw.innerHTML = warnBox(testWarnings(p));
  var sp = $('#slugPrev'); if (sp) sp.textContent = 'Live address: https://globalpalate.co/product/' + p.slug + '/' + (S.origSlug[p.key] && S.origSlug[p.key] !== p.slug ? '   (old address /product/' + S.origSlug[p.key] + '/ will redirect automatically)' : '');
}
function counters() {
  $$('[data-count]').forEach(function (el) {
    var r = el.dataset.count.split('-').map(Number), n = el.value.length, s = $('[data-cnt-for="' + el.id + '"]'); if (!s) return;
    s.textContent = n + ' / ' + r[0] + '-' + r[1]; s.className = 'cnt ' + (n >= r[0] && n <= r[1] ? 'ok' : (n === 0 ? 'bad' : 'warn'));
  });
}
function viewPages() {
  var paths = Object.keys(S.defaults).length ? Object.keys(S.defaults) : Object.keys(PAGE_NAMES);
  var q = S.pq.toLowerCase();
  return '<h1>Page SEO</h1><p class="hint">Override the search title and description of any page. Leave a field empty to keep the built-in text (shown greyed as the placeholder).</p><div class="bar2"><input type="search" id="pq" placeholder="Filter pages" value="' + esc(S.pq) + '" aria-label="Filter pages"></div>' +
    paths.filter(function (p) { return !q || (p + ' ' + (PAGE_NAMES[p] || '')).toLowerCase().indexOf(q) >= 0; }).map(function (path) {
      var d = S.defaults[path] || {}, b = 'pages.' + path + '.', o = (S.data.pages || {})[path] || {}, has = o.title || o.description || o.og_title || o.og_desc || o.canonical || o.noindex;
      return '<details class="k"' + (has ? ' open' : '') + '><summary>' + esc(PAGE_NAMES[path] || path) + ' <small style="font-weight:400">' + esc(path) + (has ? ' · customised' : '') + '</small></summary><div>' +
        F('SEO title', b + 'title', { count: [30, 60], ph: d.title || '' }) + F('Meta description', b + 'description', { type: 'area', rows: 2, count: [140, 160], ph: d.description || '' }) +
        '<div class="g2">' + F('Social title', b + 'og_title') + F('Canonical URL', b + 'canonical', { type: 'url' }) + '</div>' + F('Social description', b + 'og_desc', { type: 'area', rows: 2 }) + F('Hide this page from search engines (noindex)', b + 'noindex', { type: 'check' }) + '</div></details>';
    }).join('');
}
function viewSettings() {
  return '<h1>Site settings</h1><div class="card"><h3>Contact</h3><div class="g2">' + F('Sales phone', 'settings.phone') + F('Second phone', 'settings.phone2') + F('Sales email', 'settings.email', { type: 'email' }) + F('Parent company', 'settings.parent') + F('Opening hours', 'settings.hours') + F('Reply time', 'settings.response', { hint: 'Completes "We reply …", e.g. within one business day.' }) + '</div>' +
    '<h3 style="margin-top:22px">Ordering</h3><div class="g2">' + F('Minimum order (powders)', 'settings.moq') + F('Site-wide lead-time sentence', 'settings.lead_time') + '</div>' +
    '<h3 style="margin-top:22px">Announcement bar & meetings</h3>' + F('Announcement text', 'settings.show', { hint: 'Leave empty to hide the bar. "Book a meeting now!" at the end becomes a link.' }) + F('Booking link', 'settings.booking_url', { type: 'url', ph: 'https://calendly.com/…' }) +
    '<h3 style="margin-top:22px">Addresses</h3><div class="g2">' + F('Warehouse street', 'settings.warehouse.street') + F('Warehouse city', 'settings.warehouse.city') + F('State', 'settings.warehouse.state') + F('ZIP', 'settings.warehouse.zip') + F('Office street', 'settings.office.street') + F('Office city', 'settings.office.city') + F('State', 'settings.office.state') + F('ZIP', 'settings.office.zip') + '</div>' +
    '<h3 style="margin-top:22px">SEO & tracking</h3><div class="g2">' + F('Google Analytics 4 ID', 'settings.ga4', { ph: 'G-XXXXXXXXXX', hint: 'Adds the cookie banner automatically.' }) + F('Cloudflare Turnstile site key', 'settings.turnstile') + F('Google Search Console verification code', 'settings.gsc_verification', { hint: 'The content="…" value of the verification meta tag.' }) + '</div>' +
    F('Social profile links (one per line)', 'settings.same_as', { type: 'area', lines: 1, rows: 3, hint: 'LinkedIn, etc. Added to the Organization structured data.' }) + F('Extra robots.txt rules', 'settings.robots_extra', { type: 'area', rows: 3, hint: 'Advanced. Added after the default rules.' }) + '</div>';
}
function viewCerts() {
  var a = S.data.certs;
  return '<h1>Certificates</h1><p class="hint">Shows buyers which certificate covers which product, who holds it and how to verify it.</p>' + a.map(function (c, i) {
    var b = 'certs.' + i + '.';
    return '<div class="card" style="margin-bottom:12px"><div class="g3">' + F('Certification', b + 'name') + F('Applies to (product keys, or "all")', b + 'applies') + F('Holder', b + 'holder') + F('Holder type', b + 'htype', { type: 'select', options: [['', '—'], ['Origin processor', 'Origin processor'], ['Warehouse', 'Warehouse'], ['Global Palate', 'Global Palate']] }) + F('Certifier', b + 'certifier') + F('Certificate number', b + 'number') + F('Expiry date', b + 'expiry', { type: 'date' }) + F('Verification link', b + 'url', { type: 'url', ph: 'https://organic.ams.usda.gov/integrity/…' }) + '</div><div class="acts"><button class="btn sm danger" data-act="del" data-path="certs" data-idx="' + i + '">Remove certificate</button></div></div>';
  }).join('') + '<button class="btn" data-act="add" data-path="certs" data-tpl="' + esc(JSON.stringify({ name: '', applies: 'all', holder: '', htype: '', certifier: '', number: '', expiry: '', url: '' })) + '">+ Add certificate</button>';
}
function viewCompany() {
  var known = COMPANY.map(function (x) { return x[0]; }), extra = Object.keys(S.data.company || {}).filter(function (k) { return known.indexOf(k) < 0; });
  return '<h1>Company facts & policies</h1><p class="hint">Published as written on the About, Quality, Ordering and product pages. Empty fields are not shown.</p><div class="card">' + COMPANY.map(function (x) { return F(x[0], 'company.' + x[0], { type: 'area', rows: x[2] + 1, hint: x[1] }); }).join('') + extra.map(function (k) { return F(k, 'company.' + k, { type: 'area', rows: 3 }); }).join('') + '</div>';
}
function viewTransit() {
  return '<h1>Transit times</h1><p class="hint">Business days from the Compton, CA warehouse. Rows with region West or East appear on the matching turmeric region page; all rows appear on Ordering & terms.</p><div class="row-edit r5" aria-hidden="true"><strong>State</strong><strong>Region</strong><strong>LTL days</strong><strong>Truckload days</strong><strong>Notes</strong></div>' +
    rows('transit', [{ k: 'state', ph: 'State' }, { k: 'region', ph: 'Region', sel: ['West', 'Central', 'East', 'Canada'] }, { k: 'ltl', ph: '1-2' }, { k: 'ftl', ph: '1' }, { k: 'note', ph: 'Notes' }], 'Add state', 'r5');
}
function viewRedirects() {
  return '<h1>Redirects</h1><p class="hint">301 redirects from old addresses to new ones. When you change a live product\'s URL slug, the redirect is added automatically on save.</p><div class="row-edit" aria-hidden="true"><strong>Old address (e.g. /old-page/)</strong><strong>New address</strong></div>' + rows('redirects', [{ k: 'from', ph: '/old-page/' }, { k: 'to', ph: '/product/organic-turmeric-powder/' }], 'Add redirect');
}
function viewHistory() { return '<h1>History</h1><p class="hint">Every save keeps the previous version (last 30). Restoring creates a new draft; publish it to make it live.</p><div id="hist">Loading…</div>'; }
function loadHistory() {
  api('history').then(function (x) {
    var h = $('#hist'); if (!h) return; if (!x.j.ok) { h.textContent = x.j.error || 'Could not load.'; return; }
    h.innerHTML = '<table class="list"><thead><tr><th>Saved</th><th>What changed</th><th></th></tr></thead><tbody>' + (x.j.items.map(function (i) { return '<tr><td>' + esc(new Date(i.at).toLocaleString()) + '</td><td>' + esc(i.summary || '—') + '</td><td><button class="btn sm" data-act="restore" data-id="' + esc(i.id) + '">Restore this version</button></td></tr>'; }).join('') || '<tr><td colspan="3">No earlier versions yet.</td></tr>') + '</tbody></table>';
  });
}

// ---------- actions ----------
function slugify(s) { return String(s).toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80); }
function uniqueKey(base) { var k = base || 'product', n = 2, keys = S.data.products.map(function (p) { return p.key; }), slugs = S.data.products.map(function (p) { return p.slug; }); var kk = k; while (keys.indexOf(kk) >= 0 || slugs.indexOf(kk) >= 0) kk = k + '-' + (n++); return kk; }
function blankCommercial() { return { price_from: '', price_to: '', price_unit: '', price_basis: '', tiers: '', price_valid: '', in_stock: '', qty: '', ships_within: '', lot: '', pack_format: '', net_weight: '', packs_per_pallet: '', pallet_net: '', origin_region: '', supplier: '', last_audit: '' }; }
function newProduct(name, botanical, slug) {
  var key = uniqueKey(slugify(name).replace(/^organic-/, '') || 'product'), sl = slug || ('organic-' + key);
  var short = name.replace(/^organic\s+/i, '').slice(0, 60) || name;
  return { key: key, slug: slugify(sl) || key, status: 'draft', updated: '', name: name, short: short, common: short.split(' ')[0].toLowerCase(), botanical: botanical || '', part: '', tag: '', unit_mode: 'kg', box: '100 kg', title: name + ' in Bulk | Global Palate', meta: '', h1: 'Bulk ' + name + ', shipped from U.S. stock', lead: '', card: '', desc: [''], specs: [['Botanical name', botanical || ''], ['Plant part', ''], ['Country of origin', 'India'], ['Shelf life', ''], ['Storage', 'Cool, dry place; airtight container']], purity: [], ttk_sub: '', ttk: [], faq: [], plant: '', look: '', alt: name, image: { src: 'static', id: '' }, seo: { canonical: '', noindex: false, og_title: '', og_desc: '', focus_keyword: '' }, commercial: blankCommercial(), tests: STANDARD.map(function (x) { return { param: x, limit: '', method: '', result: '' }; }) };
}
function preSave() {
  var today = new Date().toISOString().slice(0, 10), added = [];
  S.data.products.forEach(function (p) {
    var c = JSON.parse(JSON.stringify(p)); delete c.updated;
    if (S.origJson[p.key] !== JSON.stringify(c)) p.updated = today;
    var old = S.origSlug[p.key];
    if (old && old !== p.slug && p.status === 'published') { var from = '/product/' + old + '/', to = '/product/' + p.slug + '/'; if (!S.data.redirects.some(function (r) { return r.from === from; })) { S.data.redirects.push({ from: from, to: to }); added.push(from); } }
  });
  S.data.redirects = S.data.redirects.filter(function (r) { return r.from !== r.to; });
  return added;
}
function save(quiet) {
  var added = preSave();
  return api('data', { method: 'PUT', body: { data: S.data, baseRev: S.rev } }).then(function (x) {
    if (x.status === 401) { showLogin('Session expired. Sign in again; your edits are still on screen.'); return false; }
    if (x.status === 409) { modal('Newer changes exist', '<p>' + esc(x.j.error) + '</p>', [{ label: 'Reload (discard my edits)', cls: 'primary', fn: function () { load(); } }, { label: 'Keep editing', fn: function () {} }]); return false; }
    if (!x.j.ok) { modal('Fix this before saving', '<ul>' + (x.j.errors || [x.j.error]).map(function (e) { return '<li>' + esc(e) + '</li>'; }).join('') + '</ul>', [{ label: 'OK', cls: 'primary', fn: function () {} }]); return false; }
    S.data = x.j.data; S.rev = x.j.rev; S.dirty = false; S.pub.same = false; snapshot(); render();
    if (!quiet) toast('Draft saved' + (added.length ? ' · redirect added for ' + added.join(', ') : ''));
    return true;
  });
}
function publish() {
  (S.dirty ? save(true) : Promise.resolve(true)).then(function (ok) {
    if (!ok) return;
    var live = S.data.products.filter(function (p) { return p.status === 'published'; }), low = live.filter(function (p) { return score(p).pct < 65; });
    var body = '<p>This makes your saved draft the live version and rebuilds the website.</p><ul><li>' + live.length + ' published products, ' + (S.data.products.length - live.length) + ' drafts (not shown)</li><li>' + (low.length ? low.length + ' product(s) with an SEO score under 65%: ' + esc(low.map(function (p) { return p.name; }).join(', ')) : 'All published products score 65% or higher') + '</li></ul>' + (S.hook ? '' : '<p class="err">No deploy hook is configured, so the site will not rebuild automatically. See the setup guide.</p>');
    modal('Publish to the live site?', body, [{ label: 'Cancel', fn: function () {} }, { label: 'Publish now', cls: 'primary', fn: function () { api('publish', { method: 'POST', body: {} }).then(function (x) { if (x.j.ok) { S.pub = { same: true, at: new Date().toISOString() }; chrome(); toast(x.j.note || 'Published', !x.j.triggered && S.hook); } else toast(x.j.error || 'Publish failed', true); }); } }]);
  });
}
function prepImage(file) {
  return createImageBitmap(file).then(function (bm) {
    var s = Math.min(1, 1400 / Math.max(bm.width, bm.height)), c = D.createElement('canvas'); c.width = Math.round(bm.width * s); c.height = Math.round(bm.height * s); c.getContext('2d').drawImage(bm, 0, 0, c.width, c.height);
    return new Promise(function (res) { c.toBlob(function (b) { if (b && b.size < 4 * 1024 * 1024) res(b); else c.toBlob(function (b2) { res(b2); }, 'image/jpeg', .85); }, 'image/webp', .88); });
  });
}
D.addEventListener('click', function (e) {
  var mb = e.target.closest && e.target.closest('[data-mbtn]'); if (mb) { var b = modal.btns[+mb.dataset.mbtn]; closeModal(); if (b && b.fn) b.fn(); return; }
  var t = e.target.closest && e.target.closest('[data-act]'); if (!t) return; var a = t.dataset.act, i = +t.dataset.i;
  if (a === 'nav') { S.view = t.dataset.view; render(); }
  else if (a === 'tab') { S.tab = t.dataset.tab; render(); }
  else if (a === 'edit') { S.pi = i; S.tab = 'basics'; S.view = 'product'; render(); window.scrollTo(0, 0); }
  else if (a === 'up' || a === 'down') { var j = a === 'up' ? i - 1 : i + 1, ps = S.data.products; if (j >= 0 && j < ps.length) { var x = ps[i]; ps[i] = ps[j]; ps[j] = x; markDirty(); render(); } }
  else if (a === 'dup') { var c = JSON.parse(JSON.stringify(S.data.products[i])); c.key = uniqueKey(c.key + '-copy'); c.slug = slugify(c.slug + '-copy'); c.name += ' (copy)'; c.status = 'draft'; c.updated = ''; c.title = c.name + ' | Global Palate'; S.data.products.splice(i + 1, 0, c); markDirty(); render(); toast('Duplicated as a draft. Edit its URL slug and title.'); }
  else if (a === 'newp') { modal('Add a product', '<label for="np1">Product name</label><input id="np1" placeholder="Organic Black Pepper Powder"><label for="np2">Botanical (Latin) name</label><input id="np2" placeholder="Piper nigrum"><p class="hint">It starts as a draft with the standard test rows. Fill in the tabs, then set it to Published.</p>', [{ label: 'Cancel', fn: function () {} }, { label: 'Create draft', cls: 'primary', fn: function () { var n = ($('#np1') || {}).value; } }]); var cb = $('#ma .btn:last-child'); cb.dataset.mbtn = 'x'; cb.dataset.create = '1'; $('#np1').focus(); }
  else if (a === 'delp') { var p = S.data.products[i]; modal('Delete "' + p.name + '"?', '<p>This removes the product and its page on the next publish. You can bring it back from History.</p><label><input type="checkbox" id="delRed" checked> Redirect /product/' + esc(p.slug) + '/ to the homepage</label><p class="hint">Prefer to hide it temporarily? Set its status to Draft instead.</p>', [{ label: 'Cancel', fn: function () {} }, { label: 'Delete product', cls: 'danger solid', fn: function () { if (p.status === 'published' && $('#delRed') && false) {} } }]); var db = $('#ma .btn:last-child'); db.dataset.mbtn = 'x'; db.dataset.del = i; }
  else if (a === 'add') { var arr = get(t.dataset.path); if (!arr) { set(t.dataset.path, []); arr = get(t.dataset.path); } arr.push(JSON.parse(t.dataset.tpl)); markDirty(); render(); }
  else if (a === 'del') { get(t.dataset.path).splice(+t.dataset.idx, 1); markDirty(); render(); }
  else if (a === 'stdtests') { var p2 = P(), have = p2.tests.map(function (x) { return x.param; }); STANDARD.forEach(function (s) { if (have.indexOf(s) < 0) p2.tests.push({ param: s, limit: '', method: '', result: '' }); }); markDirty(); render(); }
  else if (a === 'restore') { modal('Restore this version?', '<p>It becomes your current draft. Nothing goes live until you publish.</p>', [{ label: 'Cancel', fn: function () {} }, { label: 'Restore', cls: 'primary', fn: function () { api('history/restore', { method: 'POST', body: { id: t.dataset.id } }).then(function (x) { if (x.j.ok) { toast('Restored as draft'); S.view = 'products'; load(); } else toast(x.j.error, true); }); } }]); }
});
// modal buttons that need the live DOM (create / delete) are handled here before the generic handler
D.addEventListener('click', function (e) {
  var b = e.target.closest && e.target.closest('#ma .btn'); if (!b) return;
  if (b.dataset.create) { e.stopImmediatePropagation(); var n = $('#np1').value.trim(); if (!n) { $('#np1').focus(); return; } var np = newProduct(n, $('#np2').value.trim()); closeModal(); S.data.products.push(np); S.pi = S.data.products.length - 1; S.tab = 'basics'; S.view = 'product'; markDirty(); render(); toast('Draft created. Fill in the tabs, then Save.'); }
  else if (b.dataset.del != null && b.dataset.del !== '') { e.stopImmediatePropagation(); var i = +b.dataset.del, p = S.data.products[i], red = $('#delRed') && $('#delRed').checked; closeModal(); S.data.products.splice(i, 1); if (red && p.status === 'published') S.data.redirects.push({ from: '/product/' + p.slug + '/', to: '/' }); markDirty(); S.view = 'products'; render(); toast('Deleted. Save to keep the change.'); }
}, true);
D.addEventListener('keydown', function (e) { if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); if (S.data) save(); } if (e.key === 'Escape' && !$('#modal').hidden) closeModal(); });
function onEdit(e) {
  var el = e.target; if (el.id === 'q') { S.q = el.value; var pos = el.selectionStart; $('#main').innerHTML = viewProducts(); var q = $('#q'); q.focus(); q.setSelectionRange(pos, pos); return; }
  if (el.id === 'pq') { S.pq = el.value; var pos2 = el.selectionStart; $('#main').innerHTML = viewPages(); counters(); var q2 = $('#pq'); q2.focus(); q2.setSelectionRange(pos2, pos2); return; }
  if (el.id === 'imgFile') return;
  if (!el.dataset || !el.dataset.bind) return;
  var v = el.type === 'checkbox' ? el.checked : el.value;
  if (el.dataset.lines) v = v.split('\n').map(function (x) { return x.trim(); }).filter(Boolean);
  if (el.dataset.slug && e.type === 'change') { v = slugify(v); el.value = v; }
  set(el.dataset.bind, v); markDirty();
  if (el.dataset.count) counters();
  if (S.view === 'product') live();
}
D.addEventListener('input', onEdit); D.addEventListener('change', function (e) {
  if (e.target.id === 'imgFile' && e.target.files[0]) {
    var f = e.target.files[0], m = $('#imgMsg'); m.textContent = 'Uploading…';
    prepImage(f).then(function (blob) { return api('upload', { method: 'POST', body: blob, raw: true, type: blob.type }); }).then(function (x) {
      if (!x.j.ok) { m.textContent = x.j.error || 'Upload failed'; return; }
      var p = P(); p.image = { src: 'kv', id: x.j.id }; markDirty(); $('#imgPrev').src = '/api/img/' + x.j.id; $('#imgPrev').style.visibility = 'visible'; m.textContent = 'Uploaded. Save the draft to keep it.'; live();
    }).catch(function () { m.textContent = 'Could not read that image.'; });
    return;
  }
  onEdit(e);
});
$('#loginForm').addEventListener('submit', function (e) {
  e.preventDefault(); var err = $('#loginErr'); err.hidden = true;
  api('login', { method: 'POST', body: { password: $('#pw').value } }).then(function (x) { if (x.j.ok) { $('#pw').value = ''; load(); } else { err.textContent = x.j.error || 'Sign in failed'; err.hidden = false; } });
});
$('#saveBtn').addEventListener('click', function () { save(); });
$('#publishBtn').addEventListener('click', publish);
$('#logoutBtn').addEventListener('click', function () { api('logout', { method: 'POST', body: {} }).then(function () { S.data = null; showLogin(); }); });
window.addEventListener('beforeunload', function (e) { if (S.dirty) { e.preventDefault(); e.returnValue = ''; } });
boot();
})();
