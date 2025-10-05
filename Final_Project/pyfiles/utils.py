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
