import aiohttp
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from models import CloneMemory, ScrapeArtifacts, StylePalette
import re

class ZepMemoryStore:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.getzep.com/v2"
        self.session = None
        self.session_id = "agentic-cloner-session"
        
    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        return self.session
    
    async def create_memory_from_artifacts(self, artifacts: ScrapeArtifacts, url: str) -> CloneMemory:
        """
        Analyze artifacts and create structured memory
        """
        # Extract domain
        domain = url.split("//")[1].split("/")[0] if "//" in url else url.split("/")[0]
        
        # Analyze CSS for style palette
        style_palette = await self._extract_style_palette(artifacts.css_content)
        
        # Extract layout keywords
        layout_keywords = await self._extract_layout_keywords(artifacts.dom_html, artifacts.css_content)
        
        # Generate semantic summary
        semantic_summary = await self._generate_summary(artifacts)
        
        return CloneMemory(
            id=str(uuid.uuid4()),
            url=url,
            domain=domain,
            style_palette=style_palette,
            layout_keywords=layout_keywords,
            semantic_summary=semantic_summary
        )
    
    async def _extract_style_palette(self, css_content: str) -> StylePalette:
        """Extract color palette and typography from CSS"""
        # Extract colors using regex
        color_patterns = [
            r'#[0-9a-fA-F]{6}',  # hex colors
            r'#[0-9a-fA-F]{3}',   # short hex
            r'rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)',  # rgb
            r'rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)'  # rgba
        ]
        
        colors = set()
        for pattern in color_patterns:
            colors.update(re.findall(pattern, css_content, re.IGNORECASE))
        
        # Extract fonts
        font_matches = re.findall(r'font-family:\s*([^;}]+)', css_content, re.IGNORECASE)
        fonts = list(set([f.strip().strip('"\'') for f in font_matches[:3]]))
        
        # Determine layout type
        layout_type = "grid" if "grid" in css_content.lower() else "flex" if "flex" in css_content.lower() else "traditional"
        
        # Determine spacing
        spacing_scale = "tight" if "gap: 0" in css_content or "margin: 0" in css_content else "loose" if "gap: 2" in css_content else "normal"
        
        return StylePalette(
            primary_colors=list(colors)[:5],
            fonts=fonts,
            layout_type=layout_type,
            spacing_scale=spacing_scale
        )
    
    async def _extract_layout_keywords(self, dom_html: str, css_content: str) -> List[str]:
        """Extract layout-related keywords"""
        keywords = []
        
        # Check for common layout patterns
        if "header" in dom_html.lower():
            keywords.append("header")
        if "nav" in dom_html.lower():
            keywords.append("navigation")
        if "hero" in dom_html.lower() or "banner" in dom_html.lower():
            keywords.append("hero")
        if "sidebar" in dom_html.lower():
            keywords.append("sidebar")
        if "footer" in dom_html.lower():
            keywords.append("footer")
        if "grid" in css_content.lower():
            keywords.append("grid")
        if "flex" in css_content.lower():
            keywords.append("flexbox")
        if "card" in dom_html.lower():
            keywords.append("cards")
        
        return keywords[:10]  # Limit to top 10
    
    async def _generate_summary(self, artifacts: ScrapeArtifacts) -> str:
        """Generate semantic summary of the website"""
        # Simple extraction based on content
        title = artifacts.metadata.get("title", "")
        description = artifacts.metadata.get("description", "")
        
        # Extract main headings from DOM
        h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', artifacts.dom_html, re.IGNORECASE | re.DOTALL)
        main_heading = h1_matches[0] if h1_matches else ""
        
        summary_parts = []
        if title:
            summary_parts.append(f"Title: {title[:100]}")
        if description:
            summary_parts.append(f"Description: {description[:200]}")
        if main_heading:
            summary_parts.append(f"Main heading: {main_heading[:100]}")
        
        return " | ".join(summary_parts)[:500]
    
    async def upsert_memory(self, memory: CloneMemory) -> None:
        """Store memory in Zep"""
        session = await self._get_session()
        
        memory_data = {
            "memory_id": memory.id,
            "content": memory.semantic_summary,
            "metadata": {
                "url": memory.url,
                "domain": memory.domain,
                "style_palette": memory.style_palette.dict(),
                "layout_keywords": memory.layout_keywords,
                "created_at": memory.created_at.isoformat()
            }
        }
        
        try:
            response = await session.post(
                f"{self.base_url}/sessions/{self.session_id}/memory",
                json=memory_data
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to upsert memory: {str(e)}")
            # Continue without failing - memory is optional
    
    async def search_similar_styles(self, style_palette: StylePalette, limit: int = 5) -> List[CloneMemory]:
        """Search for memories with similar styles"""
        session = await self._get_session()
        
        # Create search query based on style characteristics
        search_query = f"colors: {' '.join(style_palette.primary_colors[:3])} layout: {style_palette.layout_type}"
        
        try:
            response = await session.post(
                f"{self.base_url}/sessions/{self.session_id}/memory/search",
                json={
                    "query": search_query,
                    "limit": limit,
                    "search_type": "similarity"
                }
            )
            
            if response.status == 200:
                results = await response.json()
                memories = []
                
                for result in results.get("results", []):
                    metadata = result.get("metadata", {})
                    if metadata:
                        memory = CloneMemory(
                            id=result.get("memory_id", ""),
                            url=metadata.get("url", ""),
                            domain=metadata.get("domain", ""),
                            style_palette=StylePalette(**metadata.get("style_palette", {})),
                            layout_keywords=metadata.get("layout_keywords", []),
                            semantic_summary=result.get("content", ""),
                            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat()))
                        )
                        memories.append(memory)
                
                return memories
            
        except Exception as e:
            print(f"Memory search failed: {str(e)}")
        
        return []  # Return empty list if search fails
    
    async def get_memory(self, memory_id: str) -> Optional[CloneMemory]:
        """Retrieve specific memory by ID"""
        # Implementation would depend on Zep's API for retrieving specific memories
        # For now, return None as fallback
        return None
    
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> None:
        """Update existing memory with new data"""
        # Implementation for updating memory
        pass 