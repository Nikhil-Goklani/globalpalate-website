# -*- coding: utf-8 -*-
from lib import *
from pages1 import price_label, _t, names

def industries_hub():
    cur = '/industries/'
    desc = "Global Palate supplies organic ingredients to dietary supplement, functional food and beverage, herbal formulation and spice manufacturers across North America."
    cards = ''.join(f'<a class="card" style="text-decoration:none" href="{rel(cur,"/industries/"+i["slug"]+"/")}"><span class="n">0{n+1}</span><h3>{E(i["short"])}</h3><p>{E(i["blurb"])}</p></a>' for n, i in enumerate(INDUSTRIES))
    body = crumbs_html(cur, [("Industries", cur)]) + page_hero("Who we supply", "Ingredients built around four buyer types", "Each segment has its own quality, documentation and regulatory questions. These guides cover what buyers ask for and how we support them.") + f'<section class="sec"><div class="wrap"><div class="grid4" style="grid-template-columns:repeat(2,1fr)">{cards}</div></div></section>' + band(cur, "Not sure which fits your business?", "Tell us what you are making and we will point you to the right ingredients.")
    return layout(cur, "Industries We Supply | Global Palate", desc, body, crumbs=[("Industries", cur)], nav='/industries/')

def industry_page(i):
    cur = f"/industries/{i['slug']}/"
    prods = [PRODUCT_BY_KEY[k] for k in i['products'] if k in PRODUCT_BY_KEY] or PRODUCTS[:3]
    pc = ''.join(f'<a class="pcard" href="{rel(cur,ppath(p))}">{img(cur,p["key"],320,p["alt"],"",True,"84px")}<h3>{E(p["name"])}</h3><div class="bot">{E(p["botanical"])}</div><p>{E(p["card"])}</p><div class="foot"><span>{price_label(p)}</span><span class="arrow">View product</span></div></a>' for p in prods)
    body = (crumbs_html(cur, [("Industries", "/industries/"), (i['short'], cur)]) + page_hero("Industry", i['h1'], i['blurb'])
      + f'''<section class="sec"><div class="wrap two"><div class="rich"><h2>How we support {E(i["short"])}</h2>{"".join(f"<p>{E(x)}</p>" for x in i["intro"])}<h2>Compliance notes</h2>{"".join(f"<p>{E(x)}</p>" for x in i["comp"])}</div>
<div><h2>What buyers in this segment ask for</h2><ul class="ticks">{"".join(f"<li>{E(x)}</li>" for x in i["ask"])}</ul></div></div></section>
<section class="sec alt"><div class="wrap"><div class="head"><h2>Ingredients to evaluate</h2></div><div class="grid3">{pc}</div></div></section>
<section class="sec"><div class="wrap"><div class="head" style="text-align:center;margin-inline:auto"><h2>Frequently asked questions</h2></div>{faq_html(i["faqs"])}</div></section>'''
      + band(cur, f"Sourcing for {i['short']}?", "Request pricing, a sample or the documentation packet."))
    return layout(cur, f"{i['short']} Ingredients | Global Palate", i['meta'], body, schema=[faq_ld(i['faqs'])],
                  crumbs=[("Industries", "/industries/"), (i['short'], cur)], nav='/industries/')


def facts_cards(pairs):
    pairs = [(h, v) for h, v in pairs if v]
    if not pairs: return ''
    return '<div class="facts">' + ''.join(f'<div class="f"><h3>{E(h)}</h3><p>{E(v)}</p></div>' for h, v in pairs) + '</div>'

def quality_facts():
    return facts_cards([('FDA food facility registration', co('FDA food facility registration')), ('FSVP / importer of record', co('FSVP / importer of record')),
        ('GMP', co('GMP statement')), ('Steam sterilization / kill step', co('Kill step statement')), ('ETO and irradiation', co('ETO / irradiation statement')),
        ('Heavy metals', co('Heavy metals compliance statement')), ('Recall and non-conformance', co('Recall / non-conformance policy')), ('Product liability insurance', co('Product liability insurance'))])

