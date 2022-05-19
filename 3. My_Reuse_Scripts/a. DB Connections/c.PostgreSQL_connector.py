import psycopg2
from psycopg2 import OperationalError

def create_connection(db_name, db_user, db_password, db_host, db_port):
    connection = None
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection
  
  connection = create_connection(
    "postgres", "db_user", "<db_pw>", "<db_host#>", "<port#>"
)
  
def create_database(connection, query):
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")

create_database_query = "CREATE DATABASE <db_name>"
create_database(connection, create_database_query)

connection = create_connection(
    "<db_name>", "db_user", "<db_pw>", "<db_host#>", "<port#>"
)
  
