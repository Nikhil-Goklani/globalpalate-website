# -*- coding: utf-8 -*-
"""Builds the owner workbook. Yellow cells = fill in. Everything is optional: the site shows only what is filled in."""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from content import PRODUCTS

HDR = 5
F = 'Arial'
YEL = PatternFill('solid', fgColor='FFF7C2'); PUR = PatternFill('solid', fgColor='E1DCF2'); GRN = PatternFill('solid', fgColor='224029')
thin = Side(style='thin', color='C9C9C9'); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
wb = Workbook()

def sheet(name, title, note, cols, widths, rows, example=None, first=False):
    ws = wb.active if first else wb.create_sheet()
    ws.title = name
    ws['A1'] = title; ws['A1'].font = Font(name=F, bold=True, size=14, color='224029')
    ws['A2'] = note; ws['A2'].font = Font(name=F, size=10); ws['A2'].alignment = Alignment(wrap_text=True, vertical='top')
    ws.merge_cells(start_row=2, start_column=1, end_row=3, end_column=min(len(cols), 8)); ws.row_dimensions[2].height = 30
    ws['A4'] = 'Yellow = please fill in. Leave blank anything you do not have: the website will not show it (nothing is invented).'
    ws['A4'].font = Font(name=F, size=9, italic=True)
    for i, c in enumerate(cols, 1):
        x = ws.cell(HDR, i, c); x.font = Font(name=F, bold=True, color='FFFFFF'); x.fill = GRN; x.alignment = Alignment(wrap_text=True, vertical='center'); x.border = BOX
        ws.column_dimensions[x.column_letter].width = widths[i-1]
    ws.row_dimensions[HDR].height = 34
    r = HDR + 1
    if example:
        for i, v in enumerate(example, 1):
            x = ws.cell(r, i, v); x.font = Font(name=F, size=9, italic=True, color='666666'); x.fill = PUR; x.border = BOX; x.alignment = Alignment(wrap_text=True, vertical='top')
        ws.cell(r, 1).value = 'EXAMPLE: ' + str(example[0]); r += 1
    for row in rows:
        for i, v in enumerate(row, 1):
            x = ws.cell(r, i, v); x.font = Font(name=F, size=10); x.border = BOX; x.alignment = Alignment(wrap_text=True, vertical='top')
            if i > (len(row) - len([1 for _ in row if False])) and False: pass
        r += 1
    ws.freeze_panes = ws.cell(HDR + 1, 2)
    return ws, r

def yellow(ws, c0, r0, r1, ncols):
    for r in range(r0, r1):
        for c in range(c0, ncols + 1):
            ws.cell(r, c).fill = YEL

# ---- Start here
ws = wb.active; ws.title = 'Start here'
lines = [('Global Palate: details we need from you', True),
 ('', False),
 ('How this works', True),
 ('1. Fill in the yellow cells on each sheet. Skip anything you do not have yet; the website simply leaves it out. We never invent prices, limits or certificates.', False),
 ('2. Save the file as global-palate-data.xlsx and send it back, together with any PDFs listed below.', False),
 ('3. We rebuild the site from this file, so everything updates in one pass.', False),
 ('', False),
 ('Sheets', True),
 ('Commercial: price range, volume tiers, price basis, stock, lot, pack sizes, pallet quantities, origin and supplier per product.', False),
 ('Specs: each test with the limit, method and typical result (moisture, ash, mesh, heavy metals, micro, adulterants, ETO).', False),
 ('Certificates: which certificate covers which product, who holds it, the certifier, number, expiry and a verification link.', False),
 ('Company facts: years in business, story, FDA registration, FSVP, GMP, insurance, recall and returns policy, payment terms, references.', False),
 ('Transit: LTL / full-truckload days from Compton, CA by state.', False),
 ('', False),
 ('Files to send as PDFs (optional but strongly recommended)', True),
 ('For each product: a sample Certificate of Analysis (redacted is fine) and a one-page specification sheet. Name them like turmeric-sample-coa.pdf and turmeric-spec-sheet.pdf (use turmeric, ashwagandha, moringa, ginger, tamarind, arrowroot).', False),
 ('A copy of your product liability insurance certificate (or just the coverage amount in Company facts).', False)]
for i, (t, b) in enumerate(lines, 1):
    c = ws.cell(i, 1, t); c.font = Font(name=F, bold=b, size=14 if i == 1 else 11, color='224029' if b else '000000'); c.alignment = Alignment(wrap_text=True, vertical='top')
