/**
 * KenPom Scraper
 * 
 * This script logs into the KenPom website and downloads FanMatch HTML data.
 * It then calls the Python parser to convert the HTML to CSV format.
 * The CSV file is saved to data/kp.csv
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration options
const CONFIG = {
  waitForNewDays: false, // Set to true if you want to wait for new days to appear
  maxChecks: 10, // Maximum number of checks for new days
  waitTimeBetweenChecks: 60000, // Wait time in ms between checks (1 minute)
  saveHTML: true, // Save HTML of each page
  outputDir: path.join(__dirname, '../../kenpom-data'), // Directory to save HTML and data
  csvOutputPath: path.join(__dirname, '../../data/kp.csv'), // Fixed output path for the CSV
  headless: true, // Run in headless mode (no browser UI)
  navigationTimeout: 30000, // Navigation timeout in ms (30 seconds)
  // Load credentials from environment variables
  credentials: {
    email: process.env.EMAIL || '',
    password: process.env.PASSWORD || ''
  },
  // User agent to mimic a real browser
  userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
};

/**
 * Ensures a directory exists, creating it if necessary
 * @param {string} directory - Path to directory
 */
function ensureDirectoryExists(directory) {
  if (!fs.existsSync(directory)) {
    fs.mkdirSync(directory, { recursive: true });
    console.log(`Created directory: ${directory}`);
  }
}

/**
 * Saves HTML content to a file
 * @param {string} html - HTML content
 * @param {string} filename - Output filename
 */
function saveHTML(html, filename) {
  try {
    const filePath = path.join(CONFIG.outputDir, filename);
    fs.writeFileSync(filePath, html, 'utf8');
    console.log(`✅ Saved HTML to: ${filePath}`);
    return filePath;
  } catch (error) {
    console.error(`❌ Error saving HTML: ${error.message}`);
    throw error;
  }
}

/**
 * Gets the formatted date for today
 * @returns {string} Date in YYYY-MM-DD format
 */
function getTodayDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Main scraping function
 */
async function scrapeKenPom() {
  console.log('🚀 Starting KenPom scraper...');
  
  // Ensure output directory exists
  ensureDirectoryExists(CONFIG.outputDir);

  // Check credentials
  if (!CONFIG.credentials.email || !CONFIG.credentials.password) {
    console.error('❌ Missing credentials. Set EMAIL and PASSWORD environment variables.');
    process.exit(1);
  }

  let browser;
  try {
    // Launch browser
    console.log('🌐 Launching browser...');
    browser = await chromium.launch({
      headless: CONFIG.headless,
      args: [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled'
      ]
    });

    // Create context with custom user agent
    const context = await browser.newContext({
      userAgent: CONFIG.userAgent,
      viewport: { width: 1920, height: 1080 }
    });

    const page = await context.newPage();

    // Set navigation timeout
    page.setDefaultTimeout(CONFIG.navigationTimeout);

    // Navigate to login page
    console.log('🔐 Navigating to login page...');
    await page.goto('https://kenpom.com/', { waitUntil: 'networkidle' });
    
    // Fill login form
    console.log('📝 Filling login credentials...');
    await page.fill('input[name="email"]', CONFIG.credentials.email);
    await page.fill('input[name="password"]', CONFIG.credentials.password);
    
    // Submit form
    console.log('✉️  Submitting login form...');
    await page.click('input[type="submit"]');
    await page.waitForLoadState('networkidle');
    
    console.log('✅ Successfully logged in!');

    // Navigate to FanMatch page
    const today = getTodayDate();
    const fanmatchUrl = `https://kenpom.com/fanmatch.php?d=${today}`;
    
    console.log(`📊 Navigating to FanMatch for ${today}...`);
    await page.goto(fanmatchUrl, { waitUntil: 'networkidle' });
    
    // Wait for the table to load
    await page.waitForSelector('table.fanmatch', { timeout: CONFIG.navigationTimeout });
    
    // Get HTML content
    const html = await page.content();
    
    // Save HTML if enabled
    if (CONFIG.saveHTML) {
      const filename = `fanmatch-${today}.html`;
      saveHTML(html, filename);
    }
    
    console.log('✅ Successfully scraped FanMatch data!');
    
    // Close browser
    await browser.close();
    console.log('🏁 Scraping complete!');
    
  } catch (error) {
    console.error('❌ Error during scraping:', error.message);
    if (browser) {
      await browser.close();
    }
    process.exit(1);
  }
}

// Run the scraper
scrapeKenPom().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
