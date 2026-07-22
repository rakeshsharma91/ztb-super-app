# ZTB Super App
> Zero Trust Branch Assessment & POV Planning Tool

---

## Overview

**ZTB Super App** is an internal web application built for Zscaler Sales Engineers and Solution Consultants to streamline the delivery of **Zero Trust Branch (ZTB)** customer engagements. It provides a centralized platform to run structured customer assessments, manage curated libraries of Value Propositions, Assets, Test Cases, POV Steps, and Roadblocks, and automatically generate polished Excel reports — all from a clean, modern browser-based interface.

---

## Features

- **Admin Dashboard** with 7 distinct management sections
- **Inline-Editable Library Tables** for Value Props, Assets, Test Cases, POV Planner, and Roadblocks — edit any cell in place without modals
- **Dynamic Columns** — add, delete, rename, and reorder columns via drag-and-drop on any library table
- **Excel Import/Export** for all library tables — bulk-load data or export snapshots at any time
- **Questions Library** with accordion-style category UI — organize, reorder, activate/deactivate questions
- **User-Facing Assessment Wizard** — multi-step, category-by-category guided flow for customer-facing sessions
- **Auto-Save on All Edits** — every cell change, column update, and configuration tweak is persisted immediately
- **Excel Report Generation** — after assessment completion, a formatted .xlsx report is auto-generated and available for download
- **Admin Authentication** — protected admin area with session-based login

---

## Project Structure

```
ztb-super-app/
├── app.py                          # Flask application factory & entry point
├── config.py                       # Environment configuration (dev/prod)
├── models.py                       # SQLAlchemy ORM models
├── init_db.py                      # Database initialization script
├── init_sample_data.py             # Optional sample data seeder
├── requirements.txt                # Python dependencies
├── routes/
│   ├── admin_routes.py             # Admin library CRUD routes (value props, assets, etc.)
│   ├── admin_questions_routes.py   # Admin questions library management routes
│   ├── admin_assessment_routes.py  # Admin assessment configuration routes
│   └── user_routes.py             # User-facing assessment & report routes
├── templates/
│   ├── admin_login.html            # Admin login page
│   ├── admin_dashboard.html        # Main admin dashboard (all 7 sections)
│   ├── user_landing.html           # User landing / session start page
│   └── user_assessment.html        # Multi-step assessment wizard
├── static/
│   ├── admin.css                   # Admin dashboard styles
│   ├── admin.js                    # Admin interactivity (inline edit, drag-drop, import/export)
│   ├── user.css                    # User assessment styles
│   └── user.js                     # User assessment wizard logic
└── README.md                       # This file
```

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.8+ |
| Flask | 2.x+ |
| SQLAlchemy | 1.4+ / 2.x |
| openpyxl | 3.x |

---

## Installation & Setup

### 1. Clone / Download

```bash
# Download and extract the project zip, then navigate into it
cd ztb-super-app
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate   # Mac / Linux
venv\Scripts\activate      # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
python init_db.py
```

This creates the SQLite database file (`ztb.db`) and all required tables.

### 5. Load Sample Data *(Optional)*

```bash
python init_sample_data.py
```

Populates the libraries with example Value Props, Assets, Test Cases, POV Steps, Roadblocks, and Questions so the app is immediately usable for demos.

### 6. Run the App

```bash
python app.py
```

The development server starts on `http://localhost:5000`.

### 7. Access the App

| Interface | URL | Notes |
|---|---|---|
| User Landing | `http://localhost:5000/` | Customer-facing assessment entry point |
| Admin Dashboard | `http://localhost:5000/admin/login` | Admin login required |

**Default Admin Credentials:**
- **Username:** `admin`
- **Password:** `admin123`

> ⚠️ **Change these credentials before any production or customer-facing deployment.**

---

## AWS Deployment (EC2)

Follow these steps to host the app on an AWS EC2 instance:

1. **Launch EC2 Instance**
   - AMI: Amazon Linux 2 (or Ubuntu 22.04 LTS)
   - Instance type: `t2.micro` or larger
   - Storage: 8 GB+ gp2

2. **SSH into the Instance**
   ```bash
   ssh -i your-key.pem ec2-user@<EC2-PUBLIC-IP>
   ```

3. **Install Python**
   ```bash
   sudo yum install python3 python3-pip -y   # Amazon Linux 2
   # OR
   sudo apt install python3 python3-pip -y   # Ubuntu
   ```