def cert_register():
    cs = D['certs']
    if not cs: return ''
    def row(c):
        v = f'<a class="vlink" href="{E(c["url"])}" rel="noopener" target="_blank">Verify</a>' if c['url'].startswith('http') else ''
        return f'<tr><td><strong>{E(c["name"])}</strong></td><td>{E(c["applies"] or "all products")}</td><td>{E(c["holder"])}{" ("+E(c["htype"])+")" if c["htype"] and c["htype"].lower() != c["holder"].lower() else ""}</td><td>{E(c["certifier"])}</td><td>{E(c["number"])}{" &middot; exp. "+E(c["expiry"]) if c["expiry"] else ""}</td><td>{v}</td></tr>'
    return '<section class="sec"><div class="wrap"><div class="head"><h2>Certificate register</h2><p>Which certificate covers which product, who holds it and how to verify it.</p></div>' + _t(''.join(row(c) for c in cs), ['Certificate', 'Products', 'Held by', 'Certified by', 'Number', 'Verify']) + '</div></section>'

def about_extra():
    parts = []
    if co('Company story'): parts.append(f'<h2>Our story</h2><p>{E(co("Company story"))}</p>')
    if co('Years in business'): parts.append(f'<p><strong>{E(co("Years in business"))}</strong></p>')
    if co('Origin and supplier audit status'): parts.append(f'<h2>Origin and suppliers</h2><p>{E(co("Origin and supplier audit status"))}</p>')
    if co('Customer references'): parts.append(f'<h2>References</h2><p>{E(co("Customer references"))}</p>')
    if co('Planned products'): parts.append(f'<h2>Coming next</h2><div class="soon">' + ''.join(f'<span>{E(x.strip())}</span>' for x in co('Planned products').split(',') if x.strip()) + '</div><p>Not yet stocked. <a href="mailto:%s">Tell us what you need</a> and we will let you know.</p>' % SITE['email'])
    if not parts: return ''
    return '<section class="sec"><div class="wrap"><div class="rich">' + ''.join(parts) + '</div></div></section>'

