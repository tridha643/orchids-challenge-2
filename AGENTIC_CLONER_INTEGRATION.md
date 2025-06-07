# Agentic Cloner v0.1 Integration

## 🚀 Overview

Your existing Website Cloner has been enhanced with **Agentic Cloner v0.1** - an AI-powered website cloning system with memory and style intelligence.

## ✨ New Features Added

### Backend Enhancements

1. **New Services**:
   - `BrowserbaseScraper` - Advanced web scraping with Browserbase
   - `SupabaseStorage` - Cloud storage for artifacts
   - `ZepMemoryStore` - AI memory for style intelligence
   - `ClaudeGenerator` - HTML generation with Claude 3.5 Sonnet
   - `PromptBuilder` - Optimized prompt construction
   - `ImageProcessor` - Hero image processing

2. **New Endpoint**: `/api/agentic-clone`
   - AI-powered cloning with style options
   - Memory-based similar site detection
   - Direct result return (no polling needed)

3. **Enhanced Models**:
   - `StyleType` enum (modern, minimal, corporate, creative)
   - `ScrapeArtifacts`, `CloneMemory`, `TokenUsage`
   - Extended `CloneOptions` with style preferences

### Frontend Enhancements

1. **Cloner Toggle**: Switch between Standard and Agentic modes
2. **Style Options**: Target style selection with descriptions
3. **Enhanced UI**: Modern toggle switches and better UX
4. **Direct Results**: Agentic cloner shows results immediately

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install anthropic>=0.7.8 supabase>=2.3.0
```

### 2. Environment Variables

Add these to your `.env` file:

```bash
# Agentic Cloner API Keys
BROWSERBASE_API_KEY=your_browserbase_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_service_key
ZEP_API_KEY=your_zep_api_key
ANTHROPIC_API_KEY=your_claude_api_key
GEMINI_API_KEY=your_gemini_fallback_key

# Optional Configuration
MAX_TOKENS=8000
COST_LIMIT_USD=0.10
TIMEOUT_SECONDS=25
SUPABASE_BUCKET_NAME=rawsites
TARGET_IMAGE_WIDTH=400
```

### 3. API Key Setup

1. **Browserbase**: Sign up at [browserbase.com](https://browserbase.com)
2. **Supabase**: Create project at [supabase.com](https://supabase.com)
3. **Zep**: Get API key from [getzep.com](https://getzep.com)
4. **Anthropic**: Get Claude API key from [console.anthropic.com](https://console.anthropic.com)

### 4. Run the Application

```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend (in another terminal)
cd frontend
npm run dev
```

## 🎯 How It Works

### Agentic Cloner Pipeline

1. **Scrape**: Browserbase extracts clean DOM, CSS, and screenshots
2. **Store**: Artifacts uploaded to Supabase for persistence
3. **Memory**: Zep analyzes style patterns and finds similar sites
4. **Generate**: Claude creates modern HTML with style intelligence
5. **Return**: Complete result with metrics and artifacts

### Style Intelligence

- **Memory System**: Learns from previous clones
- **Style Matching**: Finds similar designs for reference
- **Target Styles**: Modern, Minimal, Corporate, Creative
- **Smart Prompts**: Token-optimized with visual context

## 🔄 Usage

1. **Toggle Mode**: Choose between Standard or Agentic cloner
2. **Set Style**: Select target aesthetic (Modern, Minimal, etc.)
3. **Configure Options**: Animations, mobile-first, etc.
4. **Clone**: Get instant results with AI-powered generation

## 📊 Benefits

- **Faster Results**: Direct response vs polling
- **Better Quality**: AI-powered with style intelligence
- **Memory Learning**: Improves over time
- **Cost Tracking**: Token usage and cost monitoring
- **Artifact Storage**: Persistent cloud storage

## 🛠️ Fallbacks

- **Service Failures**: Graceful degradation to standard cloner
- **API Limits**: Token budget management
- **Error Handling**: Comprehensive error responses
- **Offline Mode**: Standard cloner always available

## 🚀 Next Steps

1. Set up API keys
2. Test with a simple website
3. Explore different style options
4. Monitor costs and performance
5. Scale based on usage patterns

---

**Emergency Mode**: If you need to disable Agentic features, simply toggle to "Standard" mode in the UI or comment out the Agentic endpoint in `main.py`. 