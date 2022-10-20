import psycopg2
import os

def create_db_connection():
    print("welcome")
    return
    # if "DB_HOST" or "DB_USER" or "DB_NAME" or "DB_PASSWORD" not in os.environ:
    #     from dotenv import load_dotenv
    #     load_dotenv("../.env")
    #     # Connect to an existing database
    #     connection = psycopg2.connect(user=os.getenv("DB_USER"),
    #                                   password=os.getenv("DB_PASSWORD"),
    #                                   host=os.getenv("DB_HOST"),
    #                                   port="5432",
    #                                   database=os.getenv("DB_HOST"))

    #     # Create a cursor to perform database operations
    #     cursor = connection.cursor()
    #     return cursor

# except (Exception, Error) as error:
#     print("Error while connecting to PostgreSQL", error)


create_db_connection()
