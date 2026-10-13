"""Minimal Flask app demonstrating MySQL connection and parameterized query."""

from flask import Flask, render_template, request, session, redirect, url_for,flash
import mysql.connector
from mysql.connector import Error
import config
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = 'as54d65as4d6548was5d4'
def get_db_connection():
    """Return a new MySQL connection using values from config.py."""
    return mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        port=config.DB_PORT,
    )

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    error = None
    if not username:
        error = 'Enter a username.'
    elif not email:
        error = 'Enter an Email.'
    elif not password:
        error = 'Enter a Password.'
    if error is None:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            #use Max to find next ID
            cursor.execute("SELECT MAX(UserID) AS MaxID FROM User")
            ID = cursor.fetchone()
            #Id is 1 if no users otherwise get next ID after greatest
            if ID['MaxID'] is None:
                UserId = 1
            else:
                UserId = ID['MaxID'] + 1

            #get DateCreated
            DateCreated = datetime.now()
            # insert user into the table
            query = "INSERT INTO User (UserID, Username, Email, PasswordHash, DateCreated)" \
            " VALUES (%s, %s, %s,%s,%s)"
            cursor.execute(query, (UserId, username, email, generate_password_hash(password), DateCreated))
            conn.commit()

        #failed to insert into table via unique constraints
        except mysql.connector.IntegrityError:
            error = f"User '{username}' or email '{email}' is already registered."
        except Error as e: #other errors
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    return render_template('index.html', error=error)
@app.route('/login', methods=['POST'])
def login():
    username_or_email = request.form.get('username_email', '').strip()
    password = request.form.get('login_password', '').strip()
    error = None
    #check that all inputs were provided
    if not username_or_email:
        error = 'Enter your username or email.'
    elif not password:
        error = 'Enter your password.'
    if error is None:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            #query for the user given username or email
            query = "SELECT * FROM User WHERE Username = %s OR Email = %s"
            cursor.execute(query, (username_or_email, username_or_email))
            user = cursor.fetchone()
            #check if a user was found and that password matches result stored with it
            if user is None or not check_password_hash(user['PasswordHash'], password):
                error = 'Invalid username/email or password try again.'
            else:
                session['user_id'] = user['UserID']
                session['username'] = user['Username']
                return redirect(url_for('index'))
        except Error as e: #any errors
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    #failed to login return errors
    return render_template('index.html', error=error)
@app.route('/logout')
def logout():
    session.clear() #clear the login session values to logout
    return redirect(url_for('index'))

@app.route('/collections/create', methods=['POST'])
def create_collection():
    collection_name = request.form.get('collection_name')
    description = request.form.get('description')
    user_id = session.get('user_id')
    date_created = datetime.now()
    
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        #set the collection ID based on maxID to prevent overwriting others if deleted
        cursor.execute("SELECT MAX(CollectionID) AS MaxID FROM Collection")
        IDs = cursor.fetchone()
        #if no collection default 1 otherwise next ID after the greatest ID
        if IDs['MaxID'] is None:
            collection_id = 1
        else:
            collection_id = IDs['MaxID'] + 1

        cursor.execute(
            "INSERT INTO Collection "
            "(CollectionID, UserID, CollectionName, Description, DateCreated)" \
            " VALUES (%s, %s, %s, %s, %s)",
            [collection_id, user_id, collection_name, description, date_created]
        )
        conn.commit()
        cursor.callproc('GetUserCollectionsAndNotes', [user_id])
        procedure_results = list(cursor.stored_results())
        user_collections = procedure_results[0].fetchall()
        user_notes = procedure_results[1].fetchall()
    except Error as e:
        error = str(e)
        return render_template('index.html', error=error)
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
            
    return render_template(
        'index.html',
        user_collections=user_collections,
        user_notes=user_notes,
        error=error,
        active_tab='collections'
    )

