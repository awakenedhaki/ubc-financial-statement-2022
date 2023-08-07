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

DATA = Path(__file__).parents[1] / "data"
UBC_PROGRAMS = DATA / "ubc_grad_programs.csv"

BASE_URL = "https://www.grad.ubc.ca"
RESEARCHERS_VIEW = "view-researcher-lists"
CONTENT_VIEW = "view-content"
NEXT_PAGE = "pager_next"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="scraping.log",
    filemode="a",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)


# Helper Functions
def parse_supervisor(supervisor_html):
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
    for supervisor_html in supervisors_html:
        yield parse_supervisor(supervisor_html)


def scrape_supervisors(url):
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
            program_url = BASE_URL + next_page_path.a["href"]
            logging.info(f"Scraping next page: {program_url}")
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

    with (DATA / "supervisors_by_program.json").open(mode="w") as f:
        json.dump(supervisors_by_program, fp=f)


if __name__ == "__main__":
    logging.info("Starting a new scraping run.")
    main()
