# %% [markdown]
# # Indeed Job Scraper
#
# A modular web scraping tool for collecting job postings from Indeed.com
#
# ## 📋 Project Overview
#
# This project scrapes job listings from Indeed.com using Selenium WebDriver with:
# - **Multi-threading** for faster data collection
# - **Anti-detection features** to avoid being blocked
# - **Modular design** for easy maintenance and collaboration
#
# ## 📁 File Structure
#
# ```
# ├── README.ipynb                    # This file - documentation
# ├── 1_config.ipynb                  # Configuration and imports
# ├── 2_utils.ipynb                   # Helper functions
# ├── 3_scraping_functions.ipynb      # Core scraping logic
# ├── 4_main_scraper.ipynb            # Main execution workflow
# └── 5_save_data.ipynb               # Data export functions
# ```
#
# ## 🚀 Quick Start
#
# ### 1. Install Required Packages
#
# ```bash
# pip install selenium pandas openpyxl
# ```
#
# ### 2. Install ChromeDriver
#
# - Download ChromeDriver: https://chromedriver.chromium.org/
# - Make sure it matches your Chrome browser version
# - Add to PATH or place in project directory
#
# ### 3. Run the Notebooks in Order
#
# 1. **README.ipynb** (this file) - Read documentation
# 2. **1_config.ipynb** - Set up configuration
# 3. **2_utils.ipynb** - Load utility functions
# 4. **3_scraping_functions.ipynb** - Load scraping functions
# 5. **4_main_scraper.ipynb** - Execute the scraper
# 6. **5_save_data.ipynb** - Export data to CSV/Excel/JSON
#
# ## 💡 Usage Example

# %%
# Example: How to use the scraper
"""
1. Run notebooks 1-3 to load all functions
2. In 4_main_scraper.ipynb, enter:
   - Job title: "Data Analyst"
   - City: "New York"
   - State: "NY"
   - Starting page: 0
   - Number of pages: 2
   - Threads: 5

3. Wait for scraping to complete
4. Run 5_save_data.ipynb to export data
"""

