import anthropic
from typing import Dict, Any
import json
import os
import re
import requests
from urllib.parse import urljoin, urlparse

class ClaudeGenerator:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-4-sonnet"
        self.max_tokens = 8000
        
    async def generate_html(self, prompt: str, source_url: str = None) -> Dict[str, Any]:
        """
        Generate HTML using Claude with token tracking and CSS inlining
        """
        try:
            # Enhanced prompt to ensure CSS inlining
            enhanced_prompt = f"""
            {prompt}
            
            IMPORTANT: Create a complete, standalone HTML file that includes:
            1. All CSS styles inlined within <style> tags in the <head>
            2. Do NOT reference external CSS files or stylesheets
            3. Include all necessary styles directly in the HTML
            4. Make sure the page is fully styled and functional without any external dependencies
            5. Use modern CSS with responsive design
            """
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": enhanced_prompt
                }]
            )
            
            html_content = message.content[0].text
            
            # Extract HTML if wrapped in code blocks
            if "```html" in html_content:
                html_content = html_content.split("```html")[1].split("```")[0].strip()
            elif "```" in html_content:
                html_content = html_content.split("```")[1].split("```")[0].strip()
            
            # Additional cleanup: Remove any remaining external CSS references
            html_content = self._remove_external_css_references(html_content)
            
            # If source URL provided, try to fetch and inline any remaining CSS
            if source_url:
                html_content = await self._fetch_and_inline_css(html_content, source_url)
            
            # Calculate token usage and cost
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            
            # Claude pricing (as of Jan 2025)
            input_cost = (input_tokens / 1000) * 0.003  # $0.003 per 1K input tokens
            output_cost = (output_tokens / 1000) * 0.015  # $0.015 per 1K output tokens
            total_cost = input_cost + output_cost
            
            return {
                "html": html_content,
                "token_usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_cost_usd": round(total_cost, 4)
                }
            }
            
        except Exception as e:
            # Fallback to basic HTML template
            fallback_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Cloned Website</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; }}
                    .container {{ max-width: 1200px; margin: 0 auto; }}
                    .error {{ color: #dc3545; padding: 20px; background: #f8d7da; border-radius: 8px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error">
                        <h2>Generation Error</h2>
                        <p>Failed to generate HTML: {str(e)}</p>
                        <p>This is a fallback template.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return {
                "html": fallback_html,
                "token_usage": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost_usd": 0.0
                }
            }
    
    def _remove_external_css_references(self, html_content: str) -> str:
        """Remove external CSS link tags and @import statements"""
        # Remove <link> tags that reference CSS files
        html_content = re.sub(r'<link[^>]*rel=["\']stylesheet["\'][^>]*>', '', html_content, flags=re.IGNORECASE)
        
        # Remove @import statements from style blocks
        html_content = re.sub(r'@import[^;]+;', '', html_content, flags=re.IGNORECASE)
        
        return html_content
    
    async def _fetch_and_inline_css(self, html_content: str, source_url: str) -> str:
        """Fetch external CSS files and inline them"""
        try:
            # Find CSS link tags
            css_links = re.findall(r'<link[^>]*href=["\']([^"\']*\.css[^"\']*)["\'][^>]*>', html_content, re.IGNORECASE)
            
            inline_styles = []
            
            for css_url in css_links:
                try:
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(source_url, css_url)
                    
                    # Fetch CSS content
                    response = requests.get(absolute_url, timeout=10)
                    if response.status_code == 200:
                        css_content = response.text
                        inline_styles.append(css_content)
                except:
                    continue  # Skip failed CSS fetches
            
            # Remove link tags and add inlined styles
            html_content = self._remove_external_css_references(html_content)
            
            if inline_styles:
                # Insert styles before closing </head> tag
                combined_css = '\n'.join(inline_styles)
                style_block = f'<style>\n{combined_css}\n</style>'
                
                if '</head>' in html_content:
                    html_content = html_content.replace('</head>', f'{style_block}\n</head>')
                else:
                    # If no head tag, add one
                    html_content = f'<head>{style_block}</head>\n{html_content}'
            
            return html_content
            
        except Exception as e:
            print(f"Error inlining CSS: {e}")
            return html_content 