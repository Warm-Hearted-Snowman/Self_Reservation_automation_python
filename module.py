import requests
from json import dump, load
from selenium import webdriver
from selenium.webdriver.common.by import By

with open('info.json', 'r') as f:
    info = load(f)
    default_username=info['username']
    defalt_password=info['password']

def generate_cookies(username=default_username, password=defalt_password):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    with webdriver.Chrome(options=options) as driver:
        driver.get("https://self.shahroodut.ac.ir")

        driver.find_element('id', 'username').send_keys(username)

        driver.find_element('id', 'password').send_keys(password)

        driver.find_element(By.CLASS_NAME, "btn.btn-primary.btn-block.btn-flat").click()

        RequestVerificationToken = driver.get_cookies()[0]['value']
        JahangostarSetare = driver.get_cookies()[1]['value']
        cookies = {
            "__RequestVerificationToken": RequestVerificationToken,
            "JahangostarSetare": JahangostarSetare
        }
        with open('cookies.json', 'w') as f:
            dump(cookies, f)

    return cookies


def get_cookies():
    try:
        with open('cookies.json', 'r') as f:
            cookies = load(f)
    except FileNotFoundError:
        return generate_cookies()
    return cookies


def get_reserve_data(session=None):
    if not session:
        session = requests.Session()
    response = session.get("https://self.shahroodut.ac.ir/api/v0/Reservation?lastdate=&navigation=0",
                           cookies=get_cookies(),
                           allow_redirects=False)
    return response


def read_reserve_data():
    with open('reservation_data.json', 'r') as f:
        reservation_data = load(f)
    return reservation_data
