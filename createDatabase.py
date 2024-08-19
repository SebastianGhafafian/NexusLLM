from utils import query_raven
from typing import List
from dataclasses import dataclass
# Warning control
import warnings
warnings.filterwarnings('ignore')
import sqlite3
import os
from tqdm import tqdm
from datasets import load_dataset
import os
import inspect
from sqlite3 import ProgrammingError
import argparse


dataclass_schema_representation = '''
@dataclass
class Record:
    agent_name : str # The agent name
    customer_email : str # customer email if provided, else ''
    customer_order : str # The customer order number if provided, else ''
    customer_phone : str # the customer phone number if provided, else ''
    customer_sentiment : str # Overall customer sentiment, either 'frustrated', or 'happy'. Always MUST have a value.
'''

# Let's call exec to insert the dataclass into our python interpreter so it understands this. 
exec(dataclass_schema_representation)

def initialize_db():

    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('./data/extracted.db')
    cursor = conn.cursor()

    # Fixed table name
    table_name = "customer_information"

    # Fixed schema
    columns = """
    id INTEGER PRIMARY KEY, 
    agent_name TEXT, 
    customer_email TEXT, 
    customer_order TEXT, 
    customer_phone TEXT, 
    customer_sentiment TEXT
    """

    # Ensure the table name is enclosed in quotes if it contains special characters
    quoted_table_name = f'"{table_name}"'

    # Check if a table with the exact name already exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name={quoted_table_name}")
    if cursor.fetchone():
        print(f"Table {table_name} already exists.")
    else:
        # Create the new table with the fixed schema
        cursor.execute(f'''CREATE TABLE {quoted_table_name} ({columns})''')
        print(f"Table {table_name} created successfully.")

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

from dataclasses import dataclass, fields
def update_knowledge(results_list : List[Record]):
    """
    Registers the information necessary
    """


    # Reconnect to the existing SQLite database
    conn = sqlite3.connect('./data/extracted.db')
    cursor = conn.cursor()

    # Fixed table name
    table_name = "customer_information"

    # Prepare SQL for inserting data with fixed column names
    column_names = "agent_name, customer_email, customer_order, customer_phone, customer_sentiment"
    placeholders = ", ".join(["?"] * 5) 
    sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

    # Insert each record
    for record in results_list:
        try:
            record_values = tuple(getattr(record, f.name) for f in fields(record))
            cursor.execute(sql, record_values)
        except ProgrammingError as e:
            print(f"Error with record. {e}")
            continue

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("Records inserted successfully.")


if __name__ == "__main__":
    # Define the parser
    parser = argparse.ArgumentParser(description='Short sample app')
    parser.add_argument('--n', action="store", dest='n_records', default=10, type=int)
    args = parser.parse_args()
    # Remove the existing database file if it exists
    if os.path.exists("extracted.db"):
        os.remove("extracted.db")
    else:
        print("The file does not exist")

    # Initialize the database
    initialize_db()

    # schema_id = ("agent_name", "customer_email", \
    #         "customer_order", "customer_phone", "customer_sentiment")
    
    # load the data
    cwd = os.getcwd()
    dialogue_data = load_dataset(cwd + "/data/", cache_dir="./cache")["train"]

    
    # # create the prompt parts
    # prompt = "\n" + dialogue_string
    # signature = inspect.signature(update_knowledge)
    # signature = str(signature).replace("__main__.Record", "Record")
    # docstring = update_knowledge.__doc__
    # # combine parts to create the prompt
    # raven_prompt = f'''{dataclass_schema_representation}\nFunction:\n{update_knowledge.__name__}{signature}\n    """{docstring}"""\n\n\nUser Query:{prompt}<human_end>'''
    print(len(dialogue_data))
    for i in tqdm(range(0, args.n_records)):
        data = dialogue_data[i] # Get the data
        dialogue_string = data["conversation"].replace("\n\n", "\n") # Get the dialogue
        
        # Ask Raven to extract the information we want out of this dialogue. 
        # create the parts for the prompt
        prompt = "\n" + dialogue_string
        signature = inspect.signature(update_knowledge)
        docstring = update_knowledge.__doc__
        # combine parts to create the prompt
        raven_prompt = f'''{dataclass_schema_representation}\nFunction:\n{update_knowledge.__name__}{signature}\n    """{docstring}"""\n\n\nUser Query:{prompt}<human_end>'''
        raven_call = query_raven(raven_prompt)
        print (raven_call)
        exec(raven_call)

    # my_record = Record(agent_name = "Agent Smith", \
    #                 customer_email = "", customer_order = "12346", \
    #                 customer_phone = "", customer_sentiment = "happy")
    # update_knowledge([my_record])