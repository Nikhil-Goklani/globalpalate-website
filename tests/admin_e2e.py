import sys, os, re, json, time, urllib.request
from playwright.sync_api import sync_playwright
B = 'http://localhost:8788'; SCR = sys.argv[1]; OUTD = '/home/claude/gp3/out'
res = []
def ok(name, cond, extra=''): res.append((name, bool(cond))); print(('PASS' if cond else 'FAIL'), name, extra)
def get(url):
    try: return urllib.request.urlopen(B + url).read().decode()
    except urllib.error.HTTPError as e: return 'HTTP%d' % e.code
with sync_playwright() as p:
    br = p.chromium.launch(); ctx = br.new_context(viewport={'width': 1366, 'height': 900}); pg = ctx.new_page()
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    pg.goto(B + '/admin/'); pg.wait_for_selector('#login:not([hidden])')
    ok('login screen shown when signed out', pg.is_visible('#loginForm') and not pg.is_visible('#app'))
    pg.fill('#pw', 'wrong'); pg.click('#loginForm button'); pg.wait_for_selector('#loginErr:not([hidden])'); ok('wrong password rejected', 'Wrong password' in pg.inner_text('#loginErr'))
    pg.fill('#pw', 'admin'); pg.click('#loginForm button'); pg.wait_for_selector('#app:not([hidden])')
    ok('login card is hidden once signed in', not pg.is_visible('#login'))
    ok('products list shows 6 seeded products', pg.locator('table.list tbody tr').count() == 6)
    ok('seo score column rendered', pg.locator('table.list .score').count() == 6)
    # --- edit turmeric SEO
    pg.locator('table.list tbody tr', has_text='Organic Turmeric Powder').get_by_role('button', name='Edit').click()
    pg.click('[data-tab=seo]'); pg.fill('[data-bind="products.0.title"]', 'Organic Turmeric Powder Bulk | Global Palate'); pg.fill('[data-bind="products.0.seo.focus_keyword"]', 'organic turmeric powder')
    ok('char counter updates', '/ 30-60' in pg.inner_text('[data-cnt-for="f_products_0_title"]'))
    ok('SERP preview reflects title', 'Organic Turmeric Powder Bulk' in pg.inner_text('.serp .t'))
    ok('checklist shows keyword-in-title pass', pg.locator('.checks li.pass', has_text='in the SEO title').count() == 1)
    ok('status chip shows unsaved', 'Unsaved' in pg.inner_text('#status'))
    pg.click('[data-tab=pricing]'); pg.fill('[data-bind="products.0.commercial.price_from"]', '5.5')
    # pack mismatch warning on ashwagandha
    pg.click('[data-act=nav][data-view=products]'); pg.locator('table.list tbody tr', has_text='Ashwagandha').get_by_role('button', name='Edit').click(); pg.click('[data-tab=pricing]')
    ok('pack mismatch warning shown', 'net weight per pack is 20' in pg.inner_text('#commWarn'))
    pg.click('[data-act=nav][data-view=products]'); pg.locator('table.list tbody tr', has_text='Moringa').get_by_role('button', name='Edit').click(); pg.click('[data-tab=tests]')
    ok('over-limit test warning shown (moringa ash)', 'Total ash' in pg.inner_text('#testWarn'))
    # --- change moringa slug (auto redirect)
    pg.click('[data-tab=basics]'); pg.fill('[data-bind="products.2.slug"]', 'Organic Moringa Powder!'); pg.press('[data-bind="products.2.slug"]', 'Tab')
    ok('slug is sanitised', pg.input_value('[data-bind="products.2.slug"]') == 'organic-moringa-powder')
    # --- add product
    pg.click('[data-act=nav][data-view=products]'); pg.click('[data-act=newp]'); pg.fill('#np1', 'Organic Black Pepper Powder'); pg.fill('#np2', 'Piper nigrum'); pg.click('#ma .btn:last-child')
    ok('new product opens in editor as draft', 'Draft' in pg.inner_text('#main h1') and pg.input_value('[data-bind="products.6.slug"]') == 'organic-black-pepper-powder')
    pg.fill('[data-bind="products.6.status"]'.replace('input', 'select'), '') if False else pg.select_option('[data-bind="products.6.status"]', 'published')
    pg.click('[data-tab=content]'); pg.fill('[data-bind="products.6.lead"]', 'Organic black pepper powder in bulk for spice blenders.'); pg.fill('[data-bind="products.6.card"]', 'Pungent black pepper for seasoning blends.')
    pg.fill('[data-bind="products.6.desc.0"]', 'Our organic black pepper is milled from Piper nigrum berries.')
    pg.click('[data-tab=pricing]'); pg.fill('[data-bind="products.6.commercial.price_from"]', '9.5'); pg.fill('[data-bind="products.6.commercial.price_to"]', '11'); pg.select_option('[data-bind="products.6.commercial.in_stock"]', 'Yes'); pg.fill('[data-bind="products.6.commercial.ships_within"]', '2-3 business days')
    pg.click('[data-tab=seo]'); pg.fill('[data-bind="products.6.meta"]', 'Organic black pepper powder in bulk from our Compton, CA warehouse. Batch COA, 100 kg minimum, fast quotes for spice blenders and food makers.')
    pg.click('[data-tab=image]'); pg.set_input_files('#imgFile', SCR + '/pepper.png'); pg.wait_for_function("document.getElementById('imgMsg').textContent.indexOf('Uploaded')>=0", timeout=15000); ok('image uploaded', True)
    # --- delete arrowroot
    pg.click('[data-act=nav][data-view=products]'); pg.locator('table.list tbody tr', has_text='Arrowroot').get_by_role('button', name='Delete').click(); ok('delete asks for confirmation', 'Delete "Organic Arrowroot Powder"?' in pg.inner_text('#mt')); pg.click('#ma .btn:last-child')
    ok('arrowroot removed from list', pg.locator('table.list tbody tr', has_text='Arrowroot').count() == 0)
    # --- save
    pg.click('#saveBtn'); pg.wait_for_function("document.getElementById('toast').textContent.indexOf('Draft saved')>=0"); ok('draft saved toast with redirect note', 'Draft saved' in pg.inner_text('#toast') and '/product/organic-moringa-leaf-powder/' in pg.inner_text('#toast'), pg.inner_text('#toast'))
    pg.reload(); pg.wait_for_selector('#app:not([hidden])'); ok('changes persist after reload', pg.locator('table.list tbody tr').count() == 6 and pg.locator('table.list', has_text='Black Pepper').count() == 1)
    ok('status chip says saved, not published', 'not published' in pg.inner_text('#status'))
    pg.click('[data-act=nav][data-view=redirects]'); ok('redirects page lists auto + deletion redirects', '/product/organic-moringa-leaf-powder/' in pg.inner_html('#main') and '/product/organic-arrowroot-powder/' in pg.inner_html('#main'))
    pg.click('[data-act=nav][data-view=pages]'); pg.locator('details.k', has_text='About').locator('summary').click(); pg.fill('[data-bind="pages./about/.title"]', 'About Global Palate | Organic Ingredient Distributor'); pg.click('#saveBtn'); pg.wait_for_function("document.querySelector('#status').textContent.indexOf('Unsaved')<0")
    pg.click('[data-act=nav][data-view=settings]'); pg.fill('[data-bind="settings.show"]', ''); pg.fill('[data-bind="settings.hours"]', 'Monday-Friday, 8 AM-6 PM PT'); pg.click('#saveBtn'); pg.wait_for_function("document.querySelector('#status').textContent.indexOf('Unsaved')<0")
    # --- validation error: duplicate slug
    pg.click('[data-act=nav][data-view=products]'); pg.locator('table.list tbody tr', has_text='Ginger').get_by_role('button', name='Edit').click(); pg.fill('[data-bind="products.3.slug"]', 'organic-turmeric-powder'); pg.press('[data-bind="products.3.slug"]', 'Tab'); pg.click('#saveBtn')
    pg.wait_for_selector('#modal:not([hidden])'); ok('duplicate slug blocked with message', 'share the URL slug' in pg.inner_text('#mb')); pg.click('#ma .btn'); pg.fill('[data-bind="products.3.slug"]', 'organic-ginger-powder'); pg.press('[data-bind="products.3.slug"]', 'Tab')
    pg.click('#saveBtn'); pg.wait_for_function("document.querySelector('#status').textContent.indexOf('Unsaved')<0")
    # --- publish
    pg.click('#publishBtn'); pg.wait_for_selector('#modal:not([hidden])'); ok('publish confirmation shown', 'Publish to the live site' in pg.inner_text('#mt')); pg.click('#ma .btn:last-child')
    pg.wait_for_function("document.getElementById('toast').textContent.indexOf('Build started')>=0", timeout=15000); ok('publish toast', True)
    for _ in range(60):
        st = json.loads(get('/__build-status'))
        if not st['building'] and st['lastBuild'].startswith('exit'): break
        time.sleep(1)
    ok('local rebuild finished OK', st['lastBuild'].startswith('exit 0'), st['lastBuild'][:300])
    br2 = ctx.new_page(); br2.on('pageerror', lambda e: errs.append(str(e)))
    ok('new product page is live', '<title>Organic Black Pepper Powder in Bulk | Global Palate</title>' in get('/product/organic-black-pepper-powder/'))
    bp = get('/product/organic-black-pepper-powder/'); ok('new product shows price and stock', '$9.50' in bp and 'In stock' in bp)
    ok('new product schema has offers', '"lowPrice": "9.50"' in bp)
    ok('deleted product page gone', get('/product/organic-arrowroot-powder/').startswith('HTTP404') or 'Page not found' in get('/product/organic-arrowroot-powder/'))
    ok('turmeric SEO title updated', '<title>Organic Turmeric Powder Bulk | Global Palate</title>' in get('/product/organic-turmeric-powder/'))
    ok('turmeric price updated', '$5.50' in get('/product/organic-turmeric-powder/'))
    ok('about page title override applied', '<title>About Global Palate | Organic Ingredient Distributor</title>' in get('/about/'))
    home = get('/'); ok('home lists the new product card, not arrowroot', 'Black Pepper' in home and 'Arrowroot' not in home)
    ok('announcement bar hidden when text empty', 'class="bar"' not in home)
    ok('hours setting applied', '8 AM-6 PM PT' in get('/contact/'))
    sm = get('/sitemap.xml'); ok('sitemap has new product with lastmod, not deleted one', 'organic-black-pepper-powder/</loc><lastmod>' in sm and 'arrowroot' not in sm)
    ok('moringa slug changed', 'organic-moringa-powder' in get('/product/organic-moringa-powder/') or get('/product/organic-moringa-powder/').startswith('<!DOCTYPE'))
    rd = open(OUTD + '/_redirects').read(); ok('_redirects has 301s for slug change and deletion', '/product/organic-moringa-leaf-powder/  /product/organic-moringa-powder/  301' in rd and '/product/organic-arrowroot-powder/  /  301' in rd)
    ok('uploaded image processed to webp', os.path.getsize(OUTD + '/images/black-pepper-powder-640.webp') > 500 and os.path.exists(OUTD + '/images/og-black-pepper-powder.jpg'))
    ok('admin not in sitemap, blocked in robots', 'admin' not in sm and 'Disallow: /admin/' in get('/robots.txt'))
    ok('llms.txt lists new product', 'Organic Black Pepper Powder' in get('/llms.txt'))
    # modal product list on public site
    pub = br2; pub.goto(B + '/'); ok('quote modal lists new product', 'black-pepper-powder' in pub.get_attribute('body', 'data-products'))
    pub.click('.head-actions [data-quote]'); ok('modal opens with dynamic product checkboxes', pub.locator('dialog.gpm input[name=products][value=black-pepper-powder]').count() == 1)
    ok('no JS errors', not errs, str(errs[:3]))
    br.close()
f = [r for r in res if not r[1]]; print('\n', len(res) - len(f), 'passed,', len(f), 'failed'); sys.exit(1 if f else 0)
