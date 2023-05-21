import logging
import sqlite3
import sys
import os

# Set the base directory as the parent directory of the current file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the base directory to the system path
sys.path.append(BASE_DIR)

# Import the backend module from the backend package
from backend import backend_module


# Function to create a database connection to the SQLite database
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        return sqlite3.connect(db_file)
    except sqlite3.Error as e:
        logging.error(f"Error creating connection to database. {e}")

    return None


# Function to check if a user exists in the bot database
def check_user_exist(user_id, conn=None):
    if conn is None:
        conn = create_connection(r"../self_automate.db")
    sql = "SELECT * FROM bot WHERE user_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (user_id,))
    result = cur.fetchall()
    if not result:
        logging.warning('User does not exist!')
        return False
    return True


# Function to add a user to the bot database
def add_user_to_bot_database(user_id, username, password, conn=None):
    if conn is None:
        conn = create_connection(r"../self_automate.db")
    sql = f"INSERT INTO bot (user_id, username) VALUES (?, ?);"
    cur = conn.cursor()
    try:
        cur.execute(sql, (user_id, username))
        conn.commit()
        backend_module.add_user_to_login_database(user_id, password)
    except Exception as e:
        logging.error(e)
        conn.rollback()
    conn.close()


# Function to update user information in the bot database
def update_user_info_in_data(user_id, username, password, conn=None):
    if conn is None:
        conn = create_connection(r"../self_automate.db")
    sql = f"UPDATE bot set username= ? WHERE user_id= ?;"
    cur = conn.cursor()
    try:
        cur.execute(sql, (username, user_id))
        conn.commit()
        backend_module.update_user_info_in_database(user_id, password)
    except Exception as e:
        logging.error(e)
        conn.rollback()
    conn.close()


# Function to get the username of a user from the bot database
def get_username(user_id, conn=None):
    if conn is None:
        conn = create_connection(r"../self_automate.db")
    sql = "SELECT username FROM bot WHERE user_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (user_id,))
    result = cur.fetchall()
    username = result[0][0]
    cur.close()
    return username
