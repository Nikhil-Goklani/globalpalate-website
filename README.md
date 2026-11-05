# Global Palate website

Static site (Python build) + Cloudflare Pages Functions (forms, admin API). Start with **ADMIN-SETUP.md**.

- `build/` page builder, templates and copy. `data/site-data.json` is the committed seed for products, SEO, settings (the admin takes over after first deploy).
- `public/` static files copied into the site (CSS, JS, images, `_headers`, the admin page at `public/admin/`).
- `functions/` Cloudflare Pages Functions: `api/lead.js` (forms), `api/admin/` (admin API), `api/export.js`, `api/img/`.
- `data/documents/` PDFs (sample COAs, spec sheets, testing reports) named like `turmeric-sample-coa.pdf`, `turmeric-spec-sheet.pdf`, `turmeric-testing-report.pdf`. They are published on each product page; you can also commit new ones via GitHub.
- `docs/legacy-import-workbook.xlsx` the workbook used to create the first seed.

