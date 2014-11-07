from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from datetime import *
from dateutil.relativedelta import *
import sys
from pyvirtualdisplay import Display
from ConfigParser import SafeConfigParser
from argparse import ArgumentParser
import logging
import logging.config

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders


LOGIN = "60017396"
PWD = "9809"
BASE_URL = "https://online.fusion-lifestyle.com/Connect3/MRMLogin.aspx"

# the browser visibility
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
RESULT_LINK = "ctl00_MainContent__advanceSearchResultsUserControl_Activities_ctl02_Activity"
NEXT_DAY = "ctl00$MainContent$btnNextDate"
CONFIRM = "ctl00$MainContent$btnBook"
COURTS = {"ctl00$MainContent$grdResourceView$ctl02$ctl00": 1,
          "ctl00$MainContent$grdResourceView$ctl02$ctl01": 2}


GMAIL_USER = "stefano.borgia@gmail.com"
GMAIL_PWD = "Yttwoaifbtvotamhd"

def mail(to, subject, text, attach=None):
   msg = MIMEMultipart()
   msg['From'] = GMAIL_USER
   msg['To'] = to
   msg['Subject'] = subject
   if attach:
      msg.attach(MIMEText(text))
      part = MIMEBase('application', 'octet-stream')
      part.set_payload(open(attach, 'rb').read())
      Encoders.encode_base64(part)
      part.add_header('Content-Disposition',
                      'attachment; filename="{0}"'.format(path.basename(attach)))
      msg.attach(part)
   mailServer = smtplib.SMTP("smtp.gmail.com", 587)
   mailServer.ehlo()
   mailServer.starttls()
   mailServer.ehlo()
   mailServer.login(GMAIL_USER, GMAIL_PWD)
   mailServer.sendmail(GMAIL_USER, to, msg.as_string())
   mailServer.close()

def main():
    court = 0
    display = Display(visible=VISIBILITY, size=(800, 600))
    display.start()

    logging.basicConfig(filename='golden_lane.log',level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    log = logging.getLogger("golden_lane")

    # parser = ArgumentParser()
    # cfg = SafeConfigParser()
    # cfg.read(cfiles)

    now = datetime.now()

    booked = False  # booked flag
    start_hour = "19"
    end_hour = "20"
    start_day_to_book = (now + relativedelta(weeks=+1)).strftime("%d/%m/%Y") + " {0}:00:00".format(start_hour)
    end_day_to_book = (now + relativedelta(weeks=+1)).strftime("%d/%m/%Y") + " {0}:00:00".format(end_hour)

    log.info("booking outdoor tennis on day {0}".format(start_day_to_book))

    driver = webdriver.Firefox()
    driver.implicitly_wait(20)
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
    select.select_by_value(start_hour)

    # select end time
    select = Select(driver.find_element_by_name(END_HOUR_SELECTION))
    select.select_by_value(end_hour)

    # click search button
    element = driver.find_element_by_id(SEARCH_BUTTON)
    element.click()

    # wait
    wait = WebDriverWait(driver, 20)

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
    # element.click()

    log.info("booked court nr {0} for day {1}".format(court, start_day_to_book))
    mail("stefano.borgia@gmail.com",
        "Tennis (Court {0})".format(court),
        "day: {0}".format(start_day_to_book))
    # close selenium
    driver.close()

    # close xephyr
    display.stop()

if __name__ == "__main__":
    main()