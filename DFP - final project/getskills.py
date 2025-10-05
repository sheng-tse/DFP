import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import time
import os
import re

# --- CONFIGURATION ---
INPUT_CSV_FILE = '/Users/zedrick/desktop/ONET_Occupation_Links_2025-10-03.csv'
OUTPUT_CSV_FILE = '/Users/zedrick/desktop/ONET_Technology_Skills_FINAL_Output.csv'
CHROMEDRIVER_PATH = '/users/zedrick/desktop/chromedriver'

def main():
    """
    Final production version: Processes all occupation links from the CSV file.
    """
    # --- File and Browser Setup ---
    if not os.path.exists(INPUT_CSV_FILE):
        print(f"Error: Input file not found at '{INPUT_CSV_FILE}'.")
        return

    service = Service(executable_path=CHROMEDRIVER_PATH)
    options = webdriver.ChromeOptions()
    # If you don't want to see the browser window, uncomment the line below
    # options.add_argument('--headless') 
    
    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome browser started successfully!")
    except WebDriverException as e:
        print(f"\nError: Failed to start the browser.\nError details: {e}")
        return
        
    try:
        # Read the entire CSV file
        df = pd.read_csv(INPUT_CSV_FILE)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        if driver: driver.quit()
        return

    # --- Core Processing Logic ---
    results = []
    total_rows = len(df)
    print(f"\n--- Starting to process all {total_rows} occupation links ---")

    # Iterate over each row in the CSV file
    for index, row in df.iterrows():
        occupation_name = row['occupation_name']
        url = row['url']
        print(f"Processing ({index + 1}/{total_rows}): {occupation_name}")
    
        try:
            # 1. Visit the page
            driver.get(url)
            
            # 2. Locate the section
            wait = WebDriverWait(driver, 15)
            technology_section_xpath = "//h2[text()='Technology Skills']/.."
            technology_section_element = wait.until(
                EC.presence_of_element_located((By.XPATH, technology_section_xpath))
            )

            # 3. Click the expand button
            try:
                expand_button = technology_section_element.find_element(By.CSS_SELECTOR, 'button[data-bs-target=".long_TechnologySkills"]')
                driver.execute_script("arguments[0].click();", expand_button)
                time.sleep(1) # Wait 1 second for content to load after click
            except Exception:
                # It's okay if the expand button is not found, just continue
                pass

            # 4. Extract HTML and parse
            section_html = technology_section_element.get_attribute('innerHTML')
            soup = BeautifulSoup(section_html, 'html.parser')
            
            occupation_skills = []
            skill_list = soup.find('ul', class_='list-unstyled')
            
            if skill_list:
                list_items = skill_list.find_all('li')
                
                for item in list_items:
                    category_tag = item.find('b')
                    if not category_tag: continue
                    category_name = category_tag.get_text(strip=True)
                    
                    full_text = item.get_text(" ", strip=True)
                    examples_text = full_text.replace(category_name, "", 1).strip()
                    if examples_text.startswith('—'):
                        examples_text = examples_text[1:].strip()
                    
                    examples_text = re.sub(r'; \d+ more$', '', examples_text)
                    
                    examples = [e.strip() for e in examples_text.split(';')]
                    
                    for example in examples:
                        if example:
                             occupation_skills.append(f"{category_name} — {example}")

            # 5. Format results
            if occupation_skills:
                all_skills_in_one_cell = "\n".join(occupation_skills)
                results.append({
                    'occupation_name': occupation_name,
                    'technology_skills': all_skills_in_one_cell
                })
            else:
                results.append({'occupation_name': occupation_name, 'technology_skills': ""})

        except TimeoutException:
            print(f"  -> 'Technology Skills' section not found, skipping.")
            results.append({'occupation_name': occupation_name, 'technology_skills': "Section not found"})
        except Exception as e:
            print(f"  -> An unknown error occurred during processing: {e}")
            results.append({'occupation_name': occupation_name, 'technology_skills': "Error"})
    
    # --- After processing all links ---
    if driver:
        driver.quit()
        print("\nBrowser has been closed.")

    # --- Save Results ---
    if results:
        output_df = pd.DataFrame(results)
        output_df.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8-sig')
        print(f"\n--- All processing is complete! ---")
        print(f"Successfully processed {len(output_df)} occupations.")
        print(f"Results have been saved to your desktop: '{OUTPUT_CSV_FILE}'")
    else:
        print("\n--- Processing finished, but no data was generated. ---")

if __name__ == "__main__":
    main()