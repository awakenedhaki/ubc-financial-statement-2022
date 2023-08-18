# FY22 UBC Financial Statement

This repo explores the distribution of UBC employee remunerations.

The University of British Columbia (UBC) releases financial statements each year reflecting the assets, liabilities, revenues and expenses of UBC within a fiscal year. UBC also provides unaudited supplemental information about the remunerations of UBC employees that earn greater than 75,000 CAD.

The financial reports can be found here: <https://finance.ubc.ca/reporting-planning-analysis/financial-reports>

The project's codebase is structured as in three main repositories:

1. `scripts`: The scripts directory contains the code used for scraping, processing, and visualizing the data. Web scraping is performed using `requests` or `playwright`. Visualization is performed using `ggplot2`. The processing of data is a combination of the `tidyverse` and `pandas`.
2. `notebooks`: Jupyter notebooks are used as a simple platform to inspect data that has been generate, scraped, or processed. The data processing or collection does not occur within the notebooks.
3. `cli`: Command-line interfaces were implemented using `click` to stream line manual corrections of the data sets being generated.