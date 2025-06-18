from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

# Setup Chrome with options
options = uc.ChromeOptions()
#options.add_argument("--headless")  # Run in background
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")


driver = uc.Chrome(options=options, version_main=137)  # match your Chromium version
driver.get("https://bot.sannysoft.com/")


def crawl_area(url, depth=0):
    driver.get(url)
    time.sleep(2)

    # Check for sub-areas
    subareas = driver.find_elements(By.CSS_SELECTOR, "div.area a.mappin.located")
    
    if subareas:
        for a in subareas:
            crawl_area(a.get_attribute("href"), depth + 1)
    else:
        # No more sub-areas, extract lat/long and name
        name = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]').get_attribute("content")
        lat = driver.find_element(By.CSS_SELECTOR, 'meta[property="place:location:latitude"]').get_attribute("content")
        lon = driver.find_element(By.CSS_SELECTOR, 'meta[property="place:location:longitude"]').get_attribute("content")
        print(name, lat, lon)


crawl_area("https://www.thecrag.com/en/climbing/world")
