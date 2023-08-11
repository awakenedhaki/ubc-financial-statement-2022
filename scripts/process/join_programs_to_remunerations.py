# Loading Packages
import json
import pandas as pd

from pathlib import Path
from collections import defaultdict


# Constants
DATA = Path(__file__).parents[2] / "data"
REMUNERATIONS = DATA / "processed" / "all_remunerations.csv"
UBC_GRAD_PROGRAMS = DATA / "processed" / "ubc_grad_programs.csv"
SUPERVISORS = DATA / "references" / "supervisors_by_program.json"

# Loading Data
with SUPERVISORS.open(mode="r") as f:
    supervisors_by_program = json.load(f)

remunerations = pd.read_csv(REMUNERATIONS)
ubc_grad_programs = pd.read_csv(UBC_GRAD_PROGRAMS)


# Helper Functions
def invert_supervisors_by_program(programs):
    """
    Invert a dictionary of supervisors by program to create a dictionary of programs by supervisor.

    Args:
        programs (dict): A dictionary mapping program names to lists of supervisor details.

    Returns:
        defaultdict: A defaultdict where keys are normalized supervisor names and values are lists of programs.

    Description:
        This function takes a dictionary `programs` as input, where keys are program names and values are lists
        of supervisor details. It iterates through the supervisors for each program, extracts normalized supervisor
        names, and creates a new defaultdict where keys are normalized supervisor names and values are lists of programs.

    Note:
        - The `programs` argument should be a dictionary mapping program names to lists of supervisor details.
        - The normalized supervisor names are converted to lowercase using the `casefold` method.
    """
    programs_by_supervisor = defaultdict(list)
    for program, supervisors in programs.items():
        for supervisor in supervisors:
            name = supervisor["name"].casefold()
            programs_by_supervisor[name].append(program)
    return programs_by_supervisor


def collapsing_programs_to_specialization(supervisors):
    """
    Collapse UBC programs to specialization for each supervisor.

    Args:
        supervisors (dict): A dictionary mapping normalized supervisor names to lists of programs.

    Returns:
        defaultdict: A defaultdict where keys are normalized supervisor names and values are lists of specializations.

    Description:
        This function takes a dictionary `supervisors` as input, where keys are normalized supervisor names and values
        are lists of UBC programs. It collapses the UBC programs to unique specializations for each supervisor.
        The result is a defaultdict where keys are normalized supervisor names and values are lists of specializations.

    Note:
        - The `supervisors` argument should be a dictionary mapping normalized supervisor names to lists of programs.
        - This function assumes that `ubc_grad_programs` is defined and contains relevant program information.
    """
    specializations_by_supervisor = defaultdict(list)
    for supervisor, programs in supervisors.items():
        specializations_by_supervisor[supervisor] = (
            ubc_grad_programs[ubc_grad_programs["program_page"].isin(programs)][
                "specialization"
            ]
            .unique()
            .tolist()
        )
    return specializations_by_supervisor


# Main Function
if __name__ == "__main__":
    specializations_by_supervisor = collapsing_programs_to_specialization(
        invert_supervisors_by_program(supervisors_by_program)
    )

    remunerations["appointment"] = (
        remunerations["name"]
        .str.casefold()
        .apply(lambda name: "\t".join(specializations_by_supervisor[name]))
    )

    supervisor_flag = remunerations["appointment"].apply(lambda value: value != "")
    remunerations[["name", "remuneration", "expenses", "appointment"]].loc[
        supervisor_flag
    ].to_csv(DATA / "processed" / "research_supervisor_remunerations.csv", index=False)
