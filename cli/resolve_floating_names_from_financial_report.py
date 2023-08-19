# Loading Packages
import click
import pandas as pd

from uuid import uuid4
from pathlib import Path

# Constants
DATA = Path(__file__).parents[2] / "data" / "all_remunerations.csv"


# Helper Functions
def load_unresolved_rows(path):
    df = pd.read_csv(DATA)
    return df[~df["ambiguous_name"].isnull()]


# Main Functions
@click.command()
def main():
    pass


if __name__ == "__main__":
    pass
