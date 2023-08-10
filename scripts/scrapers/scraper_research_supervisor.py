# Loading Packages
import re
import json
import logging
import requests
import pandas as pd

from uuid import uuid4
from time import sleep
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict

# Constants
SLEEP_TIME = 3

DATA = Path(__file__).parents[2] / "data"
UBC_PROGRAMS = DATA / "references" / "ubc_grad_programs.csv"

BASE_URL = "https://www.grad.ubc.ca"
RESEARCHERS_VIEW = "view-researcher-lists"
CONTENT_VIEW = "view-content"
NEXT_PAGE = "pager-next"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="research_supervisor_scraping.log",
    filemode="a",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)


# Helper Functions
def parse_supervisor(supervisor_html):
    """
    Parse HTML content of a research supervisor's information to extract relevant details.

    Args:
        supervisor_html (Tag): A BeautifulSoup Tag representing the HTML content of a research supervisor's information.

    Returns:
        dict or None: A dictionary containing extracted details of the research supervisor, or None if parsing fails.

    Description:
        This function takes a BeautifulSoup Tag `supervisor_html` as input, representing the HTML content of a research
        supervisor's information. It uses regular expressions to match and extract the supervisor's name and keywords
        (if available) from the HTML text. The extracted details are then organized into a dictionary containing keys
        like "id", "page", "name", and "keywords". If parsing fails, the function returns None.

    Note:
        The `supervisor_html` argument is expected to be a BeautifulSoup Tag representing the HTML content of a
        research supervisor's information.
    """
    supervisor_match = re.match(
        pattern=r"^([\w'\-,\.\s]+)(?: \((.*)\))?$",
        string=supervisor_html.get_text().strip(),
    )

    supervisor_name = supervisor_match.group(1)
    supervisor_keywords = supervisor_match.group(2)

    try:
        supervisor = {
            "id": str(uuid4()),
            "page": supervisor_html.a["href"],
            "name": supervisor_name,
            "keywords": (
                re.split(r"[;,] ", supervisor_keywords) if supervisor_keywords else None
            ),
        }
    except TypeError as e:
        logging.error(
            f"""Error: {e}
{supervisor_html}"""
        )
        return None
    else:
        return supervisor


def parse_supervisors(supervisors_html):
    """
    Parse HTML content of research supervisors' information to extract relevant details.

    Args:
        supervisors_html (list[Tag]): A list of BeautifulSoup Tags representing the HTML content of research supervisors' information.

    Yields:
        dict or None: A generator that yields dictionaries containing extracted details of research supervisors.

    Description:
        This function takes a list of BeautifulSoup Tags `supervisors_html` as input, each representing the HTML content
        of a research supervisor's information. It iterates through the list and yields dictionaries containing the
        extracted details of each research supervisor using the `parse_supervisor` function.

    Note:
        The `supervisors_html` argument is expected to be a list of BeautifulSoup Tags representing the HTML content of
        research supervisors' information.
    """
    for supervisor_html in supervisors_html:
        yield parse_supervisor(supervisor_html)


def scrape_supervisors(url):
    """
    Scrape research supervisor information from a given URL.

    Args:
        url (str): The URL to scrape research supervisor information from.

    Returns:
        list[dict]: A list of dictionaries containing extracted details of research supervisors.

    Description:
        This function scrapes research supervisor information from a specified URL using the requests library.
        It retrieves the HTML content from the URL, parses it using BeautifulSoup, and then extracts the information
        of research supervisors using the `parse_supervisor` function. The function handles pagination by following
        "Next" links until there are no more pages.

    Note:
        - The `url` argument should be a valid URL containing a list of research supervisors.
        - This function assumes that `RESEARCHERS_VIEW`, `CONTENT_VIEW`, and `NEXT_PAGE` constants are defined.
          Make sure they are properly defined in the script's context.
    """
    supervisors_list = []
    next_page = True
    while next_page:
        try:
            with requests.get(url) as response:
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.RequestException,
        ) as e:
            logging.error(f"Error: {e}")
            return supervisors_list

        supervisors = soup.find(name="div", attrs={"class": RESEARCHERS_VIEW})
        if supervisors is not None:
            supervisors_list.extend(
                [
                    parse_supervisor(supervisor_html)
                    for supervisor_html in supervisors.find(
                        attrs={"class": CONTENT_VIEW}
                    ).find_all(name="li")
                ]
            )
        else:
            logging.warning("Supervisors list not found on the page.")
            break

        next_page_path = soup.find(attrs={"class": NEXT_PAGE})
        if next_page_path is not None:
            url = BASE_URL + next_page_path.a["href"]
            logging.info(f"Scraping next page: {url}")
        else:
            next_page = False
        sleep(SLEEP_TIME)

    return supervisors_list


# Main function
def main():
    # Loading Data
    programs = pd.read_csv(UBC_PROGRAMS)

    # Scraping Supervisors
    supervisors_by_program = defaultdict(list)
    for program in programs["Program Page"]:
        program_url = BASE_URL + program
        logging.info(f"Scraping supervisors for program: {program_url}")
        supervisors = scrape_supervisors(program_url)
        supervisors_by_program[program] = supervisors

    with (DATA / "references" / "supervisors_by_program.json").open(mode="w") as f:
        json.dump(supervisors_by_program, fp=f)


if __name__ == "__main__":
    logging.info("Starting a new scraping run.")
    main()
