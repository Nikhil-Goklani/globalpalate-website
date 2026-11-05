# -*- coding: utf-8 -*-
from lib import *

# ---------------- HOME ----------------
def names(prods=None):
    c = [p['common'] for p in (prods or PRODUCTS)]
    return (', '.join(c[:-1]) + ' and ' + c[-1]) if len(c) > 1 else (c[0] if c else 'ingredients')

def collage(cur):
    cls = ['bowl b1', 'bowl b2', 'bowl b3']; sz = ['(max-width:960px) 70vw, 340px', '(max-width:960px) 40vw, 220px', '(max-width:960px) 40vw, 220px']
    return ''.join(img(cur, p['key'], 640, p['alt'], cls[i], False, sz[i]) for i, p in enumerate(PRODUCTS[:3]))

def home():
    cur = '/'
    nm = names()
    desc = f"Certified organic {nm}, shipped from U.S. stock. COA with every batch. Request a quote today."
    if not 140 <= len(desc) <= 160: desc = "Certified organic botanical ingredients shipped from U.S. stock. Batch COA with every order, 100 kg minimums and fast quotes. Request a quote today."
    cards = ''.join(f'''<a class="pcard" href="{rel(cur, ppath(p))}">{img(cur,p["key"],320,p["alt"],"",True,"84px")}<span class="kicker" style="margin-bottom:4px">{E(p["tag"])}</span><h3>{E(p["name"])}</h3><div class="bot">{E(p["botanical"])}</div><p>{E(p["card"])}</p><div class="foot"><span>{price_label(p)}</span><span class="arrow">View product</span></div></a>''' for p in PRODUCTS)
    inds = ''.join(f'<a class="card" href="{rel(cur, "/industries/"+i["slug"]+"/")}" style="text-decoration:none"><span class="n">0{n+1}</span><h3>{E(i["short"])}</h3><p>{E(i["blurb"])}</p></a>' for n, i in enumerate(INDUSTRIES))
    body = f'''<section class="hero"><div class="wrap"><div>
<h1>Certified organic ingredients, shipped from U.S. stock.</h1>
<p class="lead">{E(nm[0].upper() + nm[1:])}, held in our Compton, California warehouse, with a Certificate of Analysis on every batch.</p>
<div class="hero-cta">{cta(cur,"Request a quote","btn btn-primary btn-lg")}</div>
<p class="hero-note">Need a sample first? <a href="{rel(cur,'/contact/#quote')}" data-quote="sample">Request a sample</a>.</p></div>
<div class="collage" aria-hidden="false">{collage(cur)}</div></div></section>
<div class="proof"><ul><li>{IC["leaf"]}USDA organic</li><li>{IC["flask"]}COA with every batch</li><li>{IC["truck"]}Ships from U.S. stock</li><li>{IC["box"]}100 kg minimum on powders</li></ul></div>
<section class="sec"><div class="wrap"><div class="head"><h2>Why manufacturers buy from stock instead of importing</h2><p>Importing direct means ocean freight, customs clearance and lot sizes built for containers. Buying from a U.S. warehouse removes those steps from your production schedule.</p></div>
<div class="rows"><div class="row"><h3>Held in the U.S.</h3><p>Inventory is held in our warehouse in Compton, California, so orders ship domestically instead of waiting on an import.</p></div>
<div class="row"><h3>Documented batches</h3><p>Every batch is tested and ships with a Certificate of Analysis. Request the documentation packet before you place an order.</p></div>
<div class="row"><h3>Practical minimums</h3><p>Powders have a 100 kg minimum, which suits pilot batches and new-product trials. Tamarind paste is sold by the drum.</p></div>
<div class="row"><h3>One team</h3><p>Quotes, documents and reorders go through the same sales team, by phone, email or the quote form.</p></div></div></div></section>
<section class="sec alt" id="products"><div class="wrap"><div class="head"><h2>Organic ingredients in stock</h2><p>Six ingredients, each with its own specification, documentation and quote request.</p></div><div class="grid3">{cards}</div></div></section>
<section class="sec"><div class="wrap"><div class="head"><h2>Who we supply</h2><p>Manufacturers with real QA requirements, across four segments.</p></div><div class="grid4">{inds}</div></div></section>
<section class="sec tint"><div class="wrap"><div class="head"><h2>Where we ship from</h2></div><div class="loc"><div><span class="kicker">Warehouse</span><h3>{SITE["warehouse"]["name"]}</h3><address>{E(addr(SITE["warehouse"]))}</address><p>All inventory is stocked here and ships by LTL or full-truckload freight to customers across the United States and Canada.</p></div>
<div><span class="kicker">Office</span><h3>{SITE["office"]["name"]}</h3><address>{E(addr(SITE["office"]))}</address><p>Our East Coast office. Call or email for pricing, documents and order support.</p></div></div></div></section>
<section class="sec"><div class="wrap"><div class="band"><div><h2>Review the documentation first</h2><p>Request the specification sheets and sample COAs before you ask for a quote.</p></div><div class="hero-cta2"><a class="btn btn-primary" href="{rel(cur,'/quality/#documents')}">Request documentation</a></div></div></div></section>'''
    return layout(cur, "Organic Ingredients Supplier in the USA | Global Palate", desc, body,
                  schema=[org_ld()], og='og-default.jpg', nav='/')

