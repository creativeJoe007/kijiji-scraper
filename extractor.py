import re
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of, presence_of_element_located
import json
from pathlib import Path
import csv

class Extractor():
 #------------------------------------------------------------------------
 # This is where we extract all the data we need while scrapping
 # We take our screenshots here, get titles, find social media pages
 #  Of users we extract
 #------------------------------------------------------------------------
  def __init__(self, driver, query, email_address, password, file_name):
    self._driver = driver
    self._total_pages = 1
    self.email = email_address
    self.password = password
    self.query = query
    self._file_name = file_name

    # We loop through the enter data wrapped under pagination
    search_ads = f"https://www.kijiji.ca/b-medicine-hat/{self.query}/k0l1700231?dc=true"
    self.get_pagination(search_ads)

  def get_pagination(self, url):
    while True:
      try:
        search_ads = url
        self._driver.get(search_ads)
        self.scrape_ads_page()

        next_button = self._driver.find_element_by_css_selector("div.pagination")\
          .find_element_by_xpath("//a[@title='Next']")
        
        self.get_pagination(next_button.get_attribute("href"))
      except NoSuchElementException as e:
        break

  def scrape_ads_page(self):
    #---------------------------------------------------------------------------------------
    # We scrape all ads in the page
    # extract the data like image, description, title and price
    # We add this to our individual data dict
    #---------------------------------------------------------------------------------------
    ads_data = self._driver.find_elements_by_css_selector("div.search-item.regular-ad")
    for ads in ads_data:
      self._ad = {
        "title": "",
        "image": "",
        "price": "",
        "description": "",
        "ad_url": "",
        "mobile": "",
      }
      ads_title_container = ads.find_element_by_css_selector("a.title")
      self._ad["price"] = ads.find_element_by_css_selector("div.price").text
      self._ad["description"] = ads.find_element_by_css_selector("div.description").text
      self._ad["title"] = ads_title_container.text
      self._ad["ad_url"] = ads_title_container.get_attribute("href")

      # Because some products don't have pictures so we have to prevent an error
      try:
        self._ad["image"] = ads.find_element_by_css_selector("div.left-col")\
          .find_element_by_css_selector("div.image")\
          .find_element_by_tag_name("picture")\
          .find_element_by_tag_name("img")\
          .get_attribute("src")
      except NoSuchElementException as e:
        continue

      self.open_advertisement()
      self.write_to_file(self._ad)
      print(f"\nAds\n: {self._ad}")
      # break

  def open_advertisement(self):
    # Start a new tab
    self.window_handler("start")
    self._driver.get(self._ad["ad_url"] )
    # time.sleep(5)
    default_text = "Hi, I'm interested! Please contact me if this is still available."
    self.send_message(True)
    self.window_handler("stop")

  def login(self):
    # load login page
    try:
      WebDriverWait(self._driver, 20).until(
        presence_of_element_located((By.CLASS_NAME, "modalScrollContainer-1392547362"))
      )

      self._driver.switch_to.frame(self._driver.find_element_by_id("iframeAuth-undefined"));
      WebDriverWait(self._driver, 10).until(
        presence_of_element_located((By.CLASS_NAME, "loginForm-1114518310"))
      )

      modal = self._driver.find_element_by_css_selector("form.loginForm-1114518310")
      email = modal.find_element_by_id("emailOrNickname")
      password = modal.find_element_by_id("password")

      email.send_keys(self.email)
      password.send_keys(self.password)

      modal.find_element_by_css_selector("button.signInButton-1815033393").click()
      # Wait for the loging process to get completed
      WebDriverWait(self._driver, 10).until(
        staleness_of(modal)
      )
      self._driver.switch_to.default_content()
      #---------------------------------------------------------------------------------------
      # Because Kijiji throws when you just login and attempt to send a message
      # We refresh the page and proceed with our scraping
      #---------------------------------------------------------------------------------------
      self._driver.refresh()
    except NoSuchElementException as e:
      print(e)
      print(f"Login error: {str(e)}")
    except TimeoutException as er:
      print(er)
      print(f"Timeout error: {str(er)}")

  def extract_phone_number(self):
    try:
      number_container = self._driver.find_element_by_css_selector("div.profileItem-324401486")
      # We click the reveal button
      reveal_button = number_container.find_element_by_css_selector("button.phoneNumberContainer-69344174").click()
      # We make the system sleep, should the reveal button takes time to change the number
      time.sleep(3)
      self._ad["mobile"] = number_container.find_element_by_css_selector("span.phoneShowNumberButton-1052915314").text

    except NoSuchElementException as e:
      print(f"Most likely doesn't have a mobile number {str(e)}")

  def window_handler(self, action):
    if action =="start":
      self._driver.execute_script("window.open('');")
      self._driver.switch_to.window(self._driver.window_handles[len(self._driver.window_handles) - 1])

    else:
      self._driver.close()
      self._driver.switch_to.window(self._driver.window_handles[len(self._driver.window_handles) - 1])

  def send_message(self, should_wait: bool):
    try:
      #---------------------------------------------------------------------------------------
      # We check if the message is the default in Kijiji
      # If yes, the user hasn't logged in
      # The "should_wait" parameter is useful for checking if we are performing a login first
      #---------------------------------------------------------------------------------------
      message_box_container = WebDriverWait(self._driver, (20 if should_wait == True else 5)).until(
        presence_of_element_located((By.CSS_SELECTOR, "form.form-4168487082"))
      )
      # Perform random scrolling
      message_field = message_box_container\
        .find_element_by_id("message")

      #---------------------------------------------------------------------------------------
      # Kijiji, usually auto fill the box for us should the user not be logged in
      # So if it doesn't fill it up for us, then the user is logged in
      # So to show a submit button on Kijiji we would need to focus on the message box
      # That's we are doing with this if below
      #---------------------------------------------------------------------------------------

      # We check if the login link is present, meaning the user hasn't logged in
      try:
        submit_button = message_box_container\
          .find_element_by_css_selector("div.fieldWithSpace-703296978")\
          .find_element_by_css_selector("button.submitButton-2507489961")
        login_box = self._driver.find_element_by_css_selector("div.root-882857460")
        login_href = login_box.find_element_by_css_selector("a.link-2454463992")
        # We click the submit button
        submit_button.click()
        #---------------------------------------------------------------------------------------
        # Because user has logged in, the submit button would
        # Ask the user to login, so this function handles that
        #---------------------------------------------------------------------------------------
        self.login()
      except NoSuchElementException as e:
        print(e)
        print("User is already logged in")

      # After performing login, we go ahead to send a message
      try:
        self.extract_phone_number()

        message_field.clear()
        time.sleep(1)
        message_field.send_keys("Hello, what's up")
        submit_button = message_box_container\
          .find_element_by_css_selector("button.submitButton-2507489961.button-1997310527")
        # We click the submit button
        time.sleep(1)
        submit_button.click()
        time.sleep(1)
        self.resolve_captcha()
        self.screengrab(self._ad["title"])
        time.sleep(60)
      except StaleElementReferenceException as e:
        print("Stale element")
        self.send_message(False)

    except NoSuchElementException as e:
      print(e)
      print(f"Sending message Page: {str(e)}")
    except TimeoutException as e:
      print(e)
      print("Opps timed out")

  def resolve_captcha(self):
    captcha_frame = self._driver.find_element_by_xpath("//iframe[@title='recaptcha challenge']")
    grand_parent_element = captcha_frame.find_element_by_xpath("../..")

    while grand_parent_element.is_displayed():
      pass
  
  def screengrab(self, file_name: str):
   try:
    # Close every modal should any arise
    ActionChains(self._driver).send_keys(Keys.ESCAPE).perform()

    self._driver.find_element_by_tag_name('body').screenshot(file_name)

   except NoSuchElementException as e:
     print("Opps, failed")

  def scroll_page_randomly(self, scroll_x_times: int):
    from random import randrange
    scrolled_x_times = 0
    while scrolled_x_times <= scroll_x_times:
      scroll_to = randrange(1080)
      self._driver.execute_script(f"window.scrollTo(0, {scroll_to});")
      scrolled_x_times += 1
      time.sleep(2)
    self._driver.execute_script(f"window.scrollTo(0, 0);")

  def write_to_file(self, data: dict):
    # ------------------------------------------------------------------------
    # We check if the file already exist before we being, if the file
    # Exist, we simply append the new data as the header for the CSV file has
    # Already be created
    # Else we add CSV header first before adding the data to file
    # ------------------------------------------------------------------------
    extracted_path = Path("extracted/")
    save_file_to = extracted_path / f"{self._file_name}.csv"
    file_path_object = Path(save_file_to)
    file_exist = file_path_object.is_file()
    if file_exist is False:
      Path(save_file_to).touch()

    with open(save_file_to, 'a', newline='') as file:
        writer = csv.writer(file, delimiter='|')
        # Add header only if the file doesn't exist
        if file_exist is False: writer.writerow(data.keys())
        # Add new data 
        writer.writerow(data.values())
        file.close()