def ordering():
    cur = '/ordering/'
    desc = "Global Palate ordering terms: minimums, pack formats, payment terms, credit applications, freight transit, returns and recall policy for organic ingredients."
    rows = [('Minimum order', (f"{SITE['moq']} on powders" + ("; " + names([p for p in PRODUCTS if p['unit_mode'] == 'drum']) + " by the drum" if any(p['unit_mode'] == 'drum' for p in PRODUCTS) else ""))), ('Payment terms', co('Payment terms')), ('Price basis', co('Default price basis')),
            ('Lead time', lead()), ('Credit', co('Credit application')), ('Returns', co('Returns policy')), ('Recall / non-conformance', co('Recall / non-conformance policy')),
            ('Product liability insurance', co('Product liability insurance'))]
    for p in PRODUCTS:
        if not pack_ok(p): continue
        bits = [cf(p, 'Pack format'), (cf(p, 'Packs per pallet') + (' drums/pallet' if 'drum' in cf(p, 'Pack format').lower() else ' packs/pallet')) if cf(p, 'Packs per pallet') else '', (cf(p, 'Pallet net') + ('/pallet' if cf(p, 'Pallet net').lower().endswith(('kg', 'mt')) else ' kg/pallet')) if cf(p, 'Pallet net') else '']
        bits = [b for b in bits if b]
        if bits: rows.append((f'Packing: {p["short"]}', ', '.join(bits)))
    tb = ''.join(f'<tr><th scope="row">{E(k)}</th><td>{E(v)}</td></tr>' for k, v in rows if v)
    tr = ''
    if D['transit']:
        tr = '<section class="sec alt"><div class="wrap"><div class="head"><h2>Transit times from Compton, CA</h2></div>' + _t(''.join(f'<tr><td>{E(t["state"])}</td><td>{E(t["ltl"])}</td><td>{E(t["ftl"])}</td><td>{E(t["note"])}</td></tr>' for t in D['transit']), ['State', 'LTL (business days)', 'Full truckload (business days)', 'Notes']) + '</div></section>'
    faqs = [("What is the minimum order?", f"The minimum order is {SITE['moq']} on powders." + (" " + names([p for p in PRODUCTS if p['unit_mode'] == 'drum']).capitalize() + " is sold by the drum." if any(p['unit_mode'] == 'drum' for p in PRODUCTS) else "")),
            ("How do I apply for credit?", "Send the credit application below. " + (co('Credit application') or "Our team will confirm terms after review.")),
            ("What is your returns policy?", co('Returns policy') or "Contact us with the batch number and we will review the lot with you."),
            ("What happens if a lot is out of specification?", co('Recall / non-conformance policy') or "Contact us right away with the batch number. We will review it with you and confirm next steps in writing.")]
    body = (crumbs_html(cur, [("Ordering & terms", cur)]) + page_hero("Ordering & terms", "How ordering works, from quote to delivery.", "Minimums, packing, payment terms, credit, freight and what happens if something is wrong.")
      + f'<section class="sec"><div class="wrap two"><div><table class="spec" style="background:#fff">{tb}</table><p class="note" style="margin-top:12px">Everything is confirmed on your written quote.</p></div>'
      f'<form class="form box" id="credit" data-lead="credit" method="post" action="#"><h2 style="font-size:1.3rem">Credit application</h2><div class="hp" aria-hidden="true"><label>Leave blank<input name="website" tabindex="-1" autocomplete="off"></label></div>'
      '<label class="req" for="k-n">Full name</label><input id="k-n" name="first_name" autocomplete="name" required><label class="req" for="k-e">Work email</label><input id="k-e" name="email" type="email" autocomplete="email" required>'
      '<label class="req" for="k-c">Company (legal name)</label><input id="k-c" name="company" autocomplete="organization" required><div class="r2"><div><label for="k-p">Phone</label><input id="k-p" name="phone" type="tel"></div><div><label for="k-u">Company website</label><input id="k-u" name="company_url"></div></div>'
      '<label for="k-m">Expected monthly volume, products, and two trade references</label><textarea id="k-m" name="message" rows="4"></textarea><div class="ts"></div><button class="btn btn-dark" type="submit">Send credit application</button></form></div></section>'
      + tr + f'<section class="sec"><div class="wrap"><div class="head" style="text-align:center;margin-inline:auto"><h2>Frequently asked questions</h2></div>{faq_html(faqs)}</div></section>')
    return layout(cur, "Ordering, Terms & Credit | Global Palate", desc, body, schema=[faq_ld(faqs)], crumbs=[("Ordering & terms", cur)])

