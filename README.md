# AI Resume Analyzer

A Django web application that analyzes resumes using AI, helping users get feedback on their resume content, structure, and fit for specific roles.

## Features

- Upload and parse resumes
- AI-powered analysis and feedback (via `ai_engine.py`)
- Web interface built with Django templates
- SQLite database for local development

## Tech Stack

- **Backend:** Django (Python)
- **Database:** SQLite (development)
- **AI Engine:** Custom analysis logic in `ai_engine.py`
- **Frontend:** Django templates (HTML/CSS)

## Project Structure

```
AI_RESUME_ANALYZER/
├── analyzer/           # Main Django app (models, views, logic)
├── config/              # Project settings (settings.py, urls.py, wsgi.py)
├── templates/            # HTML templates
├── ai_engine.py          # AI/analysis logic
├── app.py                # App entry point / helper script
├── db.sqlite3             # SQLite database
├── manage.py              # Django management script
├── requirements.txt        # Python dependencies
├── test_ai.py              # Tests for AI engine
└── .gitignore
```

## Getting Started

### Prerequisites

- Python 3.9+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Nameera29/AI_RESUME_ANALYZER.git
   cd AI_RESUME_ANALYZER
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (create a `.env` file):
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   # Add any AI API keys your ai_engine.py requires
   ```

5. Apply migrations:
   ```bash
   python manage.py migrate
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

7. Visit `http://127.0.0.1:8000/` in your browser.

## Running Tests

```bash
python manage.py test
# or, for the AI engine specifically
python test_ai.py
```

## Deployment

Before deploying to production:
- Set `DEBUG = False` in `config/settings.py`
- Configure `ALLOWED_HOSTS` properly
- Move all secrets to environment variables
- Switch from SQLite to a production database (e.g. PostgreSQL)
- Set up static file handling (`collectstatic`, WhiteNoise, etc.)

See platforms like Railway, Render, or Fly.io for straightforward Django hosting.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push to the branch and open a Pull Request


## Contact

Maintained by [Nameera29](https://github.com/Nameera29).
