import requests
from json import dump, load
from selenium import webdriver
from selenium.webdriver.common.by import By
import logging
import sqlite3
from sqlite3 import Error
from bs4 import BeautifulSoup
import jdatetime
from os import path, mkdir

logging.basicConfig(filename='backend.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s', encoding='utf-8')


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        return sqlite3.connect(db_file)
    except Error as e:
        logging.error(f"Error creating connection to database. {e}")

    return None


def generate_cookies(username):
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    password = check_if_user_exist(username)

    with webdriver.Chrome(options=options) as driver:
        driver.get("https://self.shahroodut.ac.ir")

        driver.find_element('id', 'username').send_keys(username)

        driver.find_element('id', 'password').send_keys(password)

        driver.find_element(By.CLASS_NAME, "btn.btn-primary.btn-block.btn-flat").click()

        error = BeautifulSoup(driver.page_source, 'html.parser').find('div', attrs={"class": "text-red ng-binding"})
        if error is None:
            request_verification_token = driver.get_cookies()[0]['value']
            jahangostar_setare = driver.get_cookies()[1]['value']

            insert_cookies(request_verification_token, jahangostar_setare, username)
            # Log success message
            logging.info("Cookies generated successfully")

        else:
            # Log error message
            logging.error(f"Failed to generate cookies. {error.string.strip()}")
            update_password(username)
            raise Exception("Failed to generate cookies")


def insert_cookies(request_verification_token, jahangostar_setare, usename, conn=None):
    if conn is None:
        conn = create_connection(r"../self_automate.db")
    sql = "UPDATE backend SET cookie_requestverificationtoken = ?, cookie_jahangostarsetare = ? WHERE username = ?;"
    cur = conn.cursor()
    cur.execute(sql, (request_verification_token, jahangostar_setare, usename))
    conn.commit()
    cur.close()
    conn.close()


def get_cookies(username, conn=None):
    """
    Get cookies for a given username from the database.
    If cookies are not found in the database, generate new ones.
    :param username: The username to look up cookies for.
    :param conn: Optional connection object to use for the database. If None, create a new connection.
    :return: A dictionary containing the cookies.
    """
    if conn is None:
        conn = create_connection(r"../self_automate.db")
    sql = "SELECT cookie_requestverificationtoken, cookie_jahangostarsetare FROM backend WHERE username = ?;"
    cur = conn.cursor()
    cur.execute(sql, (username,))
    result = cur.fetchall()
    cur.close()
    if not result:
        # Log error message
        logging.error("Cookies not found in database, generating new cookies...")
        generate_cookies(username)  # Generate and return the cookies
        return get_cookies(username)
    cookies = {
        "JahangostarSetare": result[0][1],
        "__RequestVerificationToken": result[0][0]
    }
    # Log success message
    logging.info("Cookies loaded successfully")
    return cookies


def get_reserve_data(username, session=None):
    if not session:
        session = requests.Session()
    if check_day():
        response = session.get("https://self.shahroodut.ac.ir/api/v0/Reservation?lastdate=&navigation=0",
                               cookies=get_cookies(username),
                               allow_redirects=False)
    else:
        response = session.get("https://self.shahroodut.ac.ir/api/v0/Reservation?lastdate=&navigation=+7",
                               cookies=get_cookies(username),
                               allow_redirects=False)

    # Log success message
    logging.info("Reservation data retrieved successfully")

    return response


def check_day():
    # Check if the weekday is greater than or equal to 4 (i.e., Thursday)
    if jdatetime.datetime.now().date().weekday() >= 4:
        # If the weekday is Thursday or later, return False
        return False

    # If the weekday is earlier than Thursday, return True
    return True

def update_password(username, conn=None):
    password = input('enter new password')
    sql = "UPDATE backend SET password = ? WHERE username = ?;"
    if conn is None:
        conn = create_connection(r"../self_automate.db")
    cur = conn.cursor()
    cur.execute(sql, (password, username))
    conn.commit()
    conn.close()
    return generate_cookies(username)


def read_reserve_data(username):
    with open(f'./reservation_datas/reservation_data_{username}.json', 'r', encoding='utf-8') as f:
        reservation_data = load(f)
        # Log success message
        logging.info("Reservation data loaded successfully")
    return reservation_data


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        logging.error(f"Error creating table. {e}")


def create_tables(conn):
    sql_create_backend_table = """ CREATE TABLE IF NOT EXISTS backend (
                                    username integer PRIMARY KEY,
                                    password text NOT NULL,
                                    cookie_requestverificationtoken text,
                                    cookie_jahangostarsetare
                                ); """

    create_table(conn, sql_create_backend_table)
    sql_create_urls_table = """CREATE TABLE IF NOT EXISTS bot (
                                    user_id integer PRIMARY KEY,
                                    username text NOT NULL,
                                    password integer NOT NULL
                                );"""

    create_table(conn, sql_create_urls_table)


def initialize_data_base():

    if not path.isdir('./reservation_datas/'):
        mkdir('./reservation_datas/')

    database = r"../self_automate.db"

    conn = create_connection(database)

    if conn is not None:
        create_tables(conn)
    else:
        logging.error("Error! cannot create the database connection.")


def add_user_to_backend_database(username, password, conn):
    sql = f"INSERT INTO backend ( username, password) VALUES (?, ?);"
    cur = conn.cursor()
    cur.execute(sql, (username, password))
    conn.commit()
    cur.close()


def check_if_user_exist(username, conn=None):
    if conn is None:
        conn = create_connection(r"../self_automate.db")
    sql = "SELECT password FROM backend WHERE username = ?"
    cur = conn.cursor()
    cur.execute(sql, (int(username),))
    result = cur.fetchall()
    if not result:
        logging.warning('User does not exist!')
        password = input('Enter a password for this user: ')
        add_user_to_backend_database(username, password, conn)
        return check_if_user_exist(username)
    password = result[0][0]
    cur.close()
    return password