def about():
    cur = '/about/'
    desc = "Global Palate is a U.S.-based B2B supplier of certified organic ingredients, stocked in Compton, CA for manufacturers in the United States and Canada."
    body = (crumbs_html(cur, [("About", cur)]) + page_hero("About Global Palate", "We supply certified organic ingredients to manufacturers, from U.S. stock.", "Global Palate is a U.S.-based business-to-business supplier serving the United States and Canada.")
     + f'''<section class="sec"><div class="wrap two"><div class="rich"><h2>What we do</h2><p>We hold certified organic ingredients in a warehouse in Compton, California and sell them in bulk to manufacturers. Our catalog today is {E(names())}, and we plan to add more.</p>
<p>Buyers come to us so that a trial batch or a reorder does not depend on an ocean shipment. Every batch is tested and ships with a Certificate of Analysis, and the documentation packet is available before you order.</p></div>
<div class="rich"><h2>Who we are</h2><p>Global Palate is a North America division of {E(SITE["parent"])}. Our warehouse is at {E(addr(SITE["warehouse"]))}, and our office is at {E(addr(SITE["office"]))}.</p>
<p>We work with {len(INDUSTRIES)} types of manufacturer: <a href="{rel(cur,"/industries/nutraceutical-dietary-supplement/")}">dietary supplement</a>, <a href="{rel(cur,"/industries/functional-food-beverage/")}">functional food and beverage</a>, <a href="{rel(cur,"/industries/herbal-traditional-formulation/")}">herbal and traditional formulation</a>, and <a href="{rel(cur,"/industries/spice-seasoning/")}">spice and seasoning</a>.</p></div></div></section>
{about_extra()}<section class="sec alt"><div class="wrap"><div class="head"><h2>How we work</h2></div><div class="grid3"><div class="card"><span class="n">01</span><h3>Documented</h3><p>Batch Certificates of Analysis and certificates are available before you commit to an order.</p></div><div class="card"><span class="n">02</span><h3>In stock</h3><p>Inventory is held in the U.S., so orders ship domestically.</p></div><div class="card"><span class="n">03</span><h3>Practical</h3><p>Minimums sized for manufacturers who need a trial run before scaling.</p></div></div></div></section>'''
     + band(cur, "Talk to our team", "Request pricing, a sample or the documentation packet."))
    return layout(cur, "About Global Palate | Organic Ingredient Supplier", desc, body, crumbs=[("About", cur)], nav='/about/')

def contact():
    cur = '/contact/'
    desc = "Contact Global Palate for organic ingredient pricing, samples and documentation. Call, email or send a request and our sales team will reply."
    prods = ''.join(f'<label><input type="checkbox" name="products" value="{p["key"]}"> {E(p["short"])}</label>' for p in PRODUCTS)
    meet = (f'<a class="btn btn-primary" href="{SITE["booking_url"]}">Book a meeting</a>' if SITE['booking_url'] else f'<a class="btn btn-primary" href="mailto:{SITE["email"]}?subject=Meeting%20at%20Supply%20Side%20Global">Email us to book a meeting</a>')
    body = (crumbs_html(cur, [("Contact", cur)]) + page_hero("Contact", "Talk to our sales team", f"Send a request below, call, or email. We reply {SITE['response']}.")
     + f'''<section class="sec"><div class="wrap two"><div class="contact-i box"><div class="it"><div><h4>Phone</h4><p><a href="tel:{SITE["phone"].replace(" ","")}">{SITE["phone"]}</a><br><a href="tel:{SITE["phone2"].replace(" ","")}">{SITE["phone2"]}</a></p></div></div>
<div class="it"><div><h4>Email</h4><p><a href="mailto:{SITE["email"]}">{SITE["email"]}</a></p></div></div><div class="it"><div><h4>Hours</h4><p>{SITE["hours"]}</p></div></div>
<div class="it"><div><h4>Warehouse</h4><p>{E(addr(SITE["warehouse"]))}</p></div></div><div class="it"><div><h4>Office</h4><p>{E(addr(SITE["office"]))}</p></div></div></div>
<form class="form box" id="quote" data-lead="quote" method="post" action="#"><h2 style="font-size:1.3rem">Request a quote, sample or information</h2><div class="hp" aria-hidden="true"><label>Leave blank<input name="website" tabindex="-1" autocomplete="off"></label></div>
<label for="c-t">I would like to</label><select id="c-t" name="req_type"><option value="quote">Request a quote</option><option value="sample">Request a sample</option><option value="inquiry">Ask a general question</option></select>
<div class="r2"><div><label class="req" for="c-fn">First name</label><input id="c-fn" name="first_name" autocomplete="given-name" required></div><div><label for="c-ln">Last name</label><input id="c-ln" name="last_name" autocomplete="family-name"></div></div>
<div class="r2"><div><label class="req" for="c-em">Work email</label><input id="c-em" name="email" type="email" autocomplete="email" required></div><div><label class="req" for="c-co">Company</label><input id="c-co" name="company" autocomplete="organization" required></div></div>
<div class="r2"><div><label for="c-ph">Phone (optional)</label><input id="c-ph" name="phone" type="tel" autocomplete="tel"></div><div><label for="c-zip">Delivery ZIP / postal code</label><input id="c-zip" name="zip" autocomplete="postal-code"></div></div>
<fieldset style="border:0;padding:0;margin:0"><legend class="sr">Products of interest</legend><label>Products of interest</label><div class="checks">{prods}</div></fieldset>
<div class="r2"><div><label for="c-q">Quantity</label><div style="display:grid;grid-template-columns:1fr 90px;gap:8px"><input id="c-q" name="quantity" type="number" min="1" step="any"><select name="unit" aria-label="Unit"><option value="kg">kg</option><option value="drum">drums</option></select></div></div><div><label for="c-d">Needed by</label><input id="c-d" name="needed_by" type="date"></div></div>
<label for="c-u">Intended use</label><select id="c-u" name="intended_use"><option value="">Select&hellip;</option><option>Dietary supplement</option><option>Functional food &amp; beverage</option><option>Herbal / traditional formulation</option><option>Spice &amp; seasoning</option><option>Other</option></select>
<label for="c-m">Message</label><textarea id="c-m" name="message"></textarea><div class="ts"></div><button class="btn btn-dark" type="submit">Send request</button></form></div></section>
<section class="sec alt" id="meeting"><div class="wrap"><div class="band"><div><h2>Meet us at Supply Side Global</h2><p>{E(SITE["show"].replace(" Book a meeting now!",""))}</p></div><div class="hero-cta2">{meet}</div></div></div></section>''')
    if not SITE.get('show'): body = __import__('re').sub(r'<section class="sec alt" id="meeting">.*?</section>', '', body, flags=__import__('re').S)
    return layout(cur, "Contact Global Palate | Request a Quote or Sample", desc, body, schema=[org_ld()], crumbs=[("Contact", cur)], nav='/contact/')

