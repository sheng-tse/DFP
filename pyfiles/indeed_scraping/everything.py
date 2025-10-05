from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import csv
import pandas as pd
from datetime import datetime
import json

# Timing configurations (in seconds)
PAGE_LOAD_MIN = 3
PAGE_LOAD_MAX = 5
JOB_LOAD_MIN = 2
JOB_LOAD_MAX = 4
THREAD_DELAY_MIN = 0.5
THREAD_DELAY_MAX = 1.5
PAGE_SWITCH_MIN = 2
PAGE_SWITCH_MAX = 4

# WebDriver wait timeout
WEBDRIVER_TIMEOUT = 10

# Threading configuration
DEFAULT_THREADS = 3
MAX_THREADS = 15

# Indeed pagination (jobs per page)
JOBS_PER_PAGE = 10


def get_chrome_options():
    """Returns configured Chrome options for anti-detection"""
    options = webdriver.ChromeOptions()

    # Window settings
    options.add_argument("--start-maximized")

    # Anti-detection features
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Headless mode (comment out to see browser)
    options.add_argument("--headless")

    return options


# User agent string
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"

print_lock = Lock()


def get_url(job_title, city, state, page=0):
    """
    Generate Indeed search URL with optional page number

    Args:
        job_title: Job title to search for
        city: City name
        state: State name
        page: Page number (0 for first page, 1 for second, etc.)

    Returns:
        Formatted Indeed search URL
    """
    template = "https://www.indeed.com/jobs?q={}&l={}"
    if page > 0:
        template += "&start={}".format(page * JOBS_PER_PAGE)

    # Format inputs
    job_title = job_title.strip().replace(" ", "+")
    city = city.strip().replace(" ", "+")
    state = state.strip().replace(" ", "+")
    city_state = city + "+" + state

    url = template.format(job_title, city_state)
    return url


def create_driver():
    """
    Create and configure a new Chrome WebDriver instance
    with anti-detection features

    Returns:
        Configured Chrome WebDriver
    """
    options = get_chrome_options()
    driver = webdriver.Chrome(options=options)

    # Set custom user agent
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": USER_AGENT
    })

    return driver


def safe_print(message):
    """
    Thread-safe print function
    Ensures only one thread prints at a time

    Args:
        message: String to print
    """
    with print_lock:
        print(message)


def get_job_basic_info(post):
    """
    Extract basic information from a job posting card

    Args:
        post: Selenium WebElement of job card

    Returns:
        Tuple: (title, company, location, salary, job_url) or None if error
    """
    try:
        title = post.find_element(By.CSS_SELECTOR, "h2.jobTitle").text
        company = post.find_element(
            By.CSS_SELECTOR, "span[data-testid='company-name']").text
        location = post.find_element(
            By.CSS_SELECTOR, "div[data-testid='text-location']").text
        job_url = post.find_element(
            By.CSS_SELECTOR, "h2.jobTitle a").get_attribute("href")

        return (title, company, location, job_url)
    except Exception as e:
        print(f"Error extracting basic info: {e}")
        return None


def get_job_description(job_url):
    """
    Get full job description and salary by opening the job URL
    Uses a fresh browser instance for anti-detection

    Args:
        job_url: URL of the job posting

    Returns:
        Tuple: (salary, job_description) where salary may be empty string
    """
    driver = create_driver()
    salary = ""
    job_description = "None"

    try:
        driver.get(job_url)
        time.sleep(random.randint(JOB_LOAD_MIN, JOB_LOAD_MAX))

        WebDriverWait(driver, WEBDRIVER_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "jobDescriptionText"))
        )
        job_description = driver.find_element(By.ID, "jobDescriptionText").text

        # NEW: Try to get salary from the detail page
        try:
            # Method 1: Try the salaryInfoAndJobType div with specific class
            salary_element = driver.find_element(
                By.CSS_SELECTOR, "span.css-1oc7tea")
            salary = salary_element.text.strip()
        except NoSuchElementException:
            try:
                # Method 2: Try alternative salary container
                salary_element = driver.find_element(
                    By.ID, "salaryInfoAndJobType")
                salary_span = salary_element.find_element(
                    By.CSS_SELECTOR, "span.css-1oc7tea")
                salary = salary_span.text.strip()
            except NoSuchElementException:
                try:
                    # Method 3: Try broader search in salary section
                    salary_container = driver.find_element(
                        By.CSS_SELECTOR, "div#salaryInfoAndJobType")
                    salary_text = salary_container.text.split('-')[0].strip()
                    if salary_text:
                        salary = salary_container.text.split('\n')[0].strip()
                except NoSuchElementException:
                    salary = ""

    except (NoSuchElementException, TimeoutException):
        job_description = "None"
        salary = ""
    except Exception as e:
        safe_print(f"Error getting job details: {e}")
        job_description = "None"
        salary = ""
    finally:
        driver.quit()

    return (salary, job_description)