def money(x): return f'${x:,.2f}'
def price_label(p):
    pr = price_of(p)
    if not pr: return 'Price on request'
    lo, hi, unit, basis = pr
    return (f'{money(lo)}\u2013{money(hi)}/{unit}' if hi != lo else f'{money(lo)}/{unit}')

# ---------------- PRODUCT ----------------
def product_faqs(p):
    q = [("What is the wholesale pricing for " + p['name'] + "?",
          (f"Indicative pricing is {price_label(p).replace('/', ' per ')}" + (f", {price_of(p)[3]}" if price_of(p)[3] else "") + ", depending on volume. " if price_of(p) else "Pricing depends on quantity and delivery location. ") + "Request a quote and we will confirm pricing " + SITE['response'] + ".")]
    q += p['faq_extra']
    q += [("Which part of the plant is used?", f"The powder is made from the {p['plant']}." if p['unit_mode'] != 'drum' else f"The paste is made from the {p['plant']}."),
          ("What is the minimum order?", "This ingredient is sold by the drum. Request a quote with the number of drums you need." if p['unit_mode'] == 'drum' else f"The minimum order is {SITE['moq']}. Request a quote for your quantity."),
          ("Is it stocked in the United States?", "Yes. Inventory is held in our warehouse in Compton, California. " + lead(p)),
          ("What does it look like?", f"It is {p['look']}."),
          ("How is it tested?", "Every batch is tested for heavy metals, microbiological safety and pesticide residue, and the results are reported on the batch Certificate of Analysis." + (" " + co('Heavy metals compliance statement') if co('Heavy metals compliance statement') else "")),
          ("Does it contain any major allergens?", "No. The ingredient is free from the major allergens listed in its specification."),
          ("What is the shelf life and how should it be stored?", "Shelf life is 24 months. Store in a cool, dry place in a sealed container.")]
    return q

def compare_rows(p):
    moq = 'Drum quantities' if p['unit_mode'] == 'drum' else SITE['moq'] + ' on powders'
    return [("Where the stock is", "U.S. warehouse, Compton CA", "At origin until shipped"),
            ("Minimum order", moq, "Often container-scale lots"),
            ("Documentation", "Batch COA; certificates on request", "Varies by supplier"),
            ("Delivery", "LTL or full-truckload within the U.S.", "Ocean freight plus customs clearance"),
            ("Contact", "One sales team for quotes and reorders", "Often several parties")]


def _t(rows, head=None):
    h = f'<thead><tr>{"".join(f"<th scope=col>{E(x)}</th>" for x in head)}</tr></thead>' if head else ''
    return f'<div class="tbl-wrap"><table class="reg">{h}<tbody>{rows}</tbody></table></div>'

def _re_unit(s):
    import re
    return bool(re.search(r'(kg|mt)\s*$', s, re.I))

