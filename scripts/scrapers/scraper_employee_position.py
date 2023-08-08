# Loading Libraries
import asyncio
import logging
import pandas as pd

from uuid import uuid4
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Constants
DATA = Path(__file__).parents[2] / "data"
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
def search_employee():
    pass


def parse_results():
    pass


def normalize_name():
    pass


def main():
    employee_remunerations = pd.read_csv(
        DATA / "processed" / "all_remunerations.csv"
    ).loc[:, "name"]


if __name__ == "__main__":
    main()
