# Put the site live: GitHub + Cloudflare Pages (step by step)

Time: about 45 minutes the first time, plus DNS waiting time. You need: a GitHub account, a Cloudflare account (free), and access to wherever `globalpalate.co` is registered (Hostinger).

Do the steps in order. Cloudflare's screens change now and then; the names below are the ones to look for.

---
## Part 1. Put the code on GitHub (10 min)
1. github.com > **New repository** > name it `global-palate-site` > **Private** > Create (leave "add README" unticked).
2. On the empty repo page click **uploading an existing file**.
3. Unzip `global-palate-github-repo.zip` on your computer. Open the unzipped folder and **drag everything inside it** (folders `build`, `data`, `docs`, `functions`, `public`, `tests` and the loose files, including `.gitignore`) into the GitHub page. Do not drag the outer folder itself.
   - It is about 55 files, under GitHub's 100-files-per-upload limit. If your computer hides `.gitignore`, that is fine; it is optional.
4. Commit message `First upload` > **Commit changes**.
5. Check the repo shows `build`, `functions`, `public`, `data` at the top level (not inside another folder). If everything sits inside one extra folder, the Cloudflare build will fail. Re-upload.

(Prefer Git? `git init`, `git add .`, `git commit -m "First upload"`, `git remote add origin <url>`, `git push -u origin main`.)

## Part 2. Create the Cloudflare Pages project (10 min)
1. dash.cloudflare.com > **Workers & Pages** > **Create** > choose **Pages** > **Connect to Git** (if the page pushes you to Workers, look for "Looking to deploy Pages? Get started").
2. Authorise GitHub, pick `global-palate-site`, **Begin setup**.
3. Settings:
   - Project name: `global-palate` (your temporary address becomes `global-palate.pages.dev`)
   - Production branch: `main`
   - Framework preset: **None**
   - Build command: `pip install -r requirements.txt && python3 build/build.py`
   - Build output directory: `out`
   - Environment variables (open the section): `PYTHON_VERSION` = `3.11`
4. **Save and Deploy.** The first build takes about 1-2 minutes. It should end green and show `https://global-palate.pages.dev`.
   - If the log says `python3: command not found`, change the build command to `pip install -r requirements.txt && python build/build.py`.
5. Open the `.pages.dev` address and check the site looks right. (Forms and admin are not set up yet.)

## Part 3. Storage and secrets for the admin and forms (10 min)
1. **KV store:** dashboard > **Storage & Databases > KV > Create** > name `gp-admin`.
2. In your Pages project: **Settings > Bindings > Add > KV namespace** > Variable name **`GP_KV`** (exactly) > choose `gp-admin` > Save. Add it for **Production** (and Preview if you want).
3. **Settings > Variables and secrets > Add** (Production):

| Name | Type | Value |
|---|---|---|
| `ADMIN_PASSWORD` | Secret | Long passphrase, 16+ characters. This is your admin login. |
| `BUILD_TOKEN` | Text | A random string, 32+ characters (use a password generator). |
| `EXPORT_URL` | Text | `https://global-palate.pages.dev/api/export` for now. Change to `https://globalpalate.co/api/export` after Part 5. |
| `DEPLOY_HOOK_URL` | Secret | Created in step 4 below. |
| `ZOHO_XNQSJSDP`, `ZOHO_XMIWTLD`, `ZOHO_ACTIONTYPE` | Text | From your Zoho CRM Web-to-Lead form (hidden fields). Needed for forms to send leads. |
| `RESEND_API_KEY`, `NOTIFY_TO`, `NOTIFY_FROM` | optional | Email copy of every lead. |
| `TURNSTILE_SECRET` | Secret | Optional spam check (site key goes in the admin under Site settings). |

   `BUILD_TOKEN` is a plain Text variable on purpose: the site build needs to read it as well as the admin.
4. **Deploy hook:** **Settings > Builds > Deploy hooks > Add** > name `admin-publish`, branch `main` > copy the URL > paste it as `DEPLOY_HOOK_URL` above.
5. **Redeploy** so the new settings apply: **Deployments > latest > Retry deployment** (or push any change).

## Part 4. Test the admin (10 min)
1. Open `https://global-palate.pages.dev/admin/`, sign in with `ADMIN_PASSWORD`. You should see 6 products.
2. Change a product's SEO title > **Save draft** > **Publish**. Wait 1-2 minutes (watch **Deployments**: a new build appears). Reload the product page: the title changed.
3. In the build log of that deployment look for `Using published admin data from ...`. If you see `WARNING: could not fetch published data`, check `EXPORT_URL` and `BUILD_TOKEN` (they must match exactly and the first publish must have happened).
4. Submit a test quote on the live site and confirm the lead appears in Zoho (or your email).

## Part 5. Connect globalpalate.co (30 min + waiting)
Your domain is at Hostinger and the old site may be running there. Switching DNS replaces the old site, so do this when you are ready to go live.
1. Cloudflare dashboard > **Add a domain** > `globalpalate.co` > Free plan. Cloudflare scans and copies your existing DNS records. **Check that every email record is there** (MX, SPF/TXT, DKIM, DMARC). Compare against Hostinger's DNS zone. If email is hosted at Hostinger, these must be copied exactly.
2. At Hostinger, turn **DNSSEC off** for the domain if it is on.
3. At Hostinger (Domains > your domain > DNS / Nameservers), replace the nameservers with the two Cloudflare gives you. Cloudflare emails you when it is active (minutes to a few hours).
4. Pages project > **Custom domains > Set up a custom domain** > `globalpalate.co`, then add `www.globalpalate.co` too. Cloudflare creates the DNS records and the HTTPS certificate.
5. Change `EXPORT_URL` to `https://globalpalate.co/api/export`, then redeploy.
6. In the admin, **Redirects**: add any old WordPress addresses that changed, then Publish.
7. Google Search Console: add the domain, submit `https://globalpalate.co/sitemap.xml`.
8. Keep a backup of the old Hostinger site until you are happy.

## Part 6. Lock it down (10 min, recommended)
- **Cloudflare Zero Trust > Access > Applications > Add > Self-hosted**: protect `globalpalate.co/admin*` and `globalpalate.co/api/admin*`, allow only your email. (Free for up to 50 users.)
- Never share `ADMIN_PASSWORD`. To change it: edit the variable, redeploy.
- Remove the Netlify site or point it at the new domain, so buyers only ever see `globalpalate.co`.

## Day-to-day
- Content changes: `/admin/` > edit > Save draft > Publish.
- Sample COA / spec sheet / testing report PDFs: add them to `data/documents/` in GitHub (web upload works), named like `turmeric-sample-coa.pdf`. Cloudflare rebuilds on every GitHub change.
- Code or copy changes (home page text, About, etc.): edit files in `build/` on GitHub; Cloudflare rebuilds automatically.
