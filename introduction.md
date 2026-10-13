# Introduction: Flask + MySQL Website Demo

This project is a small beginner-friendly example of how a website can connect a **frontend** page to a **backend** server, and how the backend can talk to a **MySQL database**.

The demo lets a user search for employees by name. The user types a name into a web page, submits the form, and Flask uses that search text to query a MySQL database. The matching employee rows are then sent back to the web page and displayed in a table.

---

## 1. The big picture

A website usually has three main parts:

1. **Frontend**  
   The part the user sees in the browser. In this project, that is `index.html`.

2. **Backend**  
   The Python/Flask application that receives requests from the browser, runs logic, talks to the database, and sends back a response. In this project, that is `app.py`.

3. **Database**  
   The place where data is stored. In this project, the database is MySQL, and the code searches the `Employee` table in the `Company` database.

The flow looks like this:

```text
User's browser
     |
     | 1. User opens the page or submits the search form
     v
Flask backend: app.py
     |
     | 2. Flask reads the search text from the URL
     v
MySQL database
     |
     | 3. MySQL returns matching employee rows
     v
Flask backend: app.py
     |
     | 4. Flask sends the results into index.html
     v
User's browser
     |
     | 5. Browser shows the table of results
```

---

## 2. Files in this project

### `app.py`

This is the main Flask backend application.

It does four important jobs:

- Creates the Flask app.
- Connects to MySQL.
- Defines the `/` web route.
- Sends search results to the HTML page.

### `config.py`

This file stores the database connection settings, such as:

- database host
- database username
- database password
- database name
- database port

The backend imports this file so the database settings are kept separate from the main application code.

> Important: Do not commit real passwords to a public GitHub repository. For real projects, use environment variables or a `.env` file instead.

### `index.html`

This is the frontend page.

It contains:

- the search form
- the input box where the user types an employee name
- the Search button
- the table that displays employee results
- messages for errors or no results

In a standard Flask project, this file should usually be placed inside a folder named `templates`, like this:

```text
project-folder/
  app.py
  config.py
  templates/
    index.html
```

That is because Flask's `render_template("index.html")` looks for HTML files inside the `templates` folder by default.

---

## 3. How the frontend sends information to the backend

In `index.html`, the search form looks like this:

```html
<form method="get" action="/" class="mb-3">
```

This means:

- `method="get"`: the form sends data through the URL query string.
- `action="/"`: the form sends the request to the home route of the Flask app.

The input field looks like this:

```html
<input type="text" name="q" ...>
```

The important part is:

```html
name="q"
```

That name becomes the key Flask uses to read the search value.

For example, if a user types:

```text
Ann
```

and clicks **Search**, the browser sends a request like:

```text
/?q=Ann
```

So the frontend communicates with the backend by sending a URL request that includes the search value.

---

## 4. How Flask receives the search text

In `app.py`, this line gets the value of `q` from the URL:

```python
q = request.args.get('q', '').strip()
```

This means:

- `request.args` contains values from the URL query string.
- `.get('q', '')` tries to get the value named `q`.
- If there is no `q`, it uses an empty string instead.
- `.strip()` removes extra spaces at the beginning or end.

Example:

```text
/?q=Ann
```

becomes:

```python
q = "Ann"
```

If the user has not searched yet, then:

```python
q = ""
```

---

## 5. How Flask connects to MySQL

The function `get_db_connection()` creates a new connection to the MySQL database:

```python
def get_db_connection():
    return mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        port=config.DB_PORT,
    )
```

Instead of typing the database settings directly in `app.py`, the code reads them from `config.py`.

This line imports the settings:

```python
import config
```

So when the code says:

```python
config.DB_HOST
```

it means:

```text
Use the DB_HOST value from config.py.
```

This keeps the app code cleaner and makes it easier to change database settings later.

---

## 6. How Flask searches the database

The search only happens if the user typed something:

```python
if q:
```

If `q` has text, Flask connects to the database:

```python
conn = get_db_connection()
```

Then it creates a cursor:

```python
cursor = conn.cursor(dictionary=True)
```

