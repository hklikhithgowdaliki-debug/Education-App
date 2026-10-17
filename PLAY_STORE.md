# Publishing KSEAB Papers on Google Play

## 1. Build the release bundle
```bash
cd app
flutter build appbundle --release
# output: app/build/app/outputs/bundle/release/app-release.aab
```
Release signing reads `app/android/key.properties` (never commit it or the `.jks` file):
```
storePassword=...
keyPassword=...
keyAlias=upload
storeFile=/absolute/path/to/upload-keystore.jks
```
Create a new upload key if you need one:
`keytool -genkeypair -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload`
Keep the keystore and passwords safe: every future update must be signed with the same upload key
(Play App Signing lets Google reset a lost upload key, but it takes days).

Before each new release, bump `version:` in `app/pubspec.yaml` (e.g. `1.0.1+2`).

## 2. Play Console steps
1. Create a developer account at https://play.google.com/console (one-time US$25).
2. **Create app** → name `KSEAB Papers`, default language English (India), App, Free.
3. **Store listing** – use the text below, the icon `store/icon-512.png` and the feature graphic
   `store/feature-graphic.png`; add 2–8 phone screenshots from `store/screenshots/`.
4. **App content**
   - Privacy policy URL: `https://github.com/hklikhithgowdaliki-debug/Education-App/blob/main/PRIVACY_POLICY.md`
   - Ads: No ads. App access: all functionality available without login.
   - Content rating: fill the questionnaire (Education reference app, no user content) → Everyone.
   - Target audience: 13–15, 16–17, 18+ (students). Data safety: **No data collected or shared**.
   - Government apps: **No** (the app is not affiliated with any government body).
5. **Testing → Internal testing** → upload `app-release.aab`, add your own email as tester, check it
   on a phone. New personal developer accounts must run a **closed test with 12 testers for 14 days**
   before production access is granted.
6. **Production** → create release → upload the same `.aab` → roll out.

## 3. Store listing text
**App name:** KSEAB Papers – SSLC, PUC & VTU

**Short description (≤80 chars):**
Karnataka SSLC, 2nd PUC & VTU engineering previous year question papers

**Full description:**
KSEAB Papers puts thousands of previous-year and model question papers for Karnataka students in one
simple, free app.

• Karnataka SSLC (10th): Mathematics, Science, Social Science, all first/second/third languages and
  vocational subjects – main and supplementary exams, every medium and set, 2012 onwards.
• Karnataka 2nd PUC (12th): Science, Commerce, Arts, languages and vocational subjects – Exam 1, 2 and
  3 papers for 2024 and 2025.
• VTU Engineering: model question papers for every branch – CSE, ISE, AI&ML, ECE, EEE, Mechanical,
  Civil, Aeronautical, Biotechnology, Chemical and more – 2014 to 2025 schemes.

Features
• Browse by board → stream/subject → year → exam
• Fast search by subject name, subject code or year
• Built-in PDF viewer with pinch-to-zoom
• Papers you open are saved for offline study
• Paper list updates automatically – no app update needed
• No login, no ads, no tracking

Disclaimer: This app is not affiliated with KSEAB, the Department of Pre-University Education or
VTU. Question papers are published by the respective boards and are linked from their publicly
available sources.

**Category:** Education  **Tags:** Education, Exam preparation