def avail_section(cur, p):
    rows = []
    pr = price_of(p)
    if pr: rows.append(('Indicative price', price_label(p) + (f' ({pr[3]})' if pr[3] else '') + (f' as of {cf(p,"Price valid")}' if cf(p, 'Price valid') else '')))
    if cf(p, 'Volume tiers'): rows.append(('Volume pricing', f'<span class="tiers">{E(norm_tiers(cf(p,"Volume tiers")))}</span>'))
    qty = fmt_qty(p)
    if in_stock(p): rows.append(('Availability', f'<span class="stock">In stock</span>' + (f': {E(qty)} on hand' if qty else '') + (f'. Ships within {E(cf(p,"Ships within"))}' if cf(p, 'Ships within') else '')))
    elif cf(p, 'In stock').lower() in ('no', 'n'): rows.append(('Availability', 'Currently out of stock. Request a quote for the next lot.'))
    if cf(p, 'Lot'): rows.append(('Lot / crop year', cf(p, 'Lot')))
    pk = pack_ok(p)
    if pk and cf(p, 'Pack format'): rows.append(('Pack format', cf(p, 'Pack format')))
    if pk and (cf(p, 'Packs per pallet') or cf(p, 'Pallet net')): rows.append(('Per pallet', ', '.join(x for x in [cf(p, 'Packs per pallet') and cf(p, 'Packs per pallet') + (' drums' if 'drum' in cf(p, 'Pack format').lower() else ' packs'), cf(p, 'Pallet net') and (cf(p, 'Pallet net') + (' net' if _re_unit(cf(p, 'Pallet net')) else ' kg net'))] if x)))
    rows.append(('Minimum order', 'Sold by the drum' if p['unit_mode'] == 'drum' else SITE['moq']))
    if co('Payment terms'): rows.append(('Payment terms', co('Payment terms')))
    if cf(p, 'Origin region') or cf(p, 'Supplier'): rows.append(('Origin', ', '.join(x for x in [cf(p, 'Origin region') and (cf(p, 'Origin region') if 'india' in cf(p, 'Origin region').lower() else cf(p, 'Origin region') + ', India'), cf(p, 'Supplier') and 'processed by ' + cf(p, 'Supplier')] if x)))
    if cf(p, 'Last audit') and not cf(p, 'Last audit').isdigit(): rows.append(('Supplier audit', cf(p, 'Last audit')))
    if not (pr or in_stock(p)): rows.insert(0, ('Pricing', 'Quoted per order. Send the quantity and ZIP below.'))
    tb = ''.join(f'<tr><th scope="row">{E(k)}</th><td>{v if k in ("Volume pricing","Availability") else E(v)}</td></tr>' for k, v in rows)
    return f'''<section class="sec alt" id="availability"><div class="wrap avail"><div><h2>Pricing, availability and terms</h2><table class="spec" style="background:#fff">{tb}</table><p class="note" style="margin-top:12px">Quantities and prices are indicative and confirmed on your written quote. <a href="{rel(cur,"/ordering/")}">Ordering, credit and returns</a>.</p></div>
<form class="form box" data-lead="quote" method="post" action="#"><h3>Quick quote for {E(p["short"])}</h3><div class="hp" aria-hidden="true"><label>Leave blank<input name="website" tabindex="-1" autocomplete="off"></label></div><input type="hidden" name="products" value="{p["key"]}">
<div class="r2"><div><label class="req" for="r-n-{p["key"]}">Full name</label><input id="r-n-{p["key"]}" name="first_name" autocomplete="name" required></div><div><label class="req" for="r-e-{p["key"]}">Work email</label><input id="r-e-{p["key"]}" name="email" type="email" autocomplete="email" required></div></div>
<label class="req" for="r-c-{p["key"]}">Company</label><input id="r-c-{p["key"]}" name="company" autocomplete="organization" required>
<div class="r2"><div><label class="req" for="r-q-{p["key"]}">Quantity</label><div style="display:grid;grid-template-columns:1fr 90px;gap:8px"><input id="r-q-{p["key"]}" name="quantity" type="number" min="1" step="any" required><select name="unit" aria-label="Unit"><option value="{'drum' if p['key']=='tamarind' else 'kg'}">{'drums' if p['key']=='tamarind' else 'kg'}</option></select></div></div><div><label class="req" for="r-z-{p["key"]}">Delivery ZIP</label><input id="r-z-{p["key"]}" name="zip" autocomplete="postal-code" required></div></div>
<label for="r-d-{p["key"]}">Needed by</label><input id="r-d-{p["key"]}" name="needed_by" type="date"><div class="ts"></div><button class="btn btn-dark" type="submit">Get my quote</button></form></div></section>'''

