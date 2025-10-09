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

# Create safe print
print_lock = Lock()

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
WEBDRIVER_TIMEOUT = 15

# Threading configuration
DEFAULT_THREADS = 3
MAX_THREADS = 15

# Indeed pagination (jobs per page)
JOBS_PER_PAGE = 10
