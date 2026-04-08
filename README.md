# Sports Week Tournament

A full-stack web application to manage a galaxy-themed sports tournament.  
**8 Galaxies** compete across multiple sports. Admins record results; the live leaderboard updates automatically.

---

## Tech Stack

| Layer     | Technology                              |
|-----------|-----------------------------------------|
| Frontend  | React 19, Vite, TailwindCSS, React Query v5 |
| Backend   | Django 4.2, Django REST Framework, SimpleJWT |
| Database  | PostgreSQL 16                           |
| Container | Docker + Docker Compose                 |

---

## Project Structure

```
sports/
├── backend/                  # Django project
│   ├── sports_backend/       # Django settings, URLs, WSGI
│   ├── tournament/           # App: models, serializers, views, URLs
│   ├── manage.py
│   ├── seed.py               # Seed 8 galaxies + sample data
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # React 19 app
│   ├── src/
│   │   ├── api/client.js     # Axios + JWT interceptor
│   │   ├── context/          # AuthContext
│   │   ├── components/       # Navbar, Layout, Modal, Spinner…
│   │   └── pages/
│   │       ├── Leaderboard.jsx
│   │       ├── Matches.jsx
│   │       └── admin/        # Login, Dashboard, Galaxies, Sports, Matches
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

---

## Quick Start — Docker (recommended)

```bash
# 1. Clone / enter the project
cd sports

# 2. Start everything (DB + backend + frontend)
docker-compose up --build

# Services:
#   Frontend  → http://localhost:3000
#   Backend   → http://localhost:8000
#   DB        → localhost:5432
```

The `seed.py` script runs automatically on backend startup.  
Default admin credentials: **admin / admin123**

---

## Local Development Setup

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env — set DB_* credentials to match your local PostgreSQL

# Run migrations
python manage.py migrate

# Seed the database (creates admin user + 8 galaxies + sample matches)
python seed.py

# Start the dev server
python manage.py runserver
# → http://localhost:8000
```

### Frontend

```bash
cd frontend

# Install dependencies (requires Node 18+)
npm install

# Copy environment file
cp .env.example .env
# VITE_API_BASE_URL=http://localhost:8000  (default — Vite proxy handles /api)

# Start the dev server
npm run dev
# → http://localhost:5173
```

---

## API Reference

### Authentication
| Method | Endpoint              | Description              | Auth required |
|--------|-----------------------|--------------------------|---------------|
| POST   | `/api/auth/login/`    | Obtain JWT tokens        | No            |
| POST   | `/api/auth/refresh/`  | Refresh access token     | No            |

### Galaxies
| Method | Endpoint              | Description              | Auth required |
|--------|-----------------------|--------------------------|---------------|
| GET    | `/api/galaxies/`      | List all galaxies        | No            |
| POST   | `/api/galaxies/`      | Create galaxy            | Admin         |
| GET    | `/api/galaxies/{id}/` | Get single galaxy        | No            |
| PATCH  | `/api/galaxies/{id}/` | Update galaxy            | Admin         |
| DELETE | `/api/galaxies/{id}/` | Delete galaxy            | Admin         |

### Sports
| Method | Endpoint             | Description              | Auth required |
|--------|----------------------|--------------------------|---------------|
| GET    | `/api/sports/`       | List all sports          | No            |
| POST   | `/api/sports/`       | Create sport             | Admin         |
| PATCH  | `/api/sports/{id}/`  | Update sport             | Admin         |
| DELETE | `/api/sports/{id}/`  | Delete sport             | Admin         |

### Matches
| Method | Endpoint              | Description              | Auth required |
|--------|-----------------------|--------------------------|---------------|
| GET    | `/api/matches/`       | List matches (filterable)| No            |
| POST   | `/api/matches/`       | Create match             | Admin         |
| GET    | `/api/matches/{id}/`  | Get single match         | No            |
| PATCH  | `/api/matches/{id}/`  | Update result            | Admin         |
| DELETE | `/api/matches/{id}/`  | Delete match             | Admin         |

**Filter params for GET /api/matches/:** `sport=<id>`, `is_final=true`, `winner=<id>`

### Dashboard
| Method | Endpoint         | Description         | Auth required |
|--------|------------------|---------------------|---------------|
| GET    | `/api/dashboard/`| Admin stats summary | Admin         |

---

## Business Logic

- When a match **winner** is set, `points_awarded` are automatically added to that galaxy's `total_points`.
- If `is_final = true`, an additional **bonus** (default: 5 pts, configurable via `FINAL_BONUS_POINTS` env var) is included in the leaderboard display.
- Galaxy points are **recalculated from scratch** on every match save — prevents double-counting on edits.
- Changing or removing a winner correctly revokes the old winner's points.

---

## Environment Variables

### Backend (`backend/.env`)
```
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=sports_tournament
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
FINAL_BONUS_POINTS=5
```

### Frontend (`frontend/.env`)
```
VITE_API_BASE_URL=http://localhost:8000
```

---

## Default Seed Data

| Galaxies      |
|---------------|
| Andromeda     |
| Milky Way     |
| Triangulum    |
| Whirlpool     |
| Sombrero      |
| Pinwheel      |
| Black Eye     |
| Cartwheel     |

Sports seeded: Cricket, Football, Badminton, Table Tennis, Basketball  
Admin user: `admin` / `admin123`
