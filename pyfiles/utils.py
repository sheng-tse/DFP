import config


def get_chrome_options():
    """Returns configured Chrome options for anti-detection"""
    options = config.webdriver.ChromeOptions()

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
        template += "&start={}".format(page * config.JOBS_PER_PAGE)

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
    driver = config.webdriver.Chrome(options=options)

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
    with config.print_lock:
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
        title = post.find_element(config.By.CSS_SELECTOR, "h2.jobTitle").text
        company = post.find_element(
            config.By.CSS_SELECTOR, "span[data-testid='company-name']").text
        location = post.find_element(
            config.By.CSS_SELECTOR, "div[data-testid='text-location']").text
        job_url = post.find_element(
            config.By.CSS_SELECTOR, "h2.jobTitle a").get_attribute("href")

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
        config.time.sleep(config.random.randint(
            config.JOB_LOAD_MIN, config.JOB_LOAD_MAX))

        config.WebDriverWait(driver, config.WEBDRIVER_TIMEOUT).until(
            config.EC.presence_of_element_located(
                (config.By.ID, "jobDescriptionText"))
        )
        job_description = driver.find_element(
            config.By.ID, "jobDescriptionText").text

        # NEW: Try to get salary from the detail page
        try:
            # Method 1: Try the salaryInfoAndJobType div with specific class
            salary_element = driver.find_element(
                config.By.CSS_SELECTOR, "span.css-1oc7tea")
            salary = salary_element.text.strip()
        except config.NoSuchElementException:
            try:
                # Method 2: Try alternative salary container
                salary_element = driver.find_element(
                    config.By.ID, "salaryInfoAndJobType")
                salary_span = salary_element.find_element(
                    config.By.CSS_SELECTOR, "span.css-1oc7tea")
                salary = salary_span.text.strip()
            except config.NoSuchElementException:
                try:
                    # Method 3: Try broader search in salary section
                    salary_container = driver.find_element(
                        config.By.CSS_SELECTOR, "div#salaryInfoAndJobType")
                    salary_text = salary_container.text.split('-')[0].strip()
                    if salary_text:
                        salary = salary_container.text.split('\n')[0].strip()
                except config.NoSuchElementException:
                    salary = ""

    except (config.NoSuchElementException, config.TimeoutException):
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
    config.time.sleep(config.random.uniform(
        config.THREAD_DELAY_MIN, config.THREAD_DELAY_MAX))

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
        writer = config.csv.writer(file)
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

    df = config.pd.DataFrame(records, columns=[
        "Title", "Company", "Location", "Salary", "URL", "Description"])
    # Save with auto-column width
    with config.pd.ExcelWriter(filename, engine='openpyxl') as writer:
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
        config.json.dump(jobs_list, f, indent=2, ensure_ascii=False)

    print(f"✓ Data saved to {filename}")
    print(f"  Records: {len(jobs_list)}")


def save_data(records, option, job_title):
    filename_base = f"indeed_job_{job_title}"
    job_title = job_title.strip().replace(" ", "_")
    if option == 0:
        save_to_csv(records, f"{filename_base}.csv")
    elif option == 1:
        save_to_json(records, f"{filename_base}.json")
    elif option == 2:
        save_to_excel(records, f"{filename_base}.xlsx")
    elif option == 3:
        save_to_csv(records, f"{filename_base}.csv")
        print()
        save_to_json(records, f"{filename_base}.json")
        print()
        save_to_excel(records, f"{filename_base}.xlsx")
    elif option == 4:
        print("Exiting without saving.")
        return
    else:
        print(
            "❌ Invalid input. Please enter:\n"
            "0 → CSV\n1 → JSON\n2 → Excel\n3 → All formats\n4 → Quit"
        )
        save_data(records, option, job_title)
