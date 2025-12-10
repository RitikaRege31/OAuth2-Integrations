# 🎭 Puppeteer Frontend Testing - Complete Technical Guide

## 📚 Table of Contents
1. [What is Puppeteer?](#what-is-puppeteer)
2. [How Puppeteer Works](#how-puppeteer-works)
3. [Integration in Your Project](#integration-in-your-project)
4. [Screenshot Capture Deep Dive](#screenshot-capture-deep-dive)
5. [Frontend Testing Workflow](#frontend-testing-workflow)
6. [Best Practices](#best-practices)
7. [Common Patterns](#common-patterns)

---

## 🎯 What is Puppeteer?

**Puppeteer** is a Node.js library that provides a high-level API to control Chrome/Chromium browsers programmatically. Think of it as a robot that can:
- Open websites
- Click buttons
- Fill forms
- Take screenshots
- Extract data
- Test web applications

### Key Concepts

**Browser Instance**: The actual Chrome/Chromium process launched by Puppeteer
```javascript
const browser = await puppeteer.launch({ headless: false });
```

**Page**: A tab/window within the browser (one browser can have many pages)
```javascript
const page = await browser.newPage();
```

**Headless Mode**: 
- `headless: true` → Browser runs invisibly (faster, for CI/CD)
- `headless: false` → You see the browser (better for debugging)

---

## ⚙️ How Puppeteer Works

### Architecture

```
Your Test Script (Node.js)
    ↓
Puppeteer API
    ↓
Chrome DevTools Protocol (CDP)
    ↓
Chrome/Chromium Browser
    ↓
Renders Web Page
```

### Communication Flow

1. **Your script** calls Puppeteer API (e.g., `page.goto()`)
2. **Puppeteer** translates this to Chrome DevTools Protocol commands
3. **Chrome** receives commands via WebSocket connection
4. **Chrome** executes the command (navigate, click, etc.)
5. **Chrome** sends results back through CDP
6. **Puppeteer** returns the result to your script

### Example: What Happens When You Call `page.goto()`

```javascript
await page.goto('http://localhost:3000/login');
```

**Behind the scenes:**
1. Puppeteer sends `Page.navigate` CDP command
2. Chrome starts loading the URL
3. Chrome fires `Page.frameNavigated` event
4. Chrome fires `Page.loadEventFired` when page loads
5. Puppeteer waits for `networkidle2` (no network requests for 500ms)
6. Promise resolves, your code continues

---

## 🔌 Integration in Your Project

### Installation

```json
// package.json
{
  "dependencies": {
    "puppeteer": "^24.32.0"
  }
}
```

Puppeteer automatically downloads Chromium when you install it.

### Project Structure

```
zoe-frontend/
├── scripts/
│   ├── test-login-page.js      # Login page test
│   ├── test-analysis-page.js   # Analysis page test
│   └── test-saved-claims-page.js # Saved claims test
├── package.json                 # npm scripts defined here
└── PUPPETEER_DETAILED_GUIDE.md # This file
```

### npm Scripts Integration

```json
// package.json
{
  "scripts": {
    "test:puppeteer:login": "cross-env node scripts/test-login-page.js",
    "test:puppeteer:login:watch": "cross-env HEADLESS=false node scripts/test-login-page.js"
  }
}
```

**Why `cross-env`?**
- Windows PowerShell doesn't support `VAR=value command` syntax
- `cross-env` makes environment variables work cross-platform
- Allows: `HEADLESS=false npm run test:puppeteer:login:watch`

---

## 📸 Screenshot Capture Deep Dive

### How Screenshots Work in Puppeteer

#### 1. **Basic Screenshot**

```javascript
await page.screenshot({ path: 'screenshot.png' });
```

**What happens:**
1. Puppeteer sends `Page.captureScreenshot` CDP command
2. Chrome renders the current viewport to a bitmap
3. Chrome encodes bitmap as PNG/JPEG
4. Chrome sends image data back via CDP
5. Puppeteer writes the data to the file system
6. Returns the buffer (if no path specified)

#### 2. **Full Page Screenshot**

```javascript
await page.screenshot({ 
  path: 'full-page.png',
  fullPage: true  // Captures entire scrollable area
});
```

**Technical Process:**
1. Puppeteer queries page dimensions: `Page.getLayoutMetrics`
2. Gets viewport height and content height
3. If `fullPage: true`, calculates total scroll height
4. Takes multiple viewport screenshots while scrolling
5. Stitches them together into one image
6. Saves the composite image

**Code Flow:**
```javascript
// Simplified version of what Puppeteer does internally
const metrics = await page.evaluate(() => ({
  width: document.documentElement.scrollWidth,
  height: document.documentElement.scrollHeight
}));

// Scroll and capture each section
for (let y = 0; y < metrics.height; y += viewportHeight) {
  await page.evaluate((scrollY) => window.scrollTo(0, scrollY), y);
  // Capture viewport screenshot
  // Append to full image
}
```

#### 3. **Screenshot Options**

```javascript
await page.screenshot({
  path: 'screenshot.png',
  type: 'png',              // 'png' or 'jpeg'
  quality: 90,              // 0-100, only for JPEG
  fullPage: true,           // Capture entire page
  clip: {                   // Capture specific region
    x: 0,
    y: 0,
    width: 800,
    height: 600
  },
  omitBackground: false,    // Include background
  encoding: 'base64'        // Return as base64 string
});
```

### Login Screen Screenshot Example

Let's trace through your login test:

```javascript
// 1. Launch browser
const browser = await puppeteer.launch({ headless: false });
const page = await browser.newPage();

// 2. Navigate to login page
await page.goto('http://localhost:3000/login', { 
  waitUntil: 'networkidle2' 
});

// 3. Wait for React to render
await new Promise(resolve => setTimeout(resolve, 500));

// 4. Fill form
await page.type('input[type="email"]', 'user@example.com');
await page.type('input[type="password"]', 'password123');

// 5. Click submit
await page.click('button[type="submit"]');

// 6. Wait for navigation
await page.waitForNavigation({ waitUntil: 'networkidle2' });

// 7. Take screenshot
await page.screenshot({ 
  path: 'login-page-smoke.png',
  fullPage: true 
});
```

**Screenshot Timeline:**
```
Time  Action
----  ------
0ms   Browser launches
500ms Navigate to /login
1000ms Page loads, React hydrates
1500ms Form fields filled
2000ms Submit clicked
3000ms Login request sent
4000ms Redirect to /dashboard
4500ms Dashboard loads
5000ms Screenshot captured ← Final state
```

### Screenshot Data Flow

```
Chrome Browser
    ↓ (renders DOM to bitmap)
Chrome Rendering Engine
    ↓ (encodes bitmap)
PNG/JPEG Image Data
    ↓ (via CDP)
Puppeteer API
    ↓ (writes to disk)
File System
    ↓
login-page-smoke.png
```

---

## 🧪 Frontend Testing Workflow

### Complete Testing Flow

#### 1. **Setup Phase**

```javascript
// Launch browser
const browser = await puppeteer.launch({
  headless: HEADLESS,
  defaultViewport: { width: 1280, height: 900 },
  args: ['--no-sandbox', '--disable-setuid-sandbox']
});

// Create page
const page = await browser.newPage();
page.setDefaultTimeout(45000); // 45 second timeout
```

**What this does:**
- Spawns a new Chrome process
- Creates a new tab
- Sets viewport size (simulates screen size)
- Configures timeouts for all operations

#### 2. **Navigation Phase**

```javascript
await page.goto(`${BASE_URL}/login`, { 
  waitUntil: 'networkidle2',
  timeout: 30000
});
```

**Wait Strategies:**
- `load` - Wait for `load` event
- `domcontentloaded` - Wait for DOM ready
- `networkidle0` - No network requests for 500ms
- `networkidle2` - ≤2 network requests for 500ms (recommended)

#### 3. **Interaction Phase**

```javascript
// Wait for element
await page.waitForSelector('input[type="email"]', { 
  visible: true,
  timeout: 10000
});

// Type text
await page.type('input[type="email"]', 'user@example.com', {
  delay: 30  // 30ms delay between keystrokes (simulates human)
});

// Click button
await page.click('button[type="submit"]');
```

**Element Selection Methods:**
- CSS Selector: `'input[type="email"]'`
- XPath: `page.$x("//button[contains(., 'Login')]")`
- Text: `page.waitForFunction(() => document.body.innerText.includes('Login'))`

#### 4. **Assertion Phase**

```javascript
// Wait for navigation
await page.waitForNavigation({ waitUntil: 'networkidle2' });

// Check URL
const url = page.url();
if (url.includes('/dashboard')) {
  console.log('✅ Successfully redirected');
}

// Check element exists
const element = await page.$('h1');
const text = await page.evaluate(el => el.textContent, element);
console.log('Page title:', text);
```

#### 5. **Network Monitoring**

```javascript
// Intercept requests
await page.setRequestInterception(true);
page.on('request', (request) => {
  if (request.url().includes('/api/login')) {
    // Mock or log the request
    return request.respond({ status: 200, body: '{}' });
  }
  return request.continue();
});

// Wait for specific request
const loginRequest = await page.waitForRequest(
  req => req.url().includes('/auth/login')
);
console.log('Request URL:', loginRequest.url());
console.log('Request data:', loginRequest.postData());
```

#### 6. **Screenshot Phase**

```javascript
// Take screenshot
await page.screenshot({ 
  path: 'test-result.png',
  fullPage: true 
});
```

#### 7. **Cleanup Phase**

```javascript
await browser.close();
```

---

## 🎨 Best Practices

### 1. **Wait Strategies**

❌ **Bad:**
```javascript
await page.goto('/login');
await page.click('button'); // Might fail if button not ready
```

✅ **Good:**
```javascript
await page.goto('/login', { waitUntil: 'networkidle2' });
await page.waitForSelector('button', { visible: true });
await page.click('button');
```

### 2. **Error Handling**

❌ **Bad:**
```javascript
await page.click('button');
```

✅ **Good:**
```javascript
try {
  await page.waitForSelector('button', { timeout: 10000 });
  await page.click('button');
} catch (error) {
  await page.screenshot({ path: 'error-debug.png' });
  throw error;
}
```

### 3. **Timeouts**

```javascript
// Set default timeout
page.setDefaultTimeout(45000);

// Override for specific operations
await page.waitForSelector('.slow-element', { timeout: 60000 });
```

### 4. **Screenshot on Failure**

```javascript
run().catch(async (error) => {
  const pages = await browser?.pages();
  if (pages?.[0]) {
    await pages[0].screenshot({ path: 'error.png' });
  }
  throw error;
});
```

### 5. **Environment Variables**

```javascript
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const HEADLESS = process.env.HEADLESS !== 'false';
```

**PowerShell:**
```powershell
$env:BASE_URL = "http://localhost:3000"
$env:HEADLESS = "false"
npm run test
```

**Bash:**
```bash
BASE_URL=http://localhost:3000 HEADLESS=false npm run test
```

---

## 🔄 Common Patterns

### Pattern 1: Form Filling

```javascript
// Wait for form
await page.waitForSelector('form');

// Fill fields
await page.type('#email', email);
await page.type('#password', password);

// Submit
await page.click('button[type="submit"]');
```

### Pattern 2: Waiting for Multiple Conditions

```javascript
await Promise.all([
  page.waitForNavigation(),
  page.waitForRequest(req => req.url().includes('/api/login'))
]);
```

### Pattern 3: Conditional Screenshots

```javascript
const url = page.url();
if (url.includes('/dashboard')) {
  await page.screenshot({ path: 'success.png' });
} else {
  await page.screenshot({ path: 'failure.png' });
}
```

### Pattern 4: Mocking API Responses

```javascript
await page.setRequestInterception(true);
page.on('request', (request) => {
  if (request.url().includes('/api/data')) {
    return request.respond({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ data: 'mocked' })
    });
  }
  return request.continue();
});
```

### Pattern 5: Authentication Bypass

```javascript
// Seed localStorage before navigation
await page.evaluateOnNewDocument((authData) => {
  localStorage.setItem('persist:root', JSON.stringify(authData));
}, mockAuthState);

await page.goto('/dashboard'); // Already authenticated
```

---

## 📊 Testing Your Login Screen - Complete Flow

### Step-by-Step Breakdown

```javascript
// 1. SETUP
const browser = await puppeteer.launch({ headless: false });
const page = await browser.newPage();

// 2. NAVIGATE
await page.goto('http://localhost:3000/login', {
  waitUntil: 'networkidle2'  // Wait for all network activity
});

// 3. WAIT FOR ELEMENTS
await page.waitForSelector('input[type="email"]', { visible: true });
await page.waitForSelector('input[type="password"]', { visible: true });

// 4. INTERACT
await page.type('input[type="email"]', 'user@example.com', { delay: 30 });
await page.type('input[type="password"]', 'password123', { delay: 30 });

// 5. MONITOR NETWORK
const loginRequestPromise = page.waitForRequest(
  req => req.url().includes('/auth/login')
);

// 6. SUBMIT
await page.click('button[type="submit"]');

// 7. WAIT FOR RESPONSE
await loginRequestPromise;

// 8. WAIT FOR NAVIGATION
await page.waitForNavigation({ waitUntil: 'networkidle2' });

// 9. VERIFY
const url = page.url();
console.log('Current URL:', url);

// 10. CAPTURE
await page.screenshot({ 
  path: 'login-success.png',
  fullPage: true 
});

// 11. CLEANUP
await browser.close();
```

### What Each Step Does Internally

1. **Launch**: Spawns Chrome process, establishes CDP connection
2. **Navigate**: Sends HTTP request, receives HTML, parses DOM, executes JS
3. **Wait**: Polls DOM until selector appears
4. **Type**: Simulates keyboard events, triggers React onChange handlers
5. **Monitor**: Listens to CDP Network domain events
6. **Click**: Simulates mouse click, triggers onClick handlers
7. **Wait**: Monitors network until login request appears
8. **Navigate**: Waits for location change, new page load
9. **Verify**: Reads current URL from browser
10. **Screenshot**: Renders viewport to bitmap, encodes PNG, saves file
11. **Close**: Terminates Chrome process, closes CDP connection

---

## 🛠️ Debugging Tips

### 1. **Slow Down Execution**

```javascript
// Add delays to see what's happening
await page.type('#email', email, { delay: 100 });
await new Promise(resolve => setTimeout(resolve, 1000));
```

### 2. **Take Screenshots at Key Points**

```javascript
await page.screenshot({ path: 'step1-loaded.png' });
await page.type('#email', email);
await page.screenshot({ path: 'step2-typed.png' });
```

### 3. **Log Page Content**

```javascript
const content = await page.evaluate(() => document.body.innerText);
console.log('Page content:', content);
```

### 4. **Check Network Requests**

```javascript
page.on('request', request => console.log('→', request.method(), request.url()));
page.on('response', response => console.log('←', response.status(), response.url()));
```

### 5. **Run with Visible Browser**

```javascript
const browser = await puppeteer.launch({ headless: false });
// Watch the browser to see what's happening
```

---

## 📝 Summary

**Puppeteer Testing Flow:**
1. Launch browser → Create page
2. Navigate → Wait for load
3. Find elements → Wait for visibility
4. Interact → Type, click, etc.
5. Monitor → Network requests, navigation
6. Assert → Verify state
7. Capture → Screenshots
8. Cleanup → Close browser

**Screenshot Process:**
1. Chrome renders DOM to bitmap
2. Encodes bitmap as PNG/JPEG
3. Sends via CDP to Puppeteer
4. Puppeteer writes to file system

**Key Takeaways:**
- Always wait for elements before interacting
- Use `networkidle2` for reliable page loads
- Take screenshots for debugging
- Handle errors gracefully
- Clean up browser instances

---

## 🚀 Next Steps

1. **Read your test files**: `scripts/test-*.js`
2. **Run tests**: `npm run test:puppeteer:login:watch`
3. **Modify tests**: Add your own assertions
4. **Create new tests**: Copy existing test as template
5. **Integrate CI/CD**: Run tests automatically

---

**Happy Testing! 🎉**


