# Loading Packages
import re
import json
import click

from pathlib import Path

# Constants
AMBIGUOUS_EMPLOYEES = (
    Path.cwd() / "data" / "tmp" / "ambiguous_employees_more_than_3.json"
)
DISAMBIGUATED_EMPLOYEES = Path.cwd() / "data" / "tmp" / "disambiguated_employees.json"


# Helper Functions
def load_ambiguous_employees():
    with AMBIGUOUS_EMPLOYEES.open(mode="r") as f:
        return json.load(f)


def save_json(path, data):
    with path.open(mode="w") as f:
        json.dump(data, f)


def display_results(results):
    for i, result in enumerate(results):
        result = re.sub(pattern=r"[\s]{2,}", repl=" ", string=" ".join(result[:2]))
        click.echo(message=f"{i}: {result}")


def select_retained_result(ambiguous_employees):
    retained_results = {}
    for name, results in ambiguous_employees.items():
        click.echo(message=click.style(name, fg="green"))
        display_results(results)
        index = click.prompt("Which entry do you want to retain?", type=int)
        if index < 0:
            retained_results[name] = ""
        retained_results[name] = results[index]
        click.clear()


# Main Function
@click.command()
def main():
    click.clear()
    ambiguous_employees = load_ambiguous_employees()
    retained_results = select_retained_result(ambiguous_employees)
    save_json(DISAMBIGUATED_EMPLOYEES, retained_results)


if __name__ == "__main__":
    main()
