# -*- coding: utf-8 -*-
"""Builds the static site into ./out from data/site-data.json.
Cloudflare Pages build command:  pip install -r requirements.txt && python3 build/build.py
If EXPORT_URL and BUILD_TOKEN are set, the published admin data is downloaded first (falls back to the committed seed if that fails)."""
import os, sys, io, json, shutil, re, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
SCRATCH = os.path.join(ROOT, '.build-cache'); os.makedirs(SCRATCH, exist_ok=True)

def fetch_data():
    url, tok = os.environ.get('EXPORT_URL'), os.environ.get('BUILD_TOKEN')
    if not (url and tok): return None
    try:
        req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + tok, 'User-Agent': 'gp-build'})
        raw = urllib.request.urlopen(req, timeout=30).read()
        data = json.loads(raw)
        assert data.get('products') is not None
        path = os.path.join(SCRATCH, 'published.json'); open(path, 'wb').write(raw)
        print('Using published admin data from', url, '(', len(data['products']), 'products )')
        return path
    except Exception as e:
        print('WARNING: could not fetch published data (%s). Building from data/site-data.json instead.' % e); return None
_p = fetch_data()
if _p: os.environ['GP_SITE_DATA'] = _p

from lib import *
import lib, pages1, pages2
from PIL import Image, ImageDraw, ImageFont

# ---- clean output, copy static files ----
if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree(os.path.join(ROOT, 'public'), OUT)

# ---- product images ----
def load_font(sz, bold=True):
    for pth in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'):
        if os.path.exists(pth): return ImageFont.truetype(pth, sz)
    try: return ImageFont.load_default(sz)      # Pillow >= 10.1: scalable built-in font
    except TypeError: return ImageFont.load_default()
def square(im, size):
    im = im.convert('RGBA'); w, h = im.size; s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)); return im.resize((size, size), Image.LANCZOS)
def placeholder(p, size):
    im = Image.new('RGBA', (size, size), (225, 220, 242, 255)); d = ImageDraw.Draw(im)
    d.ellipse((size * .12, size * .12, size * .88, size * .88), fill=(255, 255, 255, 255))
    f = load_font(int(size * .3)); t = (p['short'][:1] or '?').upper()
    w = d.textlength(t, font=f); d.text(((size - w) / 2, size * .33), t, font=f, fill=(34, 64, 41, 255)); return im
def img_bytes(p):
    spec = p.get('image') or {}
    if spec.get('src') == 'kv' and spec.get('id'):
        base = os.environ.get('IMG_BASE') or (os.environ.get('EXPORT_URL', '').split('/api/')[0])
        local = os.path.join(SCRATCH, 'img-' + spec['id'])
        if spec.get('path') and os.path.exists(spec['path']): return open(spec['path'], 'rb').read()
        if base:
            try:
                req = urllib.request.Request(f"{base}/api/img/{spec['id']}", headers={'User-Agent': 'gp-build'}); return urllib.request.urlopen(req, timeout=30).read()
            except Exception as e: print('WARNING: image download failed for', p['key'], e)
        elif os.path.exists(local): return open(local, 'rb').read()
    return None
for p in PRODUCTS:
    for sz in (320, 640):
        dst = f"{OUT}/images/{p['key']}-{sz}.webp"
        b = img_bytes(p)
        if b:
            try: square(Image.open(io.BytesIO(b)), sz).save(dst, 'WEBP', quality=82, method=6); continue
            except Exception as e: print('WARNING: bad image for', p['key'], e)
        if not os.path.exists(dst):
            print('NOTE: no image for', p['key'], '- using placeholder'); placeholder(p, sz).save(dst, 'WEBP', quality=82)

# ---- pages ----
write('/', pages1.home())
for p in PRODUCTS:
    write(ppath(p), pages1.product_page(p), indexable=not p['seo'].get('noindex'))
    LASTMOD[ppath(p)] = (p.get('updated') or SITE['date'])[:10]
if pages1.HAS_REGIONS:
    t = PRODUCT_BY_KEY['turmeric']
    write(ppath(t) + 'west-coast/', pages1.region_page('west-coast')); write(ppath(t) + 'east-coast/', pages1.region_page('east-coast'))
write('/industries/', pages2.industries_hub())
for i in INDUSTRIES: write(f"/industries/{i['slug']}/", pages2.industry_page(i))
write('/ordering/', pages2.ordering()); write('/about/', pages2.about()); write('/contact/', pages2.contact()); write('/quality/', pages2.quality()); write('/supply-chain/', pages2.supply())
for s in pages2.LEGAL: write(f'/{s}/', pages2.legal(s))
for t in pages2.THANKS: write(f'/thank-you/{t}/', pages2.thanks(t), indexable=False)
open(OUT + '/404.html', 'w', encoding='utf-8').write(pages2.notfound())

# ---- owner documents + redirects ----
os.makedirs(OUT + '/documents', exist_ok=True)
docdir = os.path.join(ROOT, 'data', 'documents')
for fn in (os.listdir(docdir) if os.path.isdir(docdir) else []):
    if fn.endswith('.pdf'): shutil.copy(os.path.join(docdir, fn), OUT + '/documents/' + fn)
