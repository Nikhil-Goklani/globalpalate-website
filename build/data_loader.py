# -*- coding: utf-8 -*-
"""Reads the owner workbook. Every field is optional; empty cells are dropped."""
import os
from openpyxl import load_workbook
HDR = 5
PATH = os.environ.get('GP_DATA') or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'global-palate-data.xlsx')

def _rows(ws):
    heads = [str(c.value or '').strip() for c in ws[HDR]]
    for row in ws.iter_rows(min_row=HDR + 1, values_only=True):
        if row and str(row[0] or '').startswith('EXAMPLE'): continue
        d = {h: ('' if v is None else (v if not isinstance(v, str) else v.strip())) for h, v in zip(heads, row)}
        yield d

import datetime, re
def _s(v):
    if v is None: return ''
    if isinstance(v, (datetime.datetime, datetime.date)): return v.strftime('%Y-%m-%d')
    return str(v).strip()
WARN = []
def _clean(v):
    v = re.sub(r'\s*\((?:as )?stated in (?:the )?product title\)', '', v, flags=re.I).strip()
    return '' if v.lower() in ('not stated', 'n/a', 'na', 'none') else v
def _num(s):
    m = re.match(r'\s*[<>~]?\s*([\d.]+)', s or '')
    try: return float(m.group(1)) if m else None
    except ValueError: return None

def load(path=PATH):
    out = dict(commercial={}, specs={}, certs=[], company={}, transit=[])
    if not os.path.exists(path): return out
    wb = load_workbook(path, data_only=True)
    if 'Commercial' in wb.sheetnames:
        for d in _rows(wb['Commercial']):
            k = _s(d.get('Product key'))
            if k and any(_s(v) for kk, v in d.items() if kk not in ('Product key', 'Product')): out['commercial'][k] = d
    if 'Specs' in wb.sheetnames:
        for d in _rows(wb['Specs']):
            k = _s(d.get('Product key'))
            lim, res = _clean(_s(d.get('Limit / specification'))), _clean(_s(d.get('Typical result')))
            meth = _clean(_s([v for kk, v in d.items() if kk.startswith('Test method')][0] if any(kk.startswith('Test method') for kk in d) else ''))
            mx = re.match(r'(?i)\s*(?:max\.?|nmt|not more than)\s*([\d.]+)', lim)
            if mx and res and re.match(r'\s*[\d.]+\s*(%|ppm)', res) and _num(res) is not None and _num(res) > float(mx.group(1)):
                WARN.append(f"{k} / {_s(d.get('Parameter'))}: typical result {res} is above the limit {lim}; row not published")
                continue
            if k and (lim or res):
                out['specs'].setdefault(k, []).append(dict(param=_s(d.get('Parameter')), limit=lim, method=meth, result=res))
    if 'Certificates' in wb.sheetnames:
        for d in _rows(wb['Certificates']):
            vals = {kk: _s(v) for kk, v in d.items()}
            keys = list(vals)
            if vals[keys[0]] and any(vals[k] for k in keys[1:]):
                out['certs'].append(dict(name=vals[keys[0]], applies=vals[keys[1]], holder=vals[keys[2]], htype=vals[keys[3]], certifier=vals[keys[4]], number=vals[keys[5]], expiry=vals[keys[6]], url=vals[keys[7]]))
    if 'Company facts' in wb.sheetnames:
        for d in _rows(wb['Company facts']):
            if _s(d.get('Item')) and _s(d.get('Your answer')): out['company'][_s(d['Item'])] = _s(d['Your answer'])
    if 'Transit' in wb.sheetnames:
        for d in _rows(wb['Transit']):
            ks = list(d)
            v = {k: _s(d[k]) for k in ks}
            if v[ks[0]] and (v[ks[2]] or v[ks[3]]):
                out['transit'].append(dict(state=v[ks[0]], region=v[ks[1]], ltl=v[ks[2]], ftl=v[ks[3]], note=v[ks[4]]))
    # copy-paste guard: the same long answer typed into two different company items
    seen = {}
    for item, val in list(out['company'].items()):
        if len(val) > 25 and val in seen:
            WARN.append(f"Company facts: '{item}' has the same text as '{seen[val]}'; '{item}' not published")
            del out['company'][item]
        else: seen.setdefault(val, item)
    out['warnings'] = WARN
    return out
