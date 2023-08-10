# Loading packages
import pandas as pd
from pathlib import Path

# Constants
DATA = Path(__file__).parents[2] / "data"
N_PAGES = 4
BASE_URL = "https://www.grad.ubc.ca"
UBC_GRAD_PROGRAMS = "/prospective-students/graduate-degree-programs"


# Helper Functions
def pluck(series, index):
    """
    Extract a specific element from each element of a pandas Series.

    Args:
        series (pd.Series): A pandas Series containing elements from which to extract values.
        index (int): The index of the element to extract from each element of the Series.

    Returns:
        pd.Series: A new pandas Series containing the extracted values.

    Description:
        This function takes a pandas Series `series` and an `index` as input and applies a lambda function to each
        element of the Series. The lambda function extracts the value at the specified `index` from each element.
        The function returns a new pandas Series containing the extracted values.

    Example:
        data_series = pd.Series([["John", "Doe"], ["Jane", "Smith"]])
        result_series = pluck(data_series, 0)
        print(result_series)  # Output: [John, Alice]

    Note:
        The `series` argument is expected to contain elements that are indexable, such as lists or tuples.
    """
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
table.to_csv(DATA / "references" / "ubc_grad_programs.csv", index=False)
