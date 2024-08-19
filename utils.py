import requests
import sqlite3
from langchain_community.utilities.sql_database import SQLDatabase
import inspect


API_URL = "http://nexusraven.nexusflow.ai"

headers = {
        "Content-Type": "application/json"
}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

def querychat(payload):
    response = requests.post(CHAT_URL, headers=headers, json=payload)
    return response.json()

def query_raven(prompt):
    return query({
        "inputs" : prompt,
        "parameters" : {"do_sample" : True, "temperature" : 0.001, "max_new_tokens" : 400, "stop" : ["<bot_end>", "Thought:"], "return_full_text" : False}
    })[0]["generated_text"].replace("Call:", "").replace("Thought:", "").strip()

def execute_sql(sql: str, database_path: str):
    """
    Runs SQL code for the given schema and database. Make sure to properly leverage the schema to answer the user's question in the best way possible. 
    Pay attention to use only the the column names of that belong to a table which are described in the schema description.
    Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
    
    Args:
        sql: SQL code to run
        database_name: name of the database to run the SQL code
    Returns:
        results: list of tuples containing the results of the SQL query
    """

    # Establish a connection to the database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Execute the SQL statement
    cursor.execute(sql)

    # Initialize an empty list to hold query results
    results = []

    results = cursor.fetchall()
    print("Query operation executed successfully. Number of rows returned:", len(results))

    # Close the connection to the database
    conn.close()

    # Return the results for SELECT operations; otherwise, return an empty list
    return results

def get_query(database_path, question):
    
    """ Generates a SQL query for the given table and columns. """
    db = SQLDatabase.from_uri(f"sqlite:///{database_path}")
    # gather date for the prompt
    tables =  db.get_usable_table_names()
    tables_info = db.get_table_info(tables)
    signature = inspect.signature(execute_sql)
    docstring = execute_sql.__doc__
    schema_representation = \
    f"""
    {tables_info}
    """

    # create the prompt
    raven_prompt = f'''Schema:\n{schema_representation}\nFunction:\n{execute_sql.__name__}{signature}\n    """{docstring}"""\n\n\n'''
    # add the user query and database name to the prompt
    raven_prompt = raven_prompt + \
    f"Database Name: {database_path}\n" + \
    f"User Query: {question}<human_end>"

    raven_call = query_raven(raven_prompt)

    return raven_call, raven_prompt