# %% [markdown]
# ## ⚙️ Configuration Options
#
# ### In `1_config.ipynb`:
#
# - **PAGE_LOAD_MIN/MAX**: Time to wait for pages to load (3-5 seconds)
# - **JOB_LOAD_MIN/MAX**: Time to wait for job details (2-4 seconds)
# - **DEFAULT_THREADS**: Default number of parallel threads (3)
# - **MAX_THREADS**: Maximum allowed threads (15)
# - **WEBDRIVER_TIMEOUT**: Maximum wait time for elements (10 seconds)
#
# ### Headless Mode:
#
# To see the browser while scraping, comment out this line in `1_config.ipynb`:
# ```python
# # options.add_argument("--headless")
# ```
#
# ## 🔧 Functions Reference
#
# ### 2_utils.ipynb
#
# - `get_url(job_title, city, state, page)` - Generate Indeed search URLs
# - `create_driver()` - Create configured Chrome WebDriver
# - `safe_print(message)` - Thread-safe printing
#
# ### 3_scraping_functions.ipynb
#
# - `get_job_basic_info(post)` - Extract title, company, location, salary, URL
# - `get_job_description(job_url)` - Fetch full job description
# - `process_job_with_description(job_data, index, total)` - Process single job with threading
#
# ### 5_save_data.ipynb
#
# - `save_to_csv(records, filename)` - Export to CSV
# - `save_to_excel(records, filename)` - Export to Excel with formatting
# - `save_to_json(records, filename)` - Export to JSON
#
# ## 📊 Output Format
#
# Each job record contains:
# - **Title**: Job title
# - **Company**: Company name
# - **Location**: City, State
# - **Salary**: Salary information (if available)
# - **URL**: Direct link to job posting
# - **Description**: Full job description text
#
# ## ⚠️ Important Notes
#
# ### Anti-Detection Features
#
# This scraper includes several anti-detection measures:
# - Randomized delays between requests
# - Custom user agent
# - Fresh browser instances for each job description
# - Disabled automation flags
#
# ### Rate Limiting
#
# - Use 3-5 threads for normal scraping
# - Maximum 15 threads (not recommended for long sessions)
# - Add delays between pages
# - Respect Indeed's robots.txt
#
# ### Legal Considerations
#
# - Web scraping should comply with Indeed's Terms of Service
# - Use scraped data responsibly and ethically
# - Consider rate limits to avoid overloading servers
# - This tool is for educational/research purposes
#
# ## 🐛 Troubleshooting
#
# ### "ChromeDriver not found"
# - Install ChromeDriver and add to PATH
# - Or specify path: `webdriver.Chrome(executable_path='/path/to/chromedriver')`
#
# ### "Element not found" errors
# - Indeed may have updated their HTML structure
# - Check CSS selectors in `get_job_basic_info()`
# - Increase `WEBDRIVER_TIMEOUT` in config
#
# ### Scraper gets blocked
# - Reduce number of threads
# - Increase delays in config
# - Enable headless mode
# - Wait longer between scraping sessions
#
# ### "records not found" in save_data
# - Make sure you ran `4_main_scraper.ipynb` first
# - Check if scraping completed successfully
# - Look for error messages in scraper output
#
# ## 🤝 Team Collaboration Tips
#
# ### Working on Different Components
#
# - **Config changes**: Edit `1_config.ipynb`
# - **New utility functions**: Add to `2_utils.ipynb`
# - **Scraping improvements**: Modify `3_scraping_functions.ipynb`
# - **Workflow changes**: Update `4_main_scraper.ipynb`
# - **Export formats**: Extend `5_save_data.ipynb`
#
# ### Testing Individual Components
#
# Each notebook can be tested independently:
#
# ```python
# # Test utils
# %run 1_config.ipynb
# %run 2_utils.ipynb
# test_url = get_url("engineer", "Boston", "MA")
# print(test_url)
#
# # Test scraping function
# driver = create_driver()
# driver.get(test_url)
# posts = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")
# basic_info = get_job_basic_info(posts[0])
# print(basic_info)
# driver.quit()
# ```
#
# ## 📈 Performance Tips
#
# - **Optimal threads**: 5-7 threads for balance of speed and stability
# - **Page limit**: Start with 1-2 pages for testing
# - **Headless mode**: Faster performance (enabled by default)
# - **Monitor resources**: Watch CPU/memory usage with many threads
#
# ## 🔄 Version Control with Git
#
# ```bash
# # Initialize repository
# git init
#
# # Add all notebooks
# git add *.ipynb
#
# # Commit changes
# git commit -m "Initial commit: Modular Indeed scraper"
#
# # Create .gitignore for data files
# echo "*.csv" >> .gitignore
# echo "*.xlsx" >> .gitignore
# echo "*.json" >> .gitignore
# ```
#
# ## 📝 Contributing
#
# When adding new features:
# 1. Document your changes
# 2. Test thoroughly
# 3. Update this README if needed
# 4. Follow the existing code style
# 5. Add comments for complex logic
#
# ## 📧 Support
#
# If you encounter issues:
# 1. Check the Troubleshooting section above
# 2. Review error messages carefully
# 3. Test individual components
# 4. Verify ChromeDriver version matches Chrome
#
# ## 🎯 Future Enhancements
#
# Potential improvements:
# - [ ] Add filters (job type, experience level, salary range)
# - [ ] Support for other job boards (LinkedIn, Glassdoor)
# - [ ] Database storage (SQLite, PostgreSQL)
# - [ ] Email notifications when scraping completes
# - [ ] Data visualization dashboard
# - [ ] Resume matching algorithm
# - [ ] Duplicate detection
# - [ ] Proxy rotation for large-scale scraping
#
# ## 📜 License
#
# This project is for educational purposes. Use responsibly and ethically.

# %%