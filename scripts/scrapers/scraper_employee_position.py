# Loading Libraries
import re
import json
import logging
import pandas as pd

from time import sleep
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict
from playwright.sync_api import sync_playwright

# Constants
DATA = Path(__file__).parents[2] / "data"
EMPLOYEES = DATA / "references" / "employees.json"
DIRECTORY_URL = "https://directory.ubc.ca/index.cfm"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="employees_scraping.log",
    filemode="a",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)


# Helper Functions
def search_employee(page, employee_name):
    page.locator('input[name="keywords"]').fill(employee_name)
    page.locator("#personAll").click()


def reset_page(page):
    page.locator(':nth-match(a:has-text("Home"), 1)').click()


def employee_match_found(page):
    selector = page.query_selector("#warning")
    return selector is None


def parse_results(soup):
    rows = soup.find(attrs={"class": "results"}).find("tbody").find_all(name="tr")
    results = []
    for row in rows:
        data = [cell.get_text().strip() for cell in row.find_all(name="td")]
        results.append(data)
    return data


def normalize_name(name):
    name = name.casefold()
    name = re.sub(pattern=r"^\w(\s)\w+", repl="'", string=name)
    name = re.sub(pattern=r"\s\w\.", repl="", string=name)
    name = re.match(pattern=r"(^[\w'\-\.\s]+, \w+).*", string=name).group(1)
    return name


def main(page, start, end):
    logging.info(f"Employee window: {start}, {end}")
    employee_names = (
        pd.read_csv(DATA / "processed" / "all_remunerations.csv")
        .loc[:, "name"]
        .to_list()
    )

    results = defaultdict(list)
    for name in employee_names[start:end]:
        logging.info(f"Scraping employee: {name}.")
        name = normalize_name(name)

        logging.info(f"Normalized employee name: {name}.")
        search_employee(page, name)
        sleep(1)

        if employee_match_found(page):
            logging.info(f"Parsing HTML for {name}.")
            soup = BeautifulSoup(page.content(), "html.parser")
        else:
            logging.warning(f"No matches for {name}")
            reset_page(page)
            continue
        results[name].append(parse_results(soup))

        logging.info("Preparing for next employee.")
        sleep(3)
        reset_page(page)
    return results


if __name__ == "__main__":
    logging.info("Initiating employee directory scraping.")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(DIRECTORY_URL)

        results = main(page, start=0, end=10)

    with EMPLOYEES.open(mode="a") as f:
        json.dump(results, f)
