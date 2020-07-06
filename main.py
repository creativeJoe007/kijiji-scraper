from selenium import webdriver
import argparse
from webdriver_manager.chrome import ChromeDriverManager
from extractor import Extractor
from selenium.webdriver.chrome.options import Options
from println import println

driver = None;
arguments = argparse.ArgumentParser()

arguments.add_argument('query', action='store', type=str, help="This is your kijiji search query and should be written as a string")
arguments.add_argument('--email', action='store', type=str, help="Your Kijiji Email")
arguments.add_argument('--password', action='store', type=str, help="Your Kijiji Password")
arguments.add_argument('--file', action='store', type=str, required=True, help="File name to save extracted data")

args = arguments.parse_args()

driver = None;

def main():
  chrome_options = Options()
  # chrome_options.add_argument('--headless')
  chrome_options.add_argument('--start-maximized')
  chrome_options.add_extension('./captcha.crx')

  query = args.query
  email = args.email
  password = args.password
  file_name = args.file

 # Determine If we reuse chrome instance or create a new one
  driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options);
  executor_url = driver.command_executor._url
  session_id = driver.session_id

  # Maximize chrome height to highest
  # driver.set_window_size(1920, 8000)
  extractor = Extractor(driver, query, email, password, file_name)
  
  driver.close();

main()