@app.route('/collections/delete', methods=['POST'])
def delete_collection():
    collection_name = request.form.get('collection_name')
    user_id = session.get('user_id')
    
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "DELETE FROM Collection WHERE CollectionName = %s AND UserID = %s",
            [collection_name, user_id]
        )
        conn.commit()
        cursor.callproc('GetUserCollectionsAndNotes', [user_id])
        procedure_results = list(cursor.stored_results())
        user_collections = procedure_results[0].fetchall()
        user_notes = procedure_results[1].fetchall()
    except Error as e:
        error = str(e)
        return render_template('index.html', error=error,active_tab='collections')
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
            
    return render_template(
        'index.html',
        user_collections=user_collections,
        user_notes=user_notes,
        error=error,
        active_tab='collections'
    )

@app.route('/collections/update', methods=['POST'])
def Update_collection():
    old_name = request.form.get('old_collection_name')
    new_name = request.form.get('collection_name')
    description = request.form.get('description')
    user_id = session.get('user_id')
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "UPDATE Collection SET CollectionName = %s, Description = %s " \
            "WHERE CollectionName = %s AND UserID = %s",
            [new_name, description, old_name, user_id]
        )
        conn.commit()
        cursor.callproc('GetUserCollectionsAndNotes', [user_id])
        procedure_results = list(cursor.stored_results())
        user_collections = procedure_results[0].fetchall()
        user_notes = procedure_results[1].fetchall()
    except Error as e:
        error = str(e)
        return render_template('index.html', error=error)
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
            
    return render_template(
        'index.html',
        user_collections=user_collections,
        user_notes=user_notes,
        error=error,
        active_tab='collections'
    )
@app.route('/select_event', methods=['POST'])
def select_event():
    event_id = request.form.get('selected_event_id')
    selected_event = None
    Historical_figures = []
    if event_id:
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            #query for the event clicked on
            cursor.execute(
                "SELECT EventID, Title, Description, EventDate, Year, Source " \
                "FROM Event WHERE EventID = %s",
                [event_id]
            )
            #save the resulting list for front end
            selected_event = cursor.fetchone()
            #find all historical figures for that event
            cursor.execute( 
                "SELECT hf.FigureID, hf.Name, hf.BirthYear, hf.DeathYear, hf.Description "
                "FROM HistoricalFigure hf JOIN EventFigure ef ON hf.FigureID = ef.FigureID "
                "WHERE ef.EventID = %s",
                [event_id]
            )
            Historical_figures = cursor.fetchall()
        except Exception as e:
            error = str(e)
            return render_template('index.html', error=error)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('index.html', selected_event=selected_event, Historical_figures= Historical_figures)

@app.route('/notes/create', methods=['POST'])
def create_note():
    event_id = request.form.get('event_id')
    note_text = request.form.get('note_text')
    user_id = session.get('user_id')
    date_created = datetime.now()

    if not note_text:
        error = "Note Text cannot be NULL"
        return render_template('index.html', error=error)
    else:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            #get max noteID
            cursor.execute("SELECT MAX(NoteID) AS MaxID FROM Note")
            row = cursor.fetchone()
            #No notes set default 1 otherwise next after max
            if row['MaxID'] is None:
                note_id = 1
            else:
                note_id = row['MaxID'] + 1

            cursor.execute("INSERT INTO Note (NoteID, UserID, EventID, NoteText, DateCreated) " \
            "VALUES (%s, %s, %s, %s, %s)", 
            [note_id, user_id, event_id, note_text, date_created])
            conn.commit()
        except Error as e:
            error = str(e)
            return render_template('index.html', error=error)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    return redirect(url_for('index'))
@app.route('/notes/update', methods=['POST'])
def update_note():
    noteID = request.form.get('note_id')
    new_note = request.form.get('note_text')
    user_id = session.get('user_id')
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "UPDATE Note SET NoteText = %s"\
            "WHERE noteID = %s AND UserID = %s",
            [new_note, noteID, user_id]
        )
        conn.commit()
        cursor.callproc('GetUserCollectionsAndNotes', [user_id])
        procedure_results = list(cursor.stored_results())
        user_collections = procedure_results[0].fetchall()
        user_notes = procedure_results[1].fetchall()
    except Error as e:
        error = str(e)
        return render_template('index.html', error=error)
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
            
    return render_template(
        'index.html',
        user_collections=user_collections,
        user_notes=user_notes,
        error=error,
        active_tab='notes'
    )