A cursor is an object that lets Python send SQL commands to the database.

The `dictionary=True` part means each row will come back like a Python dictionary, such as:

```python
{
    "empID": 1,
    "empName": "Ann Smith",
    "jobTitle": "Developer",
    "homeCity": "Chicago",
    "annualSalary": 80000,
    "deptID": 3
}
```

That makes the HTML template easier to read, because it can use names like:

```html
{{ row.empName }}
```

instead of numeric column positions.

---

## 7. The SQL query

The SQL query in `app.py` is:

```python
query = (
    "SELECT empID, empName, jobTitle, homeCity, annualSalary, deptID "
    "FROM Employee WHERE empName LIKE %s"
)
```

This means:

```sql
SELECT empID, empName, jobTitle, homeCity, annualSalary, deptID
FROM Employee
WHERE empName LIKE some_search_pattern;
```

The query searches the `Employee` table for employee names that match what the user typed.

The code runs the query like this:

```python
cursor.execute(query, (f"%{q}%",))
```

The percent signs make it a partial search.

For example, if the user searches for:

```text
Ann
```

then the search pattern becomes:

```text
%Ann%
```

That can match names like:

```text
Ann Smith
Joanne Lee
Mary Ann Johnson
```

---

## 8. Why the query uses `%s`

The SQL query uses `%s` as a placeholder:

```python
"WHERE empName LIKE %s"
```

Then the actual value is passed separately:

```python
cursor.execute(query, (f"%{q}%",))
```

This is called a **parameterized query**.

A parameterized query is safer than building SQL by combining strings manually. It helps protect the app from SQL injection, which is when someone tries to type harmful SQL into a form field.

Do this:

```python
cursor.execute(query, (f"%{q}%",))
```

Do not do this:

```python
cursor.execute("SELECT * FROM Employee WHERE empName LIKE '%" + q + "%'")
```

The first version lets the database connector handle the user input more safely.

---

## 9. How results are returned to Flask

After the query runs, this line gets all matching rows:

```python
results = cursor.fetchall()
```

At this point, `results` is a list of rows.

For example:

```python
[
    {
        "empID": 1,
        "empName": "Ann Smith",
        "jobTitle": "Developer",
        "homeCity": "Chicago",
        "annualSalary": 80000,
        "deptID": 3
    },
    {
        "empID": 2,
        "empName": "Joanne Lee",
        "jobTitle": "Manager",
        "homeCity": "Dallas",
        "annualSalary": 95000,
        "deptID": 2
    }
]
```

Flask then sends this list to the HTML page.

---

## 10. How Flask sends data into the HTML page

At the end of the route, Flask returns this:

```python
return render_template('index.html', results=results, q=q, error=error)
```

This means:

- Load the `index.html` template.
- Give the template a variable named `results`.
- Give the template a variable named `q`.
- Give the template a variable named `error`.

The HTML page can then use those variables.

For example, the input field uses `q` here:

```html
value="{{ q|default('') }}"
```

That keeps the user's search text visible in the search box after the page reloads.

---

## 11. How the HTML displays results

In `index.html`, this part checks whether there are results:

```html
{% if results %}
```

If there are results, the page creates a table.

This part loops through every row:

```html
{% for row in results %}
```

Inside the loop, each row is displayed using template variables:

```html
<td>{{ row.empID }}</td>
<td>{{ row.empName }}</td>
<td>{{ row.jobTitle }}</td>
<td>{{ row.homeCity }}</td>
<td>{{ row.annualSalary }}</td>
<td>{{ row.deptID }}</td>
```

So if Flask sends this data:

```python
{
    "empName": "Ann Smith",
    "jobTitle": "Developer"
}
```

the HTML can display:

```html
Ann Smith
Developer
```

This is how backend data appears on the frontend page.

---

## 12. What happens when there is an error?

The app starts with:

```python
error = None
```

If something goes wrong while connecting to MySQL or running the query, the error is saved:

```python
except Error as e:
    error = str(e)
```

Then Flask sends the error to `index.html`:

```python
return render_template('index.html', results=results, q=q, error=error)
```