def process_job_with_description(job_data, index, total):
    title, company, location, job_url = job_data
    """
    Process a single job: fetch description and create record
    Designed for parallel execution with ThreadPoolExecutor
    
    Args:
        job_data: Tuple of basic job info
        index: Job index (for progress tracking)
        total: Total number of jobs
    
    Returns:
        Complete job record tuple
    """
    safe_print(
        f"[Thread] Processing job {index + 1}/{total}: {title} at {company}")
    time.sleep(random.uniform(THREAD_DELAY_MIN, THREAD_DELAY_MAX))

    salary, job_description = get_job_description(job_url)

    record = (title, company, location, salary, job_url, job_description)
    safe_print(
        f"[Thread] Completed job {index + 1}/{total}: {title} | Salary: {salary if salary else 'Not listed'}")
    return record


def save_to_csv(records, filename="indeed_jobs.csv"):
    """
    Save job records to CSV file

    Args:
        records: List of job tuples
        filename: Output CSV filename
    """
    if not records:
        print("⚠ No records to save")
        return

    headers = ["Title", "Company", "Location", "Salary", "URL", "Description"]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(records)

    print(f"✓ Data saved to {filename}")
    print(f"  Rows: {len(records)}")


def save_to_excel(records, filename="indeed_jobs.xlsx"):
    """
    Save job records to Excel file with formatting

    Args:
        records: List of job tuples
        filename: Output Excel filename
    """
    if not records:
        print("⚠ No records to save")
        return

    df = pd.DataFrame(records, columns=[
                      "Title", "Company", "Location", "Salary", "URL", "Description"])
    # Save with auto-column width
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Jobs')

        # Auto-adjust column widths
        worksheet = writer.sheets['Jobs']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            worksheet.column_dimensions[chr(
                65 + idx)].width = min(max_length + 2, 50)

    print(f"✓ Data saved to {filename}")
    print(f"  Rows: {len(records)}")


def save_to_json(records, filename="indeed_jobs.json"):
    """
    Save job records to JSON file

    Args:
        records: List of job tuples
        filename: Output JSON filename
    """
    if not records:
        print("⚠ No records to save")
        return

    jobs_list = []
    for record in records:
        job_dict = {
            "title": record[0],
            "company": record[1],
            "location": record[2],
            "salary": record[3],
            "url": record[4],
            "description": record[5]
        }
        jobs_list.append(job_dict)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(jobs_list, f, indent=2, ensure_ascii=False)

    print(f"✓ Data saved to {filename}")
    print(f"  Records: {len(jobs_list)}")


# Job search parameters
job_title = input("Enter job title: ")
city = input("Enter city: ")
state = input("Enter state: ")

# Pagination settings
start_page_input = input(
    "Enter starting page (0 for first page, 1 for second page, etc.): ")
start_page = int(start_page_input) if start_page_input.strip() else 0
print(f"Starting from page {start_page + 1}")

pages_input = input("Enter number of pages to scrape (default 1): ")
num_pages = int(pages_input) if pages_input.strip() else 1
print(f"Will scrape {num_pages} pages")

# Threading settings
threads_input = input(
    f"Enter number of parallel threads (default {DEFAULT_THREADS}, max {MAX_THREADS}): ")
max_workers = int(threads_input) if threads_input.strip() else DEFAULT_THREADS
max_workers = min(max_workers, MAX_THREADS)
print(f"Using {max_workers} parallel threads")

# Generate initial URL
url = get_url(job_title, city, state, start_page)
print(f"\nSearch URL: {url}")

# Setup WebDriver
driver = create_driver()

# Store all job records
records = []
next_page_url = None

