# Global Palate: admin setup and user guide

The website stays a fast static site. The admin (`/admin/`) edits product and SEO data, stores it in Cloudflare KV, and **Publish** rebuilds the site from that data.

```
/admin/  --save-->  KV "draft"  --Publish-->  KV "published"  --deploy hook-->  Cloudflare build
                                                                                  |  python3 build/build.py
                                                          GET /api/export (token) <-+  reads "published", renders every page
```
Unpublished edits never reach the live site, even if a rebuild is triggered by something else.

## One-time setup (about 20 minutes)
1. **Put this folder in a private GitHub repo** (the `out/` folder is ignored; Cloudflare builds it).
2. **Cloudflare dashboard > Workers & Pages > Create > Pages > connect the repo.**
   - Build command: `pip install -r requirements.txt && python3 build/build.py`
   - Build output directory: `out`
   - Environment variable `PYTHON_VERSION` = `3.11`
3. **Create a KV namespace** (Storage & Databases > KV > Create, name it `gp-admin`). In the Pages project: *Settings > Bindings > Add > KV namespace*, variable name **`GP_KV`**.
4. **Settings > Variables and secrets** (Production), add:
   | Name | Value |
   |---|---|
   | `ADMIN_PASSWORD` | a long passphrase (16+ characters). This is the admin login. |
   | `BUILD_TOKEN` | a random 32+ character string (used only by the build to read published data) |
   | `EXPORT_URL` | `https://globalpalate.co/api/export` (use the `*.pages.dev` address until the domain is connected) |
   | `DEPLOY_HOOK_URL` | create one in *Settings > Builds > Deploy hooks* (branch: main) and paste the URL |
   | Zoho / Resend / Turnstile | as in the forms README (`ZOHO_XNQSJSDP`, `ZOHO_XMIWTLD`, `ZOHO_ACTIONTYPE`, ...) |
5. **Deploy.** The first build has nothing published yet, so it uses the data committed in `data/site-data.json`. Open `https://globalpalate.co/admin/`, sign in, and your six products are there.
6. **Recommended extra lock:** Cloudflare Zero Trust > Access > add an application for `globalpalate.co/admin*` and `globalpalate.co/api/admin*` limited to your email. The password still applies on top.

If a build cannot reach `/api/export`, it logs a warning and builds from the committed data instead, so the site never goes down because of the admin.

## Using the admin
- **Products**: add, edit, duplicate, reorder, delete. *Draft* products are saved but hidden. Each product has tabs: Basics, Content (headline, description, spec table, FAQs, "things to know"), Pricing & stock, Quality tests, Photo, SEO.
- **SEO tab** (per product): SEO title and meta description with live character counters, focus keyword, a Google preview, a 16-point checklist and score, canonical URL, noindex, social title/description. Structured data (Product, FAQ, breadcrumbs, price/stock offers), the sitemap entry (with last-modified date), the social image and `llms.txt` are generated automatically.
- **Changing a live product's URL slug** adds a 301 redirect from the old address automatically. Deleting a product offers a redirect to the homepage.
- **Page SEO**: title, meta description, social text, canonical and noindex for Home, About, Contact, Quality, Ordering, Supply chain, Industries and the legal pages.
- **Site settings**: phone, email, hours, reply time, minimum order, lead-time sentence, announcement bar (empty hides it), booking link, addresses, Google Analytics ID, Turnstile key, Search Console verification, social profiles, extra robots.txt rules.
- **Certificates, Company facts, Transit times, Redirects**: all editable; empty fields are never published.
- **History**: the last 30 saved versions with one-click restore (restoring creates a new draft).
- **Save draft** (Ctrl+S) keeps your work. **Publish** makes the saved draft live and rebuilds (about 1 to 2 minutes). Two people editing at once: the second save is refused with a "reload" message instead of overwriting.
- The admin warns you about data problems (pack weight vs pallet maths, a result above its own limit, tier prices outside the price range). Those rows are hidden on the site until fixed.

## Try it on your own computer first
```
python3 -m pip install -r requirements.txt
python3 build/build.py
node dev-server.mjs          # http://localhost:8788   admin password: admin
```
Publish in this local preview runs a real rebuild. Data lives in `.dev-kv.json` (git-ignored).

## What the admin does not edit
Body text of the home page, About, Quality, Industries and legal pages, the regional turmeric pages, and the page design are still in `build/` (`content.py`, `pages1.py`, `pages2.py`). Ask for changes there, or tell me which of these you want moved into the admin next.

## Tests
`node tests/test_admin.mjs` (API, login, validation, publish, export), `node tests/test_lead.mjs` (forms), `python3 tests/validate.py` (HTML), `python3 tests/browser.py` (public site), `tests/run_e2e.sh <scratch-dir>` (full admin browser flow).