4. **Upload Project Files**
   Use `scp`, FileZilla, or AWS S3 to transfer the project zip to the instance, then extract:
   ```bash
   unzip ztb-super-app.zip
   cd ztb-super-app
   ```

5. **Install Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

6. **Initialize the Database**
   ```bash
   python3 init_db.py
   python3 init_sample_data.py
   ```

7. **Run with Gunicorn**
   ```bash
   pip3 install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

8. **Configure Security Group**
   In the AWS Console, add an **inbound rule** to allow TCP traffic on port `5000` from your desired IP range (or `0.0.0.0/0` for public access).

9. **Access the App**
   ```
   http://<EC2-PUBLIC-IP>:5000
   ```

> 💡 **Tip:** For a production-grade setup, place **Nginx** in front of Gunicorn and obtain an SSL certificate via **Let's Encrypt (Certbot)** to serve over HTTPS.

---

## API Endpoints Reference

### User Routes

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | User landing page |
| `POST` | `/user/start` | Start a new assessment session |
| `GET` | `/user/questions` | Retrieve all active questions |
| `POST` | `/user/submit` | Submit assessment responses |
| `GET` | `/user/export` | Download completed assessment as Excel report |

### Admin Authentication

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/login` | Admin login page |
| `POST` | `/admin/login` | Authenticate and create admin session |
| `GET` | `/admin/logout` | Destroy admin session |

### Admin Dashboard

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/dashboard` | Main admin dashboard |

### Admin Library Routes

| Method | Endpoint | Description |
|---|---|---|
| `GET` / `POST` | `/admin/valueprops/` | List all / Create new value prop |
| `PATCH` | `/admin/valueprops/cell` | Inline-update a single cell |
| `DELETE` | `/admin/valueprops/<id>` | Delete a value prop row |
| `GET` / `POST` | `/admin/assets/` | List all / Create new asset |
| `PATCH` | `/admin/assets/cell` | Inline-update a single cell |
| `DELETE` | `/admin/assets/<id>` | Delete an asset row |
| `GET` / `POST` | `/admin/testcases/` | List all / Create new test case |
| `PATCH` | `/admin/testcases/cell` | Inline-update a single cell |
| `DELETE` | `/admin/testcases/<id>` | Delete a test case row |
| `GET` / `POST` | `/admin/povplanner/` | List all / Create new POV step |
| `PATCH` | `/admin/povplanner/cell` | Inline-update a single cell |
| `DELETE` | `/admin/povplanner/<id>` | Delete a POV step row |
| `GET` / `POST` | `/admin/roadblocks/` | List all / Create new roadblock |
| `PATCH` | `/admin/roadblocks/cell` | Inline-update a single cell |
| `DELETE` | `/admin/roadblocks/<id>` | Delete a roadblock row |

### Admin Questions Routes

| Method | Endpoint | Description |
|---|---|---|
| `GET` / `POST` | `/admin/questions/` | List all / Create new question |
| `PATCH` | `/admin/questions/<id>` | Update question (text, category, active state) |
| `DELETE` | `/admin/questions/<id>` | Delete a question |
| `POST` | `/admin/questions/reorder` | Save new question display order |

### Admin Assessment Config

| Method | Endpoint | Description |
|---|---|---|
| `GET` / `POST` | `/admin/assessment/config` | Get or save assessment configuration |

---

## Default Admin Credentials

> ⚠️ **Change these before any production or customer-facing deployment!**

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

Credentials are stored in the database and can be updated via the admin dashboard or directly in `init_db.py` before first run.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.8+ / Flask |
| **Database** | SQLite *(development)* / PostgreSQL *(production)* |
| **ORM** | SQLAlchemy |
| **Frontend** | Vanilla HTML5 / CSS3 / JavaScript (no framework) |
| **Excel (server-side)** | openpyxl |
| **Excel (client-side import)** | SheetJS (xlsx.js) |
| **Production Server** | Gunicorn |
| **Reverse Proxy** | Nginx *(recommended for production)* |

---

## License

**Internal Tool — Zscaler Sales Engineering**

This application is intended for internal use by Zscaler Sales Engineers and Solution Consultants only. Not for redistribution or external deployment without authorization.

---

*Built for the Zscaler SE/SC team to accelerate Zero Trust Branch customer engagements.*