_red = '# Generated by build.py from the admin (SEO > Redirects). Do not edit by hand.\n/index.html   /   301\n'
for r in REDIRECTS:
    a, b = (r.get('from') or '').strip(), (r.get('to') or '').strip()
    if a.startswith('/') and (b.startswith('/') or b.startswith('http')) and a != b: _red += f'{a}  {b}  301\n'
_nl = co('Netlify address').replace('https://', '').replace('http://', '').strip('/ ')
if _nl: _red += f'https://{_nl}/*  https://globalpalate.co/:splat  301!\n'
open(OUT + '/_redirects', 'w').write(_red)

# ---- OG images ----
def font(sz, bold=True):
    return load_font(sz, bold)
logo = Image.open(os.path.join(HERE, 'src', 'logo-full.png')); logo.thumbnail((380, 160))
def og(name, title, sub, key=None):
    im = Image.new('RGB', (1200, 630), (225, 220, 242)); d = ImageDraw.Draw(im)
    d.rectangle((0, 560, 1200, 630), fill=(34, 64, 41))
    im.paste(logo, (60, 50), logo)
    words, lines, cur_l = title.split(), [], ''
    for w in words:
        t = (cur_l + ' ' + w).strip()
        if d.textlength(t, font=font(54)) < (600 if key else 1050): cur_l = t
        else: lines.append(cur_l); cur_l = w
    lines.append(cur_l)
    y = 250
    for l in lines[:4]: d.text((60, y), l, font=font(54), fill=(34, 64, 41)); y += 66
    d.text((60, y + 10), sub[:60], font=font(28, False), fill=(79, 95, 85))
    d.text((60, 580), 'globalpalate.co', font=font(28), fill=(255, 255, 255))
    if key:
        ph = Image.open(f'{OUT}/images/{key}-640.webp').convert('RGBA').resize((420, 420))
        circ = Image.new('RGBA', (460, 460), (0, 0, 0, 0)); ImageDraw.Draw(circ).ellipse((0, 0, 459, 459), fill=(255, 255, 255, 255))
        circ.paste(ph, (20, 20), ph); im.paste(circ, (700, 70), circ)
    im.save(f'{OUT}/images/{name}', 'JPEG', quality=80, optimize=True)
og('og-default.jpg', 'Certified organic ingredients, shipped from U.S. stock', pages1.names())
for p in PRODUCTS: og(f"og-{p['key']}.jpg", p['name'], 'Bulk, from our Compton, CA warehouse', p['key'])

# ---- SEO files ----
urls = ''.join(f"  <url><loc>{BASE}{p}</loc><lastmod>{LASTMOD.get(p, SITE['date'])[:10]}</lastmod></url>\n" for p in PAGES)
open(OUT + '/sitemap.xml', 'w').write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
bots = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'PerplexityBot', 'Google-Extended', 'Applebot-Extended']
extra = (SITE.get('robots_extra') or '').strip()
open(OUT + '/robots.txt', 'w').write('User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /admin/\nDisallow: /thank-you/\n' + (extra + '\n' if extra else '') + '\n' + ''.join(f'User-agent: {b}\nAllow: /\n\n' for b in bots) + f'Sitemap: {BASE}/sitemap.xml\n')
reg = ''
if pages1.HAS_REGIONS:
    reg = f"- [Turmeric for the West Coast]({BASE}{ppath(PRODUCT_BY_KEY['turmeric'])}west-coast/)\n- [Turmeric for the East Coast]({BASE}{ppath(PRODUCT_BY_KEY['turmeric'])}east-coast/)\n"
llms = f"""# Global Palate

> Global Palate is a U.S.-based B2B supplier of certified organic ingredients ({pages1.names()}) for manufacturers in the United States and Canada. Inventory is held in Compton, California. Every batch ships with a Certificate of Analysis.

## Products
""" + ''.join(f"- [{p['name']}]({BASE}{ppath(p)}): {p['card']}\n" for p in PRODUCTS if not p['seo'].get('noindex')) + reg + """
## Industries
""" + ''.join(f"- [{i['short']}]({BASE}/industries/{i['slug']}/): {i['blurb']}\n" for i in INDUSTRIES) + f"""
## Company
- [Quality & documentation]({BASE}/quality/)
- [Ordering & terms]({BASE}/ordering/)
- [Supply chain]({BASE}/supply-chain/)
- [About]({BASE}/about/)
- [Contact]({BASE}/contact/): {SITE['phone']}, {SITE['email']}

## Facts
- Warehouse: {addr(SITE['warehouse'])}. Office: {addr(SITE['office'])}.
- Powders: {SITE['moq']} minimum order.
- Ingredients are supplied for further manufacturing.
"""
open(OUT + '/llms.txt', 'w').write(llms)

# ---- files the admin reads ----
os.makedirs(OUT + '/admin', exist_ok=True)
shutil.copy(os.environ.get('GP_SITE_DATA') or os.path.join(ROOT, 'data', 'site-data.json'), OUT + '/admin/seed.json')
json.dump({k: v for k, v in PAGE_DEFAULTS.items() if v['kind'] == 'page' and not k.startswith('/thank-you/')}, open(OUT + '/admin/pages.json', 'w'), indent=1)
for w in D.get('warnings', []): print('DATA WARNING', w)
print('pages:', len(PAGES), '| products:', len(PRODUCTS))
for x in lib.PROBLEMS: print('PROBLEM', x)
