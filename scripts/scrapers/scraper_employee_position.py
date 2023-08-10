# Loading Libraries
import re
import json
import asyncio
import logging
import pandas as pd

from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict
from playwright.async_api import async_playwright

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
    await page.locator('input[name="keywords"]').fill(employee_name)
    await asyncio.sleep(1)
    await page.locator("#personAll").click()


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
        return data


def normalize_name(name):
    """
    Normalize a given name by applying a series of transformations.

    Args:
        name (str): The name to be normalized.

    Returns:
        str: The normalized name.

    Description:
        This function takes a name as input and applies a series of transformations to normalize it.
        The transformations include converting the name to lowercase, removing middle initials, truncating titles,
        and removing non-alphanumeric characters from the end of the name.
        The function returns the normalized name.
    """
    name = name.casefold()
    name = re.sub(pattern=r"^\w(\s)\w+", repl="'", string=name)
    name = re.sub(pattern=r"\s\w\.", repl="", string=name)
    name = re.match(pattern=r"(^[\w'\-\.\s]+(, \w+)?).*", string=name).group(1)
    return name


async def scrape_employees(page, start, end):
    """
    Scrape employee information from the UBC directory website for a range of employees.

    Args:
        page (Page): An instance of a Playwright Page representing the web page where scraping will be performed.
        start (int): The index of the first employee to scrape in the employee list.
        end (int): The index of the last employee to scrape in the employee list (exclusive).

    Returns:
        defaultdict: A defaultdict where keys are normalized employee names and values are lists of parsed data.

    Description:
        This asynchronous function performs web scraping of employee information from the UBC directory website
        for a specified range of employees. It takes a Playwright `page` instance and indices `start` and `end`
        to determine which employees to scrape. The function retrieves employee names from a processed CSV file,
        normalizes each name using the `normalize_name` function, searches for each employee using the `search_employee`
        function, parses search results using the `parse_results` function, and stores the parsed data in a defaultdict.

        If no match is found for an employee, an empty list is stored in the defaultdict for that employee's name.
    """
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
        await search_employee(page, name)

        if not await employee_match_found(page):
            logging.warning(f"No matches for {name}")
            results[name] = []
            await reset_page(page)
            continue

        logging.info(f"Parsing HTML for {name}.")
        soup = BeautifulSoup(await page.content(), "html.parser")
        results_table = parse_results(soup)
        if results_table is None:
            results[name] = []
        else:
            results[name].append(parse_results(soup))

        logging.info("Preparing for next employee.")
        await asyncio.sleep(2)
        await reset_page(page)
    return results


# Main Function
async def main(start, end):
    """
    Entry point for initiating employee directory scraping.

    Args:
        start (int): The index of the first employee to scrape in the employee list.
        end (int): The index of the last employee to scrape in the employee list (exclusive).

    Returns:
        defaultdict: A defaultdict where keys are normalized employee names and values are lists of parsed data.

    Description:
        This asynchronous function serves as the entry point for initiating the scraping of employee information
        from the UBC directory website. It launches a Chromium browser using Playwright, navigates to the directory
        website, creates a new Playwright context and page, and then calls the `scrape_employees` function
        to perform the scraping process.

        After scraping is complete, the browser is closed, and a defaultdict containing the parsed data is returned.
    """
    logging.info("Initiating employee directory scraping.")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(DIRECTORY_URL)

        results = await scrape_employees(page, start, end)
        await browser.close()
    return results


if __name__ == "__main__":
    START, END = 7000, 7357
    logging.info(f"Employee window: {START}, {END}")
    results = asyncio.run(main(start=START, end=END))

    with EMPLOYEES.open(mode="r") as f:
        employees = json.load(f)

    with EMPLOYEES.open(mode="w") as f:
        employees.append(results)
        json.dump(employees, f)
