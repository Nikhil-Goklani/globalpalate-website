# -*- coding: utf-8 -*-
"""Loads the site data JSON (written by the admin) and exposes it in the shapes the page builders use."""
import os, re, json, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.environ.get('GP_SITE_DATA') or os.path.join(ROOT, 'data', 'site-data.json')

CMAP = [('price_from', 'Price from (USD)'), ('price_to', 'Price to (USD)'), ('price_unit', 'Price unit'), ('price_basis', 'Price basis'), ('tiers', 'Volume tiers'),
        ('price_valid', 'Price valid as of'), ('in_stock', 'In stock'), ('qty', 'Quantity on hand'), ('ships_within', 'Ships within'), ('lot', 'Lot / crop year'),
        ('pack_format', 'Pack format'), ('net_weight', 'Net weight per pack'), ('packs_per_pallet', 'Packs per pallet'), ('pallet_net', 'Pallet net weight (kg)'),
        ('origin_region', 'Origin region'), ('supplier', 'Supplier / processor name'), ('last_audit', 'Last audit')]

def _clean(v):
    v = re.sub(r'\s*\((?:as )?stated in (?:the )?product title\)', '', v or '', flags=re.I).strip()
    return '' if v.lower() in ('not stated', 'n/a', 'na', 'none') else v
def _num(s):
    m = re.match(r'\s*[<>~]?\s*([\d.]+)', s or '')
    try: return float(m.group(1)) if m else None
    except ValueError: return None

def load(path=None):
    path = path or PATH
    with open(path, encoding='utf-8') as f: raw = json.load(f)
    warn = []
    products = [dict(p) for p in raw.get('products', []) if p.get('status', 'published') == 'published' and p.get('key') and p.get('slug')]
    seen_slug = set()
    for p in products:
        if p['slug'] in seen_slug: warn.append(f"duplicate slug {p['slug']} on {p['key']}")
        seen_slug.add(p['slug'])
        p.setdefault('price', None)
        p['specs'] = [tuple(x) for x in p.get('specs', []) if len(x) == 2 and x[0]]
        p['ttk'] = [tuple(x) for x in p.get('ttk', []) if len(x) == 2 and x[0]]
        p['faq_extra'] = [tuple(x) for x in p.get('faq', []) if len(x) == 2 and x[0] and x[1]]
        p['desc'] = [d for d in p.get('desc', []) if d.strip()]
        p['purity'] = [d for d in p.get('purity', []) if d.strip()]
        p.setdefault('seo', {}); p.setdefault('unit_mode', 'kg'); p.setdefault('common', p['short'].split()[0].lower())
        p['title'] = p.get('title') or f"{p['name']} in Bulk | Global Palate"
        p['alt'] = p.get('alt') or p['name']
    D = dict(commercial={}, specs={}, certs=[], company={}, transit=[], warnings=warn)
    for p in raw.get('products', []):
        if p.get('status', 'published') != 'published': continue
        c = {hdr: ('' if p.get('commercial', {}).get(k) in (None, '') else str(p['commercial'][k]).strip()) for k, hdr in CMAP}
        if any(c.values()): D['commercial'][p['key']] = c
        for t in p.get('tests', []):
            lim, res, meth = _clean(str(t.get('limit', ''))), _clean(str(t.get('result', ''))), _clean(str(t.get('method', '')))
            mx = re.match(r'(?i)\s*(?:max\.?|nmt|not more than)\s*([\d.]+)', lim)
            if mx and res and re.match(r'\s*[\d.]+\s*(%|ppm)', res) and _num(res) is not None and _num(res) > float(mx.group(1)):
                warn.append(f"{p['key']} / {t.get('param')}: typical result {res} is above the limit {lim}; row not published"); continue
            if lim or res: D['specs'].setdefault(p['key'], []).append(dict(param=t.get('param', ''), limit=lim, method=meth, result=res))
    D['certs'] = [c for c in raw.get('certs', []) if c.get('name') and any(str(v).strip() for k, v in c.items() if k != 'name')]
    D['company'] = {k: v for k, v in raw.get('company', {}).items() if str(v).strip()}
    D['transit'] = [t for t in raw.get('transit', []) if t.get('state') and (t.get('ltl') or t.get('ftl'))]
    seen = {}
    for item, val in list(D['company'].items()):
        if len(val) > 25 and val in seen:
            warn.append(f"Company facts: '{item}' has the same text as '{seen[val]}'; '{item}' not published"); del D['company'][item]
        else: seen.setdefault(val, item)
    return dict(raw=raw, settings=raw.get('settings', {}), products=products, D=D, pages=raw.get('pages', {}), redirects=raw.get('redirects', []))
