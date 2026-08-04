# Student LMS Tracker

## Run Locally

1. Create and activate your virtual environment:

```powershell
cd C:\Users\vsri4\Downloads\student_lms_tracker\lms
python -m venv ..\venv
..\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Seed the database:

```powershell
python setup_dev.py
```

4. Start the app:

```powershell
python run.py
```

5. Open in browser:

```text
http://127.0.0.1:5000
```

## GitHub

The repository is already connected to:

`https://github.com/Sri-2805/student_tracker.git`

To save code to GitHub:

```powershell
git add .
git commit -m "Your message"
git push origin main
```

## Vercel Deployment

Vercel can deploy this Flask app using the `vercel.json` config.

1. Install Vercel CLI:

```powershell
npm install -g vercel
```

2. Login and link the project:

```powershell
cd C:\Users\vsri4\Downloads\student_lms_tracker
vercel login
vercel init
```

3. Deploy:

```powershell
vercel --prod
```

### Notes

- This app uses SQLite by default when `USE_SQLITE=1`.
- For production, configure a proper database and set environment variables in Vercel.
