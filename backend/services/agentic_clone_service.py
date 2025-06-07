import asyncio
import time
import hashlib
from typing import Dict, Any, Optional
from models import CloneRequest, CloneResponse, ScrapeArtifacts, CloneMemory, TokenUsage
from services.browserbase_scraper import BrowserbaseScraper
from services.supabase_storage import SupabaseStorage
from services.zep_memory import ZepMemoryStore
from services.claude_generator import ClaudeGenerator
from utils.prompt_builder import PromptBuilder
from utils.image_utils import ImageProcessor
from config import settings

class AgenticCloneService:
    def __init__(self):
        # Initialize services
        self.scraper = None
        self.storage = None
        self.memory_store = None
        self.generator = None
        self.prompt_builder = None
        self.image_processor = None
        
    async def initialize(self):
        """Initialize all services"""
        print("🚀 Initializing Agentic Clone services...")
        
        self.scraper = BrowserbaseScraper(
            api_key=settings.browserbase_api_key,
            project_id=settings.browserbase_project_id
        )
        self.storage = SupabaseStorage(
            url=settings.supabase_url,
            key=settings.supabase_service_key,
            bucket_name=settings.supabase_bucket_name
        )
        
        # Make Zep memory optional
        if settings.zep_api_key:
            self.memory_store = ZepMemoryStore(api_key=settings.zep_api_key)
            print("✅ Zep memory service enabled")
        else:
            self.memory_store = None
            print("⚠️ Zep memory service disabled (no API key)")
            
        self.generator = ClaudeGenerator(api_key=settings.anthropic_api_key)
        self.prompt_builder = PromptBuilder(max_tokens=settings.max_tokens)
        self.image_processor = ImageProcessor(target_width=settings.target_image_width)
        
        print("✅ Agentic Clone services initialized")
    
    async def clone_website(self, request: CloneRequest) -> CloneResponse:
        """
        Main cloning pipeline - processes URL through complete Agentic workflow
        """
        start_time = time.time()
        url_str = str(request.url)
        url_hash = hashlib.md5(url_str.encode()).hexdigest()[:12]
        
        try:
            # Step 1: Scrape website
            print(f"[STEP 1] Scraping {url_str}")
            artifacts = await self.scraper.scrape_site(url_str)
            
            # Step 2: Process and upload artifacts
            print(f"[STEP 2] Processing artifacts")
            processed_image = await self.image_processor.process_hero_image(artifacts.hero_image_bytes)
            
            # Generate enhanced HTML with preserved CSS
            enhanced_html = await self._create_enhanced_html(artifacts, url_hash)
            
            upload_tasks = [
                self.storage.upload_file(artifacts.dom_html.encode(), f"{url_hash}/original.html"),
                self.storage.upload_file(artifacts.css_content.encode(), f"{url_hash}/styles.css"),
                self.storage.upload_file(enhanced_html.encode(), f"{url_hash}/enhanced.html"),
                self.storage.upload_file(processed_image, f"{url_hash}/hero.png")
            ]
            
            artifact_urls = await asyncio.gather(*upload_tasks)
            artifacts_dict = {
                "original": artifact_urls[0],
                "css": artifact_urls[1],
                "enhanced": artifact_urls[2],
                "hero": artifact_urls[3]
            }
            
            # Step 3: Memory operations (optional)
            similar_memories = []
            memory_id = None
            
            if self.memory_store:
                try:
                    print(f"[STEP 3] Memory operations")
                    memory = await self.memory_store.create_memory_from_artifacts(artifacts, url_str)
                    await self.memory_store.upsert_memory(memory)
                    similar_memories = await self.memory_store.search_similar_styles(memory.style_palette, limit=3)
                    memory_id = memory.id
                except Exception as memory_error:
                    print(f"⚠️ Memory operations failed: {memory_error}")
            else:
                print(f"[STEP 3] Memory operations skipped (service disabled)")
            
            # Step 4: Generate HTML with AI (optional if Anthropic key available)
            ai_generated_html = None
            token_usage = None
            
            if settings.anthropic_api_key:
                try:
                    print(f"[STEP 4] Generating AI-enhanced HTML")
                    prompt = await self.prompt_builder.build_prompt(
                        artifacts, 
                        similar_memories, 
                        request.options.target_style
                    )
                    
                    if self.prompt_builder.count_tokens(prompt) <= settings.max_tokens:
                        generation_result = await self.generator.generate_html(prompt, artifacts.url)
                        ai_generated_html = generation_result["html"]
                        token_usage_dict = generation_result["token_usage"]
                        
                        token_usage = TokenUsage(
                            input_tokens=token_usage_dict["input_tokens"],
                            output_tokens=token_usage_dict["output_tokens"],
                            total_cost_usd=token_usage_dict["total_cost_usd"]
                        )
                        
                        # Upload AI-generated version
                        ai_url = await self.storage.upload_file(ai_generated_html.encode(), f"{url_hash}/ai_generated.html")
                        artifacts_dict["ai_generated"] = ai_url
                    else:
                        print("⚠️ Content too large for AI generation")
                except Exception as ai_error:
                    print(f"⚠️ AI generation failed: {ai_error}")
            else:
                print(f"[STEP 4] AI generation skipped (no Anthropic key)")
            
            # Update memory with final HTML if available
            if self.memory_store and memory_id and ai_generated_html:
                try:
                    await self.memory_store.update_memory(memory_id, {"html_final": ai_generated_html})
                except Exception as update_error:
                    print(f"⚠️ Memory update failed: {update_error}")
            
            processing_time = time.time() - start_time
            print(f"[COMPLETE] Processed in {processing_time:.2f}s")
            
            # Use the enhanced HTML as the primary output
            final_html = ai_generated_html if ai_generated_html else enhanced_html
            
            # Create proper preview URL pointing to Supabase
            preview_url = artifacts_dict["enhanced"].replace("?", "")  # Remove query params for clean URL
            
            return CloneResponse(
                id=url_hash,
                status="complete",
                message="Clone completed successfully",
                success=True,
                html=final_html,
                preview_url=preview_url,
                artifacts_urls=artifacts_dict,
                processing_time=processing_time,
                token_usage=token_usage,
                memory_id=memory_id,
                similar_sites_found=len(similar_memories)
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            print(f"[ERROR] {error_msg} (after {processing_time:.2f}s)")
            
            return CloneResponse(
                id=url_hash,
                status="error",
                message=f"Clone failed: {error_msg}",
                success=False,
                processing_time=processing_time
            )
    
    async def _create_enhanced_html(self, artifacts: ScrapeArtifacts, url_hash: str) -> str:
        """
        Create an enhanced HTML version with preserved styling and fixed assets
        """
        # Clean up the HTML and preserve CSS
        html_content = artifacts.dom_html
        css_content = artifacts.css_content
        image_info = artifacts.image_info or {}
        
        # Clean up the HTML content and escape any problematic characters
        clean_html_content = self._extract_body_content(html_content)
        clean_css = self._optimize_css_comprehensive(css_content)
        
        # Process images for better embedding
        processed_html = self._process_images_in_html(clean_html_content, image_info, artifacts.url)
        
        # Create a complete HTML document with embedded CSS
        enhanced_html = f"""<!DOCTYPE html>
<html lang="{artifacts.metadata.get('lang', 'en')}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{artifacts.metadata.get('title', 'Cloned Website')}</title>
    <meta name="description" content="{artifacts.metadata.get('description', '')}">
    
    <!-- External CSS Links (preserved from original) -->
    {self._extract_external_css_links(html_content)}
    
    <!-- Comprehensive Preserved CSS -->
    <style>
        /* Reset and normalization */
        * {{
            box-sizing: border-box;
        }}
        
        html, body {{
            margin: 0;
            padding: 0;
            line-height: 1.6;
        }}
        
        /* COMPREHENSIVE ORIGINAL CSS - PRESERVED FROM SOURCE */
        {clean_css}
        
        /* Enhanced image handling */
        img {{
            max-width: 100%;
            height: auto;
            display: block;
        }}
        
        /* Background image preservation for elements with CSS backgrounds */
        {self._generate_background_css(image_info)}
        
        /* Fix for broken images with better styling */
        img[src=""], img:not([src]), img.image-placeholder {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border: 2px dashed #ddd;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            color: #666;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100px;
            position: relative;
        }}
        
        img.image-placeholder::before {{
            content: "\\uD83D\\uDDBC\\FE0F Image Not Found";
            font-size: 14px;
        }}
        
        /* Preserve layout and responsiveness */
        @media (max-width: 768px) {{
            body {{
                padding: 0;
                margin: 0;
            }}
            
            .container {{
                padding-left: 15px !important;
                padding-right: 15px !important;
            }}
        }}
    </style>
</head>
<body>
    {processed_html}
    
    <!-- Cloned with Agentic Cloner -->
    <script>
        console.log('\\uD83E\\uDD16 This website was cloned using Agentic Cloner v0.1');
        
        // Fix relative URLs
        document.querySelectorAll('a[href^="/"], a[href^="./"], a[href^="../"]').forEach(link => {{
            const originalHref = link.getAttribute('href');
            link.setAttribute('data-original-href', originalHref);
            link.href = '{artifacts.url}' + (originalHref.startsWith('/') ? originalHref : '/' + originalHref);
        }});
        
        // Enhanced image handling with better error fallbacks
        document.querySelectorAll('img').forEach(img => {{
            // Handle missing src attributes
            if (!img.src || img.src === '' || img.src === window.location.href) {{
                img.style.display = 'none';
                return;
            }}
            
            // Add error handling for broken images
            img.addEventListener('error', function() {{
                // Try to construct absolute URL if it's relative
                if (this.src.startsWith('/')) {{
                    const baseUrl = new URL('{artifacts.url}');
                    const newSrc = baseUrl.origin + this.src;
                    if (newSrc !== this.src) {{
                        this.src = newSrc;
                        return; // Give it one more try
                    }}
                }}
                
                // If still failing, use placeholder
                this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIiBzdHJva2U9IiNkZGQiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSIjNjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2UgTm90IEZvdW5kPC90ZXh0Pjwvc3ZnPg==';
                this.alt = 'Image not found';
                this.className += ' broken';
            }});
            
            // Load images with retry logic
            if (img.complete && img.naturalHeight === 0) {{
                img.dispatchEvent(new Event('error'));
            }}
        }});
        
        // Fix video elements
        document.querySelectorAll('video').forEach(video => {{
            video.addEventListener('error', function() {{
                this.style.display = 'none';
            }});
        }});
    </script>
</body>
</html>"""
        
        return enhanced_html
    
    def _extract_body_content(self, html_content: str) -> str:
        """Extract content from body tag or return full content if no body tag found"""
        try:
            # Simple extraction of body content
            start_body = html_content.find('<body')
            if start_body != -1:
                start_content = html_content.find('>', start_body) + 1
                end_body = html_content.rfind('</body>')
                if end_body != -1:
                    return html_content[start_content:end_body]
            
            # If no body tag found, return the content between html tags or full content
            start_html = html_content.find('<html')
            if start_html != -1:
                start_content = html_content.find('>', start_html) + 1
                end_html = html_content.rfind('</html>')
                if end_html != -1:
                    return html_content[start_content:end_html]
            
            return html_content
        except:
            return html_content
    
    def _optimize_css_comprehensive(self, css_content: str) -> str:
        """
        Comprehensive CSS optimization while preserving ALL styling
        """
        if not css_content:
            return ""
        
        # Minimal processing to preserve all styling
        css_lines = css_content.split('\n')
        cleaned_lines = []
        
        for line in css_lines:
            # Keep all CSS content but fix encoding issues
            line = line.rstrip()  # Only remove trailing whitespace
            
            # Fix character encoding issues
            line = line.replace('ðŸ¤–', '\\uD83E\\uDD16')  # Fix robot emoji
            line = line.replace('â€™', "'")  # Fix apostrophes  
            line = line.replace('â€œ', '"').replace('â€\\x9d', '"')  # Fix quotes
            line = line.replace('Â', ' ')  # Fix non-breaking spaces
            
            # Keep the line even if it's empty or a comment - preserve structure
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_external_css_links(self, html_content: str) -> str:
        """
        Extract and preserve external CSS link tags from original HTML
        """
        import re
        
        # Find all link tags for stylesheets
        link_pattern = r'<link[^>]*rel=["\']stylesheet["\'][^>]*>'
        links = re.findall(link_pattern, html_content, re.IGNORECASE)
        
        return '\n    '.join(links) if links else ''
    
    def _generate_background_css(self, image_info: dict) -> str:
        """
        Generate CSS for background images found in the page
        """
        if not image_info or 'backgroundImages' not in image_info:
            return ""
        
        background_css = []
        
        for bg_img in image_info['backgroundImages']:
            element_class = bg_img.get('element_class', '')
            element_id = bg_img.get('element_id', '')
            element_tag = bg_img.get('element_tag', 'div')
            extracted_url = bg_img.get('extracted_url', '')
            bg_size = bg_img.get('background_size', 'cover')
            bg_position = bg_img.get('background_position', 'center')
            bg_repeat = bg_img.get('background_repeat', 'no-repeat')
            
            # Create selector
            selector = element_tag
            if element_id:
                selector = f"#{element_id}"
            elif element_class:
                # Handle multiple classes safely
                try:
                    class_str = str(element_class).strip() if element_class else ''
                    classes = class_str.split() if class_str else []
                    if classes:
                        selector = '.' + '.'.join(classes)
                except:
                    pass  # Skip if class processing fails
            
            # Only add if we have a valid URL
            if extracted_url and extracted_url.startswith('http'):
                css_rule = f"""
        {selector} {{
            background-image: url('{extracted_url}') !important;
            background-size: {bg_size} !important;
            background-position: {bg_position} !important;
            background-repeat: {bg_repeat} !important;
        }}"""
                background_css.append(css_rule)
        
        return '\n'.join(background_css)
    
    def _process_images_in_html(self, html_content: str, image_info: dict, base_url: str) -> str:
        """
        Process images in HTML to fix broken links and preserve layout
        """
        if not image_info or 'images' not in image_info:
            return html_content
        
        import re
        from urllib.parse import urljoin
        
        processed_html = html_content
        
        # Create a mapping of original to absolute URLs
        image_mapping = {}
        for img in image_info['images']:
            original_src = img.get('original_src', '')
            absolute_src = img.get('absolute_src', '')
            if original_src and absolute_src:
                image_mapping[original_src] = absolute_src
        
        # Replace img src attributes with absolute URLs
        def replace_img_src(match):
            full_tag = match.group(0)
            src_match = re.search(r'src=["\']([^"\']*)["\']', full_tag)
            
            if src_match:
                original_src = src_match.group(1)
                if original_src in image_mapping:
                    absolute_src = image_mapping[original_src]
                    # Replace the src attribute with absolute URL
                    new_tag = re.sub(
                        r'src=["\'][^"\']*["\']',
                        f'src="{absolute_src}"',
                        full_tag
                    )
                    return new_tag
                elif original_src and not original_src.startswith('http') and not original_src.startswith('data:'):
                    # Handle relative URLs that weren't in our mapping
                    try:
                        absolute_url = urljoin(base_url, original_src)
                        new_tag = re.sub(
                            r'src=["\'][^"\']*["\']',
                            f'src="{absolute_url}"',
                            full_tag
                        )
                        return new_tag
                    except:
                        pass
            
            return full_tag
        
        # Process all img tags
        img_pattern = r'<img[^>]*>'
        processed_html = re.sub(img_pattern, replace_img_src, processed_html, flags=re.IGNORECASE)
        
        return processed_html
    
    def _optimize_css(self, css_content: str) -> str:
        """
        Legacy method - redirects to comprehensive version
        """
        return self._optimize_css_comprehensive(css_content)
    
    async def close(self):
        """Cleanup all services"""
        print("🧹 Cleaning up Agentic Clone services...")
        
        if self.scraper:
            await self.scraper.close()
        if self.storage:
            await self.storage.close()
        
        print("✅ Agentic Clone services cleaned up")

# Global service instance
agentic_clone_service = AgenticCloneService() 