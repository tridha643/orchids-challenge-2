# 🤖 Agentic Website Cloner v0.1

AI-powered autonomous website cloning using intelligent agents and advanced web scraping. Deploy smart agents that analyze, understand, and recreate websites with human-like decision-making and style intelligence.

## ✨ Features

### Core Agentic Capabilities
- **Dual Cloning Modes**: Toggle between Standard and Advanced Agentic cloning
- **AI Style Intelligence**: Memory-based style analysis and pattern recognition
- **Multi-Agent Architecture**: Specialized agents for scraping, analysis, design, and code generation
- **Intelligent Content Analysis**: Agents understand content hierarchy, layout patterns, and design principles
- **Adaptive Cloning Strategies**: Agents dynamically adjust their approach based on website complexity
- **Real-time Agent Communication**: Watch agents collaborate and make decisions in real-time

### Advanced AI Services
- **Browserbase Scraping**: Advanced web scraping with cloud browser automation
- **Claude 4 Sonnet Generation**: Premium HTML/CSS generation with contextual understanding
- **Zep Memory System**: AI memory for learning style patterns and improving over time
- **Supabase Storage**: Cloud artifact storage for screenshots, CSS, and DOM data
- **Style Target Selection**: Choose from Modern, Minimal, Corporate, or Creative aesthetics
- **Cost Tracking**: Real-time token usage and cost monitoring

### Smart Features
- **Memory Learning**: System improves by learning from previous successful clones
- **Similar Site Detection**: AI finds and references similar designs for better results
- **Direct Results**: Agentic mode provides instant results (no polling required)
- **Fallback Protection**: Graceful degradation to standard cloning if AI services fail
- **Token Optimization**: Smart prompt construction to minimize API costs

## 🛠️ Tech Stack

### Backend (Agent Runtime)
- **FastAPI**: High-performance agent orchestration framework
- **Playwright**: Browser automation for agent-controlled scraping
- **Browserbase**: Cloud browser infrastructure for advanced scraping
- **Claude 4 Sonnet**: Advanced AI reasoning for HTML/CSS generation
- **OpenAI GPT-4o**: Fallback reasoning engine for autonomous agents
- **Zep**: AI memory system for style intelligence and learning
- **Supabase**: Cloud storage for artifacts and persistent data
- **BeautifulSoup**: Agent-driven HTML parsing and analysis
- **Pydantic**: Agent configuration and data validation

### Frontend (Agent Interface)
- **Next.js 15**: Real-time agent monitoring dashboard
- **TypeScript**: Type-safe agent communication
- **Tailwind CSS**: Agent-generated UI components
- **React Hooks**: Agent state management

## 📋 Prerequisites & API Keys

### Required API Keys