@app.route('/notes/delete', methods=['POST'])
def delete_note():
    noteID = request.form.get('note_id')
    user_id = session.get('user_id')
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        #delete a given user note 
        cursor.execute(
            "DELETE FROM Note WHERE NoteID = %s AND UserID = %s",
            [noteID, user_id]
        )
        conn.commit()
        cursor.callproc('GetUserCollectionsAndNotes', [user_id])
        procedure_results = list(cursor.stored_results())
        user_collections = procedure_results[0].fetchall()
        user_notes = procedure_results[1].fetchall()
    except Error as e:
        error = str(e)
        return render_template('index.html', error=error)
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
            
    return render_template(
        'index.html',
        user_collections=user_collections,
        user_notes=user_notes,
        error=error,
        active_tab='notes'
    )
@app.route('/collections/add_event', methods=['POST'])
def save_to_collection():
    user_id = session.get('user_id')
    event_id = request.form.get('event_id').strip()
    collection_name = request.form.get('collection_name').strip()
    note_text = request.form.get('note_text','')
    #check that a collection name was entered
    if not collection_name:
        error = "collection name not entered"
        return render_template('index.html', error=error)
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT MAX(CollectionID) AS MaxID FROM Collection")
        IDs = cursor.fetchone()
        #if no collection default 1 otherwise next ID after the greatest ID
        if IDs['MaxID'] is None:
            collection_id = 1
        else:
            collection_id = IDs['MaxID'] + 1
        
        cursor.callproc(
            'SaveEventToCollection',
            [user_id, collection_name, event_id, note_text, collection_id]
        )
        for result in cursor.stored_results():
            result.fetchall()
        conn.commit()
    except Exception as e:
        error = str(e)
        #print("something bad has occured")
        return render_template('index.html', error=error)
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
    return redirect(url_for('index'))
@app.route('/collections/view', methods=['POST'])
def view_collection():
    collection_id = request.form.get('collection_id')
    collection_name = request.form.get('collection_name')
    user_id = session.get('user_id')
    collection_events = []
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        #call procedure to view collection
        cursor.callproc('LoadCollectionDetails', [collection_id])
        #get results of procedure
        for result in cursor.stored_results():
            collection_events = result.fetchall()
        #if error message was returned by procedure else block
        if collection_events and 'Message' in collection_events[0]:
            #write the error and clear the list
            error = collection_events[0]['Message']
            collection_events = []
        cursor.callproc('GetUserCollectionsAndNotes', [user_id])
        procedure_results = list(cursor.stored_results())
        user_collections = procedure_results[0].fetchall()
        user_notes = procedure_results[1].fetchall()

    except Error as e:
        error = str(e)
        return render_template('index.html', error=error,active_tab='collections')
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
    return render_template(
        'index.html', 
        collection_events=collection_events,
        selected_collection_name=collection_name,
        selected_collection_id=collection_id,
        user_collections=user_collections,
        user_notes=user_notes,
        error=error,
        active_tab='collections'
    )
@app.route('/collections/remove_item', methods=['POST'])
def remove_from_collection():
    user_id = session.get('user_id')
    collection_id = request.form.get('collection_id')
    event_id = request.form.get('event_id')
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        #remove specific event
        cursor.execute("DELETE FROM CollectionEvent WHERE CollectionID = %s" \
                        " AND EventID = %s", 
                       [collection_id, event_id]
                       )
        conn.commit()
        #refresh the details list 
        cursor.callproc('LoadCollectionDetails', [collection_id])
        for result in cursor.stored_results():
            collection_events = result.fetchall()

        cursor.callproc('GetUserCollectionsAndNotes', [user_id])
        procedure_results = list(cursor.stored_results())
        user_collections = procedure_results[0].fetchall()
        user_notes = procedure_results[1].fetchall()

    except Error as e:
        error = str(e)
        return render_template('index.html', error=error, active_tab='collections')
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return render_template(
        'index.html',
        collection_events=collection_events,
        selected_collection_id=collection_id,
        user_collections=user_collections,
        user_notes=user_notes,
        error=error,
        active_tab='collections'
    )
