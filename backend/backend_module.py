import requests
from json import dump, load, loads
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from time import sleep
import logging
import sqlite3
from sqlite3 import Error
from bs4 import BeautifulSoup
import jdatetime
from os import path, mkdir
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s', encoding='utf-8')


class User:
    def __init__(self, user_id):
        """
        Initializes a User object with the provided user ID.

        Args:
            user_id (int): The ID of the user.

        Raises:
            ValueError: If the user ID is not found in the database.
        """
        conn = create_connection(r"../self_automate.db")
        sql = "SELECT bot.username, login.password FROM login INNER JOIN bot ON login.user_id = bot.user_id WHERE login.user_id = ?"
        cur = conn.cursor()
        cur.execute(sql, (user_id,))
        user_info = cur.fetchone()
        cur.close()
        conn.close()

        if user_info is None:
            # Log that the user_id was not found in the database
            logging.error(f"Failed to initialize User object. User with id {user_id} not found in the database.")
            raise ValueError("User with id {} not found in database".format(user_id))

        # Assign username and password to object attributes
        self.user_id = user_id
        self.username = user_info[0]
        self.password = user_info[1]

        # Log successful initialization of User object
        logging.info(f"Initialized User object for user {self.username} (id: {self.user_id})")


def create_connection(db_file):
    """
    Creates a database connection to the SQLite database specified by db_file.

    Args:
        db_file (str): The path to the database file.

    Returns:
        conn: Connection object or None
    """
    try:
        return sqlite3.connect(db_file)
    except Error as e:
        logging.error(f"Error creating connection to database. {e}")

    return None


