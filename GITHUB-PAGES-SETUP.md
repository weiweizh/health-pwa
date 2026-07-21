# GitHub Pages Setup for Health PWA

Get your app online in 5 minutes with a free GitHub Pages site.

---

## Step 1: Create a GitHub Account (if needed)

1. Go to https://github.com
2. Click **Sign up**
3. Follow the prompts (username, email, password)
4. Verify your email

Skip this if you already have a GitHub account.

---

## Step 2: Create a New Repository

1. Log in to GitHub
2. Click the **+** icon (top right) → **New repository**
3. Fill in:
   - **Repository name:** `health-pwa` (or any name you like)
   - **Description:** "Cycle-synced health tracking app"
   - **Public** (so GitHub Pages works)
4. **Do NOT** check "Add a README file"
5. Click **Create repository**

---

## Step 3: Upload the 4 Files

On the new repo page:

1. Click **uploading an existing file** (or drag-and-drop)
2. Upload these 4 files:
   - `health-pwa.html`
   - `manifest.json`
   - `service-worker.js`
   - `PWA-SETUP.md` (optional, for reference)

3. In the commit message, write: `Initial commit: Add health PWA files`
4. Click **Commit changes**

---

## Step 4: Enable GitHub Pages

1. In your repo, click **Settings** (top right)
2. Left sidebar → **Pages**
3. Under "Build and deployment":
   - **Source:** Select `Deploy from a branch`
   - **Branch:** Select `main`
   - **Folder:** Select `/ (root)`
4. Click **Save**

GitHub will deploy in ~1 minute. You'll see a green checkmark when it's ready.

---

## Step 5: Get Your URL

After deployment (look for the green checkmark):

Your app is at: **`https://YOUR_USERNAME.github.io/health-pwa/health-pwa.html`**

Replace `YOUR_USERNAME` with your actual GitHub username.

**Example:** `https://pumpkin.github.io/health-pwa/health-pwa.html`

---

## Step 6: Install on Your Phone

### iPhone (Safari)
1. Open the URL above in Safari
2. Tap **Share** (box with arrow)
3. Scroll down → **"Add to Home Screen"**
4. Name it "Health Check-in"
5. Tap **Add**

The app icon appears on your home screen. Tap it anytime to open the app.

### Android (Chrome)
1. Open the URL in Chrome
2. Menu (three dots) → **"Install app"**
3. Confirm

---

## Data Privacy

Your health data is stored **locally on your phone** using the browser's localStorage — it never goes to GitHub or any server. Only the app code is hosted on GitHub Pages.

---

## Updates & Syncing

**To update the app on GitHub:**
1. Edit any of the 4 files in your repo (click the file, then the pencil ✏️)
2. Make changes, write a commit message, click **Commit changes**
3. GitHub redeploys automatically (~1 min)
4. Refresh the app on your phone — the update loads

**Your data persists** across updates because it's stored locally on your device.

---

## Access From Any Device

Your app URL works from any phone, tablet, or computer:
- Open the link, tap Add to Home Screen (iOS) or Install App (Android/Chrome)
- Each device has its own local data storage
- No data syncing between devices (by design — your privacy)

---

## Troubleshooting

**Can't find your URL?**
- Go to your repo → Settings → Pages
- Look for "Your site is live at: ..."

**App not installing?**
- Make sure you opened the **full URL** (`...health-pwa.html` at the end)
- Refresh the page first
- Try a different browser

**App won't load data?**
- Check that `manifest.json` and `service-worker.js` are in the same folder as `health-pwa.html`
- Refresh the browser cache (Settings → Safari → Clear History and Website Data)

**Want to make the URL shorter?**
- Rename your repo to `health` → URL becomes `https://username.github.io/health/health-pwa.html`
- Or set up a custom domain (GitHub Pages docs)

---

## What's Deployed

- ✓ `health-pwa.html` — The app
- ✓ `manifest.json` — Install config
- ✓ `service-worker.js` — Offline support
- ✓ `PWA-SETUP.md` — Optional reference

The app automatically caches Chart.js and Google Fonts on first load, so it works offline after that.

---

Done! Your app is now live. Open the URL on your phone and install it. 🎉
