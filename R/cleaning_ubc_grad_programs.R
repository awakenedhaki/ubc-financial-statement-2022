# Loading Packages =============================================================
library(here)
library(janitor)
library(tidyverse)

# Constants ====================================================================
UBC_GRAD_PROGRAMS <- here("data", "raw", "ubc_grad_programs.csv")

# Loading Data =================================================================
programs <- read_csv(UBC_GRAD_PROGRAMS)

# Cleaning UBC Grad Programs ===================================================
cleaned_programs <- programs %>%
  clean_names() %>%
  extract(col = program_name, 
          into = c("program_name", "degree_type"), 
          regex = "(.*) \\((\\w+)\\)")

# Saving Data ==================================================================
write_csv(cleaned_programs, file = here("data", "clean", "programs.csv"))
