#!/usr/bin/env python3
"""
Build the deployable index.html from daily_health_checkin.html.

Encrypts the embedded health entries with AES-256-GCM (key derived from the
passphrase in .deploy-passphrase via PBKDF2-SHA256) so the public GitHub Pages
site never exposes plaintext health data. The page shows an unlock overlay on
first visit per device; after unlocking, entries are imported into the
browser's localStorage and the passphrase is remembered on that device.

Run after update_health_data.py whenever entries change:
    python3 encrypt_deploy.py
Then commit and push index.html.
"""

import base64
import json
import os
import re
import secrets
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ROOT = Path(__file__).parent
SOURCE = ROOT / "daily_health_checkin.html"
OUTPUT = ROOT / "index.html"
PASSPHRASE_FILE = ROOT / ".deploy-passphrase"
PBKDF2_ITERATIONS = 310000

HEAD_TAGS = """    <meta name="theme-color" content="#263928">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Health Check-in">
    <meta name="description" content="Cycle-synced health tracking with Dr. Stacy Sims insights">
    <link rel="manifest" href="manifest.json">
"""

UNLOCK_SCRIPT = """
<script>
(function () {
    'use strict';
    var E = window.ENCRYPTED_HEALTH_DATA;
    if (!E || !E.data || !window.crypto || !crypto.subtle) return;

    function b64(s) {
        var bin = atob(s), a = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
        return a;
    }

    function deriveKey(pass) {
        return crypto.subtle.importKey('raw', new TextEncoder().encode(pass),
            'PBKDF2', false, ['deriveKey'])
            .then(function (km) {
                return crypto.subtle.deriveKey(
                    { name: 'PBKDF2', salt: b64(E.salt), iterations: E.iter, hash: 'SHA-256' },
                    km, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
            });
    }

    function tryDecrypt(pass) {
        return deriveKey(pass).then(function (key) {
            return crypto.subtle.decrypt({ name: 'AES-GCM', iv: b64(E.iv) }, key, b64(E.data));
        }).then(function (plain) {
            return JSON.parse(new TextDecoder().decode(plain));
        });
    }

    // Add embedded entries this device doesn't have yet. Locally saved
    // entries always win, so a device's own check-ins are never clobbered.
    function mergeAndMaybeReload(entries) {
        var history = [];
        try { history = JSON.parse(localStorage.getItem('healthHistory') || '[]'); } catch (e) {}
        var have = {};
        history.forEach(function (d) { if (d && d.date) have[d.date] = 1; });
        var added = 0;
        entries.forEach(function (d) {
            if (d && d.date && !have[d.date]) { history.push(d); added++; }
        });
        if (added > 0) {
            localStorage.setItem('healthHistory', JSON.stringify(history));
            location.reload();
        }
    }

    function showOverlay() {
        var wrap = document.createElement('div');
        wrap.id = 'unlock-overlay';
        wrap.innerHTML =
            '<style>' +
            '#unlock-overlay{position:fixed;inset:0;z-index:99999;background:rgba(38,57,40,0.96);' +
            'display:flex;align-items:center;justify-content:center;padding:24px;}' +
            '#unlock-overlay .card{background:#faf7f0;border-radius:18px;padding:36px 32px;max-width:360px;' +
            'width:100%;text-align:center;font-family:Georgia,serif;color:#263928;box-shadow:0 20px 60px rgba(0,0,0,0.4);}' +
            '#unlock-overlay h2{margin:0 0 8px;font-size:26px;font-weight:normal;}' +
            '#unlock-overlay p{margin:0 0 20px;font-size:14px;opacity:0.75;line-height:1.5;}' +
            '#unlock-overlay input{width:100%;box-sizing:border-box;padding:12px 44px 12px 14px;font-size:16px;' +
            'border:1.5px solid #c9c2b2;border-radius:10px;background:#fff;color:#263928;outline:none;}' +
            '#unlock-overlay input:focus{border-color:#263928;}' +
            '#unlock-overlay .pass-wrap{position:relative;}' +
            '#unlock-overlay .eye-btn{position:absolute;top:0;right:0;height:100%;width:44px;margin:0;padding:0;' +
            'display:flex;align-items:center;justify-content:center;background:none;border:none;cursor:pointer;' +
            'color:#263928;opacity:0.55;}' +
            '#unlock-overlay .eye-btn:hover{opacity:0.85;}' +
            '#unlock-overlay .eye-btn svg{width:20px;height:20px;display:block;}' +
            '#unlock-overlay button{margin-top:14px;width:100%;padding:12px;font-size:16px;border:none;' +
            'border-radius:10px;background:#263928;color:#faf7f0;cursor:pointer;font-family:inherit;}' +
            '#unlock-overlay .err{color:#a04040;font-size:13px;min-height:18px;margin-top:10px;}' +
            '#unlock-overlay .skip{display:block;margin-top:16px;font-size:13px;color:#263928;' +
            'opacity:0.6;cursor:pointer;text-decoration:underline;background:none;border:none;width:auto;padding:0;margin-left:auto;margin-right:auto;}' +
            '</style>' +
            '<div class="card">' +
            '<h2>Health Check-in</h2>' +
            '<p>Your health data is encrypted.<br>Enter your passphrase to unlock it on this device.</p>' +
            '<div class="pass-wrap">' +
            '<input type="password" id="unlock-pass" placeholder="Passphrase" autocomplete="off">' +
            '<button type="button" class="eye-btn" id="unlock-eye" aria-label="Show passphrase" aria-pressed="false"></button>' +
            '</div>' +
            '<button id="unlock-btn">Unlock</button>' +
            '<div class="err" id="unlock-err"></div>' +
            '<button class="skip" id="unlock-skip">Continue without my data</button>' +
            '</div>';
        document.body.appendChild(wrap);
        var input = document.getElementById('unlock-pass');
        var err = document.getElementById('unlock-err');

        var eye = document.getElementById('unlock-eye');
        var EYE_OPEN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            + 'stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>'
            + '<circle cx="12" cy="12" r="3"/></svg>';
        var EYE_OFF = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            + 'stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20'
            + 'c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8'
            + 'a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
        eye.innerHTML = EYE_OPEN;
        eye.addEventListener('click', function () {
            var show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            eye.innerHTML = show ? EYE_OFF : EYE_OPEN;
            eye.setAttribute('aria-pressed', show ? 'true' : 'false');
            eye.setAttribute('aria-label', show ? 'Hide passphrase' : 'Show passphrase');
            input.focus();
        });

        function attempt() {
            var val = input.value.trim();
            if (!val) return;
            err.textContent = '';
            tryDecrypt(val).then(function (entries) {
                try { localStorage.setItem('healthDataPass', val); } catch (e) {}
                wrap.remove();
                mergeAndMaybeReload(entries);
            }).catch(function () {
                err.textContent = 'That passphrase didn\\u2019t work \\u2014 please try again.';
            });
        }
        document.getElementById('unlock-btn').addEventListener('click', attempt);
        input.addEventListener('keydown', function (e) { if (e.key === 'Enter') attempt(); });
        document.getElementById('unlock-skip').addEventListener('click', function () {
            try { localStorage.setItem('healthDataPass', ''); } catch (e) {}
            wrap.remove();
        });
        input.focus();
    }

    var saved = null;
    try { saved = localStorage.getItem('healthDataPass'); } catch (e) {}
    if (saved === '') return;               // user chose to skip on this device
    if (saved) {
        tryDecrypt(saved).then(mergeAndMaybeReload).catch(showOverlay);
    } else {
        showOverlay();
    }
})();
if ('serviceWorker' in navigator) {
    // When a newly deployed service worker replaces an already-active one, reload
    // once so the user immediately sees the fresh app instead of the stale cached
    // copy. Skipped on first-ever install (no prior controller), which also fires
    // controllerchange but shouldn't trigger a reload.
    var hadController = !!navigator.serviceWorker.controller;
    var swRefreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', function () {
        if (swRefreshing || !hadController) return;
        swRefreshing = true;
        window.location.reload();
    });
    navigator.serviceWorker.register('service-worker.js').catch(function () {});
}
</script>
"""


