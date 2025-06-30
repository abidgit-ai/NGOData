# NGOData

This project implements a small Flask application that lets you design surveys dynamically and stores responses in SQLite. It is cross‑platform and works on Windows with Python installed.

## Features

* Create a survey with title and description.
* Add questions of various types including optional subform groups.
* Automatically generate SQL tables for each survey and its subforms.
* Fill out the survey through a web form.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   python app.py
   ```
3. Open `http://localhost:5000` in your browser.

Use "Create Survey" to start building a survey. After adding questions, click "Generate Tables" to create the necessary response tables and begin collecting data.
