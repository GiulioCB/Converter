# MC Chart Converter

Converts Excel chart images to high-resolution PNG for the CBRE MC Builder tool.

## What this does
- Accepts image data (PNG from clipboard) via POST
- Upscales to 2400px using LANCZOS + sharpening
- Returns high-res PNG
- Serves the chart converter UI at /app (password protected)

## What this does NOT do
- No city data, no market data, no Excel files
- No authentication tokens or API keys
- No sensitive CBRE data passes through this server

## Security
- CORS restricted to claude.ai and claudeusercontent.com origins
- /app route protected by HTTP Basic Auth
- Password set via APP_PASSWORD environment variable (set in Render dashboard)

## Deployment
- Platform: Render.com (free tier)
- Build: `pip install -r requirements.txt`
- Start: `python converter_api.py`
- Set APP_PASSWORD environment variable in Render dashboard

## Setting the password
In Render dashboard → your service → Environment → add:
APP_PASSWORD = [your chosen password]
