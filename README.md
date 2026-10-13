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
