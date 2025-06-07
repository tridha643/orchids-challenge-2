import asyncio
import aiohttp
import re
import base64
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from pathlib import Path
import json

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from PIL import Image
import cssutils

from config import settings
from models import ScrapedData, CloneOptions

class WebScraper:
    """Advanced web scraper for extracting comprehensive design context from websites"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=settings.headless_browser,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape_website(self, url: str, options: CloneOptions) -> ScrapedData:
        """
        Main scraping method that extracts comprehensive design context
        """
        try:
            # Create a new page with custom viewport
            page = await self.browser.new_page(
                viewport={
                    'width': options.viewport_width,
                    'height': options.viewport_height
                }
            )
            
            # Set user agent to avoid bot detection
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            })
            
            # Navigate to the page with timeout
            await page.goto(url, wait_until='networkidle', timeout=options.max_wait_time * 1000)
            
            # Wait for dynamic content to load
            await asyncio.sleep(3)
            
            # Extract page data
            html_content = await page.content()
            title = await page.title()
            
            # Take screenshot
            screenshot_path = None
            if True:  # Always take screenshot for now
                screenshot_path = await self._take_screenshot(page, url)
            
            # Extract comprehensive UI elements
            ui_elements = await self._extract_ui_elements(page)
            
            # Extract CSS
            css_styles = await self._extract_css(page, url)
            
            # Extract layout information
            layout_info = await self._extract_layout_information(page)
            
            # Extract images
            images = []
            if options.include_images:
                images = await self._extract_images(page, url)
            
            # Extract fonts
            fonts = []
            if options.include_fonts:
                fonts = await self._extract_fonts(page)
            
            # Extract colors
            colors = []
            if options.extract_colors:
                colors = await self._extract_colors(page)
            
            # Extract interactive elements
            interactive_elements = await self._extract_interactive_elements(page)
            
            # Extract DOM structure with visual context
            dom_structure = await self._analyze_dom_structure_enhanced(page)
            
            # Extract meta information
            meta_description = await self._extract_meta_description(page)
            viewport_meta = await self._extract_viewport_meta(page)
            
            await page.close()
            
            # Combine all extracted data
            enhanced_dom_structure = {
                **dom_structure,
                "ui_elements": ui_elements,
                "layout_info": layout_info,
                "interactive_elements": interactive_elements
            }
            
            return ScrapedData(
                url=url,
                title=title,
                html=html_content,
                css=css_styles,
                images=images,
                fonts=fonts,
                colors=colors,
                screenshot_path=screenshot_path,
                dom_structure=enhanced_dom_structure,
                meta_description=meta_description,
                viewport_meta=viewport_meta
            )
            
        except Exception as e:
            if 'page' in locals():
                await page.close()
            raise Exception(f"Scraping failed: {str(e)}")
    
    async def _extract_ui_elements(self, page: Page) -> Dict:
        """Extract comprehensive UI elements with visual properties"""
        try:
            ui_elements = await page.evaluate("""
                () => {
                    const elements = {
                        buttons: [],
                        inputs: [],
                        navigation: [],
                        cards: [],
                        headers: [],
                        content_blocks: [],
                        images: [],
                        layout_containers: []
                    };
                    
                    // Helper function to get element info
                    function getElementInfo(el) {
                        const rect = el.getBoundingClientRect();
                        const styles = window.getComputedStyle(el);
                        
                        return {
                            tag: el.tagName.toLowerCase(),
                            text: el.textContent?.trim().substring(0, 100) || '',
                            class: el.className || '',
                            id: el.id || '',
                            position: {
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            },
                            styles: {
                                backgroundColor: styles.backgroundColor,
                                color: styles.color,
                                fontSize: styles.fontSize,
                                fontFamily: styles.fontFamily,
                                padding: styles.padding,
                                margin: styles.margin,
                                border: styles.border,
                                borderRadius: styles.borderRadius,
                                display: styles.display,
                                position: styles.position,
                                zIndex: styles.zIndex
                            },
                            visible: rect.width > 0 && rect.height > 0 && styles.display !== 'none'
                        };
                    }
                    
                    // Extract buttons
                    document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"], .btn, .button').forEach(el => {
                        if (el.getBoundingClientRect().width > 0) {
                            elements.buttons.push(getElementInfo(el));
                        }
                    });
                    
                    // Extract form inputs
                    document.querySelectorAll('input, textarea, select').forEach(el => {
                        if (el.getBoundingClientRect().width > 0) {
                            const info = getElementInfo(el);
                            info.type = el.type || 'text';
                            info.placeholder = el.placeholder || '';
                            elements.inputs.push(info);
                        }
                    });
                    
                    // Extract navigation elements
                    document.querySelectorAll('nav, .nav, .navbar, .navigation, [role="navigation"]').forEach(el => {
                        if (el.getBoundingClientRect().width > 0) {
                            const links = Array.from(el.querySelectorAll('a')).map(link => ({
                                text: link.textContent?.trim() || '',
                                href: link.href || '',
                                ...getElementInfo(link)
                            }));
                            elements.navigation.push({
                                ...getElementInfo(el),
                                links: links
                            });
                        }
                    });
                    
                    // Extract card-like elements
                    document.querySelectorAll('.card, .post, .item, .product, .article, [class*="card"]').forEach(el => {
                        if (el.getBoundingClientRect().width > 0) {
                            elements.cards.push(getElementInfo(el));
                        }
                    });
                    
                    // Extract headers and important sections
                    document.querySelectorAll('header, .header, h1, h2, h3').forEach(el => {
                        if (el.getBoundingClientRect().width > 0) {
                            elements.headers.push(getElementInfo(el));
                        }
                    });
                    
                    // Extract main content blocks
                    document.querySelectorAll('main, .main, .content, .container, section, article').forEach(el => {
                        if (el.getBoundingClientRect().width > 200) { // Only substantial content blocks
                            elements.content_blocks.push(getElementInfo(el));
                        }
                    });
                    
                    // Extract images with more details
                    document.querySelectorAll('img').forEach(el => {
                        if (el.getBoundingClientRect().width > 0) {
                            const info = getElementInfo(el);
                            info.src = el.src || '';
                            info.alt = el.alt || '';
                            elements.images.push(info);
                        }
                    });
                    
                    // Extract layout containers
                    document.querySelectorAll('div, section, aside, main').forEach(el => {
                        const rect = el.getBoundingClientRect();
                        const styles = window.getComputedStyle(el);
                        
                        // Only capture significant layout containers
                        if (rect.width > 300 && rect.height > 100 && 
                            (styles.display === 'flex' || styles.display === 'grid' || 
                             el.children.length > 3)) {
                            elements.layout_containers.push(getElementInfo(el));
                        }
                    });
                    
                    return elements;
                }
            """)
            
            return ui_elements
            
        except Exception as e:
            print(f"UI elements extraction failed: {e}")
            return {}
    
    async def _extract_layout_information(self, page: Page) -> Dict:
        """Extract detailed layout and positioning information"""
        try:
            layout_info = await page.evaluate("""
                () => {
                    const layout = {
                        page_structure: {},
                        grid_systems: [],
                        flexbox_layouts: [],
                        positioning: [],
                        spacing_patterns: {}
                    };
                    
                    // Analyze page structure
                    layout.page_structure = {
                        width: document.documentElement.scrollWidth,
                        height: document.documentElement.scrollHeight,
                        viewport_width: window.innerWidth,
                        viewport_height: window.innerHeight
                    };
                    
                    // Find grid layouts
                    document.querySelectorAll('*').forEach(el => {
                        const styles = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        
                        if (styles.display === 'grid' && rect.width > 0) {
                            layout.grid_systems.push({
                                element: el.tagName.toLowerCase(),
                                class: el.className || '',
                                grid_template_columns: styles.gridTemplateColumns,
                                grid_template_rows: styles.gridTemplateRows,
                                gap: styles.gap,
                                position: {
                                    x: Math.round(rect.x),
                                    y: Math.round(rect.y),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                }
                            });
                        }
                        
                        if (styles.display === 'flex' && rect.width > 0) {
                            layout.flexbox_layouts.push({
                                element: el.tagName.toLowerCase(),
                                class: el.className || '',
                                flex_direction: styles.flexDirection,
                                justify_content: styles.justifyContent,
                                align_items: styles.alignItems,
                                gap: styles.gap,
                                position: {
                                    x: Math.round(rect.x),
                                    y: Math.round(rect.y),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                }
                            });
                        }
                        
                        // Track absolute/fixed positioning
                        if (styles.position === 'absolute' || styles.position === 'fixed') {
                            layout.positioning.push({
                                element: el.tagName.toLowerCase(),
                                class: el.className || '',
                                position_type: styles.position,
                                top: styles.top,
                                left: styles.left,
                                right: styles.right,
                                bottom: styles.bottom,
                                z_index: styles.zIndex
                            });
                        }
                    });
                    
                    // Analyze spacing patterns
                    const spacings = [];
                    document.querySelectorAll('*').forEach(el => {
                        const styles = window.getComputedStyle(el);
                        if (styles.margin !== '0px' || styles.padding !== '0px') {
                            spacings.push({
                                margin: styles.margin,
                                padding: styles.padding
                            });
                        }
                    });
                    
                    // Find common spacing patterns
                    const marginCounts = {};
                    const paddingCounts = {};
                    spacings.forEach(s => {
                        marginCounts[s.margin] = (marginCounts[s.margin] || 0) + 1;
                        paddingCounts[s.padding] = (paddingCounts[s.padding] || 0) + 1;
                    });
                    
                    layout.spacing_patterns = {
                        common_margins: Object.entries(marginCounts)
                            .sort(([,a], [,b]) => b - a)
                            .slice(0, 5)
                            .map(([margin, count]) => ({ margin, count })),
                        common_paddings: Object.entries(paddingCounts)
                            .sort(([,a], [,b]) => b - a)
                            .slice(0, 5)
                            .map(([padding, count]) => ({ padding, count }))
                    };
                    
                    return layout;
                }
            """)
            
            return layout_info
            
        except Exception as e:
            print(f"Layout information extraction failed: {e}")
            return {}
    
    async def _extract_interactive_elements(self, page: Page) -> Dict:
        """Extract interactive elements and their behaviors"""
        try:
            interactive = await page.evaluate("""
                () => {
                    const interactive = {
                        clickable_elements: [],
                        form_elements: [],
                        hover_effects: [],
                        animations: []
                    };
                    
                    // Find clickable elements
                    document.querySelectorAll('a, button, [onclick], [role="button"], .clickable, [tabindex]').forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0) {
                            const styles = window.getComputedStyle(el);
                            interactive.clickable_elements.push({
                                tag: el.tagName.toLowerCase(),
                                text: el.textContent?.trim().substring(0, 50) || '',
                                class: el.className || '',
                                href: el.href || '',
                                cursor: styles.cursor,
                                position: {
                                    x: Math.round(rect.x),
                                    y: Math.round(rect.y),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                }
                            });
                        }
                    });
                    
                    // Find form elements
                    document.querySelectorAll('form').forEach(form => {
                        const formData = {
                            action: form.action || '',
                            method: form.method || 'get',
                            inputs: []
                        };
                        
                        form.querySelectorAll('input, textarea, select').forEach(input => {
                            formData.inputs.push({
                                type: input.type || 'text',
                                name: input.name || '',
                                placeholder: input.placeholder || '',
                                required: input.required || false
                            });
                        });
                        
                        interactive.form_elements.push(formData);
                    });
                    
                    // Check for potential hover effects (elements with :hover in CSS)
                    document.querySelectorAll('*').forEach(el => {
                        const styles = window.getComputedStyle(el);
                        if (styles.cursor === 'pointer' || el.tagName.toLowerCase() === 'a' || el.tagName.toLowerCase() === 'button') {
                            interactive.hover_effects.push({
                                tag: el.tagName.toLowerCase(),
                                class: el.className || '',
                                cursor: styles.cursor,
                                transition: styles.transition
                            });
                        }
                    });
                    
                    return interactive;
                }
            """)
            
            return interactive
            
        except Exception as e:
            print(f"Interactive elements extraction failed: {e}")
            return {}
    
    async def _analyze_dom_structure_enhanced(self, page: Page) -> Dict:
        """Enhanced DOM structure analysis with visual context"""
        try:
            structure = await page.evaluate("""
                () => {
                    const analysis = {
                        totalElements: document.querySelectorAll('*').length,
                        headings: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
                        images: document.querySelectorAll('img').length,
                        links: document.querySelectorAll('a').length,
                        forms: document.querySelectorAll('form').length,
                        inputs: document.querySelectorAll('input, textarea, select').length,
                        buttons: document.querySelectorAll('button, input[type="button"], input[type="submit"]').length,
                        sections: document.querySelectorAll('section, article, div').length,
                        navigation: document.querySelectorAll('nav, [role="navigation"]').length,
                        flexboxElements: 0,
                        gridElements: 0,
                        visualHierarchy: [],
                        colorDistribution: {},
                        fontUsage: {}
                    };
                    
                    // Count flexbox and grid layouts
                    const allElements = document.querySelectorAll('*');
                    const colorCounts = {};
                    const fontCounts = {};
                    
                    allElements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        
                        if (style.display === 'flex' || style.display === 'inline-flex') {
                            analysis.flexboxElements++;
                        }
                        if (style.display === 'grid' || style.display === 'inline-grid') {
                            analysis.gridElements++;
                        }
                        
                        // Track visual hierarchy by element size and position
                        if (rect.width > 100 && rect.height > 50) {
                            analysis.visualHierarchy.push({
                                tag: el.tagName.toLowerCase(),
                                area: rect.width * rect.height,
                                position: {
                                    x: Math.round(rect.x),
                                    y: Math.round(rect.y)
                                },
                                zIndex: style.zIndex
                            });
                        }
                        
                        // Track color usage
                        if (style.backgroundColor && style.backgroundColor !== 'rgba(0, 0, 0, 0)') {
                            colorCounts[style.backgroundColor] = (colorCounts[style.backgroundColor] || 0) + 1;
                        }
                        
                        // Track font usage
                        if (style.fontFamily) {
                            fontCounts[style.fontFamily] = (fontCounts[style.fontFamily] || 0) + 1;
                        }
                    });
                    
                    // Sort visual hierarchy by importance (size + position)
                    analysis.visualHierarchy.sort((a, b) => b.area - a.area);
                    analysis.visualHierarchy = analysis.visualHierarchy.slice(0, 20); // Top 20 elements
                    
                    // Get most common colors and fonts
                    analysis.colorDistribution = Object.entries(colorCounts)
                        .sort(([,a], [,b]) => b - a)
                        .slice(0, 10)
                        .reduce((obj, [color, count]) => ({ ...obj, [color]: count }), {});
                    
                    analysis.fontUsage = Object.entries(fontCounts)
                        .sort(([,a], [,b]) => b - a)
                        .slice(0, 5)
                        .reduce((obj, [font, count]) => ({ ...obj, [font]: count }), {});
                    
                    return analysis;
                }
            """)
            
            return structure
            
        except Exception as e:
            print(f"Enhanced DOM analysis failed: {e}")
            return {}
    
    async def _take_screenshot(self, page: Page, url: str) -> str:
        """Take full page screenshot with additional viewport screenshots"""
        try:
            # Generate filename based on URL
            domain = urlparse(url).netloc.replace('.', '_')
            timestamp = int(asyncio.get_event_loop().time())
            
            # Take full page screenshot
            full_screenshot = Path(settings.screenshots_path) / f"full_{domain}_{timestamp}.png"
            await page.screenshot(
                path=str(full_screenshot),
                full_page=True,
                type='png'
            )
            
            # Take viewport screenshot (what user sees immediately)
            viewport_screenshot = Path(settings.screenshots_path) / f"viewport_{domain}_{timestamp}.png"
            await page.screenshot(
                path=str(viewport_screenshot),
                full_page=False,
                type='png'
            )
            
            return str(full_screenshot)
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return None
    
    async def _extract_css(self, page: Page, url: str) -> List[str]:
        """Extract all CSS styles from the page with computed styles"""
        try:
            css_styles = []
            
            # Get inline styles
            inline_styles = await page.evaluate("""
                () => {
                    const styles = [];
                    const styleElements = document.querySelectorAll('style');
                    styleElements.forEach(style => {
                        if (style.textContent) {
                            styles.push(style.textContent);
                        }
                    });
                    return styles;
                }
            """)
            css_styles.extend(inline_styles)
            
            # Get external stylesheets
            stylesheets = await page.evaluate("""
                () => {
                    const links = [];
                    const linkElements = document.querySelectorAll('link[rel="stylesheet"]');
                    linkElements.forEach(link => {
                        if (link.href) {
                            links.push(link.href);
                        }
                    });
                    return links;
                }
            """)
            
            # Fetch external CSS
            for stylesheet_url in stylesheets:
                try:
                    absolute_url = urljoin(url, stylesheet_url)
                    async with aiohttp.ClientSession() as session:
                        async with session.get(absolute_url, timeout=10) as response:
                            if response.status == 200:
                                css_content = await response.text()
                                css_styles.append(css_content)
                except Exception as e:
                    print(f"Failed to fetch CSS from {stylesheet_url}: {e}")
            
            # Extract computed styles for key elements
            computed_styles = await page.evaluate("""
                () => {
                    const computedCSS = [];
                    const importantSelectors = [
                        'body', 'header', 'nav', 'main', 'section', 'article', 'footer',
                        '.container', '.content', '.wrapper', '.header', '.nav', '.menu'
                    ];
                    
                    importantSelectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach((el, index) => {
                            if (index < 3) { // Limit to first 3 of each type
                                const styles = window.getComputedStyle(el);
                                const relevantStyles = {
                                    selector: selector + (index > 0 ? `:nth-of-type(${index + 1})` : ''),
                                    display: styles.display,
                                    position: styles.position,
                                    width: styles.width,
                                    height: styles.height,
                                    margin: styles.margin,
                                    padding: styles.padding,
                                    backgroundColor: styles.backgroundColor,
                                    color: styles.color,
                                    fontSize: styles.fontSize,
                                    fontFamily: styles.fontFamily,
                                    border: styles.border,
                                    borderRadius: styles.borderRadius
                                };
                                computedCSS.push(relevantStyles);
                            }
                        });
                    });
                    
                    return computedCSS;
                }
            """)
            
            # Convert computed styles to CSS
            if computed_styles:
                computed_css = "/* Computed styles for key elements */\n"
                for style_obj in computed_styles:
                    selector = style_obj.pop('selector')
                    computed_css += f"{selector} {{\n"
                    for prop, value in style_obj.items():
                        if value and value != 'none' and value != 'auto':
                            css_prop = re.sub(r'([A-Z])', r'-\1', prop).lower()
                            computed_css += f"  {css_prop}: {value};\n"
                    computed_css += "}\n\n"
                css_styles.append(computed_css)
            
            return css_styles
            
        except Exception as e:
            print(f"CSS extraction failed: {e}")
            return []
    
    async def _extract_images(self, page: Page, url: str) -> List[str]:
        """Extract image URLs from the page with additional metadata"""
        try:
            images = await page.evaluate("""
                () => {
                    const imgs = [];
                    const imgElements = document.querySelectorAll('img');
                    imgElements.forEach(img => {
                        const rect = img.getBoundingClientRect();
                        if (img.src && img.src.startsWith('http') && rect.width > 0 && rect.height > 0) {
                            imgs.push({
                                src: img.src,
                                alt: img.alt || '',
                                width: rect.width,
                                height: rect.height,
                                loading: img.loading || 'eager'
                            });
                        }
                    });
                    
                    // Also check for background images
                    const elementsWithBg = document.querySelectorAll('*');
                    elementsWithBg.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const bgImage = style.backgroundImage;
                        if (bgImage && bgImage !== 'none') {
                            const match = bgImage.match(/url\(["']?([^"']*)["']?\)/);
                            if (match && match[1] && match[1].startsWith('http')) {
                                const rect = el.getBoundingClientRect();
                                imgs.push({
                                    src: match[1],
                                    alt: 'Background image',
                                    width: rect.width,
                                    height: rect.height,
                                    type: 'background'
                                });
                            }
                        }
                    });
                    
                    return [...new Set(imgs.map(img => img.src))]; // Remove duplicates, return just URLs for now
                }
            """)
            
            return images
            
        except Exception as e:
            print(f"Image extraction failed: {e}")
            return []
    
    async def _extract_fonts(self, page: Page) -> List[str]:
        """Extract font families used on the page"""
        try:
            fonts = await page.evaluate("""
                () => {
                    const fontFamilies = new Set();
                    
                    // Get computed styles for all elements
                    const elements = document.querySelectorAll('*');
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const fontFamily = style.fontFamily;
                        if (fontFamily) {
                            // Split by comma and clean up
                            fontFamily.split(',').forEach(font => {
                                const cleaned = font.trim().replace(/["']/g, '');
                                if (cleaned && !cleaned.includes('serif') && !cleaned.includes('sans-serif') && !cleaned.includes('monospace')) {
                                    fontFamilies.add(cleaned);
                                }
                            });
                        }
                    });
                    
                    return Array.from(fontFamilies);
                }
            """)
            
            return fonts
            
        except Exception as e:
            print(f"Font extraction failed: {e}")
            return []
    
    async def _extract_colors(self, page: Page) -> List[str]:
        """Extract dominant colors from the page"""
        try:
            colors = await page.evaluate("""
                () => {
                    const colors = new Set();
                    
                    // Get colors from computed styles
                    const elements = document.querySelectorAll('*');
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        
                        // Text colors
                        if (style.color && style.color !== 'rgba(0, 0, 0, 0)') {
                            colors.add(style.color);
                        }
                        
                        // Background colors
                        if (style.backgroundColor && style.backgroundColor !== 'rgba(0, 0, 0, 0)') {
                            colors.add(style.backgroundColor);
                        }
                        
                        // Border colors
                        if (style.borderColor && style.borderColor !== 'rgba(0, 0, 0, 0)') {
                            colors.add(style.borderColor);
                        }
                    });
                    
                    return Array.from(colors).slice(0, 20); // Limit to top 20 colors
                }
            """)
            
            return colors
            
        except Exception as e:
            print(f"Color extraction failed: {e}")
            return []
    
    async def _extract_meta_description(self, page: Page) -> Optional[str]:
        """Extract meta description"""
        try:
            return await page.evaluate("""
                () => {
                    const meta = document.querySelector('meta[name="description"]');
                    return meta ? meta.getAttribute('content') : null;
                }
            """)
        except:
            return None
    
    async def _extract_viewport_meta(self, page: Page) -> Optional[str]:
        """Extract viewport meta tag"""
        try:
            return await page.evaluate("""
                () => {
                    const meta = document.querySelector('meta[name="viewport"]');
                    return meta ? meta.getAttribute('content') : null;
                }
            """)
        except:
            return None 