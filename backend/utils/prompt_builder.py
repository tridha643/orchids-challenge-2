import re
import base64
from typing import List
from models import ScrapeArtifacts, CloneMemory, StyleType, TokenUsage

class PromptBuilder:
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        
    def count_tokens(self, text: str) -> int:
        """Approximate token count (4 characters ≈ 1 token)"""
        return len(text) // 4
    
    async def build_prompt(
        self, 
        artifacts: ScrapeArtifacts, 
        similar_memories: List[CloneMemory], 
        target_style: StyleType
    ) -> str:
        """
        Build optimized prompt staying within token budget
        """
        
        # Start with base template
        prompt_parts = []
        
        # System prompt
        system_prompt = f"""You are an expert web developer specializing in modern, responsive website clones.

TASK: Create a complete, production-ready HTML file with inline CSS that recreates the provided website with a {target_style.value} aesthetic.

REQUIREMENTS:
- Single HTML file with inline CSS and JavaScript
- Fully responsive design (mobile-first)
- Modern CSS techniques (Grid, Flexbox, CSS Variables)
- Smooth animations and hover effects
- Semantic HTML structure
- Accessibility compliant (ARIA labels, alt text)
- Fast loading and optimized for performance
- No external dependencies

STYLE DIRECTION: {target_style.value.upper()}
- Modern: Clean lines, bold typography, vibrant colors, subtle shadows
- Minimal: Maximum white space, limited color palette, simple typography
- Corporate: Professional blues/grays, structured layout, conservative fonts
- Creative: Bold colors, unique layouts, experimental typography, animations
"""
        
        prompt_parts.append(system_prompt)
        
        # Add memory hints if available
        if similar_memories:
            memory_hints = self._build_memory_hints(similar_memories)
            prompt_parts.append(f"\nSITE MEMORY (similar designs to reference):\n{memory_hints}")
        
        # Add truncated CSS
        css_summary = self._truncate_css(artifacts.css_content)
        prompt_parts.append(f"\nORIGINAL CSS PATTERNS:\n{css_summary}")
        
        # Add simplified DOM
        dom_summary = self._simplify_dom(artifacts.dom_html)
        prompt_parts.append(f"\nDOM STRUCTURE:\n{dom_summary}")
        
        # Add compressed hero image
        hero_b64 = self._compress_image_for_prompt(artifacts.hero_image_bytes)
        if hero_b64:
            prompt_parts.append(f"\nHERO IMAGE (base64):\n{hero_b64}")
        
        # Add generation instructions
        generation_prompt = """
GENERATION INSTRUCTIONS:
1. Analyze the provided visual and structural elements
2. Create a modern interpretation matching the target style
3. Ensure all content is functional (working links, forms, etc.)
4. Include realistic placeholder content where needed
5. Optimize for Core Web Vitals (fast loading, minimal layout shift)
6. Add subtle micro-interactions and hover effects

OUTPUT: Complete HTML file with inline CSS. Start with <!DOCTYPE html> and end with </html>.
"""
        
        prompt_parts.append(generation_prompt)
        
        # Join and check token count
        full_prompt = "\n".join(prompt_parts)
        
        # Trim if over budget
        if self.count_tokens(full_prompt) > self.max_tokens:
            full_prompt = self._trim_to_budget(prompt_parts)
        
        return full_prompt
    
    def _build_memory_hints(self, memories: List[CloneMemory]) -> str:
        """Build concise hints from similar site memories"""
        hints = []
        
        for memory in memories[:3]:  # Top 3 similar sites
            hint = f"• {memory.domain}: {memory.style_palette.layout_type} layout, "
            hint += f"colors: {', '.join(memory.style_palette.primary_colors[:3])}, "
            hint += f"keywords: {', '.join(memory.layout_keywords[:3])}"
            hints.append(hint)
        
        return "\n".join(hints)
    
    def _truncate_css(self, css_content: str) -> str:
        """Keep most important CSS rules within token budget"""
        # Extract key selectors and their rules
        important_patterns = [
            r'body\s*{[^}]+}',
            r'\.hero[^{]*{[^}]+}',
            r'\.header[^{]*{[^}]+}',
            r'\.nav[^{]*{[^}]+}',
            r'\.container[^{]*{[^}]+}',
            r'\.grid[^{]*{[^}]+}',
            r'\.flex[^{]*{[^}]+}',
            r'@media[^{]*{[^}]+}',
            r'h[1-6][^{]*{[^}]+}',
            r'\.btn[^{]*{[^}]+}'
        ]
        
        extracted_rules = []
        for pattern in important_patterns:
            matches = re.findall(pattern, css_content, re.IGNORECASE | re.DOTALL)
            extracted_rules.extend(matches[:2])  # Max 2 per pattern
        
        # Add color and font declarations
        color_rules = re.findall(r'[^{]*{[^}]*(?:color|background)[^}]*}', css_content, re.IGNORECASE)
        font_rules = re.findall(r'[^{]*{[^}]*font[^}]*}', css_content, re.IGNORECASE)
        
        extracted_rules.extend(color_rules[:5])
        extracted_rules.extend(font_rules[:3])
        
        return "\n".join(extracted_rules[:20])  # Max 20 rules
    
    def _simplify_dom(self, dom_html: str) -> str:
        """Extract key structural elements from DOM"""
        # Remove content, keep structure
        simplified = re.sub(r'>\s*[^<>\s][^<>]*\s*<', '><', dom_html)
        
        # Extract key sections
        sections = []
        
        # Header/Nav
        header_match = re.search(r'<header[^>]*>.*?</header>', simplified, re.DOTALL | re.IGNORECASE)
        if header_match:
            sections.append("HEADER: " + header_match.group(0)[:200] + "...")
        
        nav_match = re.search(r'<nav[^>]*>.*?</nav>', simplified, re.DOTALL | re.IGNORECASE)
        if nav_match:
            sections.append("NAV: " + nav_match.group(0)[:200] + "...")
        
        # Main content areas
        main_match = re.search(r'<main[^>]*>.*?</main>', simplified, re.DOTALL | re.IGNORECASE)
        if main_match:
            sections.append("MAIN: " + main_match.group(0)[:300] + "...")
        
        # Hero/Banner sections
        hero_patterns = [r'<[^>]*class="[^"]*hero[^"]*"[^>]*>.*?</[^>]+>', 
                        r'<[^>]*class="[^"]*banner[^"]*"[^>]*>.*?</[^>]+>']
        
        for pattern in hero_patterns:
            hero_match = re.search(pattern, simplified, re.DOTALL | re.IGNORECASE)
            if hero_match:
                sections.append("HERO: " + hero_match.group(0)[:200] + "...")
                break
        
        # Footer
        footer_match = re.search(r'<footer[^>]*>.*?</footer>', simplified, re.DOTALL | re.IGNORECASE)
        if footer_match:
            sections.append("FOOTER: " + footer_match.group(0)[:200] + "...")
        
        return "\n".join(sections) if sections else simplified[:1000] + "..."
    
    def _compress_image_for_prompt(self, image_bytes: bytes) -> str:
        """Convert image to base64 with size limit"""
        try:
            # For prompt efficiency, we'll indicate presence but not include full base64
            # In a full implementation, you'd resize the image first
            b64_string = base64.b64encode(image_bytes).decode('utf-8')
            
            # Truncate to reasonable size for prompt (roughly 300 chars = ~75 tokens)
            if len(b64_string) > 300:
                return b64_string[:300] + "... [IMAGE TRUNCATED]"
            
            return b64_string
            
        except Exception:
            return "[IMAGE PROCESSING FAILED]"
    
    def _trim_to_budget(self, prompt_parts: List[str]) -> str:
        """Trim prompt parts to fit within token budget"""
        target_tokens = self.max_tokens - 500  # Safety margin
        
        # Priority order for trimming
        trim_order = [
            4,  # Hero image (index 4)
            3,  # DOM structure (index 3) 
            2,  # CSS patterns (index 2)
            1   # Memory hints (index 1)
        ]
        
        current_prompt = "\n".join(prompt_parts)
        
        for trim_index in trim_order:
            if self.count_tokens(current_prompt) <= target_tokens:
                break
                
            if trim_index < len(prompt_parts):
                # Progressively reduce size of this section
                section = prompt_parts[trim_index]
                if len(section) > 500:
                    prompt_parts[trim_index] = section[:500] + "... [TRUNCATED]"
                elif len(section) > 200:
                    prompt_parts[trim_index] = section[:200] + "... [TRUNCATED]"
                else:
                    prompt_parts[trim_index] = "[SECTION REMOVED FOR TOKEN BUDGET]"
                
                current_prompt = "\n".join(prompt_parts)
        
        return current_prompt 