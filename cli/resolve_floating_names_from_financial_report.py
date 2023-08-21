# Loading Packages
import click
import pandas as pd

from pathlib import Path

# Constants
DATA = Path(__file__).parents[1] / "data" 
REMUNERATION = DATA / "processed" / "all_remunerations.csv"
TMP = DATA / "tmp"

# Helper Functions
def load_ambiguous_names(path):
    df = pd.read_csv(REMUNERATION)
    ambiguous_names = df[~df["ambiguous_name"].isnull()].drop(
        columns=["remuneration", "expenses"]
    )
    return ambiguous_names.reset_index()


# Main Functions
@click.command()
def main():
    ambiguous_names = load_ambiguous_names(DATA)
    print(ambiguous_names)
    ambiguous_names["flag"] = 0
    index = 0
    while index <= ambiguous_names.shape[0]:
        click.echo(message=click.style(ambiguous_names.loc[index, "ambiguous_name"], fg="green"))
        click.echo(message=f"0. {ambiguous_names.loc[index, 'name']}")
        click.echo(message=f"1. {ambiguous_names.loc[index + 1, 'name']}")
        name_assignment = click.prompt("Assign name [-1/0/1]", type=int)
        if name_assignment == -1:
            index += 2
            continue
        else:
            ambiguous_names.loc[index + name_assignment, "flag"] = True
        index += 2
    


if __name__ == "__main__":
    main()
