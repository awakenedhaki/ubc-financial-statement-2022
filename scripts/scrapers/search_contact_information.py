# TODO:
# 1. Select Top 10
# 2. Focus on Vancouver
# 3. Only first and last name

# Loading Libraries
import re
import json
import asyncio
import logging
import pandas as pd

from pathlib import Path
from bs4 import BeautifulSoup
from operator import itemgetter
from collections import defaultdict
from playwright.async_api import async_playwright

# Constants
DATA = Path(__file__).parents[2] / "data"
EMPLOYEES = DATA / "tmp" / "raw_employees.json"
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
first = itemgetter(0)


async def reset_page(page):
    """
    Reset the current web page to the home page of the UBC directory website using Playwright.

    Args:
        page (Page): An instance of a Playwright Page representing the web page to be reset.

    Description:
        This asynchronous function resets the current web page to the home page of the UBC directory website.
        It uses Playwright's API to locate and click on the "Home" link in the page's navigation menu.
        This action takes the user back to the main directory page.
    """
    await page.locator(':nth-match(a:has-text("Home"), 1)').click()


def parse_results(soup):
    """
    Parse the search results HTML soup to extract and organize data.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the parsed HTML content of the search results page.

    Returns:
        list: A list of lists containing the parsed data for each result row, or None if parsing fails.

    Description:
        This function parses the HTML soup of a UBC directory search results page to extract and organize the data.
        It locates the results div, extracts the table body containing result rows, and then iterates through each row.
        For each row, it retrieves the text content of each cell in the row (td elements) and appends the data to a list.
        The function returns a list of lists, where each inner list represents the parsed data for a single result row.
    """
    try:
        results_div = soup.find(attrs={"class": "results"})
        results_table_body = results_div.find(name="tbody")
        rows = results_table_body.find_all(name="tr")
    except AttributeError as e:
        logging.error(f"NoneType Error in results: {e}")
    else:
        results = []
        for row in rows:
            data = [cell.get_text().strip() for cell in row.find_all(name="td")]
            results.append(data)
        return results


async def employee_match_found(page):
    """
    Check if a match for the employee search was found on the UBC directory search results page.

    Args:
        page (Page): An instance of a Playwright Page representing the search results page.

    Returns:
        bool: True if a match for the employee search was found, False otherwise.

    Description:
        This asynchronous function checks whether a match for the employee search was found on the UBC directory
        search results page. It queries the page to locate the warning element with the id "warning".
        If the element is not found, it indicates that a match was found, and the function returns True.
        Otherwise, if the element is found, it indicates that no match was found, and the function returns False.
    """
    selector = await page.query_selector("#warning")
    return selector is None


async def search_employee(page, employee_name):
    """
    Perform a search for a specific employee name on the UBC directory website using Playwright.

    Args:
        page (Page): An instance of a Playwright Page representing the web page where the search will be conducted.
        employee_name (str): The name of the employee to search for on the UBC directory website.

    Usage:
        await search_employee(page, "John Doe")

    Description:
        This function performs a search for a given employee name on the UBC directory website.
        It uses Playwright's asynchronous API to interact with the web page.
        The function fills the search input field with the provided employee name,
        clicks on the "All People" option, and then waits for a brief moment (1 second)
        to allow the search results to load.

    Example:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            await page.goto(DIRECTORY_URL)
            await search_employee(page, "Alice Smith")

            # Additional code to process search results or perform further actions

            await browser.close()

    Important Note:
        This function assumes that the provided `page` instance is already navigated to the UBC directory website
        (specified by the `DIRECTORY_URL` constant) before calling the `search_employee` function.
    """
    logging.info(f"Scraping employee: {employee_name}.")
    await page.locator('input[name="keywords"]').fill(employee_name)
    await asyncio.sleep(1)
    await page.locator("#personAll").click()


def build_query_name(given_name, surname):
    first_name = first(given_name.split(" "))
    return f"{first_name} {surname}"


async def scrape_employee_info(page, given_name, surname):
    query_name = build_query_name(given_name, surname)

    await search_employee(page, query_name)

    if await employee_match_found(page):
        logging.info(f"Parsing HTML for {query_name}.")
        soup = BeautifulSoup(await page.content(), "html.parser")
        results_table = parse_results(soup)
        if results_table:
            return results_table

    logging.warning(f"No matches for {query_name}")
    return None


async def scrape_employees(page, employee_names):
    results = defaultdict(list)
    for _, (id, given_name, surname) in employee_names.iterrows():
        results_table = await scrape_employee_info(page, given_name, surname)
        if results_table:
            results[id] = results_table

        logging.info("Preparing for next employee.")
        await asyncio.sleep(2)
        await reset_page(page)

    return results


# Main Function
async def main(start, end):
    logging.info("Initiating employee directory scraping.")
    employee_names = pd.read_csv(DATA / "processed" / "all_remunerations.csv").loc[
        start:end, ["id", "given_name", "surname"]
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(DIRECTORY_URL)

        results = await scrape_employees(page, employee_names)
        await browser.close()
    return results


if __name__ == "__main__":
    START, END = 0, 1
    logging.info(f"Employee window: {START}, {END}")
    results = asyncio.run(main(start=START, end=END))

    with EMPLOYEES.open(mode="r") as f:
        employees = json.load(f)

    with EMPLOYEES.open(mode="w") as f:
        employees.update(results)
        json.dump(employees, f)