**For Standard Cloning:**
- **OpenAI API Key** (Required)
  - Go to [OpenAI Platform](https://platform.openai.com/)
  - Create API key (starts with `sk-...`)
  - Need GPT-4 access for optimal results

**For Agentic Cloning (Enhanced Features):**
- **Browserbase API Key** (Required for advanced scraping)
  - Sign up at [browserbase.com](https://browserbase.com)
  - Get API key from dashboard

- **Anthropic API Key** (Required for Claude 3.5)
  - Get Claude API key from [console.anthropic.com](https://console.anthropic.com)
  - Need Claude 3.5 Sonnet access

- **Supabase Keys** (Required for storage)
  - Create project at [supabase.com](https://supabase.com)
  - Get Project URL and Service Key

- **Zep API Key** (Required for memory)
  - Get API key from [getzep.com](https://getzep.com)
  - Used for style intelligence and learning

**Optional:**
- **Gemini API Key** (Fallback option)
  - For additional AI model redundancy

### System Requirements
- **Python 3.8+** for backend
- **Node.js 18+** for frontend
- **Chrome/Chromium** browser (installed automatically by Playwright)

## 🔧 Installation & Setup

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd orchids-challenge
```

### Step 2: Backend Setup (Agent Runtime)

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Install Python dependencies**
   ```bash
   # Using uv (recommended - faster)
   uv sync
   
   # OR using pip (install base + agentic dependencies)
   pip install -r requirements.txt
   pip install anthropic>=0.7.8 supabase>=2.3.0
   ```

3. **Install Playwright browsers**
   ```bash
   # If using uv
   uv run playwright install chromium
   
   # If using pip
   playwright install chromium
   ```

4. **Create environment file**
   Create a `.env` file in the `backend` directory:
   ```env
   # Required: Standard Cloning
   OPENAI_API_KEY=sk-your-openai-api-key-here
   
   # Required: Agentic Cloning (Enhanced Features)
   BROWSERBASE_API_KEY=your_browserbase_key_here
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your_supabase_service_key
   ZEP_API_KEY=your_zep_api_key
   ANTHROPIC_API_KEY=your_claude_api_key
   
   # Optional: Fallback and Configuration
   GEMINI_API_KEY=your_gemini_fallback_key
   MAX_TOKENS=8000
   COST_LIMIT_USD=0.10
   TIMEOUT_SECONDS=25
   SUPABASE_BUCKET_NAME=rawsites
   TARGET_IMAGE_WIDTH=400
   
   # Optional: CORS settings for frontend
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   
   # Optional: Agent behavior settings
   MAX_CONCURRENT_AGENTS=3
   AGENT_TIMEOUT=180
   HEADLESS_BROWSER=true
   ```

5. **Start the agent backend**
   ```bash
   # If using uv
   uv run python main.py
   
   # If using pip
   python main.py
   ```
   
   ✅ **Backend running at**: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

### Step 3: Frontend Setup (Agent Dashboard)

1. **Open new terminal and navigate to frontend**
   ```bash
   cd ../frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Start the frontend**
   ```bash
   npm run dev
   ```
   
   ✅ **Frontend running at**: `http://localhost:3000`

## 🎯 Quick Start Usage

### Standard Mode (Basic AI Cloning)
1. **Open Agent Dashboard** → `http://localhost:3000`
2. **Select "Standard" mode** → Uses OpenAI GPT-4
3. **Enter Website URL** → Example: `https://example.com`
4. **Configure basic options** → Images, responsiveness, etc.
5. **Clone and wait** → Results via polling

### Agentic Mode (Advanced AI with Memory)
1. **Toggle to "Agentic" mode** → Enhanced AI capabilities
2. **Select Target Style** → Modern, Minimal, Corporate, Creative
3. **Configure advanced options** → Animations, mobile-first, etc.
4. **Deploy Agent Squad** → Instant results with AI reasoning
5. **Review Enhanced Results** → Generated code + AI decision logs

## 🤖 Agentic Pipeline

### How Agentic Cloning Works

1. **Advanced Scraping**: Browserbase extracts clean DOM, CSS, and screenshots
2. **Cloud Storage**: Artifacts uploaded to Supabase for persistence  
3. **Memory Analysis**: Zep analyzes style patterns and finds similar sites
4. **AI Generation**: Claude creates modern HTML with style intelligence
5. **Direct Results**: Complete response with metrics and artifacts

### Agent Types & Services

1. **Scraper Agent** (BrowserbaseScraper)
   - Advanced web navigation with cloud browsers
   - Intelligent element identification and clean extraction

2. **Memory Agent** (ZepMemoryStore)
   - Style pattern learning and recognition
   - Similar site detection for reference

3. **Design Agent** (ClaudeGenerator)
   - Advanced HTML/CSS generation with Claude 3.5
   - Contextual understanding of design principles

4. **Storage Agent** (SupabaseStorage)
   - Cloud artifact management and persistence
   - Screenshot and asset processing

## 📊 API Endpoints

### Standard Cloning
- `POST /api/clone` - Start standard clone job
- `GET /api/clone/{id}` - Get clone job status
- `GET /api/clone/{id}/result` - Get clone results

### Agentic Cloning (Enhanced)
- `POST /api/agentic-clone` - Advanced AI cloning with instant results
- `GET /api/agents/status` - Agent system health
- `GET /api/agents/{squad_id}/decisions` - AI decision history
- `GET /api/agents/{squad_id}/metrics` - Performance metrics

## ⚙️ Configuration

### Environment Variables
```env
# Required - Standard Mode
OPENAI_API_KEY=sk-...                    # OpenAI GPT-4 access

# Required - Agentic Mode
BROWSERBASE_API_KEY=...                  # Advanced scraping
ANTHROPIC_API_KEY=...                    # Claude 3.5 Sonnet
SUPABASE_URL=...                         # Cloud storage
SUPABASE_SERVICE_KEY=...                 # Storage access
ZEP_API_KEY=...                          # AI memory system

# Optional - Configuration
MAX_TOKENS=8000                          # Token limit per request
COST_LIMIT_USD=0.10                      # Cost protection limit
TIMEOUT_SECONDS=25                       # Request timeout
TARGET_IMAGE_WIDTH=400                   # Image processing size

# Optional - Agent Behavior
MAX_CONCURRENT_AGENTS=3                  # Max agents running
AGENT_TIMEOUT=180                        # Agent operation timeout
HEADLESS_BROWSER=true                    # Browser GUI setting
```

### Style Options
```json
{
  "cloner_type": "agentic",
  "target_style": "modern",              // modern|minimal|corporate|creative
  "style_options": {
    "animations": true,
    "mobile_first": true,
    "accessibility": true
  },
  "memory_enabled": true,
  "similar_sites": 3
}
```

## 💰 Cost Estimation

### Standard Mode (OpenAI)
- **GPT-4o**: ~$5 per 1M input tokens, ~$15 per 1M output tokens
- **Typical clone**: 2,000-8,000 tokens
- **Estimated cost**: $0.02-$0.10 per clone

### Agentic Mode (Premium AI)
- **Claude 3.5 Sonnet**: ~$3 per 1M input, ~$15 per 1M output tokens
- **Browserbase**: ~$0.002 per second of browser time
- **Supabase**: ~$0.021 per GB storage
- **Zep Memory**: ~$0.001 per operation
- **Total estimated cost**: $0.05-$0.30 per agentic clone

### Cost Optimization Tips
- Start with Standard mode for testing
- Use cost limits in environment variables
- Monitor token usage in dashboard
- Agentic mode provides better quality for the cost

## 🐛 Troubleshooting

### Backend Issues

**"API key not found" errors**
```bash
# Check all required keys are set
cd backend
grep -E "(OPENAI|BROWSERBASE|ANTHROPIC|SUPABASE|ZEP)" .env
```

**"Agentic features not working"**
```bash
# Verify agentic dependencies installed
pip list | grep -E "(anthropic|supabase)"

# Check API key validity
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/messages
```

**"Browserbase connection failed"**
- Ensure Browserbase API key is valid and has credits
- Check if Browserbase service is operational
- Fallback: Standard mode will still work

**"Memory system errors"**
- Verify Zep API key and quota
- Check Zep service status
- System gracefully degrades without memory

### Service Fallbacks

**If Agentic services fail:**
1. System automatically falls back to Standard mode
2. OpenAI GPT-4 handles generation
3. Basic Playwright handles scraping
4. Local storage used instead of Supabase

**Emergency Mode:**
- Toggle to "Standard" in UI
- Comment out agentic endpoint in `main.py`
- All core functionality remains available

## 📈 Development

### Running Tests
```bash
# Backend tests (both modes)
cd backend
uv run pytest
# OR: pytest

# Test specific agentic features
pytest tests/test_agentic.py

# Frontend tests
cd frontend
npm test
```

### Development Commands
```bash
# Backend with auto-reload
cd backend
uv run uvicorn main:app --reload

# Frontend development
cd frontend
npm run dev

# Monitor costs and usage
tail -f logs/token_usage.log
```

## 🚀 Production Deployment

### Backend (FastAPI)
- Use production ASGI server: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`
- Set all environment variables securely
- Configure proper CORS origins
- Set up monitoring for both modes
- Implement cost alerts and limits

### Frontend (Next.js)
- Build: `npm run build`
- Deploy to Vercel, Netlify, or your platform
- Configure API endpoint environment variables
- Set up monitoring for agentic features

### Scaling Considerations
- Browserbase: Monitor browser usage and costs
- Supabase: Set up proper database limits
- Zep: Monitor memory usage and retention
- Claude API: Track token usage and rate limits

## 🎯 Benefits of Agentic Mode

- ⚡ **Faster Results**: Direct response vs polling
- 🧠 **Better Quality**: AI-powered with style intelligence  
- 📚 **Memory Learning**: Improves over time with usage
- 💰 **Cost Tracking**: Real-time token usage monitoring
- ☁️ **Artifact Storage**: Persistent cloud storage
- 🎨 **Style Intelligence**: Learns and applies design patterns
- 🔄 **Fallback Protection**: Graceful degradation when needed

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📞 Support

[Add support information here]

---

**Built with 🤖 using Autonomous AI Agents, Claude 4 Sonnet, OpenAI GPT-4o, FastAPI, and Next.js**
