/**
 * Simple Puppeteer script to capture three screenshots of the running frontend.
 * Usage:
 *   cd frontend
 *   npm install puppeteer --save-dev
 *   node ./scripts/capture_screenshots.js
 *
 * Adjust URL and viewport as needed. This script clicks the sample queries and captures screenshots.
 */

const puppeteer = require('puppeteer')

;(async () => {
  const url = process.env.URL || 'http://localhost:5173'
  const browser = await puppeteer.launch({ headless: true })
  const page = await browser.newPage()
  await page.setViewport({ width: 1200, height: 900 })
  await page.goto(url, { waitUntil: 'networkidle2' })

  // wait for chat panel to appear
  await page.waitForSelector('.card')

  // screenshot landing
  await page.screenshot({ path: 'screenshot-landing.png', fullPage: false })

  // open samples if button present
  const sampleBtn = await page.$('button.secondary')
  if (sampleBtn) {
    await sampleBtn.click()
    await page.waitForTimeout(600)
    await page.screenshot({ path: 'screenshot-samples.png' })

    // click first sample tag
    const firstTag = await page.$('.tag')
    if (firstTag) {
      await firstTag.click()
      // wait for response to appear (rudimentary)
      await page.waitForTimeout(3000)
      await page.screenshot({ path: 'screenshot-after-sample.png' })
    }
  }

  await browser.close()
  console.log('Screenshots saved: screenshot-landing.png, screenshot-samples.png, screenshot-after-sample.png')
})().catch(e => { console.error(e); process.exit(1) })
