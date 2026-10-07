# IA 642 Lab 6.2 — Mobile MASVS, Frida & Root Bypass

**Course:** IA 642 Defensive Security (Eastern Michigan University)  
**Authors:** Unais Ali (E02805019), Hafiz Usama (E02574092)

Authorized training target: **OWASP MAS UnCrackable-Level1** (no real user data).

## Contents

| Path | Description |
|------|-------------|
| `UnCrackable-Level1.apk` | Crackme APK (SHA-256 verified in lab) |
| `decomp/` | jadx decompiled Java sources |
| `evidence/` | Screenshots #1–#3, Frida console, recovered secret, class extracts |
| `bypass_root.js` | Frida hooks (root bypass + AES secret tap) |
| `build_lab62_latex.py` | Local LaTeX report builder (PDF not published here) |

## Quick notes

- Emulator: Google APIs x86_64 AVD (so `adb root` works), not Google Play.
- Frida client/server used for the capture: **16.5.9**.
- Recovered secret (from live Frida run): see `evidence/recovered_secret.txt`.

## Security note

Lab evidence and demo APK only. **No graded report PDF and no AWS/credentials are committed.**
