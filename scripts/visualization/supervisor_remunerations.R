# Loading Packages =============================================================
library(here)
library(scales)
library(tidyverse)

# Constants ====================================================================
DATA <- here("data", "processed")

# Setting ggplot2 defaults =====================================================
update_geom_defaults("bar", list(color = "black", fill = "salmon"))
theme_set(theme_minimal())
theme_update(panel.border = element_rect(color = "black", fill = "transparent"))

# Loading Data =================================================================
remunerations <- read_csv(here(DATA, "supervisor_remunerations.csv"))

# Visualizations ===============================================================
# # Top 10 Remunerations
remunerations %>%
  arrange(desc(remuneration)) %>%
  head(n = 10)

# # Top 10 Expenses
remunerations %>%
  arrange(desc(expenses)) %>%
  head(n = 10)

# # Top 10 Specializations
remunerations %>%
  separate_longer_delim(cols = appointment, delim = "\t") %>%
  summarize(median_remuneration = median(remuneration), .by = "appointment") %>%
  arrange(desc(median_remuneration)) %>%
  head(n = 10)

# Remuneration of Supervisors
remunerations %>%
  ggplot(aes(x = remuneration)) +
    geom_histogram() +
    geom_vline(aes(xintercept = median(remuneration)), linetype = "dashed") +
    scale_x_continuous(label = label_dollar())

# # Remuneration Distribution by Specialization of Interest
SPECIALIZATIONS <- c("Genome Science and Technology",
                     "Biomedical Engineering",
                     "Bioinformatics",
                     "Medical Genetics",
                     "Pathology and Laboratory Medicine",
                     "Microbiology and Immunology",
                     "Interdisciplinary Oncology",
                     "Women+ and Children's Health Sciences",
                     "Zoology",
                     "Botany")

remunerations %>%
  separate_longer_delim(cols = appointment, delim = "\t") %>%
  filter(appointment %in% SPECIALIZATIONS) %>%
  mutate(appointment = fct_reorder(appointment, remuneration, median)) %>%
  ggplot(aes(x = remuneration, y = appointment, fill = appointment)) +
    geom_boxplot(show.legend = FALSE) +
    geom_vline(aes(xintercept = median(remuneration)), linetype = "dashed") +
    scale_x_continuous(label = label_dollar()) +
    labs(x = "Remuneration (CAD)", y = "Appointment") +
    theme_classic()
  
  
