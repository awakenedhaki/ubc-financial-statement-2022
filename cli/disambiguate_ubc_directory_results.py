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
    """
    Load ambiguous employee data from a JSON file.

    Returns:
        dict: A dictionary containing ambiguous employee data.

    Description:
        This function reads and loads data from the specified JSON file containing ambiguous employee information.
        The loaded data is returned as a dictionary.

    Note:
        - The JSON file path is specified by the global variable `AMBIGUOUS_EMPLOYEES`.
    """
    with AMBIGUOUS_EMPLOYEES.open(mode="r") as f:
        return json.load(f)


def save_json(path, data):
    """
    Save data to a JSON file.

    Args:
        path (Path): The file path where the JSON data will be saved.
        data (Any): The data to be saved as JSON.

    Description:
        This function saves the provided data in JSON format to the specified file path.
    """
    with path.open(mode="w") as f:
        json.dump(data, f)


def display_results(results):
    """
    Display enumerated UBC directory search results.

    Args:
        results (list): A list of search results.

    Description:
        This function displays search results along with corresponding index numbers for selection.
    """
    for i, result in enumerate(results):
        result = re.sub(pattern=r"[\s]{2,}", repl=" ", string=" ".join(result[:2]))
        click.echo(message=f"{i}: {result}")


def select_retained_result(ambiguous_employees):
    """
    Select employee results to be retained.

    Args:
        ambiguous_employees (dict): A dictionary containing ambiguous employee data.

    Returns:
        dict: A dictionary mapping employee names to retained results.

    Description:
        This function prompts the user to select retained results for each ambiguous employee entry.
        The user can choose between no match, multiple possible matches, or specific search results.
    """
    retained_results = {}
    for name, results in ambiguous_employees.items():
        click.echo(message=click.style(name, fg="green"))
        display_results(results)
        index = click.prompt("Which entry do you want to retain?", type=int)
        if index == -1:  # No match
            retained_results[name] = "No match"
        elif index == -2:  # Multiple possible matches
            retained_results[name] = "Multiple possible matches"
        else:
            retained_results[name] = results[index]
        click.clear()
    return retained_results


# Main Function
@click.command()
def main():
    click.clear()
    ambiguous_employees = load_ambiguous_employees()
    retained_results = select_retained_result(ambiguous_employees)
    save_json(DISAMBIGUATED_EMPLOYEES, retained_results)


if __name__ == "__main__":
    main()
