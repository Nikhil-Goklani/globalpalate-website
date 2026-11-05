from playwright.sync_api import sync_playwright
import json, sys
B='http://localhost:8765'
res=[]; 
def ok(name,cond,extra=''): res.append((name,bool(cond),extra)); print(('PASS' if cond else 'FAIL'),name,extra)
with sync_playwright() as p:
    br=p.chromium.launch()
    ctx=br.new_context(viewport={'width':1366,'height':900}); pg=ctx.new_page()
    errs=[]; pg.on('console',lambda m: errs.append(m.text) if m.type=='error' and '502' not in m.text else None); pg.on('pageerror',lambda e: errs.append(str(e)))
    posted=[]
    def route(r):
        d=json.loads(r.request.post_data); posted.append(d)
        if mode['fail']: r.fulfill(status=502,content_type='application/json',body='{"ok":false,"error":"We could not record your request."}')
        else: r.fulfill(status=200,content_type='application/json',body='{"ok":true}')
    mode={'fail':False}
    pg.route('**/api/lead',route)
    pg.route('https://fonts.googleapis.com/**',lambda r:r.fulfill(status=200,content_type='text/css',body=''))
    pg.goto(B+'/'); pg.wait_for_load_state('load')
    ok('home h1',pg.inner_text('h1').startswith('Certified organic'))
    # images
    bad=pg.evaluate("[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src)")
    ok('home images load',not bad,str(bad))
    pg.screenshot(path='/tmp/home-desktop.png')
    # mega menu
    pg.hover('.nav-item>a'); ok('products menu opens on hover',pg.is_visible('.menu a'))
    ok('menu lists 6 products',pg.locator('.menu a').count()==6)
    pg.mouse.move(10,300)
    # modal open from header
    pg.click('header .btn-primary'); pg.wait_for_selector('dialog.gpm[open]')
    ok('modal opens',True)
    ok('modal has role via dialog + label',pg.get_attribute('dialog.gpm','aria-labelledby')=='gpm-t')
    ok('focus inside dialog',pg.evaluate("document.querySelector('dialog.gpm').contains(document.activeElement)"))
    ok('no literal \\u codes in modal',('\\u2' not in pg.inner_text('dialog.gpm')))
    pg.screenshot(path='/tmp/modal1.png')
    pg.keyboard.press('Escape'); ok('Esc closes modal',not pg.evaluate("document.querySelector('dialog.gpm').open"))
    # sample link opens with sample selected
    pg.click('.hero-note a'); pg.wait_for_selector('dialog.gpm[open]')
    ok('sample link preselects sample',pg.is_checked('input[name=req_type][value=sample]')); pg.keyboard.press('Escape')
    # full quote flow with failure then success
    pg.click('.hero-cta a'); pg.wait_for_selector('dialog.gpm[open]')
    pg.fill('#m-fn','Ana'); pg.fill('#m-ln','Lee'); pg.fill('#m-em','ana@acme.com'); pg.fill('#m-co','Acme')
    ok('phone optional (can advance without)',True)
    pg.click('[data-next]'); ok('advance to step 2',pg.is_visible('#m-q'))
    pg.click('button:has-text("Send request")'); ok('step2 required enforced (no post)',len(posted)==0)
    pg.fill('#m-q','250'); pg.select_option('select[name=unit]','kg'); pg.fill('#m-z','90001'); pg.select_option('#m-u','Dietary supplement'); pg.check('input[name=products][value=turmeric]')
    mode['fail']=True; pg.click('button:has-text("Send request")'); pg.wait_for_selector('dialog.gpm .err:not([hidden])')
    ok('server failure shows error, no fake success',('call' in pg.inner_text('dialog.gpm .err').lower() or 'could not' in pg.inner_text('dialog.gpm .err').lower()) and pg.url.rstrip('/')==B)
    mode['fail']=False; pg.click('button:has-text("Send request")'); pg.wait_for_url('**/thank-you/quote/')
    ok('success redirects to thank-you page',True); d=posted[-1]
    ok('payload fields',d['type']=='quote' and d['company']=='Acme' and d['zip']=='90001' and d['quantity']=='250' and d['products']==['turmeric'] and d['rendered'])
    ok('thank-you noindex',pg.get_attribute('meta[name=robots]','content').startswith('noindex'))
    # product page
    pg.goto(B+'/product/organic-ginger-powder/')
    ok('ginger page h1',pg.inner_text('h1').startswith('Organic ginger'))
    imgs=pg.evaluate("[...document.querySelectorAll('.sc')].map(s=>[s.querySelector('a.n').textContent.trim(), s.querySelector('img').getAttribute('src')])")
    exp={'Turmeric Powder':'turmeric','Ashwagandha Root Powder':'ashwagandha','Moringa Leaf Powder':'moringa','Tamarind Paste':'tamarind','Arrowroot Powder':'arrowroot'}
    ok('cross-sell images match names',all(exp[n] in s for n,s in imgs) and len(imgs)==5,str(imgs[:2]))
    pg.click('#t2'); ok('spec tab shows',pg.is_visible('#p2') and not pg.is_visible('#p1'))
    ok('no internal notes in spec',('Representative' not in pg.content() and 'Doc No' not in pg.content() and 'sci-fi' not in pg.content()))
    pg.click('#t3'); ok('docs tab has name/email/company, no dead login',pg.is_visible('#d-fn-ginger') and pg.is_visible('#d-co-ginger') and 'Login' not in pg.inner_text('#p3'))
    pg.press('#t3','ArrowLeft'); ok('tab arrow key nav',pg.get_attribute('#t2','aria-selected')=='true')
    pg.click('.sc .btn >> nth=0'); pg.wait_for_selector('dialog.gpm[open]')
    ok('cross-sell quote button opens modal w/ product checked',pg.is_checked('input[name=products][value=turmeric]')); pg.keyboard.press('Escape')
    posted.clear(); pg.click('#t3'); pg.fill('#d-fn-ginger','Bo'); pg.fill('#d-em-ginger','bo@x.com'); pg.fill('#d-co-ginger','X')
    pg.wait_for_timeout(3200); pg.click('#p3 button[type=submit]'); pg.wait_for_url('**/thank-you/documents/')
    ok('docs gate posts type=documents',posted and posted[-1]['type']=='documents' and posted[-1]['products']==['ginger'])
    # price consistency
    pg.goto(B+'/product/organic-turmeric-powder/')
    ok('turmeric hero/other pages consistent price label',pg.locator('.sc .pr').first.inner_text()=='$8.50\u2013$9.00/kg')
    pg.screenshot(path='/tmp/turmeric.png',full_page=True)
    # marquee controls
    pg.click('.bar-pause'); ok('marquee pause',pg.get_attribute('.bar-pause','aria-pressed')=='true')
    pg.click('.bar-close'); ok('bar dismissible',not pg.is_visible('.bar'))
    # mobile
    m=br.new_context(viewport={'width':375,'height':800},is_mobile=True); mp=m.new_page(); mp.route('https://fonts.googleapis.com/**',lambda r:r.fulfill(status=200,content_type='text/css',body=''))
    for path in ['/','/product/organic-turmeric-powder/','/quality/','/contact/','/about/','/supply-chain/','/industries/spice-seasoning/','/product/organic-turmeric-powder/west-coast/']:
        mp.goto(B+path); ow=mp.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth")
        ok('no horizontal overflow @375 '+path,not ow)
    mp.goto(B+'/'); ok('mobile sticky bar visible',mp.is_visible('.mbar')); mp.click('.burger'); ok('mobile nav opens',mp.is_visible('nav.primary a >> nth=0'))
    mp.screenshot(path='/tmp/home-mobile.png')
    # --- buyer feedback checks ---
    pg2=ctx.new_page(); pg2.route('**/api/lead',route); pg2.route('https://fonts.googleapis.com/**',lambda r:r.fulfill(status=200,content_type='text/css',body=''))
    pg2.goto(B+'/'); ok('announcement text appears once',pg2.evaluate("document.querySelector('.track').innerText.split('Supply Side Global').length-1")==1)
    pg2.goto(B+'/product/organic-turmeric-powder/'); ok('availability section present',pg2.is_visible('#availability'))
    pg2.fill('#r-n-turmeric','Test Buyer'); pg2.fill('#r-e-turmeric','buyer@example.com'); pg2.fill('#r-c-turmeric','Acme Foods'); pg2.fill('#r-q-turmeric','250'); pg2.fill('#r-z-turmeric','60601')
    posted.clear(); pg2.wait_for_timeout(3200); pg2.click('#availability button[type=submit]'); pg2.wait_for_timeout(600)
    ok('short RFQ posts quote with product, qty, zip',posted and posted[-1].get('type')=='quote' and posted[-1].get('products')==['turmeric'] and posted[-1].get('zip')=='60601' and posted[-1].get('quantity')=='250',str(posted[-1:] ))
    pg2.goto(B+'/ordering/'); ok('ordering page h1',pg2.inner_text('h1').startswith('How ordering'))
    pg2.fill('#k-n','Test Buyer'); pg2.fill('#k-e','buyer@example.com'); pg2.fill('#k-c','Acme Foods LLC'); posted.clear(); pg2.wait_for_timeout(3200); pg2.click('#credit button[type=submit]'); pg2.wait_for_timeout(600)
    ok('credit form posts type credit',posted and posted[-1].get('type')=='credit',str(posted[-1:]))
    m2=br.new_context(viewport={'width':375,'height':800},is_mobile=True).new_page()
    for path in ['/ordering/','/product/organic-turmeric-powder/organic']:
        pass
    m2.goto(B+'/ordering/'); ok('no overflow @375 /ordering/',not m2.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth"))
    m2.goto(B+'/product/organic-turmeric-powder/'); ok('no overflow @375 product (tables)',not m2.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth"))
    ok('no console errors',not errs,str(errs[:3]))
    br.close()
f=[r for r in res if not r[1]]; print('\n',len(res)-len(f),'passed,',len(f),'failed'); sys.exit(1 if f else 0)
