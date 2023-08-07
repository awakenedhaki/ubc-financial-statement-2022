# Loading Dependencies =========================================================
library(glue)
library(here)
library(vctrs)
library(stringi)
library(pdftools)
library(tidyverse)

# Loading Data =================================================================
statement <- pdf_text(here("data", "/FY22 UBC Statement of Financial Information.pdf"))
raw_remunerations <- statement[str_detect(string = statement, 
                                          pattern = "Name[:blank:]*Remuneration[:blank:]*")]

# Helper Functions =============================================================
remove_surrounding_text <- function(page) {
  trim_left_idx <- page %>%
    str_locate(pattern = "Expenses\\*\n{1,}") 

  trim_right_idx <- page %>%
    str_locate(pattern = "(Earnings greater than)|(Page \\|)") 

  page %>%
    substring(first = trim_left_idx[, 2], last = trim_right_idx[, 1] - 1) %>%
    str_trim()
}

remove_parentheses <- function(page) {
  page %>%
    str_replace(pattern = "\\(((?:\\d+,)?\\d+)\\)", replacement = "\\1")
}

normalize_table <- function(page) {
  page %>%
    str_split(pattern = "\n", simplify = TRUE) %>%
    str_replace(pattern = "(\\d)[:blank:]{2,}([A-z])", replacement = "\\1\n\\2") %>%
    str_split(pattern = "\n", simplify = FALSE) %>%
    unlist() %>%
    str_trim()
}

normalize_rows <- function(page) {
  page %>%
    str_replace(pattern = "^(\\w+)[:blank:]{2,}([A-Z])",       replacement = "\\1\n\\2") %>%
    str_replace(pattern = "[:blank:]\\-[:blank:]",      replacement = "\\-\n") %>%
    str_replace(pattern = "(\\d+)[:blank:]{2,}([A-z])", replacement = "\\1\n\\2") %>%
    str_split(pattern = "\n", simplify = FALSE) %>%
    unlist() %>%
    str_trim()
}

is_missing_first_name <- function(string) {
  str_detect(string, "[a-z],[:blank:]*\\d+")
}

ends_with_character <- function(string) {
  str_detect(string, "[A-z]$")
}

fill_missing_first_names <- function(page) {
  flagged_rows <- c()
  missing_first_name <- NA
  for (i in 1:length(page)) {
    if (is_missing_first_name(page[i])) {
      missing_first_name <- i
    } else if (!is.na(missing_first_name) & ends_with_character(page[i])) {
      page[missing_first_name] <- page[missing_first_name] %>%
        str_replace(pattern = "([a-z],)", replacement = glue("\\1 {page[i]}"))
      
      missing_first_name <- NA
      flagged_rows <-c(flagged_rows, i)
    }
  }
  
  if (length(flagged_rows) == 0) {
    return(page)
  }
  return(page[-flagged_rows])
}

to_tibble <- function(table) {
  table %>%
    str_split(pattern = "[:blank:]{2,}") %>%
    lapply(FUN = \(x) stri_remove_empty(x)) %>%
    as_tibble_col() %>%
    unnest_wider(col = value, names_sep = "_") %>%
    mutate(value_2 = parse_number(value_2), value_3 = parse_number(value_3)) %>%
    rename(name = value_1, remuneration = value_2, expenses = value_3)
}

ambiguous_floating_name <- function(tbl) {
  tbl %>%
    mutate(ambiguous_name = ifelse(str_detect(name, "^\\w+([,\\s]{1,2}\\w+)?$") & is.na(remuneration),
                                   name, 
                                   NA))  %>%
    mutate(ambiguous_name = vec_fill_missing(ambiguous_name,
                                             direction = "up",
                                             max_fill = 2))
}

# Parsing Remunerations ========================================================
remunerations <- raw_remunerations %>%
  map(.f = \(x) {
    x %>%
      remove_surrounding_text() %>%
      str_to_title() %>%
      remove_parentheses() %>%
      normalize_table() %>%
      normalize_rows() %>%
      fill_missing_first_names() %>%
      to_tibble() %>%
      ambiguous_floating_name()
  }) 

# Manual Checks ================================================================
# # Missing name
remunerations %>%
  lapply(FUN = \(x) {
    x %>%
      filter(is.na(name))
  })

# # Remunerations below $75,000
remunerations %>%
  lapply(FUN = \(x) {
    x %>%
      filter(remuneration < 75000)
  }) 

# # Missing remunerations
remunerations %>%
  lapply(FUN = \(x) {
    x %>%
      filter(is.na(remuneration))
  })

# # Missing comma in name
remunerations %>%
  lapply(FUN = \(x) {
    x %>%
      filter(!str_detect(name, ","))
  })

# # Non-numeric names
remunerations %>%
  lapply(FUN = \(x) {
    x %>%
      mutate(is_numeric_name = str_detect(name, "\\d+")) %>%
      filter(is_numeric_name)
  }) 

# Removing missing remunerations ===============================================
remunerations %>%
  bind_rows() %>%
  filter(!is.na(remuneration)) %>%
  write_csv(here("data", "cleaned_remunerations.csv"))