def cert_table(p):
    cs = cert_rows(p)
    if not cs: return '<p class="note">Certificate holder, certifier and verification details are provided with the batch documents.</p>'
    def row(c):
        v = f'<a class="vlink" href="{E(c["url"])}" rel="noopener" target="_blank">Verify</a>' if c['url'].startswith('http') else ''
        holder = E(c['holder']) + (f' <span class="note">({E(c["htype"])})</span>' if c['htype'] and c['htype'].lower() != c['holder'].lower() else '')
        return f'<tr><td><strong>{E(c["name"])}</strong></td><td>{holder}</td><td>{E(c["certifier"])}</td><td>{E(c["number"])}{" &middot; exp. "+E(c["expiry"]) if c["expiry"] else ""}</td><td>{v}</td></tr>'
    return _t(''.join(row(c) for c in cs), ['Certificate', 'Held by', 'Certified by', 'Number', 'Verify'])

def testing_rows(p):
    sr = spec_rows(p)
    if not sr: return ''.join(f'<tr><th scope="row">{E(k)}</th><td>{E(v)}</td></tr>' for k, v in TESTING)
    rows = ''.join(f'<tr><th scope="row">{E(r["param"])}</th><td>{E(r["limit"] or r["result"])}{" <span class=note>(typical "+E(r["result"])+")</span>" if r["limit"] and r["result"] and r["limit"].lower() != r["result"].lower() else ""}</td><td>{E(r["method"])}</td></tr>' for r in sr)
    return _t(rows, ['Parameter', 'Limit', 'Method']).replace('<th scope=col>Limit</th>', '<th scope=col>Limit / result</th>').replace('<tbody>', '<tbody>', 1)

def doc_buttons(cur, p):
    out = ''
    for suffix, label in (('sample-coa', 'Download sample COA (PDF)'), ('spec-sheet', 'Download specification sheet (PDF)'), ('testing-report', 'Download testing report (PDF)')):
        fn = f"{p['key']}-{suffix}.pdf"
        if os.path.exists(f'data/documents/{fn}'): out += f'<a class="btn btn-primary btn-sm" href="{asset(cur, "documents/"+fn)}" download>{label}</a>'
    return f'<div class="docbtns">{out}</div>' if out else ''

def hero_price(p):
    pr = price_of(p)
    if not pr and not in_stock(p): return ''
    bits = []
    if pr: bits.append(f'Indicative price: <strong style="color:#fff">{price_label(p)}</strong>' + (f' ({E(pr[3])})' if pr[3] else ''))
    if in_stock(p): bits.append('<strong style="color:#EFF291">In stock</strong>' + (f', ships within {E(cf(p,"Ships within"))}' if cf(p, 'Ships within') else ''))
    return '<p style="margin-top:-6px;color:#E1DCF2">' + ' &middot; '.join(bits) + '</p>'

def dist_points():
    pts = [x.strip() for x in co('Why Global Palate vs other U.S. distributors').split('\n') if x.strip()]
    return pts

def transit_table(region):
    key = 'West' if region == 'west-coast' else 'East'
    rows = [t for t in D['transit'] if t['region'].lower() in (key.lower(), 'central', 'canada') or False]
    rows = [t for t in D['transit'] if t['region'].lower() == key.lower()]
    if not rows: return ''
    tr = ''.join(f'<tr><td>{E(t["state"])}</td><td>{E(t["ltl"])}</td><td>{E(t["ftl"])}</td><td>{E(t["note"])}</td></tr>' for t in rows)
    return '<h2>Transit times from Compton, CA</h2>' + _t(tr, ['State', 'LTL (business days)', 'Full truckload (business days)', 'Notes'])

