# -*- coding: utf-8 -*-
import os, json, html
from content import *
import site_data
from site_data import ROOT
OUT = os.path.join(ROOT, 'out')
_SD = site_data.load()
D = _SD['D']
PRODUCTS = _SD['products']                 # replaces the defaults in content.py
SITE.update({k: v for k, v in _SD['settings'].items() if v not in (None,)})
SITE['date'] = _SD['raw'].get('updated') or SITE['date']
PAGE_DEFAULTS = {}
PAGE_SEO = _SD['pages']; REDIRECTS = _SD['redirects']; LASTMOD = {}
_co = D['company']
if SITE['response'][:1].isupper(): SITE['response'] = SITE['response'][0].lower() + SITE['response'][1:]
import re as _re
SITE['moq'] = _re.sub(r'(\d)\s*kg', r'\1 kg', SITE['moq'], flags=_re.I)
def co(item, default=''): return _co.get(item, default)
def _num(v):
    try: return float(str(v).replace('$', '').replace(',', '').strip())
    except Exception: return None
def com(p): return D['commercial'].get(p['key'], {})
def tidy(s):
    s = _re.sub(r'(\d)\s*kg\b', r'\1 kg', s, flags=_re.I)
    s = _re.sub(r'(\d)\s*MT\b', r'\1 MT', s)
    return s.replace('Business Days', 'business days').replace('Business days', 'business days').strip()
def cf(p, name):
    for k, v in com(p).items():
        if k.startswith(name) and str(v).strip(): return tidy(str(v).strip())
    return ''
def in_stock(p): return cf(p, 'In stock').lower() in ('yes', 'y', 'true')
def price_of(p):
    lo, hi = _num(cf(p, 'Price from')), _num(cf(p, 'Price to'))
    unit = cf(p, 'Price unit') or 'kg'
    basis = cf(p, 'Price basis') or co('Default price basis')
    if lo is not None:
        return (lo, hi if hi is not None else lo, unit, basis)
    return None
def lead(p=None):
    if p is not None and in_stock(p) and cf(p, 'Ships within'): return 'In stock, ships within ' + cf(p, 'Ships within') + '.'
    return SITE['lead_time']
def cert_rows(p):
    out = []
    for c in D['certs']:
        ap = [x.strip().lower() for x in c['applies'].replace(';', ',').split(',') if x.strip()]
        if not ap or 'all' in ap or p['key'] in ap: out.append(c)
    return out
def norm_tiers(t):
    out = []
    for ln in t.split('\n'):
        ln = ln.strip()
        if not ln: continue
        ln = _re.sub(r'\$(\d+\.\d)\.00', r'$\g<1>0', ln)               # $7.5.00 -> $7.50
        ln = _re.sub(r'\$(\d+\.\d)(?!\d)', r'$\g<1>0', ln)               # $7.8 -> $7.80
        ln = _re.sub(r'(\d)\s*kg', r'\1 kg', ln, flags=_re.I); ln = _re.sub(r'(\d)\s*MT', r'\1 MT', ln, flags=_re.I)
        out.append(ln)
    return '\n'.join(out)
def pack_weight(p):
    m = _re.search(r'(\d+(?:\.\d+)?)\s*kg', cf(p, 'Pack format'), _re.I)
    return float(m.group(1)) if m else None
def pack_ok(p):
    """False when the pack format weight disagrees with 'net weight per pack' or pallet maths; those rows are then not published."""
    w, n = pack_weight(p), _num(cf(p, 'Net weight'))
    ok = not (w and n and abs(w - n) > 0.01)
    if ok:
        packs, pal = _num(cf(p, 'Packs per pallet')), _re.match(r'\s*([\d.]+)\s*(kg|mt)?', cf(p, 'Pallet net'), _re.I)
        wt = n or w
        if packs and wt and pal:
            tot = float(pal.group(1)) * (1000 if (pal.group(2) or '').lower() == 'mt' else 1)
            ok = abs(packs * wt - tot) < 1
    if not ok and cf(p, 'Pack format') and p['key'] not in _PACK_WARNED:
        _PACK_WARNED.add(p['key']); D.setdefault('warnings', []).append(f"{p['key']}: pack format '{cf(p,'Pack format')}', net weight per pack {cf(p,'Net weight')}, {cf(p,'Packs per pallet')} packs/pallet and pallet {cf(p,'Pallet net')} do not agree; pack and pallet rows not published")
    return ok
_PACK_WARNED = set()
def fmt_qty(p):
    q = cf(p, 'Quantity on hand')
    if not q: return ''
    n = _num(q)
    if n is not None and _re.fullmatch(r'[\d.,]+', q): return f"{n:,.0f} kg"
    return q
