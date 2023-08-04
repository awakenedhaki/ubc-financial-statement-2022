# Loading Libraries ============================================================
library(uuid)
library(here)
library(scales)
library(tidyverse)

# Setting ggplot2 defaults =====================================================
update_geom_defaults("bar", list(color = "black", fill = "salmon"))
theme_set(theme_minimal())

# Constants ====================================================================
DATA <- here("data")

# Loading Data =================================================================
remunerations <- read_csv(here(DATA, "processed_remunerations.csv"))

# Visualizations ===============================================================
# # Top 10 Remunerations
remunerations %>%
  arrange(desc(remuneration)) %>%
  head(n = 10)

# # Top 10 Expenses
remunerations %>%
  arrange(desc(expenses)) %>%
  head(n = 10)

# # Distribution of Remuneration
remunerations %>%
  ggplot(aes(x = remuneration)) +
    geom_histogram() +
    geom_vline(aes(xintercept = median(remuneration))) +
    scale_x_continuous(breaks = seq(0, 1e6, 1e5), label = label_dollar()) +
    scale_y_continuous(label = label_comma())

# # Benford's Law
remunerations %>%
  mutate(remuneration = str_extract(remuneration, pattern = boundary("character"))) %>%
  count(first_digit = remuneration) %>%
  mutate(percent = n / sum(n)) %>%
  ggplot(aes(x = first_digit, y = percent)) +
    geom_col() +
    geom_text(aes(label = percent(percent, accuracy = 0.01)), vjust = -0.5) +
    scale_y_continuous(label = label_percent()) +
    expand_limits(y = c(0, .6))
