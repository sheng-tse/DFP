import config
import utils
import keywords_main

# jt = keywords_main.main()

job_title = input("Enter job title: ")

# job_title = jt
# print("\n" * 8)
# print("You are directing to indeed job search based on your interest earlier. ")
city = input("Enter city for job search: ")
state = input("Enter state for the city you choose: ")

# Pagination settings
start_page_input = input(
    "Enter starting page: ")
start_page = (int(start_page_input) - 1) if start_page_input.strip() else 0
print(f"Starting from page {start_page + 1}")

pages_input = input("Enter number of pages to scrape (default 1): ")
num_pages = int(pages_input) if pages_input.strip() else 1
print(f"Will scrape {num_pages} pages")

# Threading settings
threads_input = input(
    f"Enter number of parallel threads (default {config.DEFAULT_THREADS}, max {config.MAX_THREADS}): ")
max_workers = int(threads_input) if threads_input.strip(
) else config.DEFAULT_THREADS
max_workers = min(max_workers, config.MAX_THREADS)
print(f"Using {max_workers} parallel threads")

# Generate initial URL
url = utils.get_url(job_title, city, state, start_page)
print(f"\nSearch URL: {url}")

# Setup WebDriver
driver = utils.create_driver()

# Store all job records
records = []
next_page_url = None
print_lock = config.Lock()
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
                url = utils.get_url(job_title, city, state, current_page)
                driver.get(url)

        # Wait for page to load
        config.time.sleep(config.random.randint(
            config.PAGE_LOAD_MIN, config.PAGE_LOAD_MAX))
        config.WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
            config.EC.presence_of_element_located(
                (config.By.CLASS_NAME, "job_seen_beacon"))
        )

        # Find all job postings
        posts = driver.find_elements(config.By.CLASS_NAME, "job_seen_beacon")
        print(f"Found {len(posts)} jobs on page {current_page + 1}")

        # Phase 1: Collect basic info quickly
        print("\nPhase 1: Collecting basic job information...")
        job_basics = []
        for i, post in enumerate(posts):
            print(f"  Collecting job {i + 1}/{len(posts)}...", end="\r")
            basic_info = utils.get_job_basic_info(post)
            if basic_info:
                job_basics.append(basic_info)

        print(f"\n✓ Collected {len(job_basics)} job listings")

        # Save next page URL before closing
        next_page_url = None
        if page_num < num_pages - 1:
            try:
                next_button = driver.find_element(
                    config.By.CSS_SELECTOR, "a[data-testid='pagination-page-next']")
                next_page_url = next_button.get_attribute("href")
                print(f"✓ Next page URL saved")
            except config.NoSuchElementException:
                print("⚠ No next page button found")

        # Close browser to avoid detection
        driver.quit()
        print("✓ Closed listing page browser")

        # Phase 2: Fetch descriptions in parallel
        print(
            f"\nPhase 2: Fetching job descriptions ({max_workers} parallel threads)...")
        start_time = config.time.time()

        with config.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_job = {
                executor.submit(utils.process_job_with_description, job_data, i, len(job_basics)): job_data
                for i, job_data in enumerate(job_basics)
            }

            for future in config.as_completed(future_to_job):
                try:
                    record = future.result()
                    records.append(record)
                except Exception as e:
                    utils.safe_print(f"Error processing job: {e}")

        elapsed_time = config.time.time() - start_time
        print(
            f"\n✓ Completed {len(job_basics)} jobs in {elapsed_time:.2f} seconds")
        print(f"  Average: {elapsed_time/len(job_basics):.2f} seconds per job")
        print(f"\n✓ Total jobs collected so far: {len(records)}")

        # Create new driver for next page
        if page_num < num_pages - 1 and next_page_url:
            print("\nPreparing for next page...")
            driver = utils.create_driver()
            config.time.sleep(config.random.randint(
                config.PAGE_SWITCH_MIN, config.PAGE_SWITCH_MAX))
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
    df = config.pd.DataFrame(records, columns=[
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

option = int(input(
    "Enter save option (0=CSV, 1=JSON, 2=Excel, 3=All, 4=Quit): "
))

utils.save_data(records, option, job_title)
