from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, List, Literal, Any
from datetime import datetime
from enum import Enum
import uuid

# New Agentic Cloner enums and models
class StyleType(str, Enum):
    MODERN = "modern"
    MINIMAL = "minimal"  
    CORPORATE = "corporate"
    CREATIVE = "creative"

class StylePalette(BaseModel):
    primary_colors: List[str] = Field(max_items=5, default_factory=list)
    fonts: List[str] = Field(max_items=3, default_factory=list)
    layout_type: str = "traditional"  # "grid", "flex", "traditional"
    spacing_scale: str = "normal"  # "tight", "normal", "loose"

class ScrapeArtifacts(BaseModel):
    url: str
    dom_html: str
    css_content: str
    hero_image_bytes: bytes
    metadata: Dict[str, Any] = Field(default_factory=dict)
    image_info: Optional[Dict[str, Any]] = Field(default_factory=dict)
    scraped_at: datetime = Field(default_factory=datetime.now)

class CloneMemory(BaseModel):
    id: str
    url: str
    domain: str
    style_palette: StylePalette
    layout_keywords: List[str]
    semantic_summary: str = Field(max_length=500)
    html_final: Optional[str] = None
    performance_score: Optional[int] = Field(ge=0, le=100, default=None)
    created_at: datetime = Field(default_factory=datetime.now)

class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    total_cost_usd: float

# Enhanced existing models
class CloneOptions(BaseModel):
    """Options for website cloning"""
    include_images: bool = True
    include_fonts: bool = True
    mobile_responsive: bool = True
    extract_colors: bool = True
    max_wait_time: int = Field(default=90, ge=5, le=300)
    viewport_width: int = Field(default=1920, ge=320, le=3840)
    viewport_height: int = Field(default=1080, ge=240, le=2160)
    # New Agentic Cloner options
    target_style: StyleType = StyleType.MODERN
    include_animations: bool = True
    mobile_first: bool = True

class CloneRequest(BaseModel):
    """Request model for website cloning"""
    url: HttpUrl
    options: Optional[CloneOptions] = CloneOptions()

class ScrapedData(BaseModel):
    """Data extracted from the target website"""
    url: str
    title: Optional[str] = None
    html: str
    css: List[str] = []
    images: List[str] = []
    fonts: List[str] = []
    colors: List[str] = []
    screenshot_path: Optional[str] = None
    dom_structure: Optional[Dict] = None
    meta_description: Optional[str] = None
    viewport_meta: Optional[str] = None

class CloneStatus(BaseModel):
    """Status of a cloning operation"""
    id: str
    status: Literal["pending", "scraping", "processing", "generating", "complete", "error"]
    progress: int = Field(default=0, ge=0, le=100)
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None

class PrecisionMetrics(BaseModel):
    """Detailed precision metrics for website clone accuracy"""
    overall_precision: float = Field(default=0.0, ge=0.0, le=1.0)
    structure_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    content_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    styling_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    semantic_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    layout_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: Literal["low", "medium", "high"] = "medium"

class CloneResult(BaseModel):
    """Result of a website cloning operation"""
    id: str
    status: Literal["complete", "error"]
    original_url: str
    generated_html: Optional[str] = None
    generated_css: Optional[str] = None
    preview_url: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    precision_metrics: Optional[PrecisionMetrics] = None
    # Keep similarity_score for backwards compatibility
    similarity_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    # New Agentic Cloner fields
    artifacts_urls: Optional[Dict[str, str]] = None
    token_usage: Optional[TokenUsage] = None
    memory_id: Optional[str] = None
    similar_sites_found: Optional[int] = None

class CloneResponse(BaseModel):
    """Response for clone creation"""
    id: str
    status: str
    message: str
    estimated_time: Optional[int] = None
    # New Agentic Cloner fields
    success: bool = True
    html: Optional[str] = None
    preview_url: Optional[str] = None
    artifacts_urls: Optional[Dict[str, str]] = None
    processing_time: Optional[float] = None
    token_usage: Optional[TokenUsage] = None
    memory_id: Optional[str] = None
    similar_sites_found: Optional[int] = None

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    details: Optional[Dict] = None
    # New Agentic Cloner fields
    success: bool = False
    error_code: Optional[str] = None
    processing_time: Optional[float] = None

# In-memory storage for demo (replace with database in production)
clone_jobs: Dict[str, CloneStatus] = {}
clone_results: Dict[str, CloneResult] = {}

def generate_clone_id() -> str:
    """Generate a unique clone ID"""
    return str(uuid.uuid4())[:8] 