# Loading Libraries
import numpy as np
import pandas as pd

from uuid import uuid4
from pathlib import Path
from typing import List


# Constants
DATA = Path.cwd() / "data"
INPUT = DATA / "tmp" / "raw_remunerations.csv"
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


def build_employee_name(parent: str, orphan: str) -> str:
    """
    Concatenates two name parts into a complete employee name.

    This function takes two strings, 'parent' and 'orphan', representing parts of an employee's name.
    It combines these parts into a complete name with an optional space between them, based on the 'parent' string.
    
    Args:
        parent (str): The left name part.
        orphan (str): The right name part.
        
    Returns:
        str: The combined employee name.
    """
    if parent.endswith("-"):
        combined_name = f"{parent}{orphan}"
    else:
        combined_name = f"{parent} {orphan}"
    return combined_name


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
        employee_name = build_employee_name(parent_name, orphan_name)

        adopted_names_df.at[location - offset, column] = employee_name
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


def split_column(df: pd.DataFrame, column: str, delim: str) -> pd.DataFrame:
    """
    Split a DataFrame column into two columns using a specified delimiter.

    Args:
        df (pd.DataFrame): The DataFrame containing the column to split.
        column (str): The name of the column to split.
        delim (str): The delimiter used for splitting.

    Returns:
        pd.DataFrame: A new DataFrame with two columns, each containing
        one part of the split values.
    """
    return df[column].str.split(pat=delim, n=1, expand=True)


def process_table(table: pd.DataFrame) -> pd.DataFrame:
    """
    Process an individual table by applying a series of transformations.

    Args:
        table (pd.DataFrame): The input DataFrame representing a table.

    Returns:
        pd.DataFrame: A processed DataFrame after cleaning, filtering, name matching,
        NaN replacement, thousand separator removal, type casting, and name splitting.
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

    # Step 7: Split names into given and surname columns
    name_columns = ["surname", "given_name"]
    type_casted_df[name_columns] = split_column(
        type_casted_df, column="name", delim=", "
    )

    return type_casted_df


if __name__ == "__main__":
    raw_remunerations_table = pd.read_csv(INPUT)
    processed_remunerations_table = process_table(raw_remunerations_table)

    processed_remunerations_table["id"] = pd.Series(
        data=[uuid4() for _ in range(processed_remunerations_table.shape[0])]
    )

    column_order = ["id", "name", "given_name", "surname", "remuneration", "expenses"]
    processed_remunerations_table = processed_remunerations_table[column_order]

    processed_remunerations_table.to_csv(OUTPUT, index=False)
