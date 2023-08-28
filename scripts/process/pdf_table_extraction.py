# Loading Libraries
import tabula
import tomllib
import numpy as np
import pandas as pd

from pathlib import Path

# Constants
DATA = Path.cwd() / "data"
FINANCIAL_STATEMENT = DATA / "raw" / "remunerations.pdf"
OUTPUT = DATA / "processed" / "all_remunerations.csv"

# Helper Functions
def clean_column_names(df):
    df.columns = df.columns.str.replace(pat="\W", repl="", regex=True).str.casefold()
    return df


def search_empty_rows(df):
    return df.isnull().values.all(axis=1)


def match_orphaned_names(df, column):
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


def na_if(df, column, value):
    df[column] = df[column].replace(to_replace=value, value=np.nan)
    return df


def process_table(table):
    cleaned_df = clean_column_names(table)
    drop_empty_rows_df = cleaned_df[~search_empty_rows(cleaned_df)]
    matched_names_df = match_orphaned_names(drop_empty_rows_df, column="name")
    na_replace_df = na_if(matched_names_df, column="expenses", value="-")
    return na_replace_df


def process_tables(tables):
    return [process_table(table) for table in tables]


def inch_to_point(inch):
    return inch * 72


def inches_to_points(inches):
    return [inch_to_point(inch) for inch in inches]


def build_table_measurement(measurement, section, table):
    return [
        measurement[section]["top"],
        measurement["widths"][table]["left"],
        measurement[section]["bottom"],
        measurement["widths"][table]["right"],
    ]


def build_table_measurements(measurements, section):
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
