import asyncio
import json
import re
from typing import Dict, Tuple, Optional
from datetime import datetime

from openai import AsyncOpenAI

from config import settings
from models import ScrapedData, CloneOptions

class LLMService:
    """Service for generating HTML/CSS using OpenAI GPT-4"""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
    async def generate_website_clone(
        self, 
        scraped_data: ScrapedData, 
        options: CloneOptions
    ) -> Tuple[str, str]:
        """
        Generate HTML and CSS based on scraped website data
        
        Returns:
            Tuple[str, str]: (generated_html, generated_css)
        """
        try:
            # Prepare the analysis context
            analysis_context = self._prepare_analysis_context(scraped_data, options)
            
            # Generate the website clone
            system_prompt = self._get_system_prompt()
            user_prompt = self._build_user_prompt(analysis_context)
            
            # Call OpenAI API
            response = await self._call_openai_api(system_prompt, user_prompt)
            
            # Parse and validate the response
            html_content, css_content = self._parse_response(response)
            
            return html_content, css_content
            
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")
    
    def _prepare_analysis_context(self, scraped_data: ScrapedData, options: CloneOptions) -> Dict:
        """Prepare structured context for the LLM"""
        
        # Summarize the HTML structure
        html_summary = self._summarize_html_structure(scraped_data.html)
        
        # Process CSS styles
        css_summary = self._summarize_css_styles(scraped_data.css)
        
        # Create color palette
        color_palette = self._process_color_palette(scraped_data.colors)
        
        context = {
            "original_url": scraped_data.url,
            "title": scraped_data.title,
            "meta_description": scraped_data.meta_description,
            "viewport_meta": scraped_data.viewport_meta,
            "html_structure": html_summary,
            "css_summary": css_summary,
            "color_palette": color_palette,
            "fonts": scraped_data.fonts[:10],  # Limit to top 10 fonts
            "images": scraped_data.images[:20],  # Limit to top 20 images
            "dom_analysis": scraped_data.dom_structure,
            "responsive_required": options.mobile_responsive,
            "viewport_size": {
                "width": options.viewport_width,
                "height": options.viewport_height
            }
        }
        
        return context
    
    def _summarize_html_structure(self, html: str) -> Dict:
        """Extract key structural elements from HTML"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style tags for cleaner analysis
            for script in soup(["script", "style"]):
                script.decompose()
            
            structure = {
                "main_sections": [],
                "navigation": [],
                "headings": [],
                "key_content": []
            }
            
            # Extract navigation elements
            nav_elements = soup.find_all(['nav', 'header'])
            for nav in nav_elements:
                links = nav.find_all('a')
                if links:
                    nav_text = [link.get_text(strip=True) for link in links[:10]]
                    structure["navigation"].extend(nav_text)
            
            # Extract headings
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            structure["headings"] = [h.get_text(strip=True) for h in headings[:10]]
            
            # Extract main content sections
            main_sections = soup.find_all(['main', 'section', 'article'])
            for section in main_sections:
                section_text = section.get_text(strip=True)[:200]  # First 200 chars
                if section_text:
                    structure["main_sections"].append(section_text)
            
            # Extract key content areas
            content_areas = soup.find_all(['div', 'p'], class_=re.compile(r'content|main|primary'))
            for area in content_areas[:5]:
                content_text = area.get_text(strip=True)[:150]
                if len(content_text) > 20:
                    structure["key_content"].append(content_text)
            
            return structure
            
        except Exception as e:
            return {"error": f"HTML parsing failed: {str(e)}"}
    
    def _summarize_css_styles(self, css_list: list) -> Dict:
        """Summarize key CSS patterns and styles"""
        
        combined_css = '\n'.join(css_list)
        
        summary = {
            "layout_patterns": [],
            "common_classes": [],
            "key_properties": {},
            "media_queries": []
        }
        
        try:
            # Extract layout patterns
            if 'display: flex' in combined_css or 'display:flex' in combined_css:
                summary["layout_patterns"].append("flexbox")
            if 'display: grid' in combined_css or 'display:grid' in combined_css:
                summary["layout_patterns"].append("grid")
            if 'float:' in combined_css:
                summary["layout_patterns"].append("float")
            
            # Extract common class patterns
            class_matches = re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', combined_css)
            common_classes = {}
            for cls in class_matches:
                common_classes[cls] = common_classes.get(cls, 0) + 1
            
            # Get most frequent classes
            sorted_classes = sorted(common_classes.items(), key=lambda x: x[1], reverse=True)
            summary["common_classes"] = [cls for cls, count in sorted_classes[:15]]
            
            # Extract media queries
            media_matches = re.findall(r'@media[^{]*', combined_css, re.IGNORECASE)
            summary["media_queries"] = media_matches[:5]
            
        except Exception as e:
            summary["error"] = f"CSS analysis failed: {str(e)}"
        
        return summary
    
    def _process_color_palette(self, colors: list) -> list:
        """Process and clean color palette"""
        cleaned_colors = []
        
        for color in colors:
            # Convert rgba to hex if possible, clean up color values
            if color.startswith('rgb'):
                try:
                    # Simple rgba to hex conversion for common cases
                    if 'rgba(0, 0, 0, 0)' not in color and 'rgba(255, 255, 255, 1)' not in color:
                        cleaned_colors.append(color)
                except:
                    pass
            elif color.startswith('#'):
                cleaned_colors.append(color)
            elif color in ['red', 'blue', 'green', 'white', 'black', 'gray', 'yellow', 'orange', 'purple', 'pink']:
                cleaned_colors.append(color)
        
        # Remove duplicates and limit
        return list(dict.fromkeys(cleaned_colors))[:10]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for OpenAI GPT-4"""
        return """You are an expert web developer and UI/UX designer specializing in creating pixel-perfect website clones. Your task is to analyze scraped website data and generate clean, modern HTML and CSS that recreates the visual design and layout.

CORE PRINCIPLES:
1. **Semantic HTML**: Use proper HTML5 semantic elements (header, nav, main, section, article, footer)
2. **Modern CSS**: Use flexbox, grid, and modern CSS features for layouts
3. **Responsive Design**: Ensure mobile-first responsive design with proper breakpoints
4. **Accessibility**: Include proper ARIA labels, alt texts, and semantic markup
5. **Performance**: Optimize for fast loading and clean code structure
6. **Visual Accuracy**: Match colors, fonts, spacing, and layout as closely as possible

TECHNICAL REQUIREMENTS:
- Generate complete, standalone HTML with embedded CSS
- Use CSS custom properties (variables) for consistent theming
- Implement proper responsive breakpoints (mobile, tablet, desktop)
- Include hover states and basic interactions
- Use modern CSS features (flexbox, grid, custom properties)
- Ensure cross-browser compatibility
- Add proper meta tags and viewport settings

OUTPUT FORMAT:
Provide your response in this exact format:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}}</title>
    <style>
        {{CSS_CONTENT}}
    </style>
</head>
<body>
    {{HTML_CONTENT}}
</body>
</html>
```

Focus on creating a visually accurate, modern, and responsive recreation of the original website."""
    
    def _build_user_prompt(self, context: Dict) -> str:
        """Build the user prompt with website context"""
        
        prompt = f"""
Please analyze this website data and create a pixel-perfect clone:

**WEBSITE INFORMATION:**
- Original URL: {context['original_url']}
- Title: {context['title']}
- Meta Description: {context['meta_description']}
- Viewport Meta: {context['viewport_meta']}

**HTML STRUCTURE ANALYSIS:**
- Main Sections: {context['html_structure'].get('main_sections', [])}
- Navigation: {context['html_structure'].get('navigation', [])}
- Headings: {context['html_structure'].get('headings', [])}
- Key Content: {context['html_structure'].get('key_content', [])}

**DESIGN CONTEXT:**
- Color Palette: {context['color_palette']}
- Fonts Used: {context['fonts']}
- Layout Patterns: {context['css_summary'].get('layout_patterns', [])}
- Common CSS Classes: {context['css_summary'].get('common_classes', [])}

**DOM ANALYSIS:**
{json.dumps(context['dom_analysis'], indent=2)}

**REQUIREMENTS:**
- Responsive Design: {context['responsive_required']}
- Target Viewport: {context['viewport_size']['width']}x{context['viewport_size']['height']}
- Include placeholder images for: {context['images'][:5]}

**INSTRUCTIONS:**
1. Create a modern, responsive clone that captures the visual essence of the original
2. Use the extracted colors and fonts to match the design aesthetic
3. Implement proper layout structure based on the DOM analysis
4. Include navigation elements and main content sections
5. Add proper responsive breakpoints for mobile, tablet, and desktop
6. Use placeholder content that matches the content structure of the original
7. Ensure the design is clean, modern, and professional

Generate the complete HTML with embedded CSS that recreates this website's design and layout.
"""
        
        return prompt
    
    async def _call_openai_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API with the prompts"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o which is faster and cheaper than GPT-4
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                max_tokens=4096,
                temperature=0.3,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")
    
    def _parse_response(self, response: str) -> Tuple[str, str]:
        """Parse OpenAI's response to extract HTML and CSS"""
        
        try:
            # Extract HTML from code blocks
            html_match = re.search(r'```html\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
            
            if html_match:
                full_html = html_match.group(1).strip()
                
                # Extract CSS from the style tag
                css_match = re.search(r'<style[^>]*>(.*?)</style>', full_html, re.DOTALL | re.IGNORECASE)
                css_content = css_match.group(1).strip() if css_match else ""
                
                return full_html, css_content
            else:
                # Fallback: treat entire response as HTML
                return response.strip(), ""
                
        except Exception as e:
            raise Exception(f"Failed to parse LLM response: {str(e)}")
    
    async def refine_generated_code(
        self, 
        original_html: str, 
        original_css: str, 
        feedback: str
    ) -> Tuple[str, str]:
        """Refine generated code based on feedback"""
        
        refinement_prompt = f"""
Please refine this generated HTML/CSS based on the following feedback:

**CURRENT HTML:**
```html
{original_html}
```

**CURRENT CSS:**
```css
{original_css}
```

**FEEDBACK:**
{feedback}

**INSTRUCTIONS:**
1. Address all points mentioned in the feedback
2. Improve the visual accuracy and responsiveness
3. Maintain clean, semantic code structure
4. Ensure cross-browser compatibility
5. Keep the same general layout and design approach

Provide the refined version in the same format as before.
"""
        
        system_prompt = "You are an expert web developer refining HTML/CSS code to improve visual accuracy and address specific feedback."
        
        response = await self._call_openai_api(system_prompt, refinement_prompt)
        
        return self._parse_response(response) 