@app.route('/timeline')
def timeline_view():
    selected_year = request.args.get('year', type=int)
    error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT MIN(Year) AS MinYear, " \
        "MAX(Year) AS MaxYear FROM Event;"
        )
        yearStartEnd = cursor.fetchone();
        lowerBound= yearStartEnd['MinYear']
        upperBound= yearStartEnd['MaxYear']
        if selected_year == None:
            selected_year = lowerBound
        cursor.execute(
        "SELECT EventID, Title, EventDate, Description, Source "\
        "FROM Event "
        "WHERE Year = %s " 
        "ORDER BY EventID;"
        , [selected_year])
        timeline_events = cursor.fetchall()
        
        cursor.execute(
            "SELECT Year, COUNT(*) AS TotalEvents "
            "FROM Event "
            "GROUP BY Year "
            "ORDER BY Year;"
        )
        barChart_data = cursor.fetchall()
    except Error as e:
        error = str(e)
        return render_template('index.html', error= error , active_tab='timeline')
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass
    return render_template(
        'index.html',
        active_tab='timeline',
        error=error,
        min_year=lowerBound,
        max_year=upperBound,
        selected_year=selected_year,
        timeline_events=timeline_events,
        barChart_data = barChart_data 
    )   
@app.route('/', methods=['GET','POST'])
def index():
    q_event = request.args.get('q_event', '').strip()
    q_year = request.args.get('q_year', '').strip()
    q_country = request.args.get('q_country', '').strip()
    q_continent = request.args.get('q_continent', '').strip()
    q_keyword = request.args.get('q_keyword', '').strip()
    q_tag = request.args.get('q_tag', '').strip()
    preset = request.form.get('preset')
    results = []
    error = None
    q_type = None
    user_collections = []
    user_notes = []
    user_id = session.get('user_id') #user is logged in and can use collections
    if user_id:
        #retrieve user collections and notes
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.callproc('GetUserCollectionsAndNotes', [user_id])
            procedure_results = list(cursor.stored_results())
            user_collections = procedure_results[0].fetchall()
            user_notes = procedure_results[1].fetchall()
        except Error as e:
            error = (f"user collection/notes fetch error: {e}")
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    if preset == 'Military':
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
            "SELECT e.EventID, e.Title, e.Description, e.EventDate, "  
            "e.Year, e.Source " 
            "FROM Event e " 
            "WHERE e.EventID IN ( " 
                "SELECT EventID FROM EventTag " 
                "WHERE TagID IN (SELECT TagID FROM Tag WHERE TagName LIKE '%Military%') " 
            ") " 
            "ORDER BY e.EventDate;" 
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    if preset == 'regions':
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT r.Country, COUNT(e.EventID) AS TotalEvents, "
                " MIN(e.EventDate) AS EarliestEvent, MAX(e.EventDate) AS LatestEvent "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "GROUP BY r.RegionID, r.Country "
                "HAVING COUNT(e.EventID) >= 5 "
                "ORDER BY TotalEvents DESC "
                "LIMIT 15;"
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    elif preset == 'tags':
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT t.TagName, COUNT(et.EventID) AS EventCount, "
                "COUNT(DISTINCT e.RegionID) AS RegionsRepresented "
                "FROM Tag t "
                "JOIN EventTag et ON t.TagID = et.TagID "
                "JOIN Event e ON et.EventID = e.EventID "
                "GROUP BY t.TagID, t.TagName "
                "ORDER BY EventCount DESC "
                "LIMIT 15;"
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    elif q_year and q_continent and q_country and q_tag and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE e.Year = %s "
                "AND r.Continent LIKE %s AND r.Country LIKE %s AND t.TagName LIKE %s "
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_country}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_country and q_tag and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year = %s AND r.Continent LIKE %s AND r.Country LIKE %s "
                "AND t.TagName LIKE %s AND (e.Title LIKE %s OR e.Description "
                "LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_country}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_country and q_tag and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year=%s AND r.Continent LIKE %s AND r.Country LIKE %s "
                "AND t.TagName LIKE %s AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_country}%", f"%{q_tag}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_country and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year=%s AND r.Continent LIKE %s AND r.Country LIKE %s "
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_country}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_tag and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year =%s AND r.Continent LIKE %s AND t.TagName LIKE %s "
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_country and q_tag and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year =%s AND r.Country LIKE %s AND t.TagName LIKE %s "
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_country}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_country and q_tag and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE r.Continent LIKE %s AND r.Country LIKE %s AND t.TagName LIKE %s "
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_country}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    elif q_year and q_continent and q_country and q_tag:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year=%s AND r.Continent LIKE %s AND r.Country LIKE %s AND t.TagName LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_country}%", f"%{q_tag}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_country and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year=%s AND r.Continent LIKE %s AND r.Country LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_country}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_country and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "WHERE e.Year=%s AND r.Continent LIKE %s AND r.Country LIKE %s " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_country}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_tag and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year=%s AND r.Continent LIKE %s AND t.TagName LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_tag and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year=%s AND r.Continent LIKE %s AND t.TagName LIKE %s " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_tag}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year=%s AND r.Continent LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_country and q_tag and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year=%s AND r.Country LIKE %s AND t.TagName LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [q_year, f"%{q_country}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_country and q_tag and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year=%s AND r.Country LIKE %s AND t.TagName LIKE %s " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_country}%", f"%{q_tag}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_country and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year=%s AND r.Country LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_country}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_tag and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "LEFT JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE e.Year=%s AND t.TagName LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_country and q_tag and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE r.Continent LIKE %s AND r.Country LIKE %s AND t.TagName LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_country}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_country and q_tag and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE r.Continent LIKE %s AND r.Country LIKE %s AND t.TagName LIKE %s " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_country}%", f"%{q_tag}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_country and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE r.Continent LIKE %s AND r.Country LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_country}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_tag and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE r.Continent LIKE %s AND t.TagName LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_country and q_tag and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID=et.EventID "
                "LEFT JOIN Tag t ON et.TagID=t.TagID "
                "WHERE r.Country LIKE %s AND t.TagName LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_country}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    elif q_year and q_continent and q_country:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "WHERE e.Year = %s AND r.Continent LIKE %s AND r.Country LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_country}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_tag:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE e.Year = %s AND r.Continent LIKE %s AND t.TagName LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_tag}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE e.Year = %s AND r.Continent LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_continent and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "WHERE e.Year = %s AND r.Continent LIKE %s AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_country and q_tag:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE e.Year = %s AND r.Country LIKE %s AND t.TagName LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_country}%", f"%{q_tag}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_country and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE e.Year = %s AND r.Country LIKE %s "
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [q_year, f"%{q_country}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_country and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "WHERE e.Year = %s AND r.Country LIKE %s AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_country}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_tag and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "LEFT JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE e.Year = %s AND t.TagName LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [q_year, f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_tag and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "LEFT JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE e.Year = %s AND t.TagName LIKE %s AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_tag}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "LEFT JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE e.Year = %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_country and q_tag:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Continent LIKE %s AND r.Country LIKE %s AND t.TagName LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_country}%", f"%{q_tag}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_country and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Continent LIKE %s AND r.Country LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_country}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_country and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "WHERE r.Continent LIKE %s AND r.Country LIKE %s AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_country}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_tag and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Continent LIKE %s AND t.TagName LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_tag and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Continent LIKE %s AND t.TagName LIKE %s AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_tag}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Continent LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_country and q_tag and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Country LIKE %s AND t.TagName LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [f"%{q_country}%", f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_country and q_tag and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Country LIKE %s AND t.TagName LIKE %s AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_country}%", f"%{q_tag}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_country and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Country LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_country}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_tag and q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "LEFT JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE t.TagName LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    elif q_year and q_continent:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "WHERE e.Year = %s AND r.Continent LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_continent}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_country:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "WHERE e.Year = %s AND r.Country LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_country}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_tag:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "LEFT JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE e.Year = %s AND t.TagName LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_tag}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "LEFT JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE e.Year = %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [q_year, f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_year and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "LEFT JOIN Region r ON e.RegionID = r.RegionID "
                "WHERE e.Year = %s AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [q_year, f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_country:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "WHERE r.Continent LIKE %s AND r.Country LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_country}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_tag:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Continent LIKE %s AND t.TagName LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_tag}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Continent LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_continent and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "WHERE r.Continent LIKE %s AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_continent}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_country and q_tag:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Country LIKE %s AND t.TagName LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_country}%", f"%{q_tag}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_country and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE r.Country LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [f"%{q_country}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_country and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID = r.RegionID "
                "WHERE r.Country LIKE %s AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_country}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_tag and q_keyword:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "LEFT JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE t.TagName LIKE %s " 
                "AND (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) "
                "ORDER BY EventDate;",
                [f"%{q_tag}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_tag and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "LEFT JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE t.TagName LIKE %s AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_tag}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    elif q_keyword and q_event:
        try:
            q_type = 'multi'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "LEFT JOIN Region r ON e.RegionID = r.RegionID "
                "LEFT JOIN EventTag et ON e.EventID = et.EventID "
                "LEFT JOIN Tag t ON et.TagID = t.TagID "
                "WHERE (e.Title LIKE %s OR e.Description LIKE %s OR t.TagName LIKE %s) " 
                "AND e.Title LIKE %s "
                "ORDER BY EventDate;",
                [f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_keyword}%", f"%{q_event}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    elif q_keyword:
        try:
            q_type = 'keyword'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
            "SELECT DISTINCT e.EventID, e.Title, e.EventDate, r.Country "
            "FROM Event e "
            "LEFT JOIN Region r ON e.RegionID = r.RegionID "
            "LEFT JOIN EventTag et ON e.EventID = et.EventID "
            "LEFT JOIN Tag t ON et.TagID = t.TagID "
            "WHERE e.Title LIKE  %s " 
            "   OR e.Description LIKE %s " 
            "   OR t.TagName LIKE %s "
            "ORDER BY e.EventDate DESC;",
            [f"%{q_keyword}%",f"%{q_keyword}%",f"%{q_keyword}%"]
            )
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    elif q_tag:
        try:
            q_type = 'tag'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = (
                "SELECT e.EventID, e.Title, e.EventDate, t.TagName "
                "FROM Event e "
                "JOIN EventTag et ON e.EventID=et.EventID "
                "JOIN Tag t ON et.TagID=t.TagID "
                "WHERE t.TagName Like %s "
                "ORDER BY EventDate;"
            )
            cursor.execute(query, (f"%{q_tag}%",))
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    elif q_event:
        try:
            q_type = 'event'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = (
                "SELECT EventID, Title, Description,EventDate, Year, Source, RegionID "
                "FROM Event WHERE Title LIKE %s"
            )
            cursor.execute(query, (f"%{q_event}%",))
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    elif q_year:
        try:
            q_type = 'year'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = (
                "SELECT EventID, Title, Description,EventDate, Year, Source, RegionID "
                "FROM Event WHERE year LIKE %s"
                "ORDER BY EventDate;"
            )
            cursor.execute(query, (f"{q_year}",))
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    elif q_country:
        try:
            q_type = 'country'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = (
                "SELECT e.EventID, e.Title, e.EventDate, r.Country "
                "FROM Event e "
                "JOIN Region r ON e.RegionID=r.RegionID "
                "WHERE r.Country Like %s "
                "ORDER BY EventDate;"
            )
            cursor.execute(query, (f"%{q_country}%",))
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass
    elif q_continent:
        try:
            q_type = 'continent'
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = (
                "SELECT RegionID, Country, Continent "
                "FROM Region WHERE Continent LIKE %s"
            )
            cursor.execute(query, (f"%{q_continent}%",))
            results = cursor.fetchall()
        except Error as e:
            error = str(e)
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception:
                pass

    return render_template(
        'index.html', 
        results=results, q_type=q_type, error=error, q_event=q_event, q_year=q_year,
        q_country=q_country, q_continent=q_continent, q_keyword=q_keyword,
        user_collections=user_collections, user_notes = user_notes,preset=preset 
    )
if __name__ == '__main__':
    app.run(debug=True)
    