def tabs_block(cur, p):
    spec = ''.join(f'<tr><th scope="row">{E(k)}</th><td>{E(v)}</td></tr>' for k, v in p['specs'])
    sr = spec_rows(p)
    test = testing_rows(p)
    test_html = (test if sr else f'<table class="spec">{test}</table>')
    stmts = ''.join(f'<p><strong>{E(h)}:</strong> {E(co(k))}</p>' for h, k in (('Heavy metals', 'Heavy metals compliance statement'), ('Kill step', 'Kill step statement'), ('ETO / irradiation', 'ETO / irradiation statement')) if co(k))
    pur = ''.join(f'<li>{E(x)}</li>' for x in p['purity'] + ['USDA Organic'])
    alg = ''.join(f'<div><span>{E(a)}</span><b>No</b></div>' for a in ALLERGENS)
    desc = ''.join(f'<p>{E(x)}</p>' for x in p['desc'])
    return f'''<div class="tabbar" role="tablist" aria-label="Product information"><button role="tab" id="t1" aria-selected="true" aria-controls="p1">Product description</button><button role="tab" id="t2" aria-selected="false" aria-controls="p2" tabindex="-1">Specification</button><button role="tab" id="t3" aria-selected="false" aria-controls="p3" tabindex="-1">Batch documents</button></div>
<div class="tabpanel" id="p1" role="tabpanel" aria-labelledby="t1"><h3>Description</h3>{desc}</div>
<div class="tabpanel" id="p2" role="tabpanel" aria-labelledby="t2" hidden><h3>Product specification</h3><table class="spec">{spec}</table>
<h3>Quality testing, every batch</h3>{test_html}{stmts}{doc_buttons(cur, p)}<h3>Certificates for this product</h3>{cert_table(p)}<h3>Purity</h3><ul class="ticks">{pur}</ul>
<h3>Allergen statement: does it contain&hellip;</h3><div class="allergens">{alg}</div><p class="note" style="margin-top:14px">{E(co("Cross-contact statement") or "Facility cross-contact and shared-line information is provided with the batch documents on request.")} Batch results are reported on each Certificate of Analysis.</p></div>
<div class="tabpanel" id="p3" role="tabpanel" aria-labelledby="t3" hidden><h3>Get the batch documents</h3><p>Enter your details and we will email the Certificate of Analysis, specification sheet and certificates for {E(p["name"])}. No account needed.</p>
<form class="form" data-lead="documents" style="max-width:520px" method="post" action="#"><div class="hp" aria-hidden="true"><label>Leave blank<input name="website" tabindex="-1" autocomplete="off"></label></div><input type="hidden" name="products" value="{p["key"]}">
<div class="r2"><div><label class="req" for="d-fn-{p["key"]}">Full name</label><input id="d-fn-{p["key"]}" name="first_name" autocomplete="name" required></div><div><label class="req" for="d-em-{p["key"]}">Work email</label><input id="d-em-{p["key"]}" name="email" type="email" autocomplete="email" required></div></div>
<label class="req" for="d-co-{p["key"]}">Company</label><input id="d-co-{p["key"]}" name="company" autocomplete="organization" required><div class="ts"></div><button class="btn btn-dark" type="submit">Send me the documents</button></form></div>'''

def product_hero(cur, p, h1=None, extra=''):
    moq = 'Sold by the drum' if p['unit_mode'] == 'drum' else f"{SITE['moq']} minimum order"
    return f'''<section class="phero"><div class="wrap"><div class="pimg">{img(cur,p["key"],640,p["alt"],"",False)}</div><div>
<span class="kicker" style="color:#E1DCF2">Certified organic &middot; US &amp; Canada</span><h1>{E(h1 or p["h1"])}</h1><div class="bot">{E(p["botanical"])}</div><p>{E(p["lead"])}</p>{extra}
<ul class="feats"><li><span class="ic">{IC["leaf"]}</span>Certified organic and non-GMO</li><li><span class="ic">{IC["flask"]}</span>Certificate of Analysis with every batch</li><li><span class="ic">{IC["box"]}</span>{moq}</li></ul>
<div class="hero-cta2">{cta(cur,"Request a quote","btn btn-primary",False,p["key"])}{cta(cur,"Request a sample","btn btn-ghost-l",True,p["key"])}</div></div></div></section>'''

