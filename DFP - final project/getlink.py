# preparing for getskills.py

import time
import csv
import os
from datetime import datetime


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


CHROMEDRIVER_PATH = '/Users/zedrick/desktop/chromedriver' 
INDEX_URL = 'https://www.onetonline.org/find/all'

def get_occupation_data_with_selenium(index_page_url):

    occupation_data = []
    
    if not (CHROMEDRIVER_PATH and os.path.exists(CHROMEDRIVER_PATH)):
        print(f"ERROR '{CHROMEDRIVER_PATH}'")
        return []

    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service)

    try:
        driver.get(index_page_url)
        
        wait = WebDriverWait(driver, 30)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "a[href*='/link/summary/']")))
        print("Starting to extract occupation links...")

        link_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/link/summary/']")
        
        for element in link_elements:
            name = element.text
            url = element.get_attribute('href')

            if name and url:
                occupation_data.append({
                    'occupation_name': name,
                    'url': url
                })
                    
    except Exception as e:
        print(f"  - Selenium ERROR: {e}")
        return []
    finally:
        driver.quit()
        
    print(f"{len(occupation_data)} occupation links extracted.")
    return occupation_data

if __name__ == "__main__":
    output_dir = '/Users/zedrick/desktop'
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"ONET_Occupation_Links_{timestamp}.csv"
    full_file_path = os.path.join(output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)
    print(f"data will be saved in {full_file_path}")

    final_data = get_occupation_data_with_selenium(INDEX_URL)
    
    if not final_data:
        print("ERROR")
        exit()
        
    try:
        with open(full_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['occupation_name', 'url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(final_data)
        print(f"\n data has been saved in：{full_file_path} ---")
    except IOError:
        print(f"ERROR")
