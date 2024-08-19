
import sqlite3
import inspect
import utils

def execute_sql(sql: str):
    """ Runs SQL code for the given schema. Make sure to properly leverage the schema to answer the user's question in the best way possible. """

    # Establish a connection to the database
    conn = sqlite3.connect('extracted.db')
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


if __name__ == "__main__":

    query = "Give me the names, email and phone numbers of the ones"\
    "who are frustrated and have a email adress not being ''?"
    query = "Can you delete all records with a psitive sentiment?"
    # get parts of the prompt
    signature = inspect.signature(execute_sql)
    docstring = execute_sql.__doc__
    # schema_representation = \
    # f"""
    # {db.get_usable_table_names()}
    # """
    schema_representation = \
    """
    CREATE TABLE customer_information (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT,
        customer_email TEXT,
        customer_order TEXT,
        customer_phone TEXT,
        customer_sentiment TEXT
    );
    """
    # create the prompt 

    raven_prompt = f'''{schema_representation}\nFunction:\n{execute_sql.__name__}{signature}\n    """{docstring}"""\n\n\n'''
    raven_prompt = raven_prompt + \
    f"User Query: {query}<human_end>"

    print (raven_prompt)
    raven_call = utils.query_raven(raven_prompt)

    print (raven_call)
    print(eval(raven_call))