ws.column_dimensions['A'].width = 120

# ---- Commercial
cols = ['Product key', 'Product', 'Price from (USD)', 'Price to (USD)', 'Price unit (kg or drum)', 'Price basis (FOB Compton / Delivered)', 'Volume tiers (one per line, e.g. 100-499 kg: $8.50/kg)', 'Price valid as of (date)',
        'In stock? (Yes/No)', 'Quantity on hand (kg or drums)', 'Ships within (e.g. 2-3 business days)', 'Lot / crop year', 'Pack format (e.g. 25 kg multiwall bag)', 'Net weight per pack',
        'Packs per pallet', 'Pallet net weight (kg)', 'Origin region in India (state / district)', 'Supplier / processor name', 'Last audit (who, when, result)']
rows = [[p['key'], p['name']] + [''] * (len(cols) - 2) for p in PRODUCTS]
ws, end = sheet('Commercial', 'Commercial details per product', 'One row per product. Price is shown as an indicative range with the basis you state. Stock and lot are shown only if filled in.',
                cols, [13, 30, 12, 12, 12, 22, 40, 14, 11, 16, 22, 16, 26, 14, 12, 14, 26, 26, 34], rows,
                example=['turmeric', 'Organic Turmeric Powder', 6.10, 8.50, 'kg', 'FOB Compton, CA', '100-499 kg: $8.50/kg\n500-999 kg: $7.40/kg', '2026-11-01', 'Yes', 4200, '2-3 business days', 'Crop 2026', '25 kg multiwall bag', 25, 40, 1000, 'Maharashtra', 'Name of processor', 'Third-party audit, Mar 2026, passed'])
yellow(ws, 3, HDR + 2, end, len(cols))
dv = DataValidation(type='list', formula1='"Yes,No"', allow_blank=True); ws.add_data_validation(dv); dv.add(f'I{HDR+2}:I{end}')

# ---- Specs
params = ['Particle size / mesh', 'Loss on drying (moisture)', 'Total ash', 'Marker content (curcumin / withanolides / other)', 'Lead (Pb)', 'Cadmium (Cd)', 'Arsenic (As)', 'Mercury (Hg)',
          'Total plate count', 'Yeast & mold', 'E. coli', 'Salmonella', 'Aflatoxin (B1 / total)', 'Ochratoxin A', 'Pesticide residue (program and limits)',
          'Adulterant screen (turmeric: lead chromate, synthetic dyes)', 'Steam sterilization / kill step', 'ETO / irradiation status', 'Allergen statement', 'Shelf life']
rows = [[p['key'], p['name'], prm, '', '', ''] for p in PRODUCTS for prm in params]
cols = ['Product key', 'Product', 'Parameter', 'Limit / specification', 'Test method (e.g. AOAC 2011.19, ICP-MS)', 'Typical result']
ws, end = sheet('Specs', 'Specifications and test limits', 'Only rows with a limit or result are published. Heavy-metal rows build the compliance statement on each product page.', cols, [13, 30, 44, 28, 34, 22], rows,
                example=['turmeric', 'Organic Turmeric Powder', 'Lead (Pb)', 'Not more than 1.0 ppm', 'ICP-MS', '0.2 ppm'])
yellow(ws, 4, HDR + 2, end, len(cols))

# ---- Certificates
certs = ['USDA Organic (NOP)', 'NOP organic import certificate', 'FDA food facility registration', 'Kosher', 'Halal', 'Non-GMO', 'FSSC 22000', 'HACCP', 'GMP', 'Gluten free']
cols = ['Certification', 'Applies to (product keys, comma-separated, or "all")', 'Certificate holder (name)', 'Holder type (Origin processor / Warehouse / Global Palate)', 'Certifier (e.g. name of certifying body)', 'Certificate number', 'Expiry date', 'Verification link (e.g. USDA Organic Integrity Database page)']
rows = [[c, '', '', '', '', '', '', ''] for c in certs]
ws, end = sheet('Certificates', 'Certificate register', 'Shows buyers which certificate covers which product, who holds it and how to verify it.', cols, [32, 30, 28, 30, 28, 20, 14, 50], rows,
                example=['USDA Organic (NOP)', 'all', 'Name of processor in India', 'Origin processor', 'Name of accredited certifier', 'ABC-12345', '2027-06-30', 'https://organic.ams.usda.gov/integrity/'])
