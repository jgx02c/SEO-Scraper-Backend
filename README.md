# SEO Scraper Backend

A powerful FastAPI-based backend service for web scraping and SEO analysis. This service provides a robust API for scraping websites, analyzing content, and generating SEO reports.

## Features

- 🔐 Secure authentication with JWT and API keys
- 🌐 Web scraping capabilities with Selenium and BeautifulSoup
- 📊 SEO analysis and reporting
- 🗄️ MongoDB and Supabase integration for data storage
- 🚀 FastAPI for high-performance API endpoints
- 🐳 Docker support for easy deployment

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── dependencies.py      # Dependency injection
├── controllers/         # Business logic handlers
│   ├── auth_controller.py
│   ├── user_controller.py
│   ├── website_controller.py
│   └── data_controller.py
├── models/             # Data models
│   ├── user.py
│   └── report.py
├── routes/             # API route definitions
│   ├── auth.py
│   ├── user.py
│   ├── website.py
│   └── data.py
├── utils/              # Utility functions
│   ├── security.py
│   ├── jwt_handler.py
│   ├── mongodb.py
│   └── supabase.py
└── scrape/             # Web scraping modules
    ├── crawler.py
    ├── scraper.py
    ├── cleaner.py
    └── generate_report.py
```

## Prerequisites

- Python 3.9+
- Redis server
- MongoDB
- Supabase account
- Docker (optional)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SEO-Scraper-Backend.git
cd SEO-Scraper-Backend
```

2. Create and activate a virtual environment:
```bash
# Mac/Linux
python3.9 -m venv venv
source venv/bin/activate

# Windows
python3.9 -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
MONGODB_URL=your_mongodb_url
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
JWT_SECRET=your_jwt_secret
API_KEY=your_api_key
```

## Running the Application

### Development Mode
```bash
uvicorn app.main:app --reload --workers 2 --loop uvloop --http httptools
```

### Production Mode
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Using Docker
```bash
docker build -t seo-scraper .
docker run -p 8000:8000 seo-scraper
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Authentication

The API supports two authentication methods:

1. **API Key Authentication**
   - Add `X-API-KEY: your_api_key` to request headers

2. **JWT Authentication**
   - Add `Authorization: Bearer your_jwt_token` to request headers

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

- **Joshua Goodman** - [@jgx02c](https://github.com/jgx02c)