# Busie & Ian — Wedding Website

A full-featured wedding invitation website built with Flask.

## Features
- 🎨 Elegant burgundy & gold theme with Cormorant Garamond + Great Vibes fonts
- 💌 RSVP form with instant email alerts to host
- 📊 Admin dashboard with guest management
- 🔗 Personalised invite links (one-time use)
- 📱 QR code generation per invite
- 📅 Weekly RSVP summary emails (every Sunday 8am)
- 🎵 Background music player
- 📥 CSV export of all responses

---

## Quick Start (Local)

```bash
# 1. Clone and enter project
cd wedding

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your Gmail credentials and admin password

# 5. Run
python app.py
```

Visit: http://localhost:5000
Admin: http://localhost:5000/admin

---

## Add Your Assets

```
static/
  images/
    couple1.jpg    ← hero photo 1
    couple2.jpg    ← hero photo 2
    couple3.jpg    ← hero photo 3
    venue.jpg      ← venue photo
  music/
    wedding.mp3    ← your song
```

---

## Gmail SMTP Setup

1. Go to your Google Account → Security → 2-Step Verification (enable it)
2. Go to Security → App Passwords
3. Generate a password for "Mail" / "Other"
4. Paste the 16-character password into `.env` as `SMTP_PASS`

---

## Deploy to Render

1. Push code to GitHub (git init, git add ., git commit, git push)
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Set environment variables in Render dashboard:
   - `SECRET_KEY` = any random string
   - `ADMIN_PASSWORD` = your chosen password
   - `SMTP_USER` = your Gmail
   - `SMTP_PASS` = your App Password
   - `HOST_EMAIL` = where alerts go (Khwezi's email)
5. Add a Disk in Render (for SQLite persistence):
   - Mount path: `/var/data`
   - Then update DATABASE_URL: `sqlite:////var/data/wedding.db`

---

## Deploy to Railway

1. Push to GitHub
2. railway.app → New Project → Deploy from GitHub
3. Add environment variables in Railway dashboard
4. Done — Railway auto-detects the Procfile

---

## Admin Password

Default: `busieian2026`  
Change this in your `.env` file before deploying.

Admin URL: `yourdomain.com/admin`