CERTS = [("USDA Organic", "#E1DCF2", "var(--forest)", '<path d="M5 20a15 15 0 0 1 15-15h1v1a15 15 0 0 1-15 15H5z"/><path d="M5 20 19 6"/>'),
         ("FSSC 22000", "#FDEFC0", "#6b5313", '<path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3Z"/><path d="m9 12 2 2 4-4"/>'),
         ("HACCP", "#E6D9F2", "#4a2f6b", '<path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3Z"/><path d="m9 12 2 2 4-4"/>'),
         ("Kosher", "#DCEAF5", "#1f4a69", '<path d="m12 2 2.4 4.9 5.4.8-3.9 3.8.9 5.4-4.8-2.5-4.8 2.5.9-5.4-3.9-3.8 5.4-.8Z"/>'),
         ("Halal", "#DDEFE2", "#1f6a3d", '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z"/>'),
         ("Non-GMO", "#F5DCE0", "#7a2434", '<circle cx="12" cy="12" r="9"/><path d="M8 8l8 8M16 8l-8 8"/>'),
         ("Gluten free", "#EFE3D4", "#6b4c24", '<path d="M12 2c-1 3-4 4-4 8a4 4 0 0 0 8 0c0-4-3-5-4-8Z"/><path d="M12 14v8"/>')]

def quality_block():
    q = quality_facts()
    return f'<section class="sec alt"><div class="wrap"><div class="head"><h2>Compliance and policies</h2></div>{q}</div></section>' if q else ''

