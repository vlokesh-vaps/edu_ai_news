# edu-news-ticker

A production-ready FastAPI REST API that fetches real-time AI and Education news from multiple RSS feeds and returns concise, shortened headlines for a frontend breaking-news ticker.

## Features

- ✅ **FastAPI Framework**: Modern, fast, and easy-to-use Python web framework
- 📰 **Multi-Source RSS Feeds**: Aggregates news from:
  - Google News (AI Education)
  - Google News (EdTech)
  - OpenAI Blog
  - Google Blog
  - Bloomberg Technology News
- 🤖 **AI-Powered Headline Shortening**: Uses Groq API with Llama 3.3 70B to intelligently shorten headlines to ≤10 words
- 🔄 **Duplicate Detection**: Automatically removes duplicate headlines
- ⚡ **Error Handling**: Graceful handling of feed failures and API errors
- 📊 **Structured Responses**: Clean, consistent JSON responses
- 🛡️ **CORS Support**: Ready for frontend integration
- 🏥 **Health Checks**: Built-in monitoring endpoints
- 📝 **Comprehensive Logging**: Detailed logging for debugging and monitoring
- 📚 **Type Hints & Docstrings**: Production-grade code documentation

## Project Structure

```
edu_ai_news/
├── app/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI app setup & configuration
│   ├── config.py                # Environment configuration
│   ├── routes/
│   │   ├── __init__.py
│   │   └── news.py              # News API endpoints
│   └── services/
│       ├── __init__.py
│       ├── rss_service.py       # RSS feed fetching & processing
│       └── groq_service.py      # Groq API integration
├── .env                         # Environment variables (create this)
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Requirements

- Python 3.8+
- pip (Python package manager)

## Installation

1. **Clone the repository** (or navigate to the project directory):

```bash
cd C:\Users\Vaps\PycharmProjects\edu_ai_news
```

2. **Create a virtual environment** (recommended):

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:

```bash
# Copy .env file and add your Groq API key
cp .env .env.local
# Edit .env.local and add your GROQ_API_KEY
```

Get your Groq API key from: https://console.groq.com

## Running the Application

### Development Mode (with auto-reload)

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

### Production Mode (without auto-reload)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### 1. Health Check

```http
GET /
```

**Response (200 OK):**
```json
{
  "status": "running"
}
```

### 2. API Health & Info

```http
GET /api
```

**Response (200 OK):**
```json
{
  "status": "running",
  "service": "edu-news-ticker",
  "version": "1.0.0"
}
```

### 3. Get Shortened Headlines

```http
GET /api/news?limit=10
```

**Query Parameters:**
- `limit` (integer, optional): Number of news items to return (1-50). Default: 10

**Response (200 OK):**
```json
{
  "status": "success",
  "count": 10,
  "breaking_news": [
    "AI tutors improve student learning",
    "Google launches new classroom AI tools",
    "UNESCO releases AI education framework",
    "Microsoft advances AI in schools",
    "OpenAI expands education partnerships",
    "EdTech startups secure funding",
    "AI personalized learning gains traction",
    "Tech giants invest in education",
    "Online learning platforms evolve",
    "Digital skills become essential"
  ]
}
```

### 4. Get Full Headlines with Links

```http
GET /api/news/full?limit=5
```

**Response (200 OK):**
```json
{
  "status": "success",
  "count": 5,
  "news": [
    {
      "title": "Full headline about AI in education",
      "link": "https://example.com/article1"
    },
    {
      "title": "Another full news headline",
      "link": "https://example.com/article2"
    }
  ]
}
```

## Usage Examples

### cURL

```bash
# Get 5 shortened headlines
curl "http://localhost:8000/api/news?limit=5"

# Get 10 full headlines with links
curl "http://localhost:8000/api/news/full?limit=10"

# Health check
curl "http://localhost:8000/"
```

### Python (requests library)

```python
import requests

# Get shortened headlines
response = requests.get("http://localhost:8000/api/news?limit=5")
data = response.json()
print(data)

# Get full headlines
response = requests.get("http://localhost:8000/api/news/full?limit=10")
data = response.json()
print(data)
```

### JavaScript (fetch API)

```javascript
// Get shortened headlines
fetch('http://localhost:8000/api/news?limit=10')
  .then(response => response.json())
  .then(data => {
    console.log(data.breaking_news);
  });