The HTML checks for an error:

```html
{% if error %}
  <div class="alert alert-danger">{{ error }}</div>
{% endif %}
```

If `error` contains a message, the page displays it in a red Bootstrap alert box.

---

## 13. What happens when there are no results?

This part of `index.html` handles the case where the user searched, but no employees matched:

```html
{% elif q %}
  <div class="alert alert-warning">No results found for "{{ q }}".</div>
{% endif %}
```

This means:

- If there are no results,
- but the user did type a search,
- show a warning message.

Example:

```text
No results found for "XYZ".
```

---

## 14. Why the database connection is closed

After the database work is done, the app tries to close the cursor and connection:

```python
finally:
    try:
        cursor.close()
        conn.close()
    except Exception:
        pass
```

This is important because database connections use resources.

A simple way to think about it:

```text
Open connection -> Ask database a question -> Get results -> Close connection
```

Closing the connection helps prevent the app from leaving too many database connections open.

---

## 15. How the page gets styled

The HTML file includes Bootstrap:

```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
```

Bootstrap is a CSS framework. It gives the page ready-made styles.

For example:

```html
class="btn btn-primary"
```

makes the Search button look like a Bootstrap primary button.

And:

```html
class="table table-striped"
```

makes the results table look cleaner.

Bootstrap is not required for Flask or MySQL to work. It only improves the appearance of the page.

---

## 16. Step-by-step example

Imagine a user searches for:

```text
smith
```

Here is what happens:

1. The user types `smith` into the search box.
2. The user clicks **Search**.
3. The browser sends a GET request to:

   ```text
   /?q=smith
   ```

4. Flask receives the request at the `/` route.
5. Flask reads the search text:

   ```python
   q = "smith"
   ```

6. Flask opens a MySQL connection using `config.py`.
7. Flask runs a SQL query that searches for employee names like `%smith%`.
8. MySQL returns matching rows.
9. Flask sends those rows into `index.html`.
10. `index.html` loops through the rows and displays them in a table.
11. The user sees the search results in the browser.

---

## 17. Frontend and backend relationship

A simple way to remember the relationship is:

```text
Frontend asks.
Backend thinks.
Database stores.
Backend answers.
Frontend displays.
```

In this project:

- `index.html` asks for employees by sending form data.
- `app.py` receives the request and decides what to do.
- MySQL stores the employee data.
- `app.py` gets the matching data from MySQL.
- `index.html` displays the data for the user.

The frontend does not talk directly to MySQL. The backend talks to MySQL for it.

That is important because the database credentials should never be exposed in the browser.

---

## 18. Beginner checklist

To run a project like this, make sure:

- MySQL is running.
- The `Company` database exists.
- The `Employee` table exists.
- The database settings in `config.py` are correct.
- `index.html` is inside the `templates` folder.
- Flask and the MySQL connector are installed.
- You run the Flask app with:

```bash
python app.py
```

When the app starts, Flask will show a local URL such as:

```text
http://127.0.0.1:5000
```

Open that URL in your browser to use the demo.

---

## 19. Key terms

### Browser

The program the user uses to view the website, such as Chrome, Edge, Firefox, or Safari.

### Frontend

The part of the website the user sees and interacts with.

### Backend

The server-side code that handles requests, runs logic, and talks to the database.

### Route

A URL path handled by Flask. In this project, `/` is the main route.

### Request

A message sent from the browser to the backend.

### Response

A message sent from the backend back to the browser.

### Template

An HTML file that can receive variables from Flask. `index.html` is a Jinja template.

### Database

A system that stores data. This project uses MySQL.

### SQL

The language used to ask questions of a database.

### Parameterized query

A safer way to send user input into SQL without directly combining strings.

---

## 20. Summary

This demo shows the basic pattern used by many database-backed websites:

```text
HTML form -> Flask route -> MySQL query -> Flask template -> HTML results
```

The user interacts with the frontend, but the backend does the work of reading the request, connecting to the database, running the SQL query, and sending results back to the page.

Once you understand this flow, you understand one of the most important ideas in web development: the frontend and backend communicate through requests and responses.
