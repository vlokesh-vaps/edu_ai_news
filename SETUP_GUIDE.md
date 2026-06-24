# Quick Setup Guide for edu-news-ticker

This is a quick reference guide to get started with the application.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- A Groq API key (get it free at https://console.groq.com)

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

1. Open the `.env` file in the project root
2. Replace `your_groq_api_key_here` with your actual Groq API key
3. Save the file

```env
GROQ_API_KEY=gsk_your_actual_key_here
LOG_LEVEL=INFO
```

## Step 3: Run the Application

### Option A: Development Mode (recommended for testing)

```bash
uvicorn app.main:app --reload
```

This will start the server with auto-reload enabled. Any code changes will automatically restart the server.

### Option B: Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Step 4: Test the API

### Health Check
```bash
curl http://localhost:8000/
```

Expected response:
```json
{"status": "running"}
```

### Get Shortened Headlines
```bash
curl "http://localhost:8000/api/news?limit=5"
```

Expected response:
```json
{
  "status": "success",
  "count": 5,
  "breaking_news": [
    "AI tutors improve student learning",
    "Google launches classroom tools",
    ...
  ]
}
```

### Get Full Headlines with Links
```bash
curl "http://localhost:8000/api/news/full?limit=3"
```

## Step 5: Interactive API Documentation

Once the app is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive documentation where you can test the endpoints directly.

## Project Files Overview

```
edu_ai_news/
├── app/main.py                 # FastAPI app setup
├── app/config.py               # Configuration & env vars
├── app/routes/news.py          # API endpoints
├── app/services/
│   ├── rss_service.py         # RSS feed fetching
│   └── groq_service.py        # Groq API integration
├── .env                        # Environment variables (CREATE THIS)
├── requirements.txt            # Dependencies
└── README.md                   # Full documentation
```

## Key Features

✅ Fetches news from 5 major RSS feeds
✅ Removes duplicates automatically
✅ Shortens headlines to ≤10 words using Groq AI
✅ Includes full headlines with source links
✅ Comprehensive error handling
✅ Detailed logging
✅ CORS enabled for frontend integration
✅ Health check endpoints
✅ Beautiful interactive API docs

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api` | GET | API info |
| `/api/news` | GET | Get shortened headlines |
| `/api/news/full` | GET | Get full headlines with links |

All endpoints support `limit` query parameter (1-50, default 10).

## Troubleshooting

### "GROQ_API_KEY not set"
- Make sure `.env` file exists in the project root
- Ensure `GROQ_API_KEY=` line is present with your actual key
- Restart the application after editing `.env`

### "Failed to fetch feed"
- Check your internet connection
- Some RSS feeds may temporarily be unavailable
- The application will skip failed feeds and try others

### "ModuleNotFoundError"
- Run `pip install -r requirements.txt` again
- Make sure you're in the project directory
- Consider creating a virtual environment: `python -m venv venv`

### Headlines not getting shortened
- Check that your Groq API key is valid
- Verify you haven't exceeded your API quota
- Check the logs for detailed error messages

## Development Tips

1. **View Logs**: The application outputs detailed logs. Watch them in the console for debugging.

2. **Enable Debug Mode**:
   ```bash
   LOG_LEVEL=DEBUG uvicorn app.main:app --reload
   ```

3. **Add New RSS Feeds**: Edit `app/services/rss_service.py` and add URLs to `RSS_FEEDS` list.

4. **Test with Python**:
   ```python
   import requests
   response = requests.get('http://localhost:8000/api/news?limit=3')
   print(response.json())
   ```

## Architecture

The application follows a clean, modular architecture:

- **Services Layer**: Business logic (`RSSService`, `GroqService`)
- **Routes Layer**: API endpoints (`news.py`)
- **Config Layer**: Environment configuration
- **Main Layer**: FastAPI app setup

## Production Deployment

### Docker
Create a `Dockerfile` and deploy to any container platform.

### Heroku
```bash
git push heroku main
heroku config:set GROQ_API_KEY=your_key
```

### Vercel
Already configured in `vercel.json`.

## Next Steps

1. ✅ Install requirements
2. ✅ Configure `.env` with your Groq API key
3. ✅ Run the application
4. ✅ Test endpoints at http://localhost:8000/docs
5. ✅ Integrate with your frontend!

## Support

Refer to the main `README.md` for comprehensive documentation, examples, and troubleshooting guides.

---

**Happy coding! 🚀**