def ttk_block(cur, p):
    if not p['ttk']: return ''
    l = ''.join(f'<div class="ttk-i"><h4>{E(a)}</h4><p>{E(b)}</p></div>' for a, b in p['ttk'][:3])
    r = ''.join(f'<div class="ttk-i"><h4>{E(a)}</h4><p>{E(b)}</p></div>' for a, b in p['ttk'][3:])
    return f'''<section class="sec"><div class="wrap"><div class="ttk"><div class="t"><h2>Things to know about our {E(p["name"])}</h2><p>{E(p["ttk_sub"])}</p></div>
<div class="ttk-g"><div class="ttk-c">{l}</div><div class="ttk-b">{img(cur,p["key"],640,p["alt"],"",True,"190px")}</div><div class="ttk-c">{r}</div></div></div></div></section>'''

def cross_block(cur, p):
    cs = ''
    for o in PRODUCTS:
        if o['key'] == p['key']: continue
        cs += f'''<div class="sc"><a class="n" href="{rel(cur, ppath(o))}">{E(o["short"])}</a><a href="{rel(cur, ppath(o))}" tabindex="-1" aria-hidden="true">{img(cur,o["key"],320,o["alt"],"im",True,"104px")}</a><div class="pr">{price_label(o)}</div>{cta(cur,"Request a quote","btn btn-primary btn-sm",False,o["key"])}</div>'''
    return f'<section class="sec alt"><div class="wrap"><div class="head"><h2>See more ingredients</h2></div><div class="sg">{cs}</div></div></section>' if cs else ''

def dist_html():
    pts = dist_points()
    if not pts: return ''
    return '<h3 style="margin-top:20px">Compared with other U.S. distributors</h3><ul class="ticks">' + ''.join(f'<li>{E(x)}</li>' for x in pts) + '</ul>'

def why_block(p):
    rows = ''.join(f'<tr><td>{E(a)}</td><td>{E(b)}</td><td>{E(c)}</td></tr>' for a, b, c in compare_rows(p))
    return f'''<section class="sec"><div class="wrap why2"><div><h2>Buying from U.S. stock vs importing direct</h2><p>What changes for your purchasing and QA teams.</p>
<ul class="ticks"><li>The ingredient is already in the U.S., not waiting on ocean freight and customs.</li><li>A batch Certificate of Analysis is available before you commit to an order.</li><li>{E(lead(p))}</li></ul>{dist_html()}</div>
<table class="cmp"><thead><tr><th scope="col"></th><th scope="col" class="gp">Global Palate</th><th scope="col" class="ot">Importing direct</th></tr></thead><tbody>{rows}</tbody></table></div></section>'''

HAS_REGIONS = 'turmeric' in PRODUCT_BY_KEY