# Injected sync module: encrypts the dataset with the user's passphrase and pushes
# it to GitHub (data branch) so the Mac can pull it into the Excel file. The GitHub
# token is entered by the user on their device and stored only in localStorage.
SYNC_SCRIPT = """
<script>
(function () {
    'use strict';
    var REPO = 'weiweizh/health-pwa';
    var ENC_PATH = 'health_data.enc';
    var BRANCH = 'data';
    var ITER = 310000;

    function bytesToB64(bytes) {
        var bin = '';
        for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
        return btoa(bin);
    }
    function utf8ToB64(str) { return bytesToB64(new TextEncoder().encode(str)); }
    function getPass() { try { return localStorage.getItem('healthDataPass') || ''; } catch (e) { return ''; } }
    function getToken() { try { return localStorage.getItem('githubSyncToken') || ''; } catch (e) { return ''; } }
    function setToken(t) {
        try { t ? localStorage.setItem('githubSyncToken', t) : localStorage.removeItem('githubSyncToken'); } catch (e) {}
    }
    function getEntries() { try { return JSON.parse(localStorage.getItem('healthHistory') || '[]'); } catch (e) { return []; } }

    function encryptEntries(entries, pass) {
        var salt = crypto.getRandomValues(new Uint8Array(16));
        var iv = crypto.getRandomValues(new Uint8Array(12));
        return crypto.subtle.importKey('raw', new TextEncoder().encode(pass), 'PBKDF2', false, ['deriveKey'])
            .then(function (km) {
                return crypto.subtle.deriveKey(
                    { name: 'PBKDF2', salt: salt, iterations: ITER, hash: 'SHA-256' },
                    km, { name: 'AES-GCM', length: 256 }, false, ['encrypt']);
            })
            .then(function (key) {
                return crypto.subtle.encrypt({ name: 'AES-GCM', iv: iv }, key,
                    new TextEncoder().encode(JSON.stringify(entries)));
            })
            .then(function (ct) {
                return { v: 1, iter: ITER, salt: bytesToB64(salt), iv: bytesToB64(iv),
                         data: bytesToB64(new Uint8Array(ct)) };
            });
    }

    function ghHeaders(token) {
        return { 'Authorization': 'token ' + token, 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28' };
    }

    function push() {
        var token = getToken(), pass = getPass();
        if (!token) return Promise.reject(new Error('Add your GitHub token in Sync settings first.'));
        if (!pass) return Promise.reject(new Error('Unlock with your passphrase first.'));
        return encryptEntries(getEntries(), pass).then(function (blob) {
            var content = utf8ToB64(JSON.stringify(blob));
            var url = 'https://api.github.com/repos/' + REPO + '/contents/' + ENC_PATH;

            function attemptPush(sha, retries) {
                retries = retries || 0;
                var body = { message: 'Update health data ' + new Date().toISOString(),
                             content: content, branch: BRANCH };
                if (sha) body.sha = sha;
                return fetch(url, { method: 'PUT', headers: ghHeaders(token), body: JSON.stringify(body) })
                    .then(function (r) {
                        if (!r.ok) return r.json().then(function (e) {
                            var msg = e.message || ('HTTP ' + r.status);
                            if ((msg.indexOf('sha') > -1 || msg.indexOf('does not match') > -1) && retries < 2) {
                                return new Promise(function(resolve) {
                                    setTimeout(function() {
                                        fetch(url + '?ref=' + BRANCH, { headers: ghHeaders(token) })
                                            .then(function (r2) {
                                                return r2.status === 200 ? r2.json().then(function (j) { return j.sha; }) : null;
                                            })
                                            .then(function (newSha) { resolve(attemptPush(newSha, retries + 1)); });
                                    }, 300);
                                });
                            }
                            throw new Error(msg);
                        });
                        return r.json();
                    });
            }

            return fetch(url + '?ref=' + BRANCH, { headers: ghHeaders(token) })
                .then(function (r) {
                    return r.status === 200 ? r.json().then(function (j) { return j.sha; }) : null;
                })
                .then(function (sha) { return attemptPush(sha); });
        });
    }

    window.HealthSync = { push: push, getToken: getToken, setToken: setToken, encryptEntries: encryptEntries, getEntries: getEntries };

    function toast(msg) {
        var t = document.createElement('div');
        t.textContent = msg;
        t.style.cssText = 'position:fixed;left:50%;bottom:24px;transform:translateX(-50%);z-index:100000;' +
            'background:#263928;color:#faf7f0;padding:10px 18px;border-radius:20px;font-family:Georgia,serif;' +
            'font-size:14px;box-shadow:0 6px 20px rgba(0,0,0,0.3);max-width:80%;text-align:center;';
        document.body.appendChild(t);
        setTimeout(function () { t.style.transition = 'opacity 0.4s'; t.style.opacity = '0';
            setTimeout(function () { t.remove(); }, 400); }, 2600);
    }

    function openSettings() {
        var hasToken = !!getToken();
        var wrap = document.createElement('div');
        wrap.id = 'sync-settings';
        wrap.innerHTML =
            '<style>' +
            '#sync-settings{position:fixed;inset:0;z-index:100001;background:rgba(38,57,40,0.9);' +
            'display:flex;align-items:center;justify-content:center;padding:24px;}' +
            '#sync-settings .card{background:#faf7f0;border-radius:18px;padding:28px 26px;max-width:380px;width:100%;' +
            'font-family:Georgia,serif;color:#263928;box-shadow:0 20px 60px rgba(0,0,0,0.4);}' +
            '#sync-settings h2{margin:0 0 6px;font-size:22px;font-weight:normal;}' +
            '#sync-settings p{margin:0 0 16px;font-size:13px;opacity:0.75;line-height:1.5;}' +
            '#sync-settings input{width:100%;box-sizing:border-box;padding:11px 12px;font-size:15px;' +
            'border:1.5px solid #c9c2b2;border-radius:9px;background:#fff;color:#263928;outline:none;}' +
            '#sync-settings .row{display:flex;gap:8px;margin-top:12px;}' +
            '#sync-settings button{flex:1;padding:11px;font-size:14px;border:none;border-radius:9px;' +
            'font-family:inherit;cursor:pointer;}' +
            '#sync-settings .primary{background:#263928;color:#faf7f0;}' +
            '#sync-settings .ghost{background:#efe9dd;color:#263928;}' +
            '#sync-settings .status{margin-top:12px;font-size:12px;min-height:16px;text-align:center;}' +
            '#sync-settings .close{display:block;margin:16px auto 0;background:none;border:none;font-size:13px;' +
            'color:#263928;opacity:0.6;text-decoration:underline;cursor:pointer;width:auto;}' +
            '</style>' +
            '<div class="card">' +
            '<h2>Sync to GitHub</h2>' +
            '<p>Paste a GitHub token with write access to the health-pwa repo. It is stored only on this ' +
            'device and used to save your (encrypted) data so your Mac can pull it. ' +
            (hasToken ? 'A token is currently saved.' : 'No token saved yet.') + '</p>' +
            '<input type="password" id="sync-token" placeholder="ghp_... or github_pat_..." autocomplete="off">' +
            '<div class="row"><button class="primary" id="sync-save">Save token</button>' +
            '<button class="ghost" id="sync-now">Sync now</button></div>' +
            '<div class="status" id="sync-status"></div>' +
            (hasToken ? '<button class="close" id="sync-clear">Remove saved token</button>' : '') +
            '<button class="close" id="sync-close">Close</button>' +
            '</div>';
        document.body.appendChild(wrap);
        var status = document.getElementById('sync-status');
        document.getElementById('sync-save').addEventListener('click', function () {
            var v = document.getElementById('sync-token').value.trim();
            if (!v) { status.textContent = 'Enter a token first.'; return; }
            setToken(v); status.textContent = 'Token saved on this device.';
        });
        document.getElementById('sync-now').addEventListener('click', function () {
            var v = document.getElementById('sync-token').value.trim();
            if (v) setToken(v);
            status.textContent = 'Syncing...';
            push().then(function () { status.textContent = 'Synced to GitHub.'; })
                   .catch(function (e) { status.textContent = 'Failed: ' + e.message; });
        });
        var clr = document.getElementById('sync-clear');
        if (clr) clr.addEventListener('click', function () { setToken(''); wrap.remove(); toast('Token removed.'); });
        document.getElementById('sync-close').addEventListener('click', function () { wrap.remove(); });
    }

    function injectButton() {
        if (document.getElementById('sync-fab')) return;
        var b = document.createElement('button');
        b.id = 'sync-fab';
        b.title = 'Sync settings';
        b.textContent = 'Sync';
        b.style.cssText = 'position:fixed;right:14px;bottom:14px;z-index:99998;background:#263928;color:#faf7f0;' +
            'border:none;border-radius:20px;padding:9px 16px;font-family:Georgia,serif;font-size:13px;' +
            'cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,0.25);opacity:0.85;';
        b.addEventListener('click', openSettings);
        document.body.appendChild(b);
    }

    function wire() {
        injectButton();
        var form = document.getElementById('healthForm');
        if (form) {
            form.addEventListener('submit', function () {
                if (!getToken()) return;
                setTimeout(function () {
                    push().then(function () { toast('Synced to GitHub'); })
                          .catch(function (e) { toast('Sync failed: ' + e.message); });
                }, 350);
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', wire);
    } else {
        wire();
    }
})();
</script>
"""