// Get full headlines
fetch('http://localhost:8000/api/news/full?limit=5')
  .then(response => response.json())
  .then(data => {
    data.news.forEach(article => {
      console.log(`${article.title}: ${article.link}`);
    });
  });
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Logging Configuration
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
```

### Adding Custom RSS Feeds

To add custom RSS feeds, modify the `RSS_FEEDS` list in `app/services/rss_service.py`:

```python
RSS_FEEDS: List[str] = [
    "https://existing-feed.com/rss",
    "https://your-new-feed.com/rss",  # Add here
]
```

Or dynamically through the service:

```python
from app.services.rss_service import RSSService

service = RSSService()
service.add_feed("https://custom-feed.com/rss")
```

## API Documentation

Once the application is running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Code Architecture

### Service-Based Architecture

The application follows a clean, modular architecture:

- **Services Layer**: Business logic (RSSService, GroqService)
- **Routes Layer**: API endpoints (news.py)
- **Config Layer**: Environment and settings management
- **Main Layer**: Application setup and middleware

### Key Classes

#### `RSSService`
- Fetches news from multiple RSS feeds
- Handles duplicate detection
- Provides graceful error handling
- Allows dynamic feed management

#### `GroqService`
- Interfaces with Groq API
- Shortens headlines intelligently
- Provides fallback mechanisms
- Supports batch processing

#### `Settings`
- Loads configuration from environment
- Provides configuration validation
- Centralizes settings management

## Error Handling

The application handles various error scenarios:

- **Missing API Key**: Validates Groq API key on startup
- **Feed Failures**: Gracefully skips failed feeds and continues
- **Invalid Input**: Returns 400 Bad Request for invalid parameters
- **Server Errors**: Returns 500 Internal Server Error with descriptive message
- **Timeout Errors**: Logged and gracefully handled

## Logging

Logging is configured to display:
- Timestamp
- Logger name
- Log level
- Log message

Example log output:
```
2024-06-24 10:30:45,123 - app.services.rss_service - INFO - Fetching RSS feed: https://...
2024-06-24 10:30:47,456 - app.services.groq_service - INFO - Successfully shortened headline
```

## Performance Considerations

- RSS feeds are fetched sequentially (can be optimized with async)
- Headlines are shortened one at a time
- Results are not cached (consider adding Redis for production)
- Feed timeout should be configured for production

## Security Considerations

1. **API Key Management**: Store `GROQ_API_KEY` securely
2. **CORS**: Update `allow_origins` in production to specific domains
3. **Rate Limiting**: Consider adding rate limiting middleware
4. **Input Validation**: All inputs are validated
5. **Error Messages**: Avoid exposing sensitive information in errors

## Deployment

### Docker

Example Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Vercel

The project includes a `vercel.json` configuration for Vercel deployment.

### Heroku

```bash
heroku create edu-news-ticker
git push heroku main
heroku config:set GROQ_API_KEY=your_key_here
```

## Development Tips

1. **Enable Debug Logging**:
   ```bash
   LOG_LEVEL=DEBUG uvicorn app.main:app --reload
   ```

2. **Test Specific Endpoint**:
   ```bash
   curl -X GET "http://localhost:8000/api/news?limit=3"
   ```

3. **Monitor Logs**:
   Watch the console output for real-time logging

4. **Use FastAPI Docs**:
   Visit http://localhost:8000/docs for interactive testing

## Troubleshooting

### "GROQ_API_KEY environment variable is not set"

**Solution**: Create `.env` file with your Groq API key:

```bash
echo GROQ_API_KEY=your_key_here > .env
```

### "Failed to fetch feed" errors

**Solution**: 
- Check internet connection
- Verify RSS feed URL is correct
- Check feed URL is not behind authentication

### Headlines not shortened properly

**Solution**:
- Verify Groq API key is valid
- Check API quota has not been exceeded
- Enable debug logging to see detailed errors

### Module import errors

**Solution**:
```bash
pip install -r requirements.txt
```

## Future Enhancements

- [ ] Async RSS feed fetching
- [ ] Caching with Redis
- [ ] Rate limiting
- [ ] Database for feed history
- [ ] WebSocket for real-time updates
- [ ] Feed preference management
- [ ] Custom headline length configuration
- [ ] Multiple language support

## Contributing

Contributions are welcome! Please ensure:
- Code follows the existing style
- All functions have docstrings
- Type hints are used
- Error handling is comprehensive
- Logging is adequate

## License

MIT License

## Support

For issues or questions, refer to the API documentation at `http://localhost:8000/docs` after starting the server.

## Credits

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- RSS parsing with [feedparser](https://feedparser.readthedocs.io/)
- AI headlines with [Groq API](https://groq.com/)
- Environment management with [python-dotenv](https://github.com/theskumar/python-dotenv)

---

**Version**: 1.0.0  
**Created**: 2024  
**Author**: Senior Python Backend Engineer

