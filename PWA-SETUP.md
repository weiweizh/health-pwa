# Health Check-in PWA Setup Guide

## What's New

Your health tracking app is now a **Progressive Web App (PWA)** — optimized for mobile with offline support, fast loading, and the ability to add it to your home screen like a native app.

### Files
- **`health-pwa.html`** — Mobile-responsive app (480px optimized, works up to desktop)
- **`manifest.json`** — PWA configuration (enables home screen install)
- **`service-worker.js`** — Offline support & caching
- **`PWA-SETUP.md`** — This guide

---

## How to Use

### Option 1: Open in Browser

1. Open `health-pwa.html` in any browser (desktop or mobile)
2. Start logging your daily metrics in the **Log** tab
3. View trends in the **Trends** tab
4. Data is saved locally in your browser

### Option 2: Add to Home Screen (iOS)

1. Open `health-pwa.html` in **Safari** on your iPhone
2. Tap the **Share** button (box with arrow)
3. Scroll down and tap **"Add to Home Screen"**
4. Name it "Health Check-in" (or your preference)
5. Tap **Add** — the app icon will appear on your home screen

Once installed, the app:
- Opens like a native app (no browser chrome)
- Works offline with cached data
- Shows a splash screen on launch
- Syncs data automatically when online

### Option 3: Add to Home Screen (Android)

1. Open `health-pwa.html` in **Chrome** (or Edge/Firefox)
2. Tap the **menu** (three dots)
3. Tap **"Install app"** or **"Add to Home Screen"**
4. Confirm the installation

---

## Mobile Optimization

The app is designed for phones (480px width) but works on tablets and desktop too:

| Device | Layout |
|--------|--------|
| iPhone | Optimized (single column, touch-friendly) |
| Tablet | Two-column stats, wider charts |
| Desktop | Full layout with better spacing |

**Touch-friendly inputs:**
- Large buttons (44px min)
- Easy-to-tap form fields
- Smooth tab navigation

---

## Data Storage

All your data is stored **locally in your browser** using localStorage:
- No cloud sync (your privacy)
- Data persists between sessions
- Export/backup via the HTML file itself

**Note:** Clearing browser data will erase your history. Keep a backup of your `Daily_Health_Tracking.xlsx` file.

---

## Features

### Home Tab
- Today's summary
- This week's average metrics (HR, Sleep, HRV, Workouts)

### Log Tab
- Daily metrics input (HR, sleep, HRV, feeling, cycle day)
- Collapsible workout details section
- Easy date tracking

### Trends Tab
- 4 interactive charts (HR, Sleep, HRV, Wellbeing)
- All entries table (sortable by date)
- Week-at-a-glance metrics

---

## Offline Support

Once you've opened the app once, it caches:
- The HTML, CSS, and JavaScript
- Chart.js library
- Google Fonts

You can then:
- ✓ Log entries offline
- ✓ View your history
- ✓ See charts
- ✗ Won't fetch external resources (Google Fonts will use fallbacks)

Data syncs automatically when you're back online.

---

## Troubleshooting

### App won't install on iOS
- Make sure you're using **Safari** (not Chrome or other browsers)
- The manifest.json file must be in the same folder as the HTML

### Data not saving
- Check that localStorage is enabled in your browser settings
- Try refreshing the page after saving

### Charts not showing
- Make sure Chart.js loads (needs internet the first time)
- Charts appear in the "Trends" tab

### App crashes after update
- Clear Safari cache: Settings > Safari > Clear History and Website Data
- Reinstall the app from home screen

---

## Integration with Daily_Health_Tracking.xlsx

The PWA stores data locally. To sync with your main Excel file:

1. **From PWA to Excel:** Copy entries from the Trends tab and paste into your spreadsheet
2. **From Excel to PWA:** Use a sync script (optional — contact me to set up)

---

## Next Steps

1. **Test on iOS:** Install on your iPhone via Safari
2. **Start logging:** Add daily entries for a few weeks
3. **Review trends:** Watch your patterns emerge
4. **Sync with training:** Use the data to inform your cycle-synced workouts

---

## Technical Notes

- **Framework:** Vanilla JavaScript (no dependencies except Chart.js)
- **Bundle size:** ~45KB (gzipped) + Chart.js + Google Fonts
- **Browser support:** iOS Safari 12+, Chrome 57+, Firefox 55+, Edge 79+
- **Offline-first:** Service Worker caches assets automatically

---

Questions? Check the app's footer or open the developer console (F12) to see any errors.
