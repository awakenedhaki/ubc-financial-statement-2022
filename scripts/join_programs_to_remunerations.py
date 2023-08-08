# Loading Packages
import json
import pandas as pd

from pathlib import Path
from itertools import groupby
from operator import itemgetter
from collections import defaultdict


# Constants
DATA = Path(__file__).parents[1] / "data"
REMUNERATIONS = DATA / "cleaned_remunerations.csv"
UBC_GRAD_PROGRAMS = DATA / "cleaned_programs.csv"
SUPERVISORS = DATA / "supervisors_by_program.json"

# Loading Data
with SUPERVISORS.open(mode="r") as f:
    supervisors_by_program = json.load(f)

remunerations = pd.read_csv(REMUNERATIONS)
ubc_grad_programs = pd.read_csv(UBC_GRAD_PROGRAMS)


# Helper Functions
first_character = itemgetter(0)


def invert_supervisors_by_program(programs):
    programs_by_supervisor = defaultdict(list)
    for program, supervisors in programs.items():
        for supervisor in supervisors:
            name = supervisor["name"].casefold()
            programs_by_supervisor[name].append(program)
    return programs_by_supervisor


def collapsing_programs_to_specialization(supervisors):
    specialization_by_supervisor = defaultdict(list)
    for supervisor, programs in supervisors.items():
        specialization_by_supervisor[supervisor] = (
            ubc_grad_programs[ubc_grad_programs["program_page"].isin(programs)][
                "specialization"
            ]
            .unique()
            .tolist()
        )
    return specialization_by_supervisor


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

    remunerations[["name", "remuneration", "expenses", "appointment"]].to_csv(
        DATA / "supervisor_remunerations.csv"
    )
