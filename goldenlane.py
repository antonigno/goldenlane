from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

from datetime import *
from dateutil.relativedelta import *
import sys
from pyvirtualdisplay import Display
from ConfigParser import SafeConfigParser
import logging
import logging.config

import smtplib

logging.basicConfig(filename='goldenlane.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger("goldenlane")

CONFIG_FILE = "goldenlane.conf"

# Load the config files
cfg = SafeConfigParser()
cfg.read(CONFIG_FILE)

# Load configuration
LOGIN = cfg.get('goldenlane', 'LOGIN')
PWD = cfg.get('goldenlane', 'PASSWORD')
GMAIL_USER = cfg.get('mail', 'LOGIN')
GMAIL_PWD = cfg.get('mail', 'PASSWORD')
TO = cfg.get('mail', 'TO').split(',')
BASE_URL = cfg.get('main', 'BASE_URL')
START_TIME = cfg.get('booking', 'START_TIME')
END_TIME = cfg.get('booking', 'END_TIME')
DAYS_AHEAD = cfg.get('booking', 'DAYS_AHEAD')

# the browser visibility
visibility_bool = cfg.get('main', 'VISIBILITY')
if visibility_bool in ['True', 'true']:
    VISIBILITY = True
else:
    VISIBILITY = False

# element names on pages
MEMBER_ID = "ctl00$MainContent$InputLogin"
PASSWORD = "ctl00$MainContent$InputPassword"
SUBMIT_LOGIN = "ctl00$MainContent$btnLogin"
ACTIVITY_SELECTION = "ctl00$MainContent$_advanceSearchUserControl$Activities"
TENNIS_ACTIVITY = "GLTENNIS60"
START_HOUR_SELECTION = "ctl00$MainContent$_advanceSearchUserControl$StartTime"
END_HOUR_SELECTION = "ctl00$MainContent$_advanceSearchUserControl$EndTime"
SEARCH_BUTTON = "ctl00_MainContent__advanceSearchUserControl__searchBtn"
RESULT_LINK = "ctl00_MainContent__advanceSearchResultsUserControl_Activities_ctl02_Activity"  # TODO sistemare
NEXT_DAY = "ctl00$MainContent$btnNextDate"
CONFIRM = "ctl00$MainContent$btnBook"
COURTS = {"ctl00$MainContent$grdResourceView$ctl02$ctl00": 1,
          "ctl00$MainContent$grdResourceView$ctl02$ctl01": 2}


def send_mail(to, subject, text, attach=None):
    log.info("sending email...")
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.ehlo()
    session.starttls()
    session.login(GMAIL_USER, GMAIL_PWD)
    headers = " \n".join(["From: " + GMAIL_USER,
                          "Subject: " + subject,
                          "To: " + " ,".join(to),
                          "mime-version: 1.0",
                          "content-type: text/html"])

    content = headers + "\r\n\r\n" + text
    session.sendmail(GMAIL_USER, to, content)
    session.close()
    log.info("Done")


def main():
    display = Display(visible=0, size=(1024, 768))
    display.start()

    now = datetime.now()

    booked = False  # booked flag
    start_day_to_book = (now + relativedelta(weeks=+1)).strftime("%d/%m/%Y") + " {0}:00:00".format(START_TIME)
    end_day_to_book = (now + relativedelta(weeks=+1)).strftime("%d/%m/%Y") + " {0}:00:00".format(END_TIME)

    log.info("booking outdoor tennis on day {0}".format(start_day_to_book))

    driver = webdriver.Firefox()
    driver.implicitly_wait(20)

    # wait
    wait = WebDriverWait(driver, 10)

    driver.get(BASE_URL)

    # insert member id
    element = driver.find_element_by_name(MEMBER_ID)
    element.send_keys(LOGIN)

    # insert password
    element = driver.find_element_by_name(PASSWORD)
    element.send_keys(PWD)

    # submit
    element = driver.find_element_by_name(SUBMIT_LOGIN)
    element.click()

    # select Tennis Outdoor 60mins from Activity
    select = Select(driver.find_element_by_name(ACTIVITY_SELECTION))
    select.select_by_value(TENNIS_ACTIVITY)


    # # insert start date TODO this doesn't work, a javascript is run when inserting text
    # element = driver.find_element_by_name("ctl00$MainContent$_advanceSearchUserControl$startDate")
    # element.send_keys(start_day_to_book)
    # insert end date
    # element = driver.find_element_by_name("ctl00$MainContent$_advanceSearchUserControl$endDate")
    # element.send_keys(end_day_to_book)

    # select start time
    select = Select(driver.find_element_by_name(START_HOUR_SELECTION))
    select.select_by_value(START_TIME)

    # select end time
    select = Select(driver.find_element_by_name(END_HOUR_SELECTION))
    select.select_by_value(END_TIME)

    # click search button
    element = wait.until(expected_conditions.element_to_be_clickable((By.ID, SEARCH_BUTTON)))
    # element = driver.find_element_by_id(SEARCH_BUTTON)
    element.click()

    # wait until the search has been performed (the search button is no more clickable)
    _element = wait.until_not(expected_conditions.element_to_be_clickable((By.ID, SEARCH_BUTTON)))

    # follow result link
    element = driver.find_element_by_id(RESULT_LINK)
    element.click()

    # cycle the next day button 7 times
    for _ in xrange(6):
        element = driver.find_element_by_name(NEXT_DAY)
        element.click()

    # book court TODO select court 1 or 2
    try:
        elements = driver.find_elements_by_xpath("//td[@class='itemavailable']/input[@class='removeUnderLineAvailable']")
        for element in elements:
            if not booked:
                court = COURTS[element.get_attribute('name')]
                element.click()
                booked = True
    except NoSuchElementException:
        log.info("No courts available for day {0}".format(start_day_to_book))
        sys.exit()

    # confirm booking
    element = driver.find_element_by_name(CONFIRM)
    # TODO uncomment to actually book, then check for response
    #element.click()

    log.info("booked court nr {0} for day {1}".format(court, start_day_to_book))
    send_mail(TO,
              "Golden Lane {0} Court {1}".format(start_day_to_book, court),
              "day: {0}".format(start_day_to_book))

    # close selenium
    driver.close()

    # close xephyr
    display.stop()

if __name__ == "__main__":
    main()