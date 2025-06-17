# NGOData

This project provides a minimal Flask application for creating custom forms and generating SQL tables automatically. It works with SQLite and should run on Windows with Python installed.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   python app.py
   ```

Open `http://localhost:5000` in your browser. Use the "Create Form" link to define new forms. Each new form name becomes a new database table with text columns for each field you specify.
