import re
import html
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup, Comment
from difflib import SequenceMatcher
import hashlib

class PrecisionCalculator:
    """
    Calculate precision metrics comparing original scraped HTML with AI-generated HTML
    """
    
    def __init__(self):
        self.weights = {
            'structure': 0.3,     # DOM structure similarity
            'content': 0.25,      # Text content similarity  
            'styling': 0.2,       # CSS classes and inline styles
            'semantic': 0.15,     # Semantic HTML elements
            'layout': 0.1         # Basic layout patterns
        }
    
    def calculate_precision(self, original_html: str, generated_html: str) -> Dict[str, float]:
        """
        Calculate comprehensive precision metrics
        
        Args:
            original_html: The original scraped HTML
            generated_html: The AI-generated HTML
            
        Returns:
            Dict containing various precision metrics
        """
        try:
            # Parse both HTML documents
            original_soup = BeautifulSoup(original_html, 'html.parser')
            generated_soup = BeautifulSoup(generated_html, 'html.parser')
            
            # Remove comments and scripts for cleaner comparison
            original_soup = self._clean_soup(original_soup)
            generated_soup = self._clean_soup(generated_soup)
            
            # Calculate individual metrics
            structure_score = self._calculate_structure_similarity(original_soup, generated_soup)
            content_score = self._calculate_content_similarity(original_soup, generated_soup)
            styling_score = self._calculate_styling_similarity(original_soup, generated_soup)
            semantic_score = self._calculate_semantic_similarity(original_soup, generated_soup)
            layout_score = self._calculate_layout_similarity(original_soup, generated_soup)
            
            # Calculate weighted overall score
            overall_score = (
                structure_score * self.weights['structure'] +
                content_score * self.weights['content'] +
                styling_score * self.weights['styling'] +
                semantic_score * self.weights['semantic'] +
                layout_score * self.weights['layout']
            )
            
            return {
                'overall_precision': round(overall_score, 3),
                'structure_similarity': round(structure_score, 3),
                'content_similarity': round(content_score, 3),
                'styling_similarity': round(styling_score, 3),
                'semantic_similarity': round(semantic_score, 3),
                'layout_similarity': round(layout_score, 3),
                'confidence': self._calculate_confidence(original_soup, generated_soup)
            }
            
        except Exception as e:
            print(f"Error calculating precision: {e}")
            return {
                'overall_precision': 0.0,
                'structure_similarity': 0.0,
                'content_similarity': 0.0,
                'styling_similarity': 0.0,
                'semantic_similarity': 0.0,
                'layout_similarity': 0.0,
                'confidence': 'low',
                'error': str(e)
            }
    
    def _clean_soup(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove scripts, comments, and other noise for cleaner comparison"""
        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Remove empty text nodes and normalize whitespace
        for element in soup.find_all(string=True):
            if element.strip():
                element.replace_with(re.sub(r'\s+', ' ', element.strip()))
            else:
                element.extract()
        
        return soup
    
    def _calculate_structure_similarity(self, original: BeautifulSoup, generated: BeautifulSoup) -> float:
        """Calculate DOM structure similarity"""
        try:
            # Get tag structure (element types and nesting)
            original_structure = self._extract_tag_structure(original)
            generated_structure = self._extract_tag_structure(generated)
            
            # Compare using sequence matching
            similarity = SequenceMatcher(None, original_structure, generated_structure).ratio()
            
            # Also compare element counts
            original_tags = [tag.name for tag in original.find_all()]
            generated_tags = [tag.name for tag in generated.find_all()]
            
            original_counts = {tag: original_tags.count(tag) for tag in set(original_tags)}
            generated_counts = {tag: generated_tags.count(tag) for tag in set(generated_tags)}
            
            count_similarity = self._calculate_dict_similarity(original_counts, generated_counts)
            
            return (similarity + count_similarity) / 2
            
        except Exception:
            return 0.0
    
    def _calculate_content_similarity(self, original: BeautifulSoup, generated: BeautifulSoup) -> float:
        """Calculate text content similarity"""
        try:
            # Extract all text content
            original_text = self._extract_text_content(original)
            generated_text = self._extract_text_content(generated)
            
            if not original_text and not generated_text:
                return 1.0
            if not original_text or not generated_text:
                return 0.0
            
            # Calculate text similarity
            similarity = SequenceMatcher(None, original_text, generated_text).ratio()
            
            # Also check for key phrases preservation
            original_phrases = self._extract_key_phrases(original_text)
            generated_phrases = self._extract_key_phrases(generated_text)
            
            phrase_preservation = len(original_phrases.intersection(generated_phrases)) / max(len(original_phrases), 1)
            
            return (similarity + phrase_preservation) / 2
            
        except Exception:
            return 0.0
    
    def _calculate_styling_similarity(self, original: BeautifulSoup, generated: BeautifulSoup) -> float:
        """Calculate CSS classes and styling similarity"""
        try:
            # Extract class attributes
            original_classes = self._extract_classes(original)
            generated_classes = self._extract_classes(generated)
            
            class_similarity = self._calculate_set_similarity(original_classes, generated_classes)
            
            # Extract inline styles
            original_styles = self._extract_inline_styles(original)
            generated_styles = self._extract_inline_styles(generated)
            
            style_similarity = self._calculate_dict_similarity(original_styles, generated_styles)
            
            return (class_similarity + style_similarity) / 2
            
        except Exception:
            return 0.0
    
    def _calculate_semantic_similarity(self, original: BeautifulSoup, generated: BeautifulSoup) -> float:
        """Calculate semantic HTML elements similarity"""
        try:
            semantic_tags = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer', 
                           'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li']
            
            original_semantic = {tag: len(original.find_all(tag)) for tag in semantic_tags}
            generated_semantic = {tag: len(generated.find_all(tag)) for tag in semantic_tags}
            
            return self._calculate_dict_similarity(original_semantic, generated_semantic)
            
        except Exception:
            return 0.0
    
    def _calculate_layout_similarity(self, original: BeautifulSoup, generated: BeautifulSoup) -> float:
        """Calculate basic layout pattern similarity"""
        try:
            # Check for common layout patterns
            layout_indicators = ['container', 'wrapper', 'header', 'footer', 'sidebar', 'content']
            
            original_layout = sum(1 for indicator in layout_indicators 
                                if original.find(class_=re.compile(indicator, re.I)))
            generated_layout = sum(1 for indicator in layout_indicators 
                                 if generated.find(class_=re.compile(indicator, re.I)))
            
            if original_layout + generated_layout == 0:
                return 1.0
            
            return min(original_layout, generated_layout) / max(original_layout, generated_layout)
            
        except Exception:
            return 0.0
    
    def _calculate_confidence(self, original: BeautifulSoup, generated: BeautifulSoup) -> str:
        """Calculate confidence level of the precision measurement"""
        try:
            original_size = len(str(original))
            generated_size = len(str(generated))
            
            # More complex documents get lower confidence
            if original_size > 50000 or generated_size > 50000:
                return 'low'
            elif original_size > 20000 or generated_size > 20000:
                return 'medium'
            else:
                return 'high'
                
        except Exception:
            return 'low'
    
    def _extract_tag_structure(self, soup: BeautifulSoup) -> List[str]:
        """Extract hierarchical tag structure"""
        structure = []
        
        def traverse(element, depth=0):
            if hasattr(element, 'name') and element.name:
                structure.append(f"{'  ' * depth}{element.name}")
                for child in element.children:
                    traverse(child, depth + 1)
        
        traverse(soup)
        return structure
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content"""
        text = soup.get_text()
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text.lower()
    
    def _extract_key_phrases(self, text: str) -> set:
        """Extract key phrases from text"""
        # Simple approach: extract words longer than 3 characters
        words = re.findall(r'\b\w{4,}\b', text.lower())
        return set(words)
    
    def _extract_classes(self, soup: BeautifulSoup) -> set:
        """Extract all CSS classes"""
        classes = set()
        for element in soup.find_all(class_=True):
            if isinstance(element['class'], list):
                classes.update(element['class'])
            else:
                classes.add(element['class'])
        return classes
    
    def _extract_inline_styles(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Extract inline style properties"""
        styles = {}
        for element in soup.find_all(style=True):
            style_text = element['style']
            # Extract CSS properties
            properties = re.findall(r'(\w+(?:-\w+)*)\s*:', style_text)
            for prop in properties:
                styles[prop] = styles.get(prop, 0) + 1
        return styles
    
    def _calculate_set_similarity(self, set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between two sets"""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0
    
    def _calculate_dict_similarity(self, dict1: Dict, dict2: Dict) -> float:
        """Calculate similarity between two dictionaries with numeric values"""
        all_keys = set(dict1.keys()).union(set(dict2.keys()))
        
        if not all_keys:
            return 1.0
        
        similarity_sum = 0.0
        for key in all_keys:
            val1 = dict1.get(key, 0)
            val2 = dict2.get(key, 0)
            
            if val1 == 0 and val2 == 0:
                similarity_sum += 1.0
            elif val1 == 0 or val2 == 0:
                similarity_sum += 0.0
            else:
                similarity_sum += min(val1, val2) / max(val1, val2)
        
        return similarity_sum / len(all_keys)


# Global precision calculator instance
precision_calculator = PrecisionCalculator() 