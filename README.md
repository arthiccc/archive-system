# College Document Archive System

A web-based document management system for colleges to organize, search, and track administrative documents.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/arthiccc/archive-system)

> **Try it live!** Click the badge above to launch a fully functional development environment in GitHub Codespaces. No setup required - just click and start using the app in your browser.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.13 + Flask 3.1.2 |
| Database | PostgreSQL 17.7 |
| ORM | SQLAlchemy 2.0 + Flask-SQLAlchemy 3.1.1 |
| Auth | Flask-Login 0.6.3 |
| Forms | Flask-WTF 1.2.1 + WTForms 3.2.1 |
| Migrations | Flask-Migrate 4.0.5 |
| Cache | Redis 7.4.7 |
| Frontend | Jinja2 + Custom CSS (Dark theme) |
| Container | Docker + Docker Compose |

## Features

- Document upload with auto-filename title detection
- Category organization (Admissions, Finance, HR, Academics, etc.)
- Academic period tracking (Fall/Spring/Summer by year)
- Tags for flexible labeling
- Full-text search across document titles, content, and descriptions
- Automatic folder organization by period/category
- Document preview for PDF, DOC, XLS, images
- Audit logging for all actions (upload, edit, delete, download)
- Statistics dashboard with document counts and activity
- Trash/restore functionality for deleted documents
- REST API for programmatic access

## Try It Now

### Option 1: GitHub Codespaces (Recommended - No Setup)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/arthiccc/archive-system)

1. Click the badge above to launch GitHub Codespaces
2. Wait 2-3 minutes for the environment to build
3. The app will automatically start at port 5000
4. Open the forwarded port in your browser
5. Create an admin account at `/auth/login`

**Note:** Replace `arthiccc` with your GitHub username in the badge link.

### Option 2: Local Development

See the Quick Start section below.

## Prerequisites

- Docker 24+
- Docker Compose V2
- 2GB RAM minimum

## Quick Start

```bash
# Clone and enter directory
cd archive-system

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Build and start containers
docker compose up -d --build

# Initialize database with seed data
docker compose exec web python scripts/init-db.py

# Access the application
# Open http://localhost:5000
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| DB_PASSWORD | PostgreSQL password | Yes | - |
| DATABASE_URL | Full database connection string | No | Auto-built from DB_PASSWORD |
| SECRET_KEY | Flask secret key for sessions | Yes | - |
| FLASK_ENV | Environment mode | No | development |
| APP_DEBUG | Enable debug mode | No | true |
| UPLOAD_FOLDER | Document storage path | No | /data/docs |
| MAX_CONTENT_LENGTH | Max upload size (bytes) | No | 104857600 (100MB) |
| ALLOWED_EXTENSIONS | Comma-separated file types | No | pdf,doc,docx,xls,xlsx,ppt,pptx,txt,jpg,jpeg,png |
| SEARCH_RESULTS_PER_PAGE | Results per page | No | 25 |
| AUDIT_LOG_ENABLED | Enable audit logging | No | true |

### Initial Setup

On first run, visit `/auth/login` to create your admin account. The first user registered becomes the super admin.

## Usage

### Document Upload

1. Click "Upload Document" or navigate to `/documents/upload`
2. Select a file (max 100MB)
3. Choose category and academic period
4. Optionally add tags (comma-separated)
5. Title is auto-filled from filename

### Searching

1. Click "Search" in the header or visit `/search`
2. Enter keywords - searches titles, content, and descriptions
3. Filter by category, period, or tags
4. Results show relevance scoring

### Admin Tasks

- **Categories**: `/admin/categories` - Manage document categories
- **Periods**: `/admin/periods` - Manage academic periods (e.g., Fall 2025)
- **Tags**: `/admin/tags` - Manage document tags
- **Logs**: `/admin/logs` - View audit trail
- **Stats**: `/admin/stats` - View system statistics

## REST API

### Authentication

All API endpoints require authentication via session cookie (web) or Authorization header (future).

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/documents | List documents (paginated) |
| POST | /api/documents | Upload new document |
| GET | /api/documents/\<id\> | Get document details |
| PUT | /api/documents/\<id\> | Update document metadata |
| DELETE | /api/documents/\<id\> | Soft-delete document |
| GET | /api/search | Full-text search |
| GET | /api/categories | List categories |
| GET | /api/periods | List academic periods |
| GET | /api/tags | List tags |
| GET | /api/stats | Get system statistics |

### Example: Search API

```bash
curl "http://localhost:5000/api/search?q=transcript&category=3&period=5"
```

Response:
```json
{
  "results": [
    {
      "id": 123,
      "title": "Student Transcript",
      "category": "Academics",
      "period": "Fall 2024",
      "uploaded_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 25
}
```

## Project Structure

```
archive-system/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration classes
│   ├── models.py            # SQLAlchemy models
│   ├── extensions.py        # DB, LoginManager, CSRF
│   ├── api/
│   │   ├── __init__.py      # API blueprint
│   │   └── routes.py        # REST endpoints
│   ├── admin/
│   │   ├── routes.py        # Dashboard, stats, logs, etc.
│   │   └── forms.py         # Admin forms
│   ├── auth/
│   │   ├── routes.py        # Login/logout
│   │   └── forms.py         # Login form
│   ├── documents/
│   │   ├── routes.py        # CRUD, upload, download
│   │   ├── forms.py         # Upload/edit forms
│   │   └── services.py      # Text extraction, preview
│   ├── search/
│   │   └── routes.py        # Search logic
│   ├── static/
│   │   ├── css/
│   │   │   ├── admin.css    # Original Bootstrap overrides
│   │   │   └── design.css   # New dark theme
│   │   └── js/
│   │       └── admin.js     # View toggle, flash handling
│   └── templates/           # Jinja2 templates
│       ├── base.html        # Main layout
│       ├── auth/
│       ├── documents/
│       ├── search/
│       └── admin/
├── scripts/
│   ├── init-db.py           # Database initialization
│   └── seed-docs.py         # Generate test documents
├── data/                     # Uploaded documents (mounted volume)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Docker Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| web | custom (Python 3.13) | 5000 | Flask application |
| db | postgres:17-alpine | 5432 | PostgreSQL database |
| redis | redis:7.4-alpine | 6379 | Redis cache |

## Troubleshooting

### Containers won't start

```bash
# Check logs
docker compose logs

# Verify .env configuration
cat .env
```

### Database connection failed

```bash
# Ensure database is healthy
docker compose ps

# Restart services
docker compose restart web
```

### Password authentication failed

```bash
# Reset PostgreSQL password to match .env
docker compose exec db psql -U archive_admin -d archive_db \
  -c "ALTER USER archive_admin WITH PASSWORD 'your_password';"
```

### Clear all data and start fresh

```bash
docker compose down -v
docker compose up -d
docker compose exec web python scripts/init-db.py
```

## License

MIT License - Internal use only

## Support

For issues or questions, check the audit logs at `/admin/logs` or container logs with `docker compose logs web`.