def main():
    passphrase = PASSPHRASE_FILE.read_text().strip()
    html = SOURCE.read_text()

    match = re.search(r'const embeddedHealthData = \[[\s\S]*?\];', html)
    if not match:
        raise SystemExit("Could not find embeddedHealthData in source HTML")
    array_js = match.group(0)
    json_text = array_js[len('const embeddedHealthData = '):-1]
    entries = json.loads(json_text)
    print(f"Extracted {len(entries)} health entries")

    salt = secrets.token_bytes(16)
    iv = secrets.token_bytes(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                     iterations=PBKDF2_ITERATIONS)
    key = kdf.derive(passphrase.encode())
    ciphertext = AESGCM(key).encrypt(iv, json.dumps(entries).encode(), None)

    blob = json.dumps({
        "v": 1,
        "iter": PBKDF2_ITERATIONS,
        "salt": base64.b64encode(salt).decode(),
        "iv": base64.b64encode(iv).decode(),
        "data": base64.b64encode(ciphertext).decode(),
    })

    replacement = ("var embeddedHealthData = [];\n"
                   "    window.ENCRYPTED_HEALTH_DATA = " + blob + ";")
    html = html[:match.start()] + replacement + html[match.end():]

    html = html.replace("<title>Daily Health Check-in</title>",
                        "<title>Daily Health Check-in</title>\n" + HEAD_TAGS, 1)

    idx = html.rfind("</body>")
    if idx == -1:
        raise SystemExit("No </body> tag found")
    html = html[:idx] + UNLOCK_SCRIPT + SYNC_SCRIPT + html[idx:]

    OUTPUT.write_text(html)
    print(f"Wrote {OUTPUT.name} ({OUTPUT.stat().st_size / 1024:.0f} KB), "
          f"entries encrypted with AES-256-GCM")


if __name__ == "__main__":
    main()
