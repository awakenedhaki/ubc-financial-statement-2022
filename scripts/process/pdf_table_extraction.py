# Loading Libraries
import tabula
import tomllib
import pandas as pd

from pathlib import Path
from typing import Dict, Any, List

# Constants
DATA = Path.cwd() / "data"
FINANCIAL_STATEMENT = DATA / "raw" / "remunerations.pdf"
OUTPUT = DATA / "tmp" / "unprocessed_remunerations.csv"


# Helper Functions
def inch_to_point(inch: float) -> float:
    """
    Convert inches to points, where 1 inch equals 72 points.

    Args:
        inch (float): Length in inches.

    Returns:
        float: Length in points.
    """
    return inch * 72


def inches_to_points(inches: List[float]) -> List[float]:
    """
    Convert a list of lengths in inches to points using the inch_to_point function.

    Args:
        inches (List[float]): List of lengths in inches.

    Returns:
        List[float]: List of lengths in points.
    """
    return [inch_to_point(inch) for inch in inches]


def build_table_measurement(
    measurement: Dict[str, Any], section: str, table: str
) -> List[float]:
    """
    Build table measurements for a specified section and table based on a measurement dictionary.

    Args:
        measurement (Dict[str, Any]): A dictionary containing measurement values.
        section (str): The section name for which measurements are needed.
        table (str): The table (e.g., "left" or "right") for which measurements are needed.

    Returns:
        List[float]: A list of table measurements: [top, left, bottom, right].
    """
    return [
        measurement[section]["top"],
        measurement["widths"][table]["left"],
        measurement[section]["bottom"],
        measurement["widths"][table]["right"],
    ]


def build_table_measurements(
    measurements: Dict[str, Any], section: str
) -> List[List[float]]:
    """
    Build table measurements for both left and right tables in a specified section
    based on a measurement dictionary.

    Args:
        measurements (Dict[str, Any]): A dictionary containing measurement values.
        section (str): The section name for which measurements are needed.

    Returns:
        List[List[float]]: A list containing two lists of table measurements:
        [[left_table_measurements], [right_table_measurements]].
    """
    left_table = build_table_measurement(measurements, section, table="left")
    right_table = build_table_measurement(measurements, section, table="right")
    return [inches_to_points(left_table), inches_to_points(right_table)]


def extract_page_tables(
    pdf_path: str, pages: str, table_measurements: List[List[float]]
):
    return tabula.read_pdf(
        pdf_path,
        pages=pages,
        encoding="utf-8",
        stream=True,
        multiple_tables=True,
        area=table_measurements,
    )


if __name__ == "__main__":
    with (Path(__file__).parents[2] / "config.toml").open(mode="rb") as f:
        config = tomllib.load(f)
    TABLE_MEASUREMENTS = config["table_measurements"]

    raw_remunerations_table = pd.DataFrame()
    for section, parameters in config["sections"].items():
        table_measurements = build_table_measurements(
            TABLE_MEASUREMENTS, section=section
        )
        parsed_tables = extract_page_tables(
            FINANCIAL_STATEMENT,
            pages=parameters["page_numbers"],
            table_measurements=table_measurements,
        )
        raw_remunerations_table = pd.concat([table, *parsed_tables])

    raw_remunerations_table.to_csv(OUTPUT, index=False)