def quality():
    cur = '/quality/'
    desc = "Batch Certificates of Analysis, heavy-metal, microbiological and pesticide-residue testing, and certificates for each Global Palate ingredient. Get the packet."
    cc = ''.join(f'<div class="cc"><i style="background:{bg}"><svg viewBox="0 0 24 24" fill="none" stroke="{st}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{pa}</svg></i>{n}</div>' for n, bg, st, pa in CERTS)
    faqs = [("Can I get a Certificate of Analysis before ordering?", "Yes. Request the documentation packet and we will email current specification sheets and sample COAs before you ask for a quote."),
            ("Which certifications apply to which products?", "Certifications vary by ingredient. Each product page lists its purity statements, and the documentation packet includes certificate copies. Tell us which products you are evaluating and we will confirm what applies, including the certifier and certificate details."),
            ("What is tested on each batch?", "Every batch is tested for heavy metals, microbiological safety and pesticide residue, and the results are compiled into that batch's Certificate of Analysis."),
            ("What if a delivered lot does not match its COA?", co('Recall / non-conformance policy') or "Contact us right away with the batch number. We will review it with you.")]
    pf = ''.join(f'<label><input type="checkbox" name="products" value="{p["key"]}"> {E(p["short"])}</label>' for p in PRODUCTS)
    body = (crumbs_html(cur, [("Quality & Documentation", cur)]) + page_hero("Quality & documentation", "Documentation you can review before you order.", "Certificates of Analysis, specification sheets and certificates for the ingredients you are evaluating.")
     + f'''<section class="sec"><div class="wrap"><div class="head"><h2>Certifications across our catalog</h2><p>Certifications vary by ingredient. Certificate copies, including certifier and certificate details, are part of the documentation packet.</p></div><div class="cg">{cc}</div></div></section>{cert_register()}{quality_block()}
<section class="sec alt" id="documents"><div class="wrap two"><div><div class="head"><h2>What is in the documentation packet</h2></div><ul class="ticks"><li>Certificate of Analysis for the batch</li><li>Heavy-metal, microbiological and pesticide-residue results</li><li>Organic and other certificate copies</li><li>Product specification sheets</li></ul></div>
<form class="form box" data-lead="documents" method="post" action="#"><h3>Get the documentation packet</h3><div class="hp" aria-hidden="true"><label>Leave blank<input name="website" tabindex="-1" autocomplete="off"></label></div>
<label class="req" for="q-n">Full name</label><input id="q-n" name="first_name" autocomplete="name" required><label class="req" for="q-e">Work email</label><input id="q-e" name="email" type="email" autocomplete="email" required><label class="req" for="q-c">Company</label><input id="q-c" name="company" autocomplete="organization" required>
<fieldset style="border:0;padding:0;margin:0"><legend class="sr">Products</legend><label>Products you are evaluating (optional)</label><div class="checks">{pf}</div></fieldset><div class="ts"></div><button class="btn btn-dark" type="submit">Send me the packet</button></form></div></section>
<section class="sec"><div class="wrap"><div class="head"><h2>Our quality process</h2></div><div class="grid4"><div class="card"><span class="n">01</span><h3>Organic sourcing</h3><p>Certified-organic ingredients from origin.</p></div><div class="card"><span class="n">02</span><h3>Testing</h3><p>Heavy metals, microbiological and pesticide residue on each batch.</p></div><div class="card"><span class="n">03</span><h3>COA</h3><p>Results compiled into a batch Certificate of Analysis.</p></div><div class="card"><span class="n">04</span><h3>Traceability</h3><p>Batch-to-batch traceability for every shipment.</p></div></div></div></section>
<section class="sec alt"><div class="wrap"><div class="head" style="text-align:center;margin-inline:auto"><h2>Frequently asked questions</h2></div>{faq_html(faqs)}</div></section>''')
    return layout(cur, "Quality & Documentation | Global Palate", desc, body, schema=[faq_ld(faqs)], crumbs=[("Quality & Documentation", cur)], nav='/quality/')