def spec_rows(p): return D['specs'].get(p['key'], [])

BASE = SITE['base']
E = lambda s: html.escape(s, quote=True)
PAGES = []
PROBLEMS = []   # (path, indexable, priority-ish)
PRODUCT_BY_KEY = {p['key']: p for p in PRODUCTS}

def depth(path): return 0 if path == '/' else path.strip('/').count('/') + 1
def rel(cur, target):
    frag = ''
    if '#' in target: target, frag = target.split('#', 1); frag = '#' + frag
    t = target.strip('/'); pre = '../' * depth(cur)
    return pre + (t + '/index.html' if t else 'index.html') + frag
def asset(cur, p): return '../' * depth(cur) + p
def ppath(p): return f"/product/{p['slug']}/"

IC = dict(
 leaf='<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 20a15 15 0 0 1 15-15h1v1a15 15 0 0 1-15 15H5z"/><path d="M5 20 19 6"/></svg>',
 flask='<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 2v6L4 18a2 2 0 0 0 2 3h12a2 2 0 0 0 2-3l-5-10V2"/><path d="M9 2h6"/></svg>',
 box='<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 8 12 3 3 8l9 5 9-5Z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/></svg>',
 check='<svg viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>',
 truck='<svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M1 6h13v10H1zM14 10h5l3 3v3h-8"/><circle cx="6" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>',
)

def cta(cur, label='Request a quote', cls='btn btn-primary', sample=False, product=None):
    a = f' data-product="{product}"' if product else ''
    return f'<a class="{cls}" href="{rel(cur, "/contact/#quote")}" data-quote="{"sample" if sample else "quote"}"{a}>{label}</a>'

def check_meta(path, title, desc):
    if 'thank-you' not in path and not title.startswith('Page not found'):
        if not 140 <= len(desc) <= 160: PROBLEMS.append(f'{path}: meta description {len(desc)} chars: {desc}')
        if len(title) > 68: PROBLEMS.append(f'{path}: title {len(title)}: {title}')

def addr(a): return f"{a['street']}, {a['city']}, {a['state']} {a['zip']}"

def crumb_ld(crumbs):
    items = [("Home", "/")] + crumbs
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + p} for i, (n, p) in enumerate(items)]}
def faq_ld(faqs):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
def org_ld():
    w, o = SITE['warehouse'], SITE['office']
    def biz(n, a, role):
        return {"@type": "LocalBusiness", "@id": f"{BASE}/#{role}", "name": n, "url": BASE + "/", "telephone": SITE['phone'], "email": SITE['email'],
                "image": BASE + "/images/logo.webp", "parentOrganization": {"@id": BASE + "/#org"},
                "address": {"@type": "PostalAddress", "streetAddress": a['street'], "addressLocality": a['city'], "addressRegion": a['state'], "postalCode": a['zip'], "addressCountry": "US"}}
    return {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": BASE + "/#org", "name": "Global Palate", "url": BASE + "/", "logo": BASE + "/images/logo.webp",
         "email": SITE['email'], "telephone": SITE['phone'], "parentOrganization": {"@type": "Organization", "name": SITE['parent']},
         "areaServed": ["US", "CA"], "description": "U.S.-based B2B distributor of certified organic ingredients.", **({"sameAs": SITE['same_as']} if SITE.get('same_as') else {})},
        biz("Global Palate \u2013 Compton, CA warehouse", w, "compton"),
        biz("Global Palate \u2013 Edison, NJ office", o, "edison"),
        {"@type": "WebSite", "@id": BASE + "/#site", "url": BASE + "/", "name": "Global Palate", "publisher": {"@id": BASE + "/#org"}}]}
def product_ld(p):
    d = {"@context": "https://schema.org", "@type": "Product", "name": p['name'], "description": p['meta'],
         "image": [f"{BASE}/images/{p['key']}-640.webp"], "category": "Organic ingredients",
         "brand": {"@type": "Brand", "name": "Global Palate"}, "url": BASE + ppath(p), "sku": p['key'],
         "additionalProperty": [{"@type": "PropertyValue", "name": "Botanical name", "value": p['botanical']}, {"@type": "PropertyValue", "name": "Plant part", "value": p['part']}]}
    pr = price_of(p)
    if pr and pr[2] == 'kg':
        d["offers"] = {"@type": "AggregateOffer", "priceCurrency": "USD", "lowPrice": f"{pr[0]:.2f}", "highPrice": f"{pr[1]:.2f}", "url": BASE + ppath(p), "seller": {"@id": BASE + "/#org"}}
        if in_stock(p): d["offers"]["availability"] = "https://schema.org/InStock"
    return d

NAV = [("Industries", "/industries/"), ("Quality & Documentation", "/quality/"), ("Supply Chain", "/supply-chain/"), ("About", "/about/"), ("Contact", "/contact/")]

