# Loading Libraries
import tabula
import tomllib
import numpy as np
import pandas as pd

from pathlib import Path
from typing import Dict, Any, List

# Constants
DATA = Path.cwd() / "data"
FINANCIAL_STATEMENT = DATA / "raw" / "remunerations.pdf"
OUTPUT = DATA / "processed" / "all_remunerations.csv"


# Helper Functions
def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean column names of a DataFrame by removing non-alphanumeric characters
    and converting them to lowercase.

    Args:
        df (pd.DataFrame): The DataFrame with columns to be cleaned.

    Returns:
        pd.DataFrame: A new DataFrame with cleaned column names.
    """
    df.columns = df.columns.str.replace(pat="\W", repl="", regex=True).str.casefold()
    return df


def search_empty_rows(df: pd.DataFrame) -> pd.Series:
    """
    Check for the presence of NaN values in each row of a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to be checked.

    Returns:
        pd.Series: A boolean Series indicating if NaN values are present in each row.
    """
    return df.isnull().values.all(axis=1)


def match_orphaned_names(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Match orphaned names in a DataFrame by concatenating them with their preceding names.

    Args:
        df (pd.DataFrame): The DataFrame containing the names to be matched.
        column (str): The column in the DataFrame containing the names.

    Returns:
        pd.DataFrame: The DataFrame with matched names.
    """
    adopted_names_df = df.copy()
    is_orphaned_names = search_empty_rows(df.drop(columns=column, axis=1))
    adopted_names_df = adopted_names_df[~is_orphaned_names]

    orphan_location = np.flatnonzero(is_orphaned_names)
    previous_location = -1
    offset = 1
    for location in orphan_location:
        if previous_location == (location - 1):
            offset += 1
        else:
            offset = 1

        parent_name = adopted_names_df.loc[location - offset, column]
        orphan_name = df.loc[location, column]

        if parent_name.endswith("-"):
            combined_name = f"{parent_name}{orphan_name}"
        else:
            combined_name = f"{parent_name} {orphan_name}"

        adopted_names_df.at[location - offset, column] = combined_name
        previous_location = location

    return adopted_names_df


def na_if(df: pd.DataFrame, column: str, value) -> pd.DataFrame:
    """
    Replace specified values in a DataFrame column with NaN values.

    Args:
        df (pd.DataFrame): The DataFrame to be modified.
        column (str): The column in the DataFrame where replacement will be performed.
        value: The value to be replaced with NaN.

    Returns:
        pd.DataFrame: The modified DataFrame.
    """
    df[column] = df[column].replace(to_replace=value, value=np.nan)
    return df


def process_table(table: pd.DataFrame) -> pd.DataFrame:
    """
    Process an individual table by applying a series of transformations.

    Args:
        table (pd.DataFrame): The input DataFrame representing a table.

    Returns:
        pd.DataFrame: A processed DataFrame after cleaning, filtering, name matching, NaN replacement,
        thousand separator removal, and type casting
    """
    # Step 1: Normalize column names
    cleaned_df = clean_column_names(table)

    # Step 2: Remove rows that are entirely NaN
    non_empty_rows_df = cleaned_df.dropna(how="all").reset_index(drop=True)

    # Step 3: Match orphaned names
    matched_names_df = match_orphaned_names(non_empty_rows_df, column="name")

    # Step 4: Replace specific values with NaN
    na_replace_df = na_if(matched_names_df, column="expenses", value="-")

    # Step 5: Remove thousand separator from numeric values
    numeric_columns = ["remuneration", "expenses"]
    na_replace_df[numeric_columns] = na_replace_df[numeric_columns].replace(
        ",", "", regex=True
    )

    # Step 6: Type casting columns
    type_casted_df = na_replace_df.astype(
        dtype={"remuneration": "int32", "expenses": "int32"},
        errors="ignore",  # Prevent ValueError from casting NaN values
    )

    return type_casted_df


def process_tables(tables: List[pd.DataFrame]) -> List[pd.DataFrame]:
    """
    Process a list of tables by applying process_table to each table.

    Args:
        tables (List[pd.DataFrame]): A list of input DataFrames, each representing a table.

    Returns:
        List[pd.DataFrame]: A list of processed DataFrames, each representing a processed table.
    """
    return [process_table(table) for table in tables]


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


if __name__ == "__main__":
    with (Path(__file__).parents[2] / "config.toml").open(mode="rb") as f:
        config = tomllib.load(f)
    TABLE_MEASUREMENTS = config["table_measurements"]

    tables = []
    for section, parameters in config["sections"].items():
        raw_pdf_pages = tabula.read_pdf(
            FINANCIAL_STATEMENT,
            pages=parameters["page_numbers"],
            encoding="utf-8",
            stream=True,
            multiple_tables=True,
            area=build_table_measurements(TABLE_MEASUREMENTS, section=section),
        )
        processed_tables = pd.concat(process_tables(raw_pdf_pages))
        tables.append(processed_tables)

    pd.concat(tables).to_csv(OUTPUT, index=False)
