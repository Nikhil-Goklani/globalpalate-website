import os, re, json, sys
from html.parser import HTMLParser
from urllib.parse import urlparse
OUT='/home/claude/gp3/out'
VOID={'meta','link','img','input','br','hr','source','area','base','col','embed','track','wbr'}
class P(HTMLParser):
    def __init__(s): super().__init__(); s.stack=[]; s.err=[]; s.links=[]; s.ids=[]; s.imgs=[]; s.h1=0; s.ld=[]; s._ld=False
    def handle_starttag(s,t,a):
        a=dict(a)
        if t not in VOID: s.stack.append(t)
        for k in ('href','src','srcset'):
            if k in a and a[k]: 
                if k=='srcset':
                    for part in a[k].split(','): s.links.append(part.strip().split(' ')[0])
                else: s.links.append(a[k])
        if 'id' in a: s.ids.append(a['id'])
        if t=='img': s.imgs.append(a)
        if t=='h1': s.h1+=1
        if t=='script' and a.get('type')=='application/ld+json': s._ld=True
    def handle_endtag(s,t):
        if t in VOID: return
        if not s.stack or s.stack[-1]!=t: s.err.append(f'mismatch </{t}> vs {s.stack[-3:]}')
        if s.stack and t in s.stack:
            while s.stack and s.stack.pop()!=t: pass
        s._ld=False
    def handle_data(s,d):
        if s._ld: s.ld.append(d)
bad=0; titles={}; descs={}; pages=0
for root,_,files in os.walk(OUT):
    for f in files:
        if not f.endswith('.html') or os.path.relpath(root,OUT).startswith('admin'): continue
        fp=os.path.join(root,f); src=open(fp,encoding='utf-8').read(); rel=os.path.relpath(fp,OUT); pages+=1
        p=P(); p.feed(src)
        def fail(m):
            global bad; bad+=1; print('FAIL',rel,m)
        if p.err: fail(p.err[:2])
        if p.stack: fail(f'unclosed {p.stack}')
        if p.h1!=1: fail(f'h1 count {p.h1}')
        if re.search(r'\\u[0-9a-fA-F]{4}',src): fail('literal \\uXXXX escape in html')
        if len(p.ids)!=len(set(p.ids)): fail('duplicate ids '+str([i for i in p.ids if p.ids.count(i)>1][:3]))
        for im in p.imgs:
            if 'alt' not in im: fail('img missing alt '+im.get('src',''))
            if not im.get('width') or not im.get('height'): fail('img missing width/height '+im.get('src',''))
        for d in p.ld:
            try: json.loads(d)
            except Exception as e: fail('bad json-ld '+str(e))
        t=re.search(r'<title>(.*?)</title>',src).group(1); m=re.search(r'<meta name="description" content="(.*?)"',src).group(1)
        if t in titles: fail(f'duplicate title with {titles[t]}')
        titles[t]=rel
        if m in descs and 'thank-you' not in rel and rel!='404.html': fail(f'duplicate description with {descs[m]}')
        descs[m]=rel
        # link resolution (404.html uses root-absolute links)
        for l in p.links:
            u=urlparse(l)
            if u.scheme in ('http','https','mailto','tel','data') or l.startswith('#') or not l: continue
            path=u.path
            target=os.path.normpath(os.path.join(OUT,path.lstrip('/'))) if path.startswith('/') else os.path.normpath(os.path.join(os.path.dirname(fp),path))
            if os.path.isdir(target): target=os.path.join(target,'index.html')
            if not os.path.exists(target): fail(f'broken link {l}')
        if len(src)>40000: fail(f'page large {len(src)}')
for root,_,files in os.walk(OUT):
    for f in files:
        if f.endswith(('.js','.css')):
            s=open(os.path.join(root,f)).read()
            if re.search(r'\\u2715|\\u2013|\\u2014',s.replace('\\\\u','')) and f.endswith('.js'): print('NOTE js escape in',f)
print('pages checked:',pages,'failures:',bad)
sys.exit(1 if bad else 0)
