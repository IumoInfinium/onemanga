import os 
import sqlite3
from dotenv import load_dotenv

load_dotenv('../.env')

def make_dicts(cursor, row):
    # sqlite records to python object conversion
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

def get_db_connection():
    conn = sqlite3.connect(os.getenv('DB_NAME'))
    
    # enabling the foreign key PRAGMA
    conn.execute('PRAGMA foreign_keys = ON')
    
    # tracing enabled
    conn.set_trace_callback(print)

    # stop automcommit and do it manually
    # conn.isolation_level = None
    
    # Output of SQLite as a python based objects
    # conn.row_factory = sqlite3.Row
    conn.row_factory = make_dicts

    return conn 

def query_db(query: str, args = (), one = False):
    # return the result of the query of one or many records
    cur = get_db_connection().execute(query, args)

    print(query)
    output = cur.fetchall()
    cur.close()
    if one:
        return output[0] if output else None 
    return output