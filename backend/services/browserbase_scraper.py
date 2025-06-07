import os
import base64
import asyncio
from typing import Dict, Any
from playwright.async_api import async_playwright
from browserbase import Browserbase
from models import ScrapeArtifacts
from config import settings

class BrowserbaseScraper:
    def __init__(self, api_key: str, project_id: str):
        self.api_key = api_key
        self.project_id = project_id
        self.bb = Browserbase(api_key=api_key)
        
    async def scrape_site(self, url: str) -> ScrapeArtifacts:
        """
        Complete site scraping pipeline using Browserbase with proper SDK
        Following documentation: https://docs.browserbase.com/use-cases/scraping-website
        """
        
        print(f"🚀 Creating Browserbase session for: {url}")
        
        # Step 1: Create Browserbase session with project_id
        session = self.bb.sessions.create(
            project_id=self.project_id,
            # Add stealth mode and viewport settings
            browser_settings={
                "stealth": True,
                "viewport": {"width": 1920, "height": 1080}
            }
        )
        
        print(f"✅ Session created: https://browserbase.com/sessions/{session.id}")
        
        try:
            # Step 2: Connect using Playwright
            async with async_playwright() as p:
                print("🔌 Connecting to Browserbase browser...")
                browser = await p.chromium.connect_over_cdp(session.connect_url)
                
                # Get the default browser context and page
                context = browser.contexts[0]
                page = context.pages[0]
                
                # Set a realistic user agent for better compatibility
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })
                
                print(f"🌐 Navigating to: {url}")
                # Step 3: Smart navigation with adaptive timeouts for complex sites
                
                # Detect if this is a complex site that needs longer timeouts
                domain = url.lower()
                is_complex_site = any(x in domain for x in [
                    'chatgpt.com', 'openai.com', 'youtube.com', 'google.com', 
                    'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
                    'netflix.com', 'amazon.com', 'reddit.com', 'github.com',
                    'discord.com', 'slack.com', 'notion.so', 'figma.com',
                    'canva.com', 'spotify.com', 'twitch.tv'
                ])
                
                if is_complex_site:
                    print(f"🔍 Detected complex site, using extended timeout strategy")
                    timeout_ms = 120000  # 2 minutes for complex sites
                    wait_strategy = "domcontentloaded"  # Less strict wait condition
                else:
                    timeout_ms = 60000   # 1 minute for normal sites  
                    wait_strategy = "networkidle"
                
                try:
                    await page.goto(url, wait_until=wait_strategy, timeout=timeout_ms)
                    print(f"✅ Page loaded with {wait_strategy} strategy")
                    
                    # For complex sites, give extra time for JS to initialize
                    if is_complex_site:
                        print("⏱️ Waiting for JavaScript initialization...")
                        
                        # Special handling for streaming platforms
                        if 'twitch.tv' in domain or 'youtube.com' in domain:
                            print("📺 Detected streaming platform, waiting for content...")
                            await page.wait_for_timeout(10000)  # 10 seconds for streaming sites
                            
                            # Try to wait for key content elements
                            try:
                                if 'twitch.tv' in domain:
                                    await page.wait_for_selector('[data-a-target="home-live-carousel"], .home-headerbar, .top-nav', timeout=15000)
                                elif 'youtube.com' in domain:
                                    await page.wait_for_selector('#content, #header, ytd-app', timeout=15000)
                            except:
                                print("⚠️ Key elements not found, proceeding with available content")
                        else:
                            await page.wait_for_timeout(5000)  # 5 second buffer for other complex sites
                        
                except Exception as nav_error:
                    if is_complex_site:
                        print(f"⚠️ Primary strategy failed, trying fallback...")
                        # Fallback: Try with just domcontentloaded and shorter timeout
                        try:
                            await page.goto(url, wait_until="domcontentloaded", timeout=90000)
                            print(f"✅ Page loaded with fallback strategy")
                            await page.wait_for_timeout(8000)  # Extra wait for complex sites
                        except Exception as fallback_error:
                            print(f"❌ Both strategies failed: {fallback_error}")
                            raise fallback_error
                    else:
                        raise nav_error
                
                print("🧹 Cleaning up unwanted elements...")
                # Step 4: Remove unwanted elements (scripts, ads, tracking)
                await page.evaluate("""
                    // Remove scripts, ads, tracking elements
                    document.querySelectorAll(`
                        script, noscript, 
                        iframe[src*="ads"], iframe[src*="google"], iframe[src*="facebook"],
                        [class*="ad-"], [class*="ads"], [class*="advertisement"],
                        [id*="ad-"], [id*="ads"], [id*="advertisement"],
                        [class*="tracking"], [class*="analytics"], [class*="gtm"],
                        [data-ad], [data-ads]
                    `).forEach(el => el.remove());
                """)
                
                print("📄 Extracting DOM HTML...")
                # Step 5: Extract clean DOM HTML
                clean_html = await page.evaluate("document.documentElement.outerHTML")
                
                print("🎨 Extracting CSS content with smart fallback...")
                # Step 6: Smart CSS extraction with fallback for complex sites
                css_content = await page.evaluate("""
                    () => {
                        // Detect if this is a complex site that might need simpler extraction
                        const isComplexSite = document.querySelectorAll('*').length > 1000 || 
                                            document.querySelectorAll('[class*="yt-"], [id*="yt-"]').length > 0 ||
                                            window.location.hostname.includes('youtube.com') ||
                                            window.location.hostname.includes('google.com') ||
                                            window.location.hostname.includes('chatgpt.com') ||
                                            window.location.hostname.includes('openai.com') ||
                                            window.location.hostname.includes('discord.com') ||
                                            window.location.hostname.includes('twitch.tv') ||
                                            document.styleSheets.length > 10 ||
                                            document.querySelectorAll('[class*="react-"], [class*="chakra-"], [class*="discord-"], [class*="tw-"], [data-a-target]').length > 50;
                        
                        let allCSS = '';
                        
                        // Get inline styles from style tags  
                        const styleElements = document.querySelectorAll('style');
                        styleElements.forEach((style, index) => {
                            allCSS += `/* Inline Style ${index + 1} */\\n` + style.textContent + '\\n\\n';
                        });
                        
                        // Get external stylesheets (what we can access)
                        let accessibleStylesheets = 0;
                        Array.from(document.styleSheets).forEach((sheet, index) => {
                            try {
                                if (sheet.cssRules && sheet.cssRules.length > 0) {
                                    allCSS += `/* Stylesheet ${index + 1} - ${sheet.cssRules.length} rules */\\n`;
                                    Array.from(sheet.cssRules).forEach(rule => {
                                        allCSS += rule.cssText + '\\n';
                                    });
                                    allCSS += '\\n';
                                    accessibleStylesheets++;
                                }
                            } catch (e) {
                                // CORS restricted
                                allCSS += `/* External stylesheet ${index + 1} - CORS restricted */\\n`;
                                if (sheet.href) {
                                    allCSS += `/* Source: ${sheet.href} */\\n`;
                                }
                                allCSS += '\\n';
                            }
                        });
                        
                        // Use simpler computed styles for complex sites, comprehensive for simple sites
                        if (isComplexSite) {
                            // Simple extraction for complex sites like YouTube
                            allCSS += '/* Key Computed Styles (Simple Mode) */\\n';
                            // Enhanced selectors for streaming platforms and complex sites
                            let keySelectors = 'body, header, nav, main, footer, [class*="header"], [class*="nav"], [class*="content"], [class*="main"]';
                            
                            if (window.location.hostname.includes('twitch.tv')) {
                                keySelectors += ', [data-a-target], [class*="tw-"], .top-nav, .home-headerbar, [class*="layout"], [class*="carousel"]';
                            } else if (window.location.hostname.includes('youtube.com')) {
                                keySelectors += ', ytd-app, #content, #header, [class*="ytd-"], [class*="yt-"]';
                            } else if (window.location.hostname.includes('discord.com')) {
                                keySelectors += ', [class*="discord-"], [class*="container"], [class*="wrapper"], [class*="content"]';
                            }
                            
                            const keyElements = document.querySelectorAll(keySelectors);
                            
                            keyElements.forEach((element, index) => {
                                if (index < 20) { // Limit for performance
                                    const computedStyle = window.getComputedStyle(element);
                                    const tagName = element.tagName.toLowerCase();
                                    
                                    let selector = tagName;
                                    if (element.id) selector = `#${element.id}`;
                                    else if (element.className) {
                                        let classString = '';
                                        if (typeof element.className === 'string') {
                                            classString = element.className;
                                        } else if (element.className.toString) {
                                            classString = element.className.toString();
                                        }
                                        if (classString) {
                                            const firstClass = classString.trim().split(/\\s+/)[0];
                                            if (firstClass) selector = '.' + firstClass;
                                        }
                                    }
                                    
                                    // Enhanced visual properties for complex sites
                                    let keyProps = ['background', 'background-color', 'color', 'display', 'width', 'height', 'padding', 'margin', 'font-size', 'font-family'];
                                    
                                    // Add more properties for streaming platforms
                                    if (window.location.hostname.includes('twitch.tv') || window.location.hostname.includes('youtube.com')) {
                                        keyProps = keyProps.concat(['position', 'top', 'left', 'right', 'bottom', 'z-index', 'border', 'border-radius', 'box-shadow', 'flex', 'flex-direction', 'justify-content', 'align-items', 'grid-template-columns', 'overflow']);
                                    }
                                    let elementCSS = `${selector} {\\n`;
                                    let hasStyles = false;
                                    
                                    keyProps.forEach(prop => {
                                        const value = computedStyle.getPropertyValue(prop);
                                        if (value && value !== 'auto' && value !== 'normal' && value !== 'none' && value !== '0px' && value !== 'transparent') {
                                            elementCSS += `  ${prop}: ${value};\\n`;
                                            hasStyles = true;
                                        }
                                    });
                                    
                                    elementCSS += '}\\n\\n';
                                    if (hasStyles) allCSS += elementCSS;
                                }
                            });
                        } else {
                            // Comprehensive extraction for simpler sites
                            allCSS += '/* Comprehensive Computed Styles */\\n';
                            const allElements = document.querySelectorAll('*');
                            
                            allElements.forEach((element, index) => {
                                if (index < 100) { // Reasonable limit
                                    const tagName = element.tagName.toLowerCase();
                                    const hasClass = element.className && element.className.length > 0;
                                    const hasId = element.id && element.id.length > 0;
                                    const isVisualElement = ['body', 'html', 'div', 'section', 'header', 'nav', 'main', 'footer', 'article', 'aside'].includes(tagName);
                                    
                                    if (hasClass || hasId || isVisualElement) {
                                        const computedStyle = window.getComputedStyle(element);
                                        
                                        let selector = tagName;
                                        if (element.id) selector = `#${element.id}`;
                                        else if (element.className) {
                                            let classString = '';
                                            if (typeof element.className === 'string') {
                                                classString = element.className;
                                            } else if (element.className.toString) {
                                                classString = element.className.toString();
                                            }
                                            if (classString) {
                                                const classes = classString.trim().split(/\\s+/);
                                                if (classes.length > 0 && classes[0]) {
                                                    selector = '.' + classes.join('.');
                                                }
                                            }
                                        }
                                        
                                        const visualProps = [
                                            'display', 'position', 'top', 'left', 'right', 'bottom',
                                            'width', 'height', 'margin', 'padding', 'border', 'border-radius',
                                            'background', 'background-color', 'background-image', 'background-size',
                                            'color', 'font-family', 'font-size', 'font-weight', 'line-height',
                                            'flex', 'flex-direction', 'justify-content', 'align-items', 'grid-template-columns'
                                        ];
                                        
                                        let elementCSS = `${selector} {\\n`;
                                        let hasSignificantStyles = false;
                                        
                                        visualProps.forEach(prop => {
                                            const value = computedStyle.getPropertyValue(prop);
                                            if (value && value !== 'auto' && value !== 'normal' && value !== 'none' && value !== '0px' && value !== 'transparent' && value !== 'rgba(0, 0, 0, 0)') {
                                                elementCSS += `  ${prop}: ${value};\\n`;
                                                hasSignificantStyles = true;
                                            }
                                        });
                                        
                                        elementCSS += '}\\n\\n';
                                        if (hasSignificantStyles) allCSS += elementCSS;
                                    }
                                }
                            });
                        }
                        
                        console.log(`CSS extraction mode: ${isComplexSite ? 'SIMPLE' : 'COMPREHENSIVE'}, Accessible stylesheets: ${accessibleStylesheets}`);
                        return allCSS;
                    }
                """)
                
                print("🖼️ Processing images and visual assets...")
                # Step 7: Comprehensive image and visual asset processing
                image_info = await page.evaluate("""
                    () => {
                        const images = [];
                        const backgroundImages = [];
                        
                        // Process IMG elements
                        const imageElements = document.querySelectorAll('img');
                        imageElements.forEach((img, index) => {
                            const src = img.src;
                            const alt = img.alt || '';
                            const width = img.naturalWidth || img.width;
                            const height = img.naturalHeight || img.height;
                            
                            // Convert relative URLs to absolute
                            let absoluteSrc = src;
                            if (src && !src.startsWith('http') && !src.startsWith('data:')) {
                                try {
                                    absoluteSrc = new URL(src, window.location.href).href;
                                } catch (e) {
                                    absoluteSrc = src;
                                }
                            }
                            
                            images.push({
                                index,
                                original_src: src,
                                absolute_src: absoluteSrc,
                                alt,
                                width,
                                height,
                                element_tag: 'img'
                            });
                        });
                        
                        // Process background images from CSS
                        const allElements = document.querySelectorAll('*');
                        allElements.forEach((element, index) => {
                            const computedStyle = window.getComputedStyle(element);
                            const backgroundImage = computedStyle.getPropertyValue('background-image');
                            
                            if (backgroundImage && backgroundImage !== 'none') {
                                // Extract URL from CSS background-image
                                const urlMatch = backgroundImage.match(/url\\(['"]?([^'"\\)]+)['"]?\\)/);
                                if (urlMatch && urlMatch[1]) {
                                    let url = urlMatch[1];
                                    
                                    // Convert relative URLs to absolute
                                    if (!url.startsWith('http') && !url.startsWith('data:')) {
                                        try {
                                            url = new URL(url, window.location.href).href;
                                        } catch (e) {
                                            // Keep original if conversion fails
                                        }
                                    }
                                    
                                    backgroundImages.push({
                                        element_index: index,
                                        element_tag: element.tagName.toLowerCase(),
                                        element_class: element.className,
                                        element_id: element.id,
                                        original_bg_image: backgroundImage,
                                        extracted_url: url,
                                        background_size: computedStyle.getPropertyValue('background-size'),
                                        background_position: computedStyle.getPropertyValue('background-position'),
                                        background_repeat: computedStyle.getPropertyValue('background-repeat')
                                    });
                                }
                            }
                        });
                        
                        return { images, backgroundImages };
                    }
                """)

                print("📸 Taking screenshot...")
                # Step 8: Take screenshot
                screenshot_bytes = await page.screenshot(
                    type="png",
                    full_page=False,
                    clip={"x": 0, "y": 0, "width": 1920, "height": 1080}
                )
                
                print("📋 Extracting metadata...")
                # Step 9: Extract metadata
                metadata = await page.evaluate("""
                    () => ({
                        title: document.title || '',
                        description: document.querySelector('meta[name="description"]')?.content || 
                                   document.querySelector('meta[property="og:description"]')?.content || '',
                        favicon: document.querySelector('link[rel="icon"]')?.href || 
                               document.querySelector('link[rel="shortcut icon"]')?.href || '',
                        lang: document.documentElement.lang || 'en',
                        viewport: document.querySelector('meta[name="viewport"]')?.content || '',
                        keywords: document.querySelector('meta[name="keywords"]')?.content || '',
                        author: document.querySelector('meta[name="author"]')?.content || '',
                        robots: document.querySelector('meta[name="robots"]')?.content || '',
                        canonical: document.querySelector('link[rel="canonical"]')?.href || '',
                        og_title: document.querySelector('meta[property="og:title"]')?.content || '',
                        og_image: document.querySelector('meta[property="og:image"]')?.content || '',
                        og_url: document.querySelector('meta[property="og:url"]')?.content || ''
                    })
                """)
                
                print("🔒 Closing browser connection...")
                # Step 10: Close browser properly
                await page.close()
                await browser.close()
                
                print("✅ Scraping completed successfully!")
                
                return ScrapeArtifacts(
                    url=url,
                    dom_html=clean_html,
                    css_content=css_content,
                    hero_image_bytes=screenshot_bytes,
                    metadata=metadata,
                    image_info=image_info
                )
                
        except Exception as e:
            print(f"❌ Error during scraping: {str(e)}")
            raise
        
        finally:
            # Session will auto-expire, but we can log completion
            print(f"🏁 Session {session.id} processing complete")
    
    def create_session_with_metadata(self, metadata: Dict[str, Any]):
        """
        Create a session with metadata for usage tracking
        Following documentation: https://docs.browserbase.com/guides/measuring-usage
        """
        return self.bb.sessions.create(
            project_id=self.project_id,
            user_metadata=metadata,
            browser_settings={
                "stealth": True,
                "viewport": {"width": 1920, "height": 1080}
            }
        )
    
    def get_usage_stats(self):
        """
        Get project usage statistics
        Following documentation: https://docs.browserbase.com/guides/measuring-usage
        """
        import requests
        
        response = requests.get(
            f"https://api.browserbase.com/v1/projects/{self.project_id}/usage",
            headers={"X-BB-API-Key": self.api_key}
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Cleanup method for compatibility"""
        # Browserbase sessions auto-expire, no cleanup needed
        pass 