yellow(ws, 2, HDR + 2, end, len(cols))
dv2 = DataValidation(type='list', formula1='"Origin processor,Warehouse,Global Palate"', allow_blank=True); ws.add_data_validation(dv2); dv2.add(f'D{HDR+2}:D{end}')

# ---- Company facts
items = [('Years in business', 'e.g. "Operating since 2014"'), ('Company story', '2-4 sentences: who started it, why, what you stand for'),
 ('FDA food facility registration', 'Who is registered (Global Palate or warehouse) and the FEI / registration number'),
 ('FSVP / importer of record', 'Who is the importer of record and who runs the FSVP (Foreign Supplier Verification Program)'),
 ('GMP statement', 'Which cGMP standard applies (21 CFR 117 / 111) and who is audited'),
 ('Product liability insurance', 'Coverage amount and insurer (certificate available on request?)'),
 ('Recall / non-conformance policy', 'Plain statement: how a recall or out-of-spec lot is handled, who to contact, timeline'),
 ('Returns policy', 'When returns/credits are accepted, time limit, who pays freight'),
 ('Payment terms', 'e.g. "Net 30 on approved credit; prepayment for first order"'),
 ('Default price basis', 'FOB Compton, CA or Delivered (used when a product row does not state it)'),
 ('Credit application', 'Do you offer credit? Yes/No and any minimum or trade references needed'),
 ('Lead-time statement', 'One sentence for the whole site, e.g. "In stock items ship within 2-3 business days"'),
 ('Hours', 'e.g. Monday-Friday, 9 AM-5 PM PT'), ('Reply time', 'e.g. within one business day'), ('Booking link', 'Calendly or similar for meetings'),
 ('MOQ (powders)', 'e.g. 100 kg'),
 ('Kill step statement', 'e.g. "Steam sterilized at origin, validated 5-log reduction" (only if true)'),
 ('ETO / irradiation statement', 'Plain statement for all products, or say it varies by product'),
 ('Heavy metals compliance statement', 'Your limits for lead, cadmium, arsenic and the standard you follow (e.g. USP <2232>, Prop 65 safe harbor)'),
 ('Cross-contact statement', 'Does the facility handle allergens? Shared lines? Allergen controls'),
 ('Origin and supplier audit status', 'Regions in India, years working with the processor, last audit'),
 ('Why Global Palate vs other U.S. distributors', 'One point per line. Only what you can prove (e.g. "Single-origin lots", "Organic import certificate on file")'),
 ('Customer references', 'Company names you may publish and/or "References on request"'),
 ('Planned products', 'Comma-separated, e.g. black pepper, cinnamon, cardamom, standardized extracts'),
 ('Netlify address', 'The netlify.app address buyers currently see, so we can redirect it to globalpalate.co')]
rows = [[a, '', b] for a, b in items]
ws, end = sheet('Company facts', 'Company facts and policies', 'One row per item. Text is published as written, so write it the way you want a buyer to read it.', ['Item', 'Your answer', 'What we need'], [40, 90, 70], rows)
yellow(ws, 2, HDR + 1, end, 2)

# ---- Transit
states = [('California', 'West'), ('Oregon', 'West'), ('Washington', 'West'), ('Nevada', 'West'), ('Arizona', 'West'), ('Utah', 'West'), ('Idaho', 'West'), ('Texas', 'Central'), ('Illinois', 'Central'),
          ('Georgia', 'East'), ('Florida', 'East'), ('North Carolina', 'East'), ('Pennsylvania', 'East'), ('New Jersey', 'East'), ('New York', 'East'), ('Massachusetts', 'East'), ('Ontario (Canada)', 'Canada')]
rows = [[s, r, '', '', ''] for s, r in states]
ws, end = sheet('Transit', 'Transit times from Compton, CA', 'Business days door to door once the order leaves the warehouse. Add or remove rows as needed.', ['State / province', 'Region (West/Central/East/Canada)', 'LTL transit (business days)', 'Full truckload transit (business days)', 'Notes (e.g. typical freight cost per pallet)'], [26, 28, 22, 26, 44], rows,
                example=['California', 'West', '1-2', '1', ''])
yellow(ws, 3, HDR + 2, end, 5)

os.makedirs('data', exist_ok=True)
wb.save('data/global-palate-data.xlsx')
print('saved')