def supply():
    cur = '/supply-chain/'
    desc = "Global Palate stocks organic ingredients in Compton, CA and ships by LTL or truckload across the U.S. and Canada, with an East Coast office in Edison, NJ."
    rows = [("Where the stock is", "U.S. warehouse, Compton CA", "At origin until shipped"), ("Minimum order", SITE['moq'] + " on powders", "Often container-scale lots"),
            ("Documentation", "Batch COA; certificates on request", "Varies by supplier"), ("Delivery", "LTL or full-truckload within the U.S.", "Ocean freight plus customs clearance")]
    tr = ''.join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in rows)
    body = (crumbs_html(cur, [("Supply Chain", cur)]) + page_hero("Supply chain", "Stocked in California, shipped across North America.", "One warehouse, one office and one sales team for quotes, documents and reorders.")
     + f'''<section class="sec"><div class="wrap"><div class="loc"><div><span class="kicker">Warehouse &middot; all inventory</span><h3>{SITE["warehouse"]["name"]}</h3><address>{E(addr(SITE["warehouse"]))}</address><p>All stock is held here. Orders ship by LTL or full-truckload freight. {E(SITE["lead_time"])}</p></div>
<div><span class="kicker">Office &middot; East Coast</span><h3>{SITE["office"]["name"]}</h3><address>{E(addr(SITE["office"]))}</address><p>Our East Coast office for pricing, documents and order support. Stock ships from Compton.</p></div></div></div></section>
<section class="sec alt"><div class="wrap"><div class="head"><h2>How an order moves</h2></div><div class="grid4"><div class="card"><span class="n">01</span><h3>Sourced from origin</h3><p>Certified-organic ingredients, with origin in India.</p></div><div class="card"><span class="n">02</span><h3>Tested and documented</h3><p>Heavy metals, microbiological and pesticide residue, with a batch COA.</p></div><div class="card"><span class="n">03</span><h3>Held in Compton, CA</h3><p>Inventory is stocked in our U.S. warehouse.</p></div><div class="card"><span class="n">04</span><h3>Shipped to you</h3><p>LTL or full-truckload freight, confirmed with your quote.</p></div></div></div></section>
<section class="sec"><div class="wrap why2"><div><h2>Stock in the U.S. vs importing direct</h2><ul class="ticks"><li>No ocean freight or customs clearance on your side.</li><li>Order sizes suited to trials and regular production.</li><li>Documents available before you commit.</li></ul></div><table class="cmp"><thead><tr><th scope="col"></th><th scope="col" class="gp">Global Palate</th><th scope="col" class="ot">Importing direct</th></tr></thead><tbody>{tr}</tbody></table></div></section>'''
     + band(cur, "Need freight timing for your location?", "Send your delivery ZIP code and quantity and we will confirm."))
    return layout(cur, "Supply Chain & Delivery | Global Palate", desc, body, crumbs=[("Supply Chain", cur)], nav='/supply-chain/')

LEGAL = {
 'privacy': ("Privacy Policy", "Privacy policy for globalpalate.co: what information we collect through our forms, how we use it, and your choices, including California privacy rights.", [
  ("Information we collect", "When you submit a form on this site we collect the details you enter, such as your name, work email, phone number, company, product interest, quantity, delivery ZIP code and message. We also receive technical data such as your browser type and the page you submitted from. If analytics is enabled and you accept cookies, we collect usage data about how the site is used."),
  ("How we use it", "We use your information to respond to your request, send documents you ask for, provide quotes and samples, and manage our business relationship with you. We store contact records in our customer relationship management (CRM) system."),
  ("Sharing", "We do not sell your personal information. We share it with service providers that help us run the site and our CRM, and when the law requires it."),
  ("Retention", "We keep inquiry records for as long as needed for business and legal purposes."),
  ("Your choices and California rights", "You can ask to access, correct or delete your personal information, and California residents have additional rights under the CCPA, including the right to opt out of the sale or sharing of personal information. We do not sell personal information. To make a request, email " + SITE['email'] + "."),
  ("Contact", "Global Palate, " + addr(SITE['office']) + ". " + SITE['email'] + ".")]),
 'terms': ("Terms & Conditions", "Terms and conditions for using globalpalate.co, including how we treat product information, quotes, batch documentation and limits on liability for buyers.", [
  ("Use of this site", "This site provides information about ingredients supplied by Global Palate to businesses. By using it you agree to these terms."),
  ("Product information", "Product descriptions and specifications are provided for general information and may change. The Certificate of Analysis for a specific batch governs that batch."),
  ("Quotes and orders", "Quotes are not binding until accepted in writing by Global Palate. Prices, availability and lead times are confirmed on each quote."),
  ("Ingredients only", "We supply ingredients for further manufacturing. Buyers are responsible for the formulation, labeling, claims and regulatory compliance of their finished products."),
  ("Limitation of liability", "To the extent permitted by law, Global Palate is not liable for indirect or consequential damages arising from use of this site."),
  ("Contact", SITE['email'])]),
 'cookie-policy': ("Cookie Policy", "Cookie policy for globalpalate.co: how we use essential and analytics cookies, when analytics loads, and how you can accept or decline them in the banner.", [
  ("What cookies are", "Cookies are small files stored on your device by your browser."),
  ("How we use them", "The site works without tracking cookies. If we enable analytics (for example Google Analytics), it loads only after you accept cookies in the banner. Your choice is stored in your browser so we can remember it."),
  ("Your choices", "You can decline analytics cookies in the banner and clear stored choices in your browser settings at any time."),
  ("Contact", SITE['email'])]),
}
def legal(slug):
    t, d, secs = LEGAL[slug]; cur = f'/{slug}/'
    body = crumbs_html(cur, [(t, cur)]) + page_hero("Legal", t, "Last updated " + SITE['date'] + ".") + '<section class="sec"><div class="wrap"><div class="rich">' + ''.join(f'<h2>{E(h)}</h2><p>{E(x)}</p>' for h, x in secs) + '</div></div></section>'
    return layout(cur, f"{t} | Global Palate", d, body, crumbs=[(t, cur)])

