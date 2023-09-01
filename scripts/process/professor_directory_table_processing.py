# Loading Library
import re
import pandas as pd

from pathlib import Path

# Constants
DATA = Path(__file__).parents[2] / "data"
INPUT = DATA / "raw" / "raw_professor_directory.html"
OUTPUT = DATA / "processed" / "professor_directory.csv"


# Helper Functions
def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean column names of a DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with lowercase column names.
    """
    df.columns = df.columns.str.lower()
    return df


def extract_substring(df: pd.DataFrame, column: str, pattern: str) -> pd.Series:
    """
    Extract substrings from a DataFrame column using a regex pattern.

    Args:
        df (pd.DataFrame): Input DataFrame.
        column (str): Name of the column to extract from.
        pattern (str): Regular expression pattern for extraction.

    Returns:
        pd.Series: Extracted substrings.
    """
    return df[column].str.extract(pat=pattern)


def reorder_names(string: str) -> str:
    """
    Reorder names from "Last, First" to "First Last".

    Args:
        string (str): Input name in "Last, First" format.

    Returns:
        str: Reordered name in "First Last" format.
    """
    surnames, given_names = string.split(",", 1)
    name = f"{given_names.strip()} {surnames.strip()}"
    return name


def remove_degrees_from_name(string: str) -> str:
    """
    Remove degrees (e.g., 'Dr.' or 'PhD') from a name.

    Args:
        string (str): Input name with degrees.

    Returns:
        str: Name with degrees removed.
    """
    return re.sub(string=string, pattern="(Dr\.?)|((, )?PhD)", repl="")


def extract_name_title_department(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract name, title, and department from a DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame with 'name', 'title', and 'department' columns.
    """
    df["name"] = extract_substring(
        df, column="name", pattern=r"^printString\(.*\); \t(.*)$"
    )
    df[["title", "department"]] = extract_substring(
        df,
        column="title / department",
        pattern=r"^printString\(.*\); \t(.*) printString\(.*\); \t(.*)$",
    )
    return df.drop(columns=["telephone / email", "title / department"])


def process_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process names in the DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame with processed 'name' column.
    """
    df.loc[df["name"].str.contains(","), "name"] = df[df["name"].str.contains(",")][
        "name"
    ].apply(reorder_names)

    df.loc[df["name"].str.match("(Dr|PhD)"), "name"] = df[
        df["name"].str.match("(Dr|PhD)")
    ]["name"].apply(remove_degrees_from_name)

    df["name"] = df["name"].str.strip()
    return df


if __name__ == "__main__":
    # Load data
    data = pd.read_html(INPUT)[0]
    
    # Cleaning column names
    cleaned_data = clean_column_names(data)

    # Extract name, title, and department
    cleaned_data = extract_name_title_department(data)

    # Process names
    cleaned_data = process_names(cleaned_data)

    # Save the cleaned data to a CSV file
    cleaned_data.to_csv(OUTPUT, index=False)
