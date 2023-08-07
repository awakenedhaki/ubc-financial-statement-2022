# Loading packages
import pandas as pd
from pathlib import Path

# Constants
DATA = Path(__file__).parents[1] / "data"
N_PAGES = 4
BASE_URL = "https://www.grad.ubc.ca"
UBC_GRAD_PROGRAMS = "/prospective-students/graduate-degree-programs"


# Helper Functions
def pluck(series, index):
    return series.apply(lambda x: x[index])


# Retrieving UBC Grad Programs Table
tables = pd.read_html(BASE_URL + UBC_GRAD_PROGRAMS, extract_links="body")
for page in range(1, N_PAGES):
    print(f"Getting page {page}...")
    query_string = f"?page={page}"
    tables.extend(
        pd.read_html(BASE_URL + UBC_GRAD_PROGRAMS + query_string, extract_links="body")
    )

# Merging Paginated Tables
print("Processing tables...")
table = pd.concat(tables, axis=0, ignore_index=True)

# Fixing Table
table["Faculty"] = pluck(table["Faculty"], index=0)
table["Specialization"] = pluck(table["Specialization"], index=0)

table[["Program Name", "Program Page"]] = pd.DataFrame(
    table["Program Name"].tolist(), index=table.index
)

# Saving Data
print("Saving tables...")
table.to_csv(DATA / "ubc_grad_programs.csv", index=False)