def create_table(conn, create_table_sql):
    """
    Creates a table in the database using the provided SQL statement.

    Args:
        conn: Connection object.
        create_table_sql (str): A CREATE TABLE statement.

    Returns:
        None
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        logging.error(f"Error creating table. {e}")


def create_tables(conn=None):
    """
    Creates the necessary tables in the database if they don't already exist.

    Args:
        conn: Connection object.

    Returns:
        None
    """
    if conn is None:
        conn = create_connection(r"../self_automate.db")
    sql_create_login_table = """ CREATE TABLE IF NOT EXISTS login (
                                    user_id integer PRIMARY KEY,
                                    password text NOT NULL
                                ); """

    create_table(conn, sql_create_login_table)
    sql_create_bot_table = """CREATE TABLE IF NOT EXISTS bot (
                                    user_id integer PRIMARY KEY,
                                    username text NOT NULL
                                );"""

    create_table(conn, sql_create_bot_table)
    sql_create_cookie_table = """CREATE TABLE IF NOT EXISTS cookie (
                                    user_id integer PRIMARY KEY,
                                    cookie_requestverificationtoken text,
                                    cookie_jahangostarsetare text
                                );"""

    create_table(conn, sql_create_cookie_table)

    sql_create_credit_table = """CREATE TABLE IF NOT EXISTS credit (
                                        user_id integer PRIMARY KEY,
                                        credit integer
                                    );"""

    create_table(conn, sql_create_credit_table)


def initialize_data_base():
    # Function to initialize the database and create necessary directories
    if not path.isdir(f'{BASE_DIR}\\backend\\reservation_datas'):
        mkdir(f'{BASE_DIR}\\backend\\reservation_datas')
    if not path.isdir(f'{BASE_DIR}\\backend\\reservation_result'):
        mkdir(f'{BASE_DIR}\\backend\\reservation_result')
    if not path.isdir(f'{BASE_DIR}\\backend\\last_reservation'):
        mkdir(f'{BASE_DIR}\\backend\\last_reservation')
    if not path.isdir(f'{BASE_DIR}\\backend\\priority_queue\\'):
        mkdir(f'{BASE_DIR}\\backend\\priority_queue\\')

    database = r"../self_automate.db"  # Path to the database file

    conn = create_connection(database)  # Create a connection to the database

    if conn is not None:
        create_tables(conn)  # Create necessary tables in the database
    else:
        logging.error("Error! cannot create the database connection.")


def generate_cookies(user: User):
    # Function to generate cookies for a user
    options = Options()
    options.add_argument('--no-proxy-server')
    options.add_experimental_option('excludeSwitches', ['enable-quic'])
    if check_user_exist_bot_table(user.user_id):
        with webdriver.Chrome(options=options) as driver:
            driver.get("https://self.shahroodut.ac.ir")

            driver.find_element('id', 'username').send_keys(user.username)

            driver.find_element('id', 'password').send_keys(user.password)

            driver.find_element(By.CLASS_NAME, "btn.btn-primary.btn-block.btn-flat").click()

            error = BeautifulSoup(driver.page_source, 'html.parser').find('div', attrs={"class": "text-red ng-binding"})

            sleep(1.5)
            if error is None:
                request_verification_token = driver.get_cookies()[0]['value']
                jahangostar_setare = driver.get_cookies()[1]['value']

                insert_cookies(request_verification_token, jahangostar_setare, user)

                credit_element = driver.find_element(By.CLASS_NAME,
                                                     "navbar-text.text-white.text-bold.col-xs-5.col-md-2.ng-binding")

                credit_text = credit_element.text
                credit_amount = credit_text.split(':')[1].strip().split()[0]
                try:
                    credit_integer = int(credit_amount.replace(',', ''))
                except:
                    credit_integer = 0
                credit = credit_integer // 10

                insert_credit(user.user_id, credit)
                logging.info("Cookies generated successfully")
            else:
                logging.error(f"Failed to generate cookies. {error.string.strip()}")
                raise Exception("Failed to generate cookies")
    else:
        logging.error('user does not exist in database, try to add it')


def update_credit(user_id):
    # Function to update the credit for a user
    options = Options()
    options.add_argument('--no-proxy-server')
    options.add_experimental_option('excludeSwitches', ['enable-quic'])
    with webdriver.Chrome(options=options) as driver:
        driver.get("https://self.shahroodut.ac.ir")

        driver.find_element('id', 'username').send_keys(get_username(user_id))

        driver.find_element('id', 'password').send_keys(get_user_password(user_id))

        driver.find_element(By.CLASS_NAME, "btn.btn-primary.btn-block.btn-flat").click()

        error = BeautifulSoup(driver.page_source, 'html.parser').find('div', attrs={"class": "text-red ng-binding"})

        sleep(1.5)
        if error is None:
            credit_element = driver.find_element(By.CLASS_NAME,
                                                 "navbar-text.text-white.text-bold.col-xs-5.col-md-2.ng-binding")
            credit_amount = credit_element.text.split(':')[1].strip().split()[0]
            try:
                credit_integer = int(credit_amount.replace(',', ''))
            except:
                credit_integer = 0
            credit = credit_integer // 10
            logging.info("credit updated successfully")
            insert_credit(user_id, credit)
            return credit
        else:
            logging.error(f"Failed to generate cookies. {error.string.strip()}")
            raise Exception("Failed to generate cookies")


def get_credit(user_id, conn=None):
    # Function to get the credit for a user
    if conn is None:
        conn = create_connection(r"../self_automate.db")
    sql = "SELECT credit FROM credit WHERE user_id = ?;"
    cur = conn.cursor()
    cur.execute(sql, (user_id,))
    credit = cur.fetchone()
    cur.close()
    conn.close()
    if not credit:
        logging.error("credit not found in database, generating new cookies...")
        update_credit(user_id)
        return get_cookies(user_id)  # Assuming this should return the generated cookies
    logging.info("Cookies loaded successfully")
    return credit[0]


def insert_cookies(request_verification_token, jahangostar_setare, user: User, conn=None):
    """
    Inserts cookies into the cookie table in the database for a given user.
    If the user already exists in the table, updates the existing cookies.
    :param request_verification_token: The request verification token cookie value.
    :param jahangostar_setare: The JahangostarSetare cookie value.
    :param user: The User object representing the user.
    :param conn: Optional connection object to use for the database. If None, create a new connection.
    """
    if conn is None:
        conn = create_connection(r"../self_automate.db")

    if check_user_exist_cookie_table(user):
        # Update the existing cookies in the database
        sql = "UPDATE cookie SET cookie_requestverificationtoken = ?, cookie_jahangostarsetare = ? WHERE user_id = ?;"
        cur = conn.cursor()
        cur.execute(sql, (request_verification_token, jahangostar_setare, user.user_id))
        conn.commit()
        cur.close()
        conn.close()
    else:
        # Insert new cookies into the database
        sql = "INSERT INTO cookie (cookie_requestverificationtoken, cookie_jahangostarsetare, user_id) VALUES (?, ?, ?);"
        cur = conn.cursor()
        cur.execute(sql, (request_verification_token, jahangostar_setare, user.user_id))
        conn.commit()
        cur.close()
        conn.close()


def insert_credit(user_id, credit, conn=None):
    """
    Inserts credit into the credit table in the database for a given user.
    If the user already exists in the table, updates the existing credit.
    :param user_id: The ID of the user.
    :param credit: The credit value to insert/update.
    :param conn: Optional connection object to use for the database. If None, create a new connection.
    """
    if conn is None:
        conn = create_connection(r"../self_automate.db")

    if check_user_exist_credit_table(user_id):
        # Update the existing credit in the database
        sql = "UPDATE credit SET credit = ? WHERE user_id = ?;"
        cur = conn.cursor()
        cur.execute(sql, (credit, user_id))
        conn.commit()
        cur.close()
        conn.close()
    else:
        # Insert new credit into the database
        sql = "INSERT INTO credit (credit, user_id) VALUES (?, ?);"
        cur = conn.cursor()
        cur.execute(sql, (credit, user_id))
        conn.commit()
        cur.close()
        conn.close()


def get_cookies(user: User, conn=None):
    """
    Get cookies for a given username from the database.
    If cookies are not found in the database, generate new ones.
    :param user: The user_id to look up cookies for.
    :param conn: Optional connection object to use for the database. If None, create a new connection.
    :return: A dictionary containing the cookies.
    """
    if conn is None:
        conn = create_connection(r"../self_automate.db")

    sql = "SELECT cookie_requestverificationtoken, cookie_jahangostarsetare FROM cookie WHERE user_id = ?;"
    cur = conn.cursor()
    cur.execute(sql, (user.user_id,))
    result = cur.fetchall()
    cur.close()
    conn.close()

    if not result:
        # Log error message
        logging.error("Cookies not found in database, generating new cookies...")
        generate_cookies(user)  # Generate and return the cookies
        return get_cookies(user)

    cookies = {
        "JahangostarSetare": result[0][1],
        "__RequestVerificationToken": result[0][0]
    }

    proxies = {
        "http": None,
        "https": None
    }

    if requests.get("https://self.shahroodut.ac.ir/api/v0/Reservation?lastdate=&navigation=0",
                    cookies=cookies,
                    allow_redirects=False,
                    proxies=proxies).status_code != 200:
        generate_cookies(user)  # Generate and return the cookies
        return get_cookies(user)

    # Log success message
    logging.info("Cookies loaded successfully")
    return cookies


def get_reserve_data(user: User, session=None):
    """
    Retrieves reservation data for a given user.
    :param user: The User object representing the user.
    :param session: Optional requests.Session object to use for making the HTTP request. If None, create a new session.
    :return: The HTTP response object containing the reservation data.
    """
    if not session:
        session = requests.Session()

    proxies = {
        "http": None,
        "https": None
    }

    if check_day():
        # Get reservation data for the current week
        response = session.get("https://self.shahroodut.ac.ir/api/v0/Reservation?lastdate=&navigation=0",
                               cookies=get_cookies(user),
                               allow_redirects=False,
                               proxies=proxies)
    else:
        # Get reservation data for the next week
        response = session.get("https://self.shahroodut.ac.ir/api/v0/Reservation?lastdate=&navigation=+7",
                               cookies=get_cookies(user),
                               allow_redirects=False,
                               proxies=proxies)

    # Log success message
    logging.info("Reservation data retrieved successfully")
    session.close()

    return response


def check_day():
    """
    Checks if the current day is before Thursday.
    :return: True if the current day is before Thursday, False otherwise.
    """
    # Check if the weekday is greater than or equal to 4 (i.e., Thursday)
    if jdatetime.datetime.now().date().weekday() >= 3:
        # If the weekday is Thursday or later, return False
        return False

    # If the weekday is earlier than Thursday, return True
    return True


def load_reserve_data(user: User):
    """
    Loads reservation data from a JSON file for a given user.
    :param user: The User object representing the user.
    :return: The reservation data loaded from the JSON file.
    """
    with open(f'{BASE_DIR}\\backend\\reservation_datas\\{user.user_id}_{user.username}_rd.json', 'r',
              encoding='utf-8') as f:
        reservation_data = load(f)
        # Log success message
        logging.info("Reservation data loaded successfully")
    return reservation_data


def get_reserved_foods(user_id):
    """
    Retrieves reserved foods for a given user.
    :param user_id: The ID of the user.
    :return: The reserved foods data.
    """
    username = get_username(user_id)
    result = []

    with open(f'{BASE_DIR}\\backend\\reservation_datas\\{user_id}_{username}_rd.json', 'r',
              encoding='utf-8') as f:
        reservation_data = load(f)

        # Log success message
        logging.info("Reservation data loaded successfully")
    return reservation_data


def add_user_to_login_database(user_id, password, conn=None):
    """
    Adds a user to the login table in the database.
    :param user_id: The ID of the user.
    :param password: The password of the user.
    :param conn: Optional connection object to use for the database. If None, create a new connection.
    """
    if conn is None:
        conn = create_connection(r"../self_automate.db")

    sql = f"INSERT INTO login (user_id, password) VALUES (?, ?);"
    cur = conn.cursor()
    cur.execute(sql, (user_id, password))
    conn.commit()
    cur.close()
    conn.close()


def update_user_info_in_database(user_id, password, conn=None):
    """
    Updates the user's password in the login table in the database.
    If the user does not exist in the table, adds a new entry.
    :param user_id: The ID of the user.
    :param password: The new password to update.
    :param conn: Optional connection object to use for the database. If None, create a new connection.
    """
    if conn is None:
        conn = create_connection(r"../self_automate.db")

    if check_user_exist_bot_table(user_id):
        # Update the user's password in the database
        sql = f"UPDATE login set password= ? WHERE user_id= ? ;"
        cur = conn.cursor()
        cur.execute(sql, (password, user_id))
        conn.commit()
        cur.close()
        conn.close()
    else:
        # Add a new user entry to the database
        add_user_to_login_database(user_id, password)


# Function to check if a user exists in the 'bot' table
def check_user_exist_bot_table(user_id, conn=None):
    # If no connection is provided, create a new connection to the database
    if conn is None:
        conn = create_connection(r"../self_automate.db")

    # SQL query to check the count of rows with the given user_id in the 'bot' table
    sql = "SELECT COUNT(*) FROM bot WHERE user_id = ?"

    # Execute the SQL query
    cur = conn.cursor()
    cur.execute(sql, (user_id,))

    # Fetch the result
    result = cur.fetchone()

    # If the count is greater than 0, the user exists in the table, so return True
    if result[0] > 0:
        return True
    else:
        return False


# Function to check if a user exists in the 'cookie' table
def check_user_exist_cookie_table(user: User, conn=None):
    # If no connection is provided, create a new connection to the database
    if conn is None:
        conn = create_connection(r"../self_automate.db")

    # SQL query to check the count of rows with the given user_id in the 'cookie' table
    sql = "SELECT COUNT(*) FROM cookie WHERE user_id = ?"

    # Execute the SQL query
    cur = conn.cursor()
    cur.execute(sql, (user.user_id,))

    # Fetch the result
    result = cur.fetchone()

    # If the count is greater than 0, the user exists in the table, so return True
    if result[0] > 0:
        return True
    else:
        return False


# Function to check if a user exists in the 'credit' table
def check_user_exist_credit_table(user_id, conn=None):
    # If no connection is provided, create a new connection to the database
    if conn is None:
        conn = create_connection(r"../self_automate.db")

    # SQL query to check the count of rows with the given user_id in the 'credit' table
    sql = "SELECT COUNT(*) FROM credit WHERE user_id = ?"

    # Execute the SQL query
    cur = conn.cursor()
    cur.execute(sql, (user_id,))

    # Fetch the result
    result = cur.fetchone()

    # If the count is greater than 0, the user exists in the table, so return True
    if result[0] > 0:
        return True
    else:
        return False


# Function to get the password of a user
def get_user_password(user_id, conn=None):
    # If no connection is provided, create a new connection to the database
    if conn is None:
        conn = create_connection(r"../self_automate.db")

    try:
        # SQL query to retrieve the password from the 'login' table for the given user_id
        sql = "SELECT password FROM login WHERE user_id = ?"

        # Execute the SQL query
        cur = conn.cursor()
        cur.execute(sql, (user_id,))

        # Fetch the result
        result = cur.fetchall()

        # Get the password from the result
        password = result[0][0]

        # Close the cursor
        cur.close()

        # Return the password
        return password
    except Exception as e:
        # Log any exceptions that occur
        logging.error(e)
        return None


# Function to get the username of a user
def get_username(user_id, conn=None):
    # If no connection is provided, create a new connection to the database
    if conn is None:
        conn = create_connection(r"../self_automate.db")

    try:
        # SQL query to retrieve the username from the 'bot' table for the given user_id
        sql = "SELECT username FROM bot WHERE user_id = ?"

        # Execute the SQL query
        cur = conn.cursor()
        cur.execute(sql, (user_id,))

        # Fetch the result
        result = cur.fetchall()

        # Get the username from the result
        username = result[0][0]

        # Close the cursor
        cur.close()

        # Return the username
        return username
    except Exception as e:
        # Log any exceptions that occur
        logging.error(e)
        return None


# Function to get the user_id based on the username
def get_user_id(user_id, conn=None):
    # If no connection is provided, create a new connection to the database
    if conn is None:
        conn = create_connection(r"../self_automate.db")

    try:
        # SQL query to retrieve the user_id from the 'bot' table based on the username
        sql = "SELECT user_id FROM bot WHERE username = ?"

        # Execute the SQL query
        cur = conn.cursor()
        cur.execute(sql, (user_id,))

        # Fetch the result
        result = cur.fetchall()

        # Get the user_id from the result
        user_id = result[0][0]

        # Close the cursor
        cur.close()

        # Return the user_id
        return user_id
    except Exception as e:
        # Log any exceptions that occur
        logging.error(e)
        return None


# Function to dump reserve data to a JSON file
def dump_reserve_data(user: User, response):
    with open(f'{BASE_DIR}\\backend\\reservation_datas\\{user.user_id}_{user.username}_rd.json', 'w+',
              encoding='utf-8') as f:
        dump(response.json(), f, indent=4, ensure_ascii=False)


# Function to dump reserve result to a JSON file
def dump_reserve_result(user: User, result: list):
    with open(f'{BASE_DIR}\\backend\\reservation_result\\{user.user_id}_{user.username}_rd.json', 'w+',
              encoding='utf-8') as f:
        dump(result, f, indent=4, ensure_ascii=False)


# Function to dump reserved foods to a JSON file
def dump_reserved_foods(user: User, result: list):
    with open(f'{BASE_DIR}\\backend\\last_reservation\\{user.user_id}_{user.username}_rd.json', 'w+',
              encoding='utf-8') as f:
        dump(result, f, indent=4, ensure_ascii=False)


# Function to load reserve result from a JSON file
def load_reserve_result(user: User):
    with open(f'{BASE_DIR}\\backend\\reservation_result\\{user.user_id}_{user.username}_rd.json', 'r',
              encoding='utf-8') as f:
        reservation_result = load(f)
        # Log success message
        logging.info("Reservation result loaded successfully")
    return reservation_result


# Function to create a priority queue for a user
def make_priority_queue(user: User):
    if not path.isfile(f'{BASE_DIR}\\backend\\priority_queue\\{user.user_id}_{user.username}_pq.json'):
        food = {}
        proxies = {
            "http": None,
            "https": None
        }
        data = requests.get(
            'https://self.shahroodut.ac.ir/api/v0/Reservation?fromdate=1401%2F07%2F01&todate=1402%2F02%2F20',
            cookies=get_cookies(user), proxies=proxies)
        data_json = loads(data.text)
        for i in data_json:
            food[i['FoodName']] = food.get(i['FoodName'], 0) + 1
        with open(f'{BASE_DIR}\\backend\\priority_queue\\{user.user_id}_{user.username}_pq.json', 'w',
                  encoding='utf-8') as f:
            dump(food, f, ensure_ascii=False)
    with open(f'{BASE_DIR}\\backend\\priority_queue\\{user.user_id}_{user.username}_pq.json', 'r',
              encoding='utf-8') as f:
        return load(f)


# Function to load reserved foods from a JSON file
def load_reserved_foods(user: User):
    with open(f'{BASE_DIR}\\backend\\last_reservation\\{user.user_id}_{user.username}_rd.json', 'r',
              encoding='utf-8') as f:
        last_reservation = load(f)
        # Log success message
        logging.info("Reservation result loaded successfully")
    return last_reservation


# Function to get the top 10 most reserved foods for a user
def get_most_reserved_food(user_id):
    if not path.isfile(f'{BASE_DIR}\\backend\\priority_queue\\{user_id}_{get_username(user_id)}_pq.json'):
        user = User(user_id)
        make_priority_queue(user)
    with open(f'{BASE_DIR}\\backend\\priority_queue\\{user_id}_{get_username(user_id)}_pq.json', 'r',
              encoding='utf-8') as f:
        data = load(f)
        sorted_dict = sorted(data.items(), key=lambda x: x[1], reverse=True)
        top_10 = sorted_dict[:10]
        return top_10
