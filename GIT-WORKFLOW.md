# Git Workflow for Health PWA Updates

Once set up, you can make changes and I can push them to GitHub automatically.

---

## One-Time Setup

### Step 1: Create a Personal Access Token on GitHub

1. Go to GitHub → Settings (top right) → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token (classic)**
3. Name it: `health-pwa-deploy`
4. Select scopes: Check `repo` (all permissions)
5. Click **Generate token**
6. **Copy the token** (you won't see it again!)

### Step 2: Initialize Git Locally

In your terminal, run these commands:

```bash
cd "/Users/weiwei/Documents/Claude/Projects/Personal trainer"

# Initialize git
git init

# Add your GitHub username and email
git config user.name "Your Name"
git config user.email "your-email@example.com"

# Add all files
git add .

# First commit
git commit -m "Initial commit: Health PWA app"

# Add your GitHub repo as remote
# Replace YOUR_USERNAME with your actual GitHub username
git remote add origin https://github.com/YOUR_USERNAME/health-pwa.git

# Push to GitHub
git branch -M main
git push -u origin main
```

When prompted for password, paste your personal access token (not your GitHub password).

### Step 3: Verify on GitHub

Go to `https://github.com/YOUR_USERNAME/health-pwa` — you should see all the files there.

---

## After Initial Setup: The Workflow

### When I make changes to the app:

1. I edit `index.html` (the main app)
2. I run these bash commands:

```bash
cd "/Users/weiwei/Documents/Claude/Projects/Personal trainer"
git add index.html
git commit -m "Update: [describe change]"
git push origin main
```

The changes go live on GitHub Pages in ~1 minute.

### When you want to make changes:

#### Option A: I make the edits (recommended)
- Tell me what to change
- I edit the file
- I push to GitHub using the commands above
- Changes live on your site

#### Option B: You edit locally
- Edit `index.html` in your editor
- In terminal:
```bash
cd "/Users/weiwei/Documents/Claude/Projects/Personal trainer"
git add index.html
git commit -m "Update: describe your change"
git push origin main
```

#### Option C: Edit on GitHub directly (slowest)
- Go to your GitHub repo
- Click on `index.html`
- Click the pencil (✏️) to edit
- Make changes
- Click "Commit changes"

---

## Files to Never Edit (git will track these automatically)

- `manifest.json` — PWA config
- `service-worker.js` — Offline support
- `index.html` — The main app (I'll handle most edits)

---

## Helpful Git Commands

**Check status:**
```bash
cd "/Users/weiwei/Documents/Claude/Projects/Personal trainer"
git status
```

**See recent changes:**
```bash
git log --oneline -5
```

**Undo last commit (before pushing):**
```bash
git reset --soft HEAD~1
```

**Pull latest from GitHub:**
```bash
git pull origin main
```

---

## If Something Goes Wrong

**"error: The following untracked working tree files would be overwritten"**
- Run: `git add .` then `git commit -m "Save work"`

**"fatal: 'origin' does not appear to be a remote"**
- Run: `git remote add origin https://github.com/YOUR_USERNAME/health-pwa.git`

**Token keeps being rejected:**
- Double-check you copied the full token
- Make sure you didn't accidentally include spaces
- Regenerate a new token if needed

---

## Quick Reference: Update Flow

```
1. I edit index.html
2. I run: git add index.html && git commit -m "Update: X" && git push
3. Changes live on GitHub in ~1 min
4. Your phone auto-reloads the updated app
```

Done! Now I can manage updates to your PWA. 🚀
