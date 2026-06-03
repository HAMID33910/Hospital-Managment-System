# Hospital Management System

A lightweight Django-based Hospital Management System with a simple frontend dashboard.

Features
- Patient, Doctor, Appointment, Room and Billing management
- REST API with JWT authentication
- Single-page dashboard using vanilla JS (see [templates/dashboard.html](templates/dashboard.html))

Requirements
- Python 3.10+

Libraries & Dependencies (4 pip installs)
The project requires the following Python packages:
1. **Django (6.0.4)** — Web framework
2. **djangorestframework** — REST API toolkit
3. **djangorestframework-simplejwt** — JWT token authentication
4. **django-cors-headers** — CORS support for API requests
5. **requests** — HTTP library for testing (optional, used in test_doctor_api.py)

Quick start (Windows)
1. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\Activate.ps1   # PowerShell
# or: venv\Scripts\activate.bat  # cmd
```

2. Install dependencies

Install all required packages one by one:
```powershell
pip install django
pip install djangorestframework
pip install djangorestframework-simplejwt
pip install django-cors-headers
pip install requests
```

Or install all at once:
```powershell
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers requests
```

3. Apply migrations and create a superuser

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

4. Run the development server

```powershell
python manage.py runserver
```

Open the dashboard at http://127.0.0.1:8000/ (frontend uses `static/` and `templates/`).

API usage
- API base: `http://127.0.0.1:8000/api`
- Common endpoints used by the frontend:
  - `GET /api/patients/` — list patients
  - `POST /api/patients/` — create patient
  - `GET /api/patients/<id>/` — patient details
  - `PATCH /api/patients/<id>/` — update patient
  - `POST /api/patients/<id>/admit/` — admit patient
  - `GET /api/rooms/available/` — available rooms

Authentication
- The project uses JWT tokens. Obtain tokens via the auth endpoint (check `hospital/urls.py` for the token URL). The frontend expects `access` token stored in `localStorage` as `access_token`.

Important files
- [hospital/models.py](hospital/models.py) — data models
- [hospital/serializers.py](hospital/serializers.py) — DRF serializers
- [templates/dashboard.html](templates/dashboard.html) — frontend dashboard HTML + JS
- [static/js/main.js](static/js/main.js) — frontend API client and helpers

Development notes
- After schema changes, run `makemigrations` and `migrate`.
- The project ships with a SQLite DB (`db.sqlite3`) for quick testing.

Contributing
- Fork the repo, create a feature branch, and open a pull request.

POWERED BY :
HAMID MEHMOOD