THANKS = {'quote': "Thanks, we have your quote request", 'sample': "Thanks, we have your sample request",
          'inquiry': "Thanks, we have your message", 'documents': "Thanks, your documents are on the way", 'credit': "Thanks, we have your credit application"}
def thanks(t):
    cur = f'/thank-you/{t}/'
    nxt = {'quote': "A member of our sales team will review it and reply with pricing and freight details.", 'sample': "A member of our sales team will confirm your sample details.",
           'inquiry': "A member of our team will reply to your message.", 'credit': "Our team will review your application and reply with terms.", 'documents': "Check your inbox for the Certificate of Analysis and specification sheets. If they do not arrive, contact us and we will resend them."}[t]
    body = f'<section class="sec"><div class="wrap" style="max-width:720px"><h1 style="font-size:2rem">{THANKS[t]}</h1><p>{nxt} We reply {SITE["response"]} ({SITE["hours"]}).</p><p>Need us sooner? Call <a href="tel:{SITE["phone"].replace(" ","")}">{SITE["phone"]}</a>.</p><div class="hero-cta2"><a class="btn btn-primary" href="{rel(cur,"/#products")}">Browse our ingredients</a><a class="btn" href="{rel(cur,"/quality/")}">Quality &amp; documentation</a></div></div></section>'
    return layout(cur, THANKS[t] + " | Global Palate", "Thank you for contacting Global Palate.", body, noindex=True, conv=t)

def notfound():
    import re as _r
    body = '<section class="sec"><div class="wrap" style="max-width:720px"><h1 style="font-size:2rem">Page not found</h1><p>The page you are looking for has moved or does not exist.</p><a class="btn btn-primary" href="/">Go to the homepage</a></div></section>'
    h = layout('/', "Page not found | Global Palate", "Page not found.", body, noindex=True)
    def fix(m):
        attr, v = m.group(1), m.group(2)
        if _r.match(r'(https?:|//|/|#|mailto:|tel:|data:)', v): return m.group(0)
        frag = ''
        if '#' in v: v, frag = v.split('#', 1); frag = '#' + frag
        v = '/' + v
        if v.endswith('index.html'): v = v[:-len('index.html')]
        return f'{attr}="{v}{frag}"'
    h = _r.sub(r'\b(href|src|srcset)="([^"]*)"', fix, h)
    h = h.replace('data-root=""', 'data-root="/"')
    return h
