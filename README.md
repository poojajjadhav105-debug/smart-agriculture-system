# Smart Agriculture Management System (Streamlit)

## Requirements
- Python 3.9 or newer

## Run locally
1. Extract the ZIP file.
2. Open a terminal in the project folder.
3. Install packages:
   `pip install -r requirements.txt`
4. Start the app:
   `streamlit run app.py`
5. Open the local URL shown in the terminal (usually http://localhost:8501).

## Included
- Registration and login with salted PBKDF2 password hashing
- Dashboard and sample sensor values
- Farm monitoring and saved readings
- Demo irrigation toggle
- Create and browse agriculture blogs
- Alerts, analytics, CSV export
- SQLite local database created automatically

## Important
Sensor values are demo/manual values until hardware or a sensor API is connected.
The irrigation toggle only changes demo state; it does not operate a real pump.
This is a local learning/demo application, not a production deployment.
