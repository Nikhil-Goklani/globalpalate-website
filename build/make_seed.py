# -*- coding: utf-8 -*-
"""One-off: builds data/site-data.json from the original content.py + the owner's workbook."""
import os, json, datetime, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content, data_loader
from site_data import CMAP, ROOT
D = data_loader.load(os.path.join(ROOT, 'docs', 'legacy-import-workbook.xlsx'))
S = content.SITE
co = D['company']
def cm(key):
    row = D['commercial'].get(key, {})
    out = {}
    for k, hdr in CMAP:
        for h, v in row.items():
            if h.startswith(hdr.split(' (')[0].split(' /')[0]) and str(v).strip(): out[k] = str(v).strip(); break
    return out
today = datetime.date.today().isoformat()
products = []
for p in content.PRODUCTS:
    c = cm(p['key'])
    if p['key'] == 'tamarind': c.setdefault('price_unit', 'kg')
    products.append(dict(key=p['key'], slug=p['slug'], status='published', updated=today, name=p['name'], short=p['short'], common=p['key'], botanical=p['botanical'], part=p['part'], tag=p['tag'],
        unit_mode='drum' if p['key'] == 'tamarind' else 'kg', box=p['box'], title=f"{p['name']} in Bulk | Global Palate", meta=p['meta'], h1=p['h1'], lead=p['lead'], card=p['card'],
        desc=p['desc'], specs=[list(x) for x in p['specs']], purity=p['purity'], ttk_sub=p['ttk_sub'], ttk=[list(x) for x in p['ttk']], faq=[list(x) for x in p['faq_extra']],
        plant=p['plant'], look=p['look'], alt=p['alt'], image=dict(src='static'), seo=dict(canonical='', noindex=False, og_title='', og_desc='', focus_keyword=''),
        commercial=c, tests=[dict(param=r['param'], limit=r['limit'], method=r['method'], result=r['result']) for r in D['specs'].get(p['key'], [])]))
cert = [dict(name=c['name'], applies=c['applies'], holder=c['holder'], htype=c['htype'], certifier=c['certifier'], number=c['number'], expiry=c['expiry'], url=c['url']) for c in D['certs']]
seed = dict(version=1, updated=today,
  settings=dict(phone=S['phone'], phone2=S['phone2'], email=S['email'], hours=co.get('Hours', S['hours']), response=co.get('Reply time', S['response']).lower(), moq=co.get('MOQ (powders)', S['moq']),
     lead_time=co.get('Lead-time statement', S['lead_time']), parent=S['parent'], booking_url=co.get('Booking link', ''), show=S['show'], ga4='', turnstile='', gsc_verification='',
     warehouse=S['warehouse'], office=S['office'], same_as=[], robots_extra=''),
  company={k: v for k, v in co.items() if k not in ('Hours', 'Reply time', 'Booking link', 'MOQ (powders)', 'Lead-time statement')},
  certs=cert, transit=D['transit'], pages={}, redirects=[], products=products)
seed['company']['Credit application'] = 'Credit is available on part of the payment, subject to trade references.'
seed['company'].pop('Kill step statement', None)
os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
json.dump(seed, open(os.path.join(ROOT, 'data', 'site-data.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('seed written:', len(products), 'products')