def product_page(p):
    cur = ppath(p)
    faqs = product_faqs(p)
    title = p['title']
    extra = hero_price(p)
    region = ''
    if p['key'] == 'turmeric' and HAS_REGIONS:
        region = f'''<section class="sec tint"><div class="wrap"><div class="head"><h2>Delivery and compliance by region</h2><p>All turmeric ships from our Compton, California warehouse. Read the regional guides for freight, lanes and state requirements.</p></div>
<div class="grid3"><a class="card" style="text-decoration:none" href="{rel(cur,cur+"west-coast/")}"><h3>Turmeric for the West Coast</h3><p>California, Oregon, Washington, Nevada, Arizona and nearby states, including Proposition 65 notes.</p></a>
<a class="card" style="text-decoration:none" href="{rel(cur,cur+"east-coast/")}"><h3>Turmeric for the East Coast</h3><p>Cross-country freight from Compton, with support from our Edison, NJ office.</p></a></div></div></section>'''
    body = (crumbs_html(cur, [("Products", "/#products"), (p['name'], cur)]) + product_hero(cur, p, extra=extra) + avail_section(cur, p)
            + f'<section class="sec"><div class="wrap">{tabs_block(cur,p)}</div></section>' + ttk_block(cur, p)
            + f'<section class="sec alt"><div class="wrap"><div class="head" style="text-align:center;margin-inline:auto"><h2>Frequently asked questions</h2></div>{faq_html(faqs)}</div></section>'
            + why_block(p) + region + cross_block(cur, p))
    return layout(cur, title, p['meta'], body, schema=[product_ld(p), faq_ld(faqs)], og=f"og-{p['key']}.jpg", seo=dict(canonical=p['seo'].get('canonical'), og_title=p['seo'].get('og_title'), og_desc=p['seo'].get('og_desc'), noindex=p['seo'].get('noindex')),
                  crumbs=[("Products", "/#products"), (p['name'], cur)], nav='products')

