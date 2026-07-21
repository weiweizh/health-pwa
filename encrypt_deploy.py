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
    navigator.serviceWorker.register('service-worker.js').catch(function () {});
}
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
    html = html[:idx] + UNLOCK_SCRIPT + html[idx:]

    OUTPUT.write_text(html)
    print(f"Wrote {OUTPUT.name} ({OUTPUT.stat().st_size / 1024:.0f} KB), "
          f"entries encrypted with AES-256-GCM")


if __name__ == "__main__":
    main()
