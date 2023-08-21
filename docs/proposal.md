# UBC Remunerations Across Departments

## Background

The University of British Columbia (UBC) is a public research university that ranks in the top 50 universities in the world across THE (2023), AWRU (2022) and QS (2023). 

As part of the British Columbia Financial Information Act, UBC is required to release the remunerations of all its employees. The remunerations are not audited and only names employees that earn greater than 75,000 CAD.

Faculty members at UBC will often require a doctorate degree (i.e. PhD, MD, JD) in their respective field of study. Tenure-tracked appointments at a research institute are generally competitive and require extensive training within a doctoral dissertation and post-doctoral work. The degree of training and competitiveness of a professorship suggests the position offers a noteable compensation.

Once a candidate is successful in securing an appointment at UBC, [their salary is discussed with their Department Head](https://www.facultyassociation.ubc.ca/worklife/salaries/) and they join the [UBC Faculty Association](https://www.facultyassociation.ubc.ca/). A faculty member's remuneration is then subject to increase by (1) collective bargaining every 2 to 4 years, (2) career progress increments, and (3) merit/performance salary adjustments.

Departmental budgets play a key role in shaping faculty compensation. The resources available to a department influence the number of faculty members it can support and their corresponding compensation. This financial interplay extends to cross-departmental appointments, where negotiations may differ based on unique circumstances. 

## Objective

To describe the remunerations between UBC Faculty members earning greater than 75,000 CAD across professorship status, department and faculty. A Faculty member, for this project, is defined as a UBC employee that holds an Assistant, Associated or Full Professorship.

## Data Sources

### Employee Remuneration (>75,000 CAD)

UBC publicly releases unanonimized remunerations for employees that earn more than 75,000 CAD as a [PDF file](https://finance.ubc.ca/sites/finserv.ubc.ca/files/FY22%20UBC%20Statement%20of%20Financial%20Information.pdf). The employee remunerations is presented as a table with three columns: Name, Remuneration, and Expenses. The table spans two column within a page of a document.

The employees are sorted in alphabetical order by last name. The names are formatted as "Last Name, Given Name". Names are wrapped in their cell if they exceed their cell's width.

All employees included in the financial report receive remuneration, which represents the total compensation allocated by UBC.

Not all personnel have documented expenses. Employee expenditures could encompass travel and lodging, activities in which not all staff members will participate.

### UBC Directory

The [UBC directory](https://directory.ubc.ca/index.cfm) is a query-based search tools that provides UBC employee name, job title, department, worksite, telephone, and email as a formatted table.

The UBC directory will provided metadata for the remunerations identified in the supplementary document of the financial report. The directory allows for the retrieval of 5, 10, 20, 50, or 100 results per query. The query is a many-to-many operation. The same employee may have multiple rows, indicating cross-appointment within UBC and campus satellites. Different employees may also share the same or similarly abbreviated names. 

## Metadata Collection

### Employee Department and Faculty

The [UBC directory](https://directory.ubc.ca/index.cfm) is scraped to link employee names to job titles, department, and faculty appointments. The employee names are retrieved from the UBC financial report supplementary information, discussed in a later section of the proposal. 

To submit a request to the UBC directory form, the `playwright` (1.36) package with the `Chromium` (115.0.5790.75) driver is used. The request is sent using the default "Quick Search" settings. The employee name inputed into the form is preprocessed by removing initials and case folding.

Once the response from the UBC directory server is received, the HTML of the page is extracted and parsed using `beautifulsoup4` (4.12.2). Only the first 10 rows of the results table are extracted. 

The results from the UBC directory are indexed by the unprocessed employee name. The cells of each row in a table are stored as unprocessed string values.

An employee name may correspond to multiple records in the UBC directory. A response with more than one result suggests that (1) the employee has more than one appointment at UBC, (2) multiple employees share the same name, or (3) the processed employee name is too ambiguous. There will be employee names from the remunerations data set that are incomplete, which is discussed in a separate section of this proposal.

## Data Processing

### Employee Remuneration Extraction

The remuneration of employees is provided as a table in a portable document format (PDF). 

The PDF file is loaded into memory and the text is extracted using the C++ library `poppler` (22.02.0) via R bindings provided in the `pdftools` (3.3.3) package. The list of characters is then filtered according to keywords associated with the relevant PDF pages. The cells, rows, and columns are then normalized using regular expressions for later mapping the text into a tibble.

The employee names that exceed their cell's width wrap to a new line. The text extraction method within `poppler` will output the wrapped names as a distinct line of text. The names that are most likely to be wrapped are given names, instead of last names. A last name can be distinguished by preceding a comma. Therefore, there will be given names that are ambiguously linked to employees. These names are retained as a separate column matching the most likely rows the given name belongs to, determined by index within the character vector. 

The ambiguous names are resolved manually by cross-referencing with the financial report. 

The data is persisted as a CSV file.

### Joining Employee Metadata and Remuneration

The employee metadata obtained from the UBC directory assigns labels that will help with stratifying employees into groups of interest for this study. The main groups of interest are (1) job title, (2) department and (3) faculty.

The results from the UBC directory are indexed by the unprocessed employee names recorded in the remunerations data set. Therefore, the employee name acts as a shared index that can be used to join the remunerations data with the employee metadata. A left outer join operation will be performed with the remuneration data being the left table, because it acts as our ground truth for current employees working at UBC that earn >75,000 CAD.

In the left outer join operation, there will be one-to-one and many-to-one matches. When employee metadata was collected from the UBC directory, it was represented as a Python dictionary which does not allow for duplicate keys. Therefore, employees with the identical processed employee names will have the UBC directory results. As such, these employee names will match to 2 or more names within the remunertaions data set.