# ---------------- TURMERIC REGION PAGES ----------------
def region_page(kind):
    p = PRODUCT_BY_KEY['turmeric']; parent = ppath(p)
    cur = parent + kind + '/'
    west = kind == 'west-coast'
    if west:
        title = "Bulk Organic Turmeric Powder, West Coast | Global Palate"
        desc = "Organic turmeric powder for West Coast manufacturers, stocked in Compton, CA near the LA/Long Beach ports. Prop 65 notes, COA with every batch, 100 kg MOQ."
        h1 = "Organic turmeric powder for West Coast manufacturers"
        lede = "Stocked in Compton, California, close to the Ports of Los Angeles and Long Beach and the freight corridors that serve the West."
        faqs = [("Where does West Coast turmeric ship from?", "Every order ships from our warehouse at 3040 E. Ana Street, Compton, CA 90221."),
                ("Which states do you deliver to from Compton?", "We deliver across the United States. For California, Oregon, Washington, Nevada, Arizona, Utah and Idaho, freight moves a shorter distance than it would from an East Coast or import-to-order source. Freight options and lead time are confirmed on your quote."),
                ("Does Proposition 65 apply to turmeric powder?", "Proposition 65 requires warnings when a product exposes consumers to listed chemicals above safe-harbor levels. Lead and cadmium are on the list and can occur naturally in botanical raw materials. Review the heavy-metal results on the batch COA as part of your own assessment. Warning decisions for finished products rest with the brand owner."),
                ("What is the minimum order?", f"The minimum order is {SITE['moq']}."),
                ("Can I get the COA before ordering?", "Yes. Request the batch documents on the product page or contact us and we will send the Certificate of Analysis and specification sheet.")]
        sections = f'''<h2>Why buy turmeric from a Compton, CA warehouse</h2>
<p>Our warehouse sits in the Los Angeles area, near the Ports of Los Angeles and Long Beach and the I-710, I-105 and I-5 freight corridors. For manufacturers in California and the Western states, that means product moves a short domestic distance rather than waiting on an import.</p>
<h2>Freight and lead time</h2><p>Orders ship by LTL or full-truckload freight. {E(lead(PRODUCT_BY_KEY["turmeric"]))} Tell us your delivery ZIP code in the quote form and we will confirm freight cost and timing.</p>
{transit_table(kind)}<h2>California compliance notes</h2><p>California buyers often ask about Proposition 65 and heavy metals. Our batches are tested for heavy metals and the results are reported on each Certificate of Analysis, so your team can review them against its own Prop 65 assessment. We supply ingredients; warning and labeling decisions for finished products belong to the manufacturer.</p>
<h2>Who buys turmeric on the West Coast</h2><p>Supplement manufacturers, functional beverage brands, spice blenders and food manufacturers. See our guides for <a href="{rel(cur,"/industries/nutraceutical-dietary-supplement/")}">supplement makers</a> and <a href="{rel(cur,"/industries/functional-food-beverage/")}">food and beverage makers</a>.</p>'''
        other = ("East Coast", parent + "east-coast/")
    else:
        title = "Bulk Organic Turmeric Powder, East Coast | Global Palate"
        desc = "Organic turmeric powder for East Coast manufacturers. Stocked in California, shipped by LTL or truckload, with support from our Edison, NJ office. COA included."
        h1 = "Organic turmeric powder for East Coast manufacturers"
        lede = "Stocked in California and shipped coast to coast, with sales support from our office in Edison, New Jersey."
        faqs = [("Where does East Coast turmeric ship from?", "Inventory is held in our Compton, California warehouse and ships by LTL or full-truckload freight. Our Edison, NJ office handles sales support for East Coast buyers."),
                ("Is there stock in New Jersey?", "No. Our stock is held in Compton, California. The Edison, NJ location is our office."),
                ("How do I compare this with importing turmeric through an East Coast port?", "Importing to order brings ocean freight, customs clearance and container-scale lot sizes. Buying from our stock removes those steps, and cross-country freight cost and timing are confirmed on your quote so you can compare."),
                ("What is the minimum order?", f"The minimum order is {SITE['moq']}."),
                ("Can I get the COA before ordering?", "Yes. Request the batch documents on the product page or contact us and we will send the Certificate of Analysis and specification sheet.")]
        sections = f'''<h2>Serving East Coast buyers from California stock</h2>
<p>Our turmeric is stocked in Compton, California. For manufacturers in New Jersey, New York, Pennsylvania, Massachusetts and the rest of the East Coast, orders move cross-country by LTL or full-truckload freight. That is a longer lane than West Coast delivery, so we confirm freight cost and timing on every quote.</p>
<h2>Support from Edison, New Jersey</h2><p>Our office at {E(addr(SITE["office"]))} supports East Coast buyers with pricing, documents and order questions. Call {SITE["phone"]} or use the quote form.</p>
{transit_table(kind)}<h2>Documentation for your supplier file</h2><p>Each batch is tested for heavy metals, microbiological safety and pesticide residue and ships with a Certificate of Analysis. Organic certificates and the specification sheet are available on request, which supports supplier approval under programs such as FDA's preventive controls rule for food facilities.</p>
<h2>Who buys turmeric on the East Coast</h2><p>Supplement manufacturers, beverage brands, spice blenders and food manufacturers. See our guides for <a href="{rel(cur,"/industries/herbal-traditional-formulation/")}">herbal formulators</a> and <a href="{rel(cur,"/industries/spice-seasoning/")}">spice and seasoning makers</a>.</p>'''
        other = ("West Coast", parent + "west-coast/")
    body = (crumbs_html(cur, [("Products", "/#products"), (p['name'], parent), ("West Coast" if west else "East Coast", cur)])
            + product_hero(cur, p, h1=h1).replace(E(p['lead']), E(lede))
            + f'<section class="sec"><div class="wrap two"><div class="rich">{sections}</div><div><div class="region-n"><h3>Product specification</h3><table class="spec">{"".join(f"<tr><th scope=row>{E(k)}</th><td>{E(v)}</td></tr>" for k,v in p["specs"][:6])}</table><p style="margin:12px 0 0"><a href="{rel(cur,parent)}">Full turmeric specification and documents</a></p></div>'
              f'<div class="region-n"><h3>Looking at the other region?</h3><p style="margin:0"><a href="{rel(cur,other[1])}">Turmeric for the {other[0]}</a></p></div></div></div></section>'
            + f'<section class="sec alt"><div class="wrap"><div class="head" style="text-align:center;margin-inline:auto"><h2>Frequently asked questions</h2></div>{faq_html(faqs)}</div></section>' + band(cur, "Ready to order turmeric?", "Tell us the quantity and delivery ZIP code and we will confirm pricing and freight."))
    return layout(cur, title, desc, body, schema=[faq_ld(faqs)], og='og-turmeric.jpg',
                  crumbs=[("Products", "/#products"), (p['name'], parent), ("West Coast" if west else "East Coast", cur)], nav='products')
