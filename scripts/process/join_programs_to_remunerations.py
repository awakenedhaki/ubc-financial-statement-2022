# Loading Packages
import json
import pandas as pd

from pathlib import Path
from collections import defaultdict


# Constants
DATA = Path(__file__).parents[2] / "data"
REMUNERATIONS = DATA / "processed" / "all_remunerations.csv"
UBC_GRAD_PROGRAMS = DATA / "processed" / "programs.csv"
SUPERVISORS = DATA / "references" / "supervisors_by_program.json"

# Loading Data
with SUPERVISORS.open(mode="r") as f:
    supervisors_by_program = json.load(f)

remunerations = pd.read_csv(REMUNERATIONS)
ubc_grad_programs = pd.read_csv(UBC_GRAD_PROGRAMS)


# Helper Functions
def invert_supervisors_by_program(programs):
    programs_by_supervisor = defaultdict(list)
    for program, supervisors in programs.items():
        for supervisor in supervisors:
            name = supervisor["name"].casefold()
            programs_by_supervisor[name].append(program)
    return programs_by_supervisor


def collapsing_programs_to_specialization(supervisors):
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
    ].to_csv(DATA / "processed" / "supervisor_remunerations.csv")
