# Puppeteer Testing Guide for Developers

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Available Tests](#available-tests)
4. [Running Tests](#running-tests)
5. [Test Details](#test-details)
6. [Environment Variables](#environment-variables)
7. [Understanding Test Results](#understanding-test-results)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

Puppeteer tests are end-to-end (E2E) tests that automate browser interactions to verify your application works correctly. These tests:

- **Simulate real user behavior** - Click buttons, fill forms, navigate pages
- **Test against real backend** - All tests use your actual API (no mocking)
- **Capture visual evidence** - Screenshots saved for verification
- **Catch regressions** - Ensure features still work after code changes

### Why Use These Tests?

- **Before deploying** - Verify critical user flows work
- **After refactoring** - Ensure you didn't break anything
- **During development** - Quick feedback on your changes
- **Documentation** - Tests serve as examples of how features work

---

## Prerequisites

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Your Development Server
In one terminal:
```bash
npm run dev
```

The server should be running on `http://localhost:3000` (or your configured port).

### 3. Set Up Test Credentials
All tests require authentication. Set your credentials:

**PowerShell:**
```powershell
$env:LOGIN_EMAIL = "your-email@example.com"
$env:LOGIN_PASSWORD = "your-password"
```

**Bash/Unix:**
```bash
export LOGIN_EMAIL="your-email@example.com"
export LOGIN_PASSWORD="your-password"
```

---

## Available Tests

Your project has **4 Puppeteer tests**, each covering a different user interaction:

| Test | Command | Purpose |
|------|---------|---------|
| **Login Test** | `test:puppeteer:login` | Tests user authentication flow |
| **Analysis Form Test** | `test:puppeteer:analysis` | Tests claim analysis form submission |
| **Saved Claims Navigation** | `test:puppeteer:saved-claims-nav` | Tests header navigation to saved claims |
| **Saved Claims Details** | `test:puppeteer:saved-claims` | Tests clicking a claim to view details |

Each test has two variants:
- **Headless** (default) - Browser runs invisibly, faster
- **Watch** (`:watch`) - Browser visible, better for debugging

---

## Running Tests

### Quick Start

**Run all tests in headless mode:**
```bash
npm run test:puppeteer:login
npm run test:puppeteer:analysis
npm run test:puppeteer:saved-claims-nav
npm run test:puppeteer:saved-claims
```

**Run with visible browser (recommended for first time):**
```bash
npm run test:puppeteer:login:watch
npm run test:puppeteer:analysis:watch
npm run test:puppeteer:saved-claims-nav:watch
npm run test:puppeteer:saved-claims:watch
```

### Test Execution Flow

1. **Test starts** → Launches Chrome browser
2. **Logs in** (if needed) → Uses credentials from env vars
3. **Performs actions** → Clicks, types, navigates
4. **Waits for responses** → Monitors network requests
5. **Takes screenshot** → Saves visual proof
6. **Closes browser** → Cleanup

---

## Test Details

### 1. Login Test (`test-login-page.js`)

**Purpose:** Verifies the authentication flow works end-to-end.

**What it tests:**
- Login page loads correctly
- Form fields are accessible
- User can enter email and password
- Login request is sent to backend
- Successful login redirects to dashboard
- Failed login shows appropriate error

**Test Flow:**
```
1. Navigate to /login
2. Wait for login form to load
3. Fill email and password fields
4. Click submit button
5. Wait for /auth/login API request
6. Wait for navigation to /dashboard
7. Verify we're on dashboard page
8. Take screenshot (login-page-smoke.png)
```

**When to use:**
- After changing login logic
- After modifying authentication flow
- Before deploying authentication changes
- To verify backend authentication works

**Screenshot:** `login-page-smoke.png`

---

### 2. Analysis Form Test (`test-analysis-page.js`)

**Purpose:** Verifies the claim analysis form can be filled and submitted.

**What it tests:**
- Dashboard loads after login
- Analysis form is visible and accessible
- All form fields can be filled (Claim ID, notes, comments)
- File upload works (medical records)
- "Start Analysis" button is clickable
- Form submission triggers `/api/start_analysis` request
- UI updates after submission

**Test Flow:**
```
1. Login to application
2. Navigate to /dashboard
3. Wait for Analysis form to load
4. Fill Claim ID field
5. Fill Claim Notes textarea
6. Fill Biller Comments textarea
7. Upload medical record file (from fixtures/)
8. Find and click "Start Analysis" button
9. Wait for /api/start_analysis POST request
10. Take screenshot (analysis-form-submission.png)
```

**When to use:**
- After modifying Analysis form component
- After changing form validation
- After updating file upload logic
- To verify form submission works
- Before deploying form changes

**Screenshot:** `analysis-form-submission.png`

**Note:** Uses test file from `scripts/fixtures/medical-record.txt` (auto-created if missing)

---

### 3. Saved Claims Navigation Test (`test-saved-claims-navigation.js`)

**Purpose:** Verifies navigation from dashboard to saved claims page via header button.

**What it tests:**
- Header "Saved Claims" button is visible
- Button is clickable
- Clicking button navigates to `/saved-claims`
- Navigation completes successfully
- Saved claims page loads

**Test Flow:**
```
1. Login to application
2. Navigate to /dashboard
3. Wait for dashboard to load
4. Find "Saved Claims" link in header
5. Click the link
6. Wait for navigation to /saved-claims
7. Verify URL contains /saved-claims
8. Take screenshot (saved-claims-navigation.png)
```

**When to use:**
- After modifying header navigation
- After changing routing logic
- After updating AppHeader component
- To verify navigation works correctly

**Screenshot:** `saved-claims-navigation.png`

---

### 4. Saved Claims Details Test (`test-saved-claims-page.js`)

**Purpose:** Verifies clicking on a saved claim loads its details correctly.

**What it tests:**
- Saved claims page loads
- Claims list is displayed (or empty state)
- Claim cards are clickable
- Clicking a claim loads details
- Claim details section appears
- Details contain expected information

**Test Flow:**
```
1. Login to application
2. Navigate to /saved-claims
3. Wait for saved claims list to load
4. Find first available claim card
5. Click on the claim card
6. Wait for claim details to load
7. Verify details section is visible
8. Take screenshot (saved-claims-details.png)
```

**When to use:**
- After modifying saved claims page
- After changing claim detail loading logic
- After updating claim card components
- To verify claim details API integration
- When claims list is empty, tests empty state

**Screenshot:** `saved-claims-details.png`

**Note:** If no saved claims exist, test will screenshot the empty state (this is expected behavior)

---

## Environment Variables

All tests support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:3000` | URL of your Next.js application |
| `HEADLESS` | `true` | Set to `false` to see browser (use `:watch` commands instead) |
| `LOGIN_EMAIL` | `testuser@example.com` | Email for authentication |
| `LOGIN_PASSWORD` | `SuperSecret123!` | Password for authentication |

### Setting Environment Variables

**PowerShell (Windows):**
```powershell
$env:BASE_URL = "http://localhost:3001"
$env:LOGIN_EMAIL = "user@example.com"
$env:LOGIN_PASSWORD = "password123"
npm run test:puppeteer:login:watch
```

**Bash/Unix:**
```bash
BASE_URL=http://localhost:3001 \
LOGIN_EMAIL=user@example.com \
LOGIN_PASSWORD=password123 \
npm run test:puppeteer:login:watch
```

**Or use the `:watch` commands** (they set `HEADLESS=false` automatically):
```bash
npm run test:puppeteer:login:watch
```

---

## Understanding Test Results

### Success Output

When a test passes, you'll see:
```
Navigating to http://localhost:3000/login ...
Filling login form...
Setting up navigation listener...
Setting up login request listener...
Clicking submit button...
Detected login request: POST http://localhost:3000/auth/login
Login request detected or timeout reached
Navigation detected or timeout reached
Waiting for page to settle...
Current URL: http://localhost:3000/dashboard
Successfully redirected to dashboard
Login smoke test completed. Screenshot: login-page-smoke.png
```

### Failure Output

When a test fails, you'll see:
```
ERROR: Puppeteer Login test failed: TimeoutError: Waiting for selector...
Error screenshot saved: login-test-error.png
Current page URL: http://localhost:3000/login
```

### Screenshots

Each test creates screenshots:

| Test | Success Screenshot | Error Screenshot |
|------|-------------------|------------------|
| Login | `login-page-smoke.png` | `login-test-error.png` |
| Analysis | `analysis-form-submission.png` | `analysis-test-error.png` |
| Saved Claims Nav | `saved-claims-navigation.png` | `saved-claims-nav-test-error.png` |
| Saved Claims Details | `saved-claims-details.png` | `saved-claims-details-test-error.png` |

**Screenshots are saved in the `zoe-frontend` directory** (same level as `package.json`).

---

## Troubleshooting

### Test Fails with "Cannot find module 'puppeteer'"

**Solution:**
```bash
npm install
```

### Test Times Out

**Possible causes:**
1. **Dev server not running** - Make sure `npm run dev` is running
2. **Wrong BASE_URL** - Check your server port matches BASE_URL
3. **Slow network** - Increase timeout in test file (not recommended)
4. **Page not loading** - Check browser console for errors

**Solution:**
- Verify dev server is running: `curl http://localhost:3000`
- Check BASE_URL matches your server port
- Run with `:watch` to see what's happening

### "Login failed" Error

**Possible causes:**
1. **Wrong credentials** - Check LOGIN_EMAIL and LOGIN_PASSWORD
2. **Backend not running** - Authentication requires backend API
3. **Account locked/inactive** - Check user status in database

**Solution:**
```powershell
# Verify credentials are set
$env:LOGIN_EMAIL
$env:LOGIN_PASSWORD

# Try logging in manually in browser first
```

### Test Can't Find Elements

**Possible causes:**
1. **Page structure changed** - Selectors might be outdated
2. **Page not fully loaded** - React might not have hydrated
3. **Different UI state** - Element might be conditionally rendered

**Solution:**
- Run with `:watch` to see the page
- Check error screenshot to see what's on the page
- Verify selectors match current HTML structure

### Browser Won't Launch

**Solution:**
```bash
# Reinstall Puppeteer's Chromium
npx puppeteer browsers install chrome
```

### Port Already in Use

**Solution:**
```powershell
# Use different port
$env:BASE_URL = "http://localhost:3001"
npm run test:puppeteer:login:watch
```

---

## Best Practices

### 1. Run Tests Before Committing

```bash
# Quick smoke test before commit
npm run test:puppeteer:login
npm run test:puppeteer:analysis
```

### 2. Use Watch Mode for Debugging

When a test fails, always run with `:watch` to see what's happening:
```bash
npm run test:puppeteer:login:watch
```

### 3. Check Screenshots

After test runs, check the screenshots:
- **Success screenshots** - Verify UI looks correct
- **Error screenshots** - See what went wrong

### 4. Keep Credentials Secure

**Never commit credentials to git:**
```bash
# Add to .gitignore (if not already)
echo "*.env" >> .gitignore
echo ".env.local" >> .gitignore
```

**Use environment variables:**
```powershell
# Set in your shell session (not in code)
$env:LOGIN_EMAIL = "your-email@example.com"
```

### 5. Run Tests in Order

Some tests depend on others:
1. **Login test** - Should always work first
2. **Analysis test** - Requires login
3. **Navigation test** - Requires login
4. **Details test** - Requires login + saved claims data

### 6. Test After Backend Changes

When backend API changes:
- Run all tests to ensure frontend still works
- Check for new error messages
- Verify API request formats

### 7. Update Tests When UI Changes

If you change:
- Button text → Update test selectors
- Form field names → Update test selectors
- Page routes → Update test URLs
- Component structure → Update test logic

---

## Test File Locations

All test files are in `zoe-frontend/scripts/`:

```
scripts/
├── test-login-page.js              # Login authentication test
├── test-analysis-page.js           # Analysis form submission test
├── test-saved-claims-navigation.js # Header navigation test
├── test-saved-claims-page.js       # Claim details loading test
└── fixtures/
    └── medical-record.txt          # Test file for uploads
```

---

## Quick Reference

### Run All Tests
```bash
npm run test:puppeteer:login:watch
npm run test:puppeteer:analysis:watch
npm run test:puppeteer:saved-claims-nav:watch
npm run test:puppeteer:saved-claims:watch
```

### Check Test Results
```bash
# List screenshots
ls *.png

# View latest screenshot (PowerShell)
Start-Process login-page-smoke.png
```

### Common Commands
```bash
# Run test with custom server
BASE_URL=http://localhost:3001 npm run test:puppeteer:login:watch

# Run test with custom credentials
LOGIN_EMAIL=test@example.com LOGIN_PASSWORD=pass123 npm run test:puppeteer:login:watch

# Run headless (faster, no browser window)
npm run test:puppeteer:login
```

---

## What Each Test Validates

### Login Test Validates:
- ✅ Login page renders
- ✅ Form submission works
- ✅ Authentication API integration
- ✅ Redirect after login
- ✅ Session management

### Analysis Form Test Validates:
- ✅ Form fields are accessible
- ✅ File upload functionality
- ✅ Form validation
- ✅ API request submission
- ✅ Button interactions

### Saved Claims Navigation Test Validates:
- ✅ Header component renders
- ✅ Navigation links work
- ✅ Routing configuration
- ✅ Page transitions

### Saved Claims Details Test Validates:
- ✅ Claims list loading
- ✅ Claim card interactions
- ✅ Details API integration
- ✅ UI state management
- ✅ Empty state handling

---

## Integration with CI/CD

These tests can be integrated into your CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run Puppeteer Tests
  run: |
    npm run dev &
    sleep 10
    npm run test:puppeteer:login
    npm run test:puppeteer:analysis
```

**Note:** CI environments typically run headless by default.

---

## Getting Help

If tests fail:

1. **Check error screenshot** - See what the page looks like
2. **Run with `:watch`** - Watch the browser to see what happens
3. **Verify dev server** - Make sure it's running and accessible
4. **Check credentials** - Verify LOGIN_EMAIL and LOGIN_PASSWORD are set
5. **Review console output** - Look for specific error messages

---

## Summary

These Puppeteer tests provide:
- **Automated verification** of critical user flows
- **Visual documentation** via screenshots
- **Regression detection** before deployment
- **Quick feedback** during development

Run them regularly to ensure your application works as expected!

---

**Last Updated:** Based on current test suite in `zoe-frontend/scripts/`

