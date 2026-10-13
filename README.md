# Flask MySQL Demo

Minimal Flask app that demonstrates connecting to a MySQL database and running a parameterized query.

Prerequisites
- Python 3.8+
- MySQL server (import data/test.sql)

Quick start
1. Import the demo database:

   mysql -u root -p < data/test.sql

   The SQL creates `Company` and sample Department/Employee tables.

2. Install dependencies:

   python -m pip install -r requirements.txt

3. Edit `config.py` and fill DB_HOST, DB_USER, DB_PASSWORD as needed (DB_NAME defaults to `Company`).

4. Run the app:

   export FLASK_APP=app.py
   flask run

5. Open http://127.0.0.1:5000 and search for an employee name (e.g., "James").

Notes
- The demo uses `mysql-connector-python` and parameterized queries to avoid injection.
- Credentials are intentionally left blank in config.py for you to supply.

Chronicle Compass

Chronicle Compass is a web application that lets users explore historical events through search, filters, and an interactive timeline. Users can create personal collections of events and save notes for future reference.

Features
Search and filter historical events by keyword, year, region, and tags.
View event details and related historical figures.
Explore events through an interactive timeline.
Create collections and save events and personal notes.
Manage user accounts and saved information.
Technologies
Python and Flask
MySQL
JavaScript, HTML, and CSS
Google Cloud Platform
Database

Designed a relational database to organize historical events, figures, regions, tags, users, collections, and notes. Includes SQL queries, indexes, stored procedures, transactions, and triggers.

Data Sources

Historical data was collected and processed from multiple public sources, including HistoryLabs, Wikipedia, and World History Encyclopedia.

Purpose

Developed as a CS411 Database Systems project to apply database design, SQL, data processing, and full-stack web development.
