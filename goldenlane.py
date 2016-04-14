from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException

import json
import pprint
from datetime import *
from dateutil.relativedelta import *
import sys
import os
from pyvirtualdisplay import Display
from ConfigParser import SafeConfigParser
import argparse
import logging
import logging.config
import smtplib
from time import sleep


parser = argparse.ArgumentParser(description='Book a tennis court at Goldenlane Leisure Center.')

parser.add_argument('-d', '--debug',
                    dest='debug',
                    action="store_true",
                    default=False,
                    help='write debug info on log file')

parser.add_argument('-c', '--crontab',
                    dest='cron',
                    action="store_true",
                    default=False,
                    help="if run from crontab don't use xephyr display")

args = parser.parse_args()

if args.debug:
    LOG_LEVEL = logging.DEBUG
else:
    LOG_LEVEL = logging.INFO

CRON = args.cron

logging.basicConfig(filename='goldenlane.log', level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger("goldenlane")


class GoldenLane:
    # element names on pages
    MEMBER_ID = "ctl00_MainContent_InputLogin"
    PASSWORD = "ctl00$MainContent$InputPassword"
    SUBMIT_LOGIN = "ctl00$MainContent$btnLogin"
    SEVEN_DAYS = "ctl00_MainContent__advanceSearchUserControl__lnkBtnSevenDaysTime"
    FACILITY_SELECTION = "ctl00$MainContent$_advanceSearchUserControl$SitesSimple"
    GOLDEN_LANE = "GLLC"
    ACTIVITY_SELECTION = "ctl00$MainContent$_advanceSearchUserControl$Activities"
    TENNIS_ACTIVITY = "GLTENNIS60"
    QUICK_BOOK = "ctl00_MainContent_MostRecentBookings1_Bookings_ctl01_bookingLink"
    START_HOUR_SELECTION = "ctl00$MainContent$_advanceSearchUserControl$StartTime"
    END_HOUR_SELECTION = "ctl00$MainContent$_advanceSearchUserControl$EndTime"
    SEARCH_BUTTON = "ctl00_MainContent__advanceSearchUserControl__searchBtn"
    RESULT_LINK = "ctl00_MainContent__advanceSearchResultsUserControl_Activities_ctl02_Activity"  # TODO sistemare
    NEXT_DAY = "ctl00$MainContent$btnNextDate"
    CONFIRM = "ctl00$MainContent$btnBook"
    COURTS = {"ctl00$MainContent$grdResourceView$ctl04$ctl00": 1,
              "ctl00$MainContent$grdResourceView$ctl04$ctl01": 2,
              #"ctl00$MainContent$grdResourceView$ctl03$ctl02": 1,  # TODO check this
              #"ctl00$MainContent$grdResourceView$ctl03$ctl00": 2
    }

    def __init__(self, config_file="goldenlane.conf"):
        cfg = json.loads(open("config.json").read())

        self.BASE_URL = cfg['config']['base_url']
        self.LOGIN = cfg['config']['login']
        self.pwd = cfg['config']['password']
        # self.booking = cfg.get('booking', 'BOOKING')
        # self.email = bool(cfg.get('booking', 'EMAIL'))
        # self.days_ahead = int(cfg.get('booking', 'DAYS_AHEAD'))
        # self.start_time = cfg.get('booking', 'START_TIME')
        # self.end_time = cfg.get('booking', 'END_TIME')
        #self.display = Display(visible=VISIBILITY, size=(1024, 768))



        display = Display(visible=0, size=(800, 800))
        display.start()
        self.driver = webdriver.Firefox()
        #     #options = webdriver.ChromeOptions()
        #     #options.binary_location = '/opt/google/chrome/google-chrome'
        #     #self.driver = webdriver.Chrome('/usr/bin/chromedriver',
        #     #                               chrome_options=options,
        #     #                               service_args=['--verbose'],
        #     #                               service_log_path='/home/isamicaste/python/goldenlane/chrome_driver.log')
        #     self.driver.implicitly_wait(2)
        #
        #     # wait
        #     wait = WebDriverWait(self.driver, 2)

    def load_first_page(self):
        self.driver.get(self.BASE_URL)

    def login(self, save_page=None):
        print "logging in"
        element = self.driver.find_element_by_id(self.MEMBER_ID)
        element.send_keys(self.LOGIN)
        # insert password
        element = self.driver.find_element_by_name(self.PASSWORD)
        element.send_keys(self.pwd)
        element = self.driver.find_element_by_name(self.SUBMIT_LOGIN)
        element.click()
        if save_page:
            self._save_page_source()

    def select_facility(self, facility_code, save_page=None):
        select = Select(self.driver.find_element_by_name(self.FACILITY_SELECTION))
        select.select_by_value(facility_code)
        element = self.driver.find_element_by_xpath("//*[@title='Tennis Outdoor 60mins']")
        # element = self.driver.find_element_by_link_text("Tennis Outdoor 60mins")
        element.click()
        element = self.driver.find_element_by_id("ctl00_MainContent_dateForward1")
        element.click()
        element = self.driver.find_element_by_id("ctl00_MainContent_cal_calbtn21")
        element.click()
        sleep(2)
        booked = False
        while not booked:
            try:
                element = self.driver.find_element_by_name("ctl00$MainContent$grdResourceView$ctl08$ctl01")  # court 2
                element.click()
                booked = True
            except selenium.common.exceptions.ElementNotVisibleException as e:
                try:
                    element = self.driver.find_element_by_name("ctl00$MainContent$grdResourceView$ctl08$ctl00")  # court 1
                    element.click()
                    booked = True
                except selenium.common.exceptions.ElementNotVisibleException as e:
                    sleep(5)

        # element = self.driver.find_element_by_xpath("//*[@id='ctl00_MainContent_grdResourceView']/tbody/tr[8]/td[2]/input")
        # element.click()
        # print len(element)
        # element[0].click()
        # print dir(element[0])
        # print element[0].get_attribute("class")
        # element[0].find_elements_by_xpath("//*[@value='10:00']")[0].click()
        # # select = Select(self.driver.find_element_by_name(self.ACTIVITY_SELECTION))
        # # select.select_by_value(self.TENNIS_ACTIVITY)
        # element = self.driver.find_element_by_name("ctl00$MainContent$_advanceSearchUserControl$startDate")
        # element.send_keys("2016-01-20")

        # element = self.driver.find_element_by_id(self.TENNIS_ACTIVITY)
        # element.click()

        if save_page:
            self._save_page_source(save_page)

    def close_session(self):
        self.driver.quit()
        # close xephyr
        # self.display.stop()
        #self.browser.quit()

    def _save_page_source(self, file_name):
        output_file = open(file_name, "w")
        output_file.write(self.driver.page_source.encode("utf-8"))


def main():
    goldenlane = GoldenLane()
    goldenlane.load_first_page()
    print dir(goldenlane)
    goldenlane.login(True)
    goldenlane.select_facility(goldenlane.GOLDEN_LANE, "output.txt")
    # goldenlane.close_session()





# DIOCANE ctl00_MainContent_cal_calbtn21 , ctl00$MainContent$grdResourceView$ctl08$ctl00, ctl00_MainContent_btnBasket
# CONFIG_FILE = "goldenlane.conf"
#
#
#
#
# # Load the config files
# cfg = SafeConfigParser()
# cfg.read(CONFIG_FILE)
#
# # Load configuration
# LOGIN = cfg.get('goldenlane', 'LOGIN')
# PWD = cfg.get('goldenlane', 'PASSWORD')
# TO = cfg.get('mail', 'TO').split(',')
# BASE_URL = cfg.get('main', 'BASE_URL')
# START_TIME = cfg.get('booking', 'START_TIME')
# END_TIME = cfg.get('booking', 'END_TIME')
# DAYS_AHEAD = int(cfg.get('booking', 'DAYS_AHEAD'))
#
# # confirm booking
# _booking = cfg.get('booking', 'BOOKING')
# if _booking in ['True', 'true']:
#     BOOKING = True
# else:
#     BOOKING = False
#
# # email sending
# _email = cfg.get('booking', 'EMAIL')
# if _email in ['True', 'true']:
#     EMAIL = True
#     GMAIL_USER = cfg.get('mail', 'LOGIN')
#     GMAIL_PWD = cfg.get('mail', 'PASSWORD')
# else:
#     EMAIL = False
#
# # the browser visibility
# _visibility = cfg.get('main', 'VISIBILITY')
# if _visibility in ['True', 'true']:
#     VISIBILITY = True
# else:
#     VISIBILITY = False
#
# # element names on pages
# MEMBER_ID = "ctl00$MainContent$InputLogin"
# PASSWORD = "ctl00$MainContent$InputPassword"
# SUBMIT_LOGIN = "ctl00$MainContent$btnLogin"
# ACTIVITY_SELECTION = "ctl00$MainContent$_advanceSearchUserControl$Activities"
# TENNIS_ACTIVITY = "GLTENNIS60"
# START_HOUR_SELECTION = "ctl00$MainContent$_advanceSearchUserControl$StartTime"
# END_HOUR_SELECTION = "ctl00$MainContent$_advanceSearchUserControl$EndTime"
# SEARCH_BUTTON = "ctl00_MainContent__advanceSearchUserControl__searchBtn"
# RESULT_LINK = "ctl00_MainContent__advanceSearchResultsUserControl_Activities_ctl02_Activity"  # TODO sistemare
# NEXT_DAY = "ctl00$MainContent$btnNextDate"
# CONFIRM = "ctl00$MainContent$btnBook"
# COURTS = {"ctl00$MainContent$grdResourceView$ctl04$ctl00": 1,
#           "ctl00$MainContent$grdResourceView$ctl04$ctl01": 2,
#           #"ctl00$MainContent$grdResourceView$ctl03$ctl02": 1,  # TODO check this
#           #"ctl00$MainContent$grdResourceView$ctl03$ctl00": 2
# }
#
#
# def send_mail(to, subject, text, attach=None):
#     log.info("sending email...")
#     session = smtplib.SMTP('smtp.gmail.com', 587)
#     session.ehlo()
#     session.starttls()
#     session.login(GMAIL_USER, GMAIL_PWD)
#     headers = " \n".join(["From: " + GMAIL_USER,
#                           "Subject: " + subject,
#                           "To: " + " ,".join(to),
#                           "mime-version: 1.0",
#                           "content-type: text/html"])
#
#     content = headers + "\r\n\r\n" + text
#     session.sendmail(GMAIL_USER, to, content)
#     session.close()
#     log.info("Done")
#
#
# def is_court_booked(day):
#     try:
#         lockfile = open("goldenlane.lock", "r")
#         for line in lockfile:
#             if day in line:
#                 return True
#     except:
#         return False
#     return False
#
#
#
#
#
# def mainOLD():
#     #if not CRON:
#         #display = Display(visible=VISIBILITY, size=(1024, 768))
#         #display.start()
#
#     now = datetime.now()
#     #browser = webdriver.Chrome()
#
#     today = (now + relativedelta(days=+DAYS_AHEAD)).strftime("%d/%m/%Y")
#     start_day_to_book = today + " {0}:00:00".format(START_TIME)
#     end_day_to_book = today + " {0}:00:00".format(END_TIME)
#
#     # check that the court isn't already been booked
#     if is_court_booked(today):
#         log.info("a court has been booked already for day {0}".format(today))
#         sys.exit()
#     log.info("booking outdoor tennis on day {0}".format(start_day_to_book))
#
#     #options = webdriver.ChromeOptions()
# #    options.binary_location = '/opt/google/chrome/google-chrome'
#     driver = webdriver.Firefox()
#     #driver = webdriver.Chrome('/usr/bin/chromedriver',
#     #                          chrome_options=options,
#     #                          service_args=['--verbose'],
#     #                          service_log_path='/home/isamicaste/python/goldenlane/chrome_driver.log')
#     driver.implicitly_wait(2)
#
#     # wait
#     wait = WebDriverWait(driver, 2)
#
#     driver.get(BASE_URL)
#
#     # insert member id
#     element = driver.find_element_by_name(MEMBER_ID)
#     element.send_keys(LOGIN)
#
#     # insert password
#     element = driver.find_element_by_name(PASSWORD)
#     element.send_keys(PWD)
#
#     # submit
#     element = driver.find_element_by_name(SUBMIT_LOGIN)
#     element.click()
#
#     # select Tennis Outdoor 60mins from Activity
#     select = Select(driver.find_element_by_name(ACTIVITY_SELECTION))
#     select.select_by_value(TENNIS_ACTIVITY)
#
#
#     # # insert start date TODO this doesn't work, a javascript is run when inserting text
#     # element = driver.find_element_by_name("ctl00$MainContent$_advanceSearchUserControl$startDate")
#     # element.send_keys(start_day_to_book)
#     # insert end date
#     # element = driver.find_element_by_name("ctl00$MainContent$_advanceSearchUserControl$endDate")
#     # element.send_keys(end_day_to_book)
#
#     # select start time
#     select = Select(driver.find_element_by_name(START_HOUR_SELECTION))
#     select.select_by_value(START_TIME)
#
#     # select end time
#     select = Select(driver.find_element_by_name(END_HOUR_SELECTION))
#     select.select_by_value(END_TIME)
#
#     # click search button
#     search_button_active = False
#     count = 1
#     while not search_button_active and count < 400:
#         try:
#             element = wait.until(expected_conditions.element_to_be_clickable((By.ID, SEARCH_BUTTON)))
#             # element = driver.find_element_by_id(SEARCH_BUTTON)
#             element.click()
#             search_button_active = True
#         except StaleElementReferenceException:
#             log.info('search button not yet available')
#         if not search_button_active:
#             count += 1
#             log.info('waiting for the search button to become active')
#
#     if not search_button_active:
#         log.error('search button not available')
#         sys.exit()
#
#     # wait until the search has been performed (the search button is no more clickable)
#     _element = wait.until_not(expected_conditions.element_to_be_clickable((By.ID, SEARCH_BUTTON)))
#
#     # follow result link
#     element = driver.find_element_by_id(RESULT_LINK)
#     element.click()
#
#
#     # cycle the next day button DAYS_AHEAD times
#     for _ in xrange(DAYS_AHEAD):
#         element = driver.find_element_by_name(NEXT_DAY)
#         element.click()
#
#     # check if the court has
#     # book court TODO select court 1 or 2
#     booked = False
#     count = 1
#     while not booked and count < 400:
#         try:
#             log.info('looking for a free court.')
#             elements = driver.find_elements_by_xpath("//td[@class='itemavailable']/input[@class='removeUnderLineAvailable']")
#             for element in elements:
#                 if not booked:
#                     court = COURTS[element.get_attribute('name')]
#                     element.click()
#                     booked = True
#         except NoSuchElementException:
#             log.debug('NoSuchElementException')
#         if not booked:
#             log.info("No courts available on day {0}. Trying again in 5 seconds. {1} tries remaining".format(
#                 start_day_to_book,
#                 400 - count))
#             count += 1
#
#     if not booked:
#         log.info("No courts available on day {0}".format(start_day_to_book))
#         driver.quit()
#         browser.quit()
#         sys.exit()
#
#     # confirm booking
#     if BOOKING:
#         element = driver.find_element_by_name(CONFIRM)
#         element.click()
#         with open('goldenlane.lock', "a") as lockfile:
#             lockfile.write(today+'\n')
#         log.info("booked court nr {0} for day {1}".format(court, start_day_to_book))
#     else:
#
#         # with open('goldenlane.lock', "a") as lockfile:
#         #     lockfile.write(today+'\n')
#         log.info("court wasn't booked because BOOKING property is set to False")
#
#     # send email
#     if EMAIL:
#         send_mail(TO,
#                   "Golden Lane {0} Court {1}".format(start_day_to_book, court),
#                   "day: {0}".format(start_day_to_book))
#
#     # close selenium
#     driver.quit()
#     if not CRON:
#         # close xephyr
#         display.stop()
#         browser.quit()
#         sys.exit()




if __name__ == "__main__":
    main()


