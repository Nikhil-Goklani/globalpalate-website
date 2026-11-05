# Host the site AND the admin on Hostinger (step by step)

How it works
- The public site is plain files in `public_html`. GitHub builds them: whenever you press **Publish** in the admin (or commit to GitHub), a GitHub "Action" builds the site and puts the finished files on a branch called `hostinger`; Hostinger copies that branch into `public_html`.
- The admin panel (`globalpalate.co/admin/`) and the forms run as small PHP files on Hostinger. Your edits, version history and uploaded photos are saved in a folder called `gp-data` that sits **next to** `public_html` (not inside it), so deployments never touch it.
- Publish -> admin saves -> calls GitHub to start the build -> the build downloads your published data from `/api/export` -> files go to Hostinger. About 3-4 minutes end to end.

Order matters. Do the parts in order.

---
## Part 1. Add the files to GitHub (10 min)
1. Unzip `global-palate-hostinger-update.zip` (right-click > Extract All). **If you added an earlier Hostinger zip, this one replaces it.**
2. Copy into your cloned folder (the one GitHub Desktop uses), replacing files when asked: the **`hostinger`** folder, **`build/hostinger.py`** (into your `build` folder), `HOSTINGER-SETUP.md`, `.gitignore`.
3. GitHub Desktop: summary `Add PHP admin for Hostinger` > **Commit to main** > **Push origin**.
4. The build file lives in a hidden-dot folder, so edit it on GitHub's website:
   - Repo > open `.github/workflows/hostinger.yml` (create it with **Add file > Create new file** if you haven't yet; type the name `.github/workflows/hostinger.yml`).
   - Replace everything with the contents of `hostinger-workflow.yml` from the zip. **Commit changes**.
5. Repo > **Settings > Actions > General > Workflow permissions** > **Read and write permissions** > Save.
6. Repo > **Actions** tab: the "Build for Hostinger" run should turn green (1-2 min). The repo now has a `hostinger` branch containing `index.html`, `.htaccess`, `admin/` and `api/` folders.

## Part 2. Connect Hostinger to GitHub (15 min)
hPanel > **Websites** > `globalpalate.co` > **Advanced > Git**. (If you don't see Git, your plan may not include it: tell me the plan name.)
1. In **PHP configuration** (hPanel > Advanced) choose **PHP 8.1 or newer**. Make sure the extensions `curl` and `mbstring` are ticked (they normally are).
2. **File Manager > public_html**: delete placeholder files such as `default.php`. Git deploys into an empty folder. Back up any old site first.
3. Git screen: **Repository address** `git@github.com:Nikhil-Goklani/globalpalate-website.git`, **Branch** `hostinger`, **Install path** empty > **Create**.
4. Hostinger shows an **SSH key**. In GitHub: repo > **Settings > Deploy keys > Add deploy key**, paste, title `Hostinger`, leave write access off.
5. Back in Hostinger: **Deploy**. Open `globalpalate.co` (or your temporary Hostinger address): the public site should load.
6. **Auto-deploy:** copy Hostinger's **Webhook URL**. GitHub: repo > **Settings > Webhooks > Add webhook** > paste it as Payload URL, content type `application/json`, "Just the push event" > Add.
7. hPanel > **Security > SSL**: make sure the free SSL is active (the site forces https).

## Part 3. Create the settings file (10 min)
This file holds all secrets and lives **outside** public_html, so it is never on GitHub or reachable from the web.
1. hPanel > **File Manager**. Go one level **up** from `public_html` (the folder that contains `public_html`).
2. Create a new file `gp-config.php`. Paste in the contents of `hostinger/gp-config.sample.php` from the zip and fill in:
   - `ADMIN_PASSWORD`: your admin login, 16+ characters. **Write it down.**
   - `BUILD_TOKEN`: a random string of 32+ characters (use a password generator). **Copy it; you need it again in Part 4.**
   - `GITHUB_TOKEN`: from Part 4 (leave empty for now).
   - Zoho and email values for the forms (see below). `NOTIFY_FROM` must be an address at your own domain; create the mailbox in hPanel > Emails.
3. Save.

Zoho: in Zoho CRM create a Web-to-Lead form and copy its three hidden fields (`xnQsjsdp`, `xmIwtLD`, `actionType`) into `ZOHO_XNQSJSDP`, `ZOHO_XMIWTLD`, `ZOHO_ACTIONTYPE`.

## Part 4. Let the Publish button start the build (10 min)
**A. GitHub token (lets the admin start the build):**
1. GitHub > your profile picture > **Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token**.
2. Name `globalpalate-admin-publish`. Expiration: 1 year (put a reminder in your calendar; when it expires, Publish will say GitHub refused the token and you make a new one).
3. **Repository access: Only select repositories** > `globalpalate-website`.
4. **Permissions > Repository permissions > Actions: Read and write.** Nothing else.
5. Generate, copy the token (starts with `github_pat_`), paste it as `GITHUB_TOKEN` in `gp-config.php`.

**B. GitHub secrets (lets the build read your published data):**
Repo > **Settings > Secrets and variables > Actions > New repository secret**. Add two:
- `EXPORT_URL` = `https://globalpalate.co/api/export` (use your temporary Hostinger address until the domain points here)
- `BUILD_TOKEN` = exactly the same value you put in `gp-config.php`

## Part 5. Test everything (10 min)
1. Open `https://globalpalate.co/admin/` and sign in. You should see 6 products. (First sign-in creates the `gp-data` folder next to `public_html`.)
2. Change a product's **SEO title**, **Save draft**, **Publish**. The toast should say "Build started".
3. GitHub > **Actions**: a new run appears. In its log, the "Build site" step should print `Using published admin data from ...`.
4. A few minutes later the live product page shows the new title. Change it back and publish again.
5. Send a test quote on the live site: it should appear in Zoho and/or your inbox.

## Day-to-day
- Content: `/admin/` > edit > Save draft > Publish. Live in about 3-4 minutes.
- PDFs (COA, spec sheet, testing report): add to `data/documents/` on GitHub named like `turmeric-sample-coa.pdf`.
- Page wording (home, about): edit `build/` files on GitHub, or ask me.

## Safety and backups
- **Backup the `gp-data` folder** (next to `public_html`) now and then: File Manager > select it > Compress > Download. It holds your drafts, 30 saved versions and uploaded photos. Hostinger's own backups usually include it too.
- Extra lock for the admin (optional): hPanel > **Advanced > Password protect directories** > `public_html/admin`. You then enter a second password before the admin page even loads.
- Never share `gp-config.php`. To change the admin password, edit it there.
- Once the site works, delete the Cloudflare Pages project (it also tries to build the `hostinger` branch and will show red).

## If something breaks
- **Admin says "ADMIN_PASSWORD is not set":** `gp-config.php` is in the wrong folder (it must sit next to `public_html`, not inside it) or has a typo. Hostinger File Manager shows a PHP error if the file has a syntax mistake.
- **"Cannot create the data folder":** add `'DATA_DIR' => '/home/<your-user>/gp-data'` to `gp-config.php` (the path hPanel shows for your account).
- **Publish says GitHub refused the token (401/403/404):** the token is expired, belongs to another repo, or lacks "Actions: Read and write".
- **Publish says "Build started" but the site doesn't change:** GitHub > Actions: if the run is red, open it and read the error; if green, check Hostinger > Git (Deploy) and the webhook under GitHub Settings > Webhooks.
- **Build log says "could not fetch published data":** `EXPORT_URL` or `BUILD_TOKEN` secret doesn't match `gp-config.php`, or the domain doesn't reach Hostinger yet. (The site still builds from the starting data.)
- **500 error on the whole site:** File Manager > rename `.htaccess` to `.htaccess-off`; if the site loads, send me the file.