try:
    for page_num in range(num_pages):
        current_page = start_page + page_num
        print(f"\n{'='*80}")
        print(f"SCRAPING PAGE {current_page + 1}")
        print(f"{'='*80}")

        # Navigate to URL
        if page_num == 0:
            driver.get(url)
        else:
            if next_page_url:
                driver.get(next_page_url)
            else:
                url = get_url(job_title, city, state, current_page)
                driver.get(url)

        # Wait for page to load
        time.sleep(random.randint(PAGE_LOAD_MIN, PAGE_LOAD_MAX))
        WebDriverWait(driver, WEBDRIVER_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "job_seen_beacon"))
        )

        # Find all job postings
        posts = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")
        print(f"Found {len(posts)} jobs on page {current_page + 1}")

        # Phase 1: Collect basic info quickly
        print("\nPhase 1: Collecting basic job information...")
        job_basics = []
        for i, post in enumerate(posts):
            print(f"  Collecting job {i + 1}/{len(posts)}...", end="\r")
            basic_info = get_job_basic_info(post)
            if basic_info:
                job_basics.append(basic_info)

        print(f"\n✓ Collected {len(job_basics)} job listings")

        # Save next page URL before closing
        next_page_url = None
        if page_num < num_pages - 1:
            try:
                next_button = driver.find_element(
                    By.CSS_SELECTOR, "a[data-testid='pagination-page-next']")
                next_page_url = next_button.get_attribute("href")
                print(f"✓ Next page URL saved")
            except NoSuchElementException:
                print("⚠ No next page button found")

        # Close browser to avoid detection
        driver.quit()
        print("✓ Closed listing page browser")

        # Phase 2: Fetch descriptions in parallel
        print(
            f"\nPhase 2: Fetching job descriptions ({max_workers} parallel threads)...")
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_job = {
                executor.submit(process_job_with_description, job_data, i, len(job_basics)): job_data
                for i, job_data in enumerate(job_basics)
            }

            for future in as_completed(future_to_job):
                try:
                    record = future.result()
                    records.append(record)
                except Exception as e:
                    safe_print(f"Error processing job: {e}")

        elapsed_time = time.time() - start_time
        print(
            f"\n✓ Completed {len(job_basics)} jobs in {elapsed_time:.2f} seconds")
        print(f"  Average: {elapsed_time/len(job_basics):.2f} seconds per job")
        print(f"\n✓ Total jobs collected so far: {len(records)}")

        # Create new driver for next page
        if page_num < num_pages - 1 and next_page_url:
            print("\nPreparing for next page...")
            driver = create_driver()
            time.sleep(random.randint(PAGE_SWITCH_MIN, PAGE_SWITCH_MAX))
        elif page_num < num_pages - 1:
            print("⚠ No next page available, stopping pagination")
            break

finally:
    try:
        driver.quit()
    except:
        pass

print(f"\n{'='*80}")
print(f"SCRAPING COMPLETE")
print(f"{'='*80}")
print(f"Total jobs collected: {len(records)}")
print(f"\nFirst 3 jobs preview:")

for i, record in enumerate(records[:3], 1):
    print(f"\n--- Job {i} ---")
    print(f"Title: {record[0]}")
    print(f"Company: {record[1]}")
    print(f"Location: {record[2]}")
    print(f"Salary: {record[3]}")
    print(f"Description: {record[5][:150]}..." if len(
        record[5]) > 150 else f"Description: {record[5]}")

if len(records) > 3:
    print(f"\n... and {len(records) - 3} more jobs")

print(f"\n{'='*80}")
print("Next step: Run save_data.ipynb to export your data")
print(f"{'='*80}")

if records:
    df = pd.DataFrame(records, columns=[
                      "Title", "Company", "Location", "Salary", "URL", "Description"])

    print("\n" + "="*80)
    print("DATA QUALITY REPORT")
    print("="*80)
    print(f"\nTotal records: {len(df)}")
    print(
        f"\nMissing salaries: {df['Salary'].eq('').sum()} ({df['Salary'].eq('').sum()/len(df)*100:.1f}%)")
    print(
        f"Missing descriptions: {df['Description'].eq('None').sum()} ({df['Description'].eq('None').sum()/len(df)*100:.1f}%)")

    print(f"\nTop 5 companies:")
    print(df['Company'].value_counts().head())

    print(f"\nTop 5 locations:")
    print(df['Location'].value_counts().head())

    print("\n" + "="*80)

# Execute CSV save
csv_filename = f"indeed_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
save_to_csv(records, csv_filename)

# Execute Excel save
excel_filename = f"indeed_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
save_to_excel(records, excel_filename)

# Execute JSON save
json_filename = f"indeed_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
save_to_json(records, json_filename)

print("\n✓ All data export operations complete!")
print(f"\nFiles created:")
print(f"  - {csv_filename}")
print(f"  - {excel_filename}")
print(f"  - {json_filename}")
