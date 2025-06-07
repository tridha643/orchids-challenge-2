# 🌐 Website Cloner

AI-powered website cloning using advanced web scraping and machine learning. Enter any website URL and watch our AI recreate it with modern HTML & CSS.

## 🚀 Features

- **Advanced Web Scraping**: Uses Playwright for reliable browser automation
- **AI-Powered Generation**: Leverages OpenAI GPT-4o to generate clean, modern HTML/CSS
- **Responsive Design**: Automatically creates mobile-responsive clones
- **Real-time Progress**: Live status updates during the cloning process
- **Preview & Download**: View generated websites and download the code
- **Customizable Options**: Control what elements to include (images, fonts, colors)

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Playwright**: Browser automation for web scraping
- **OpenAI GPT-4o**: AI model for code generation
- **BeautifulSoup**: HTML parsing and analysis
- **Pydantic**: Data validation and settings management

### Frontend
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **React Hooks**: Modern React patterns

## 📋 Prerequisites

### Required API Keys

You'll need to obtain the following API key:

1. **OpenAI API Key** (Required)
   - Go to [OpenAI Platform](https://platform.openai.com/)
   - Sign up or log in to your account
   - Navigate to [API Keys](https://platform.openai.com/api-keys)
   - Create a new secret key
   - Copy the key (starts with `sk-...`)
   - You'll need GPT-4 access (may require adding payment method)

### Optional Services

2. **Redis** (Optional - for caching)
   - Local Redis installation, or
   - Cloud Redis service (Redis Cloud, AWS ElastiCache, etc.)
   - If not provided, caching will be disabled

## 🔧 Installation & Setup

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd orchids-challenge/backend
   ```

2. **Install Python dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   uv run playwright install chromium
   # Or: playwright install chromium
   ```

4. **Set up environment variables**
   Create a `.env` file in the backend directory:
   ```env
   # Required: OpenAI API Key
   OPENAI_API_KEY=sk-your-openai-api-key-here
   
   # Optional: Redis for caching
   REDIS_URL=redis://localhost:6379
   
   # Optional: CORS settings
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   
   # Optional: Browser settings
   HEADLESS_BROWSER=true
   ```

5. **Start the backend server**
   ```bash
   uv run python main.py
   # Or: python main.py
   ```
   
   The API will be available at `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:3000`

## 🎯 Usage

1. **Open the web interface** at `http://localhost:3000`

2. **Enter a website URL** you want to clone (e.g., `https://example.com`)

3. **Configure options** (optional):
   - Include images and fonts
   - Enable mobile responsiveness
   - Extract color palette
   - Set viewport size and wait time

4. **Click "Clone Website"** and wait for the AI to work its magic

5. **View results**:
   - Live preview of the cloned website
   - Generated HTML and CSS code
   - Copy code to clipboard
   - Compare with original

## 📊 API Endpoints

### Core Endpoints
- `POST /api/clone` - Start a new clone job
- `GET /api/clone/{id}` - Get clone job status
- `GET /api/clone/{id}/result` - Get clone results
- `GET /api/clone/{id}/preview` - View generated HTML
- `DELETE /api/clone/{id}` - Cancel a clone job

### Utility Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `GET /api/clone` - List recent jobs
- `POST /api/test` - Quick functionality test

## ⚙️ Configuration

### Environment Variables

#### Backend Configuration
```env
# API Keys
OPENAI_API_KEY=sk-...                    # Required: OpenAI API key

# Application Settings
CORS_ORIGINS=http://localhost:3000       # Allowed frontend origins
MAX_CLONE_TIME=120                       # Max processing time (seconds)
MAX_CONCURRENT_CLONES=5                  # Max simultaneous jobs

# Browser Settings
HEADLESS_BROWSER=true                    # Run browser in headless mode
BROWSER_TIMEOUT=30000                    # Browser timeout (milliseconds)

# Storage
ASSETS_STORAGE_PATH=./storage/assets     # Asset storage directory
SCREENSHOTS_PATH=./storage/screenshots   # Screenshot storage directory

# Optional: Redis
REDIS_URL=redis://localhost:6379         # Redis connection URL
```

### Clone Options
```json
{
  "include_images": true,      // Extract and include images
  "include_fonts": true,       // Extract and include fonts
  "mobile_responsive": true,   // Generate responsive design
  "extract_colors": true,      // Extract color palette
  "max_wait_time": 30,        // Max wait time for page load
  "viewport_width": 1920,     // Browser viewport width
  "viewport_height": 1080     // Browser viewport height
}
```

## 🔒 Security Considerations

1. **API Key Security**
   - Never commit API keys to version control
   - Use environment variables for all secrets
   - Rotate API keys regularly

2. **Rate Limiting**
   - OpenAI has usage limits based on your plan
   - Monitor your API usage and costs
   - Implement request throttling for production

3. **Content Filtering**
   - The system will attempt to clone any accessible website
   - Consider implementing content filtering for production use
   - Respect robots.txt and website terms of service

## 💰 Cost Estimation

### OpenAI API Costs (as of 2024)
- **GPT-4o**: ~$5 per 1M input tokens, ~$15 per 1M output tokens
- **Typical clone**: 2,000-8,000 tokens per request
- **Estimated cost**: $0.02-$0.10 per website clone

### Usage Tips
- Start with simple websites to test
- Use GPT-4o-mini for development (cheaper alternative)
- Monitor usage in OpenAI dashboard
- Set billing alerts to avoid surprises

## 🐛 Troubleshooting

### Common Issues

1. **"OpenAI API key not found"**
   - Ensure `OPENAI_API_KEY` is set in your `.env` file
   - Verify the key starts with `sk-`
   - Check the key is valid and has GPT-4 access

2. **Playwright browser issues**
   - Run `playwright install chromium` to install browsers
   - Check system dependencies for your OS
   - Try running with `HEADLESS_BROWSER=false` for debugging

3. **CORS errors in frontend**
   - Ensure backend is running on port 8000
   - Check `CORS_ORIGINS` includes your frontend URL
   - Verify both services are running

4. **Slow cloning performance**
   - Reduce `max_wait_time` for faster sites
   - Disable image/font extraction for speed
   - Use smaller viewport sizes

## 📈 Development

### Running Tests
```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Backend linting
cd backend
uv run ruff check

# Frontend linting
cd frontend
npm run lint
```

## 🚀 Production Deployment

### Backend (FastAPI)
- Use production ASGI server (Gunicorn + Uvicorn)
- Set up proper environment variables
- Configure Redis for caching
- Implement rate limiting and monitoring
- Use cloud storage for assets

### Frontend (Next.js)
- Build for production: `npm run build`
- Deploy to Vercel, Netlify, or your preferred platform
- Configure environment variables for API endpoints
- Set up CDN for static assets

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📞 Support

[Add support information here]

---

**Built with ❤️ using OpenAI GPT-4o, FastAPI, and Next.js**