def layout(cur, title, desc, body, schema=(), og='og-default.jpg', noindex=False, crumbs=None, conv=None, nav=None, seo=None):
    PAGE_DEFAULTS.setdefault(cur, {'title': title, 'description': desc, 'noindex': bool(noindex), 'kind': 'product' if cur.startswith('/product/') else 'page'})
    ov = dict(PAGE_SEO.get(cur, {})); ov.update({k: v for k, v in (seo or {}).items() if v})
    title = ov.get('title') or title; desc = ov.get('description') or desc
    noindex = noindex or bool(ov.get('noindex'))
    og_title = ov.get('og_title') or title; og_desc = ov.get('og_desc') or desc
    check_meta(cur, title, desc)
    pre = '../' * depth(cur)
    canon = ov.get('canonical') or BASE + (cur if cur.endswith('/') or cur == '/' else cur)
    ld = list(schema)
    if crumbs: ld.append(crumb_ld(crumbs))
    ldh = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in ld)
    for x in ld: json.loads(json.dumps(x))
    robots = '<meta name="robots" content="noindex,follow">\n' if noindex else ''
    items = ''.join(f'<a href="{rel(cur, p)}"' + (' aria-current="page"' if nav == p else '') + f'>{E(n)}</a>' for n, p in NAV[:4])
    prods = ''.join(f'<a href="{rel(cur, ppath(p))}">{E(p["name"])}</a>' for p in PRODUCTS)
    products_item = f'<div class="nav-item"><a href="{rel(cur, "/#products")}"' + (' aria-current="page"' if nav == 'products' else '') + f'>Products</a><div class="menu">{prods}</div></div>'
    contact = f'<a href="{rel(cur, "/contact/")}"' + (' aria-current="page"' if nav == '/contact/' else '') + '>Contact</a>'
    show = E(SITE['show']).replace('Book a meeting now!', f'<a href="{rel(cur, "/contact/#meeting")}" style="color:#fff;text-decoration:underline">Book a meeting now!</a>')
    tel = SITE['phone'].replace(' ', '')
    bar = ("""<div class="bar" role="region" aria-label="Announcement"><div class="marquee"><div class="track"><span>%s</span></div></div><button type="button" class="bar-pause" aria-pressed="false">Pause</button><button type="button" class="bar-close" aria-label="Dismiss announcement">&#10005;</button></div>""" % show) if SITE.get('show') else ''
    og_abs = f"{BASE}/images/{og}"
    ga = f'<meta name="gp-ga4" content="{E(SITE["ga4"])}">\n' if SITE['ga4'] else ''
    if SITE.get('gsc_verification'): ga += f'<meta name="google-site-verification" content="{E(SITE["gsc_verification"])}">\n'
    ts = f'<meta name="gp-turnstile" content="{SITE["turnstile"]}">\n' if SITE['turnstile'] else ''
    cookie = '<div class="cookie" role="dialog" aria-label="Cookie preferences" hidden><p>We use analytics cookies to understand how the site is used. <a href="%s">Cookie policy</a></p><div class="acts"><button class="btn btn-sm" data-no>Decline</button><button class="btn btn-sm btn-dark" data-yes>Accept</button></div></div>' % rel(cur, '/cookie-policy/') if SITE['ga4'] else ''
    foot_prods = ''.join(f'<li><a href="{rel(cur, ppath(p))}">{E(p["short"])}</a></li>' for p in PRODUCTS)
    conv_attr = f' data-conv="{conv}"' if conv else ''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
{robots}<link rel="canonical" href="{canon}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Global Palate">
<meta property="og:title" content="{E(og_title)}"><meta property="og:description" content="{E(og_desc)}">
<meta property="og:url" content="{canon}"><meta property="og:image" content="{og_abs}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(og_title)}"><meta name="twitter:description" content="{E(og_desc)}"><meta name="twitter:image" content="{og_abs}">
<meta name="theme-color" content="#224029">
{ga}{ts}<link rel="icon" type="image/png" sizes="32x32" href="{pre}favicon-32.png"><link rel="icon" type="image/png" sizes="192x192" href="{pre}favicon-192.png"><link rel="apple-touch-icon" href="{pre}apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800&amp;family=IBM+Plex+Sans:wght@400;600&amp;display=swap">
<link rel="stylesheet" href="{pre}assets/css/site.css">
{ldh}</head>
<body data-root="{pre}" data-products="{E(json.dumps([[p['key'], p['short']] for p in PRODUCTS]))}" data-phone="{SITE['phone']}" data-email="{SITE['email']}" data-hours="{SITE['hours']}" data-response="{SITE['response']}"{conv_attr}>
<a class="skip" href="#main">Skip to main content</a>
{bar}
<header class="site"><div class="wrap">
<a class="logo" href="{rel(cur, '/')}" aria-label="Global Palate home"><img src="{pre}images/logo.webp" width="520" height="219" alt="Global Palate"></a>
<nav class="primary" id="nav" aria-label="Main">{products_item}{items}{contact}</nav>
<div class="head-actions"><a class="tel mono" href="tel:{tel}">{SITE['phone']}</a>{cta(cur, 'Request a quote', 'btn btn-primary btn-sm')}<button class="burger" type="button" aria-expanded="false" aria-controls="nav">Menu</button></div>
</div></header>
<main id="main">
{body}
</main>
<footer class="site"><div class="wrap">
<div class="fg"><div><img class="fl" src="{pre}images/logo-white.webp" width="520" height="219" alt="Global Palate" loading="lazy">
<address><strong>Warehouse:</strong> {E(addr(SITE['warehouse']))}<br><strong>Office:</strong> {E(addr(SITE['office']))}<br><a href="tel:{tel}">{SITE['phone']}</a> &middot; <a href="tel:{SITE['phone2'].replace(' ','')}">{SITE['phone2']}</a><br><a href="mailto:{SITE['email']}">{SITE['email']}</a></address></div>
<div><h4>Products</h4><ul>{foot_prods}</ul></div>
<div><h4>Company</h4><ul><li><a href="{rel(cur,'/about/')}">About</a></li><li><a href="{rel(cur,'/industries/')}">Industries</a></li><li><a href="{rel(cur,'/quality/')}">Quality &amp; documentation</a></li><li><a href="{rel(cur,'/supply-chain/')}">Supply chain</a></li><li><a href="{rel(cur,'/ordering/')}">Ordering &amp; terms</a></li><li><a href="{rel(cur,'/contact/')}">Contact</a></li></ul></div>
<div><h4>Legal</h4><ul><li><a href="{rel(cur,'/privacy/')}">Privacy policy</a></li><li><a href="{rel(cur,'/terms/')}">Terms &amp; conditions</a></li><li><a href="{rel(cur,'/cookie-policy/')}">Cookie policy</a></li></ul></div></div>
<div class="fb"><span>&copy; 2026 Global Palate, a North America division of {E(SITE['parent'])}</span><span>Ingredients are supplied for further manufacturing.</span></div>
</div></footer>
<div class="mbar"><a class="btn btn-sm" href="tel:{tel}">Call</a>{cta(cur, 'Request a quote', 'btn btn-primary btn-sm')}</div>
{cookie}<script src="{pre}assets/js/site.js" defer></script>
</body></html>'''

def write(cur, html_text, indexable=True):
    fp = OUT + ('/index.html' if cur == '/' else cur.rstrip('/') + '/index.html') if not cur.endswith('.html') else OUT + cur
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp, 'w', encoding='utf-8').write(html_text)
    if indexable: PAGES.append(cur)

def crumbs_html(cur, trail):
    parts = [f'<a href="{rel(cur,"/")}">Home</a>'] + [f'<a href="{rel(cur,p)}">{E(n)}</a>' for n, p in trail[:-1]] + [E(trail[-1][0])]
    return f'<nav class="wrap crumbs" aria-label="Breadcrumb">{" / ".join(parts)}</nav>'

def faq_html(faqs, first_open=True):
    return '<div class="faq">' + ''.join(f'<details{" open" if i == 0 and first_open else ""}><summary>{i+1}. {E(q)}</summary><p>{E(a)}</p></details>' for i, (q, a) in enumerate(faqs)) + '</div>'

def page_hero(kicker, h1, lead):
    return f'<section class="page-hero"><div class="wrap"><span class="kicker">{E(kicker)}</span><h1>{E(h1)}</h1><p>{E(lead)}</p></div></section>'

def band(cur, h, p):
    return f'<section class="sec alt"><div class="wrap"><div class="band"><div><h2>{E(h)}</h2><p>{E(p)}</p></div><div class="hero-cta2">{cta(cur)}{cta(cur,"Request a sample","btn btn-ghost-l",True)}</div></div></div></section>'

def img(cur, key, w, alt, cls='', lazy=True, sizes='(max-width:960px) 260px, 400px'):
    pre = '../' * depth(cur)
    return (f'<img{(" class=%s" % chr(34)+cls+chr(34)) if cls else ""} src="{pre}images/{key}-640.webp" srcset="{pre}images/{key}-320.webp 320w, {pre}images/{key}-640.webp 640w" '
            f'sizes="{sizes}" width="640" height="640" alt="{E(alt)}"{" loading=%slazy%s" % (chr(34),chr(34)) if lazy else ""}>')
