# Interpretable Analysis of U.S. County-Level Housing Prices (2022)

## Problem Statement

Housing prices vary substantially across regions in the United States.  
While it is widely recognized that socioeconomic and demographic factors such as income, education, population size, and labor market conditions are associated with housing costs, their relative importance and combined effects remain unclear at the regional level.

The goal of this project is to identify which county-level socioeconomic characteristics are most strongly associated with housing prices and to examine how much of the observed variation in housing values across U.S. counties can be explained by these factors.

Rather than focusing on maximizing predictive accuracy, this analysis prioritizes **interpretability and understanding**. The objective is to clarify which factors appear to matter most for housing prices and how their relationships change when multiple correlated characteristics are considered jointly.


## Data Sources

This project combines county-level housing price data from Zillow with socioeconomic and demographic indicators from the U.S. Census Bureau’s American Community Survey (ACS).

### Zillow Housing Data
- **Source:** Zillow Research  
- **Dataset:** County-level Zillow Home Value Index (ZHVI)  
- **File:** `County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`  
- **Description:** Monthly home value estimates for U.S. counties  
- **Processing:** Monthly ZHVI values for 2022 are aggregated into a single annual average for each county (`zhvi_2022`)

### American Community Survey (ACS)
- **Source:** U.S. Census Bureau (data.census.gov)  
- **Survey:** ACS 2022 5-Year Estimates  
- **Geographic level:** County  

**ACS tables used:**
- **B19013** – Median household income  
- **B01003** – Total population  
- **B15003** – Educational attainment  
- **B25010** – Average household size  
- **B23025** – Employment status (used to construct unemployment rate)

Margins of error provided by ACS are not used in this project, as the emphasis is on interpretable associations rather than survey uncertainty.


## Target Variable

The primary outcome variable is county-level housing prices measured using the Zillow Home Value Index.

- **Original measure:**  
  - `zhvi_2022`: Annual average Zillow Home Value Index for 2022  

- **Analysis target:**  
  - `log_zhvi = log(zhvi_2022)`

A logarithmic transformation is applied to housing prices because the raw ZHVI distribution is highly right-skewed. The log transformation reduces the influence of extremely high-priced counties, improves linearity in regression models, and allows coefficients to be interpreted approximately in percentage terms.


## Feature Variables

County-level socioeconomic characteristics derived from the ACS are used as explanatory variables. All features are aligned using standardized 5-digit county FIPS codes.

### Core Feature Candidates
- **`median_income_2022`**  
  Median household income (USD, inflation-adjusted)

- **`ba_plus_share_2022`**  
  Share of the population with a bachelor’s degree or higher

- **`population_2022`**  
  Total county population  
  (used in log-transformed form: `log_population = log1p(population_2022)`)

- **`avg_household_size_2022`**  
  Average household size

- **`unemployment_rate_2022`**  
  Unemployed population divided by the civilian labor force

### Notes on Feature Construction
- Population and labor-force scale variables exhibit strong right skewness and are log-transformed to stabilize variance.
- Education variables are expressed as proportions (0–1) for interpretability.
- All features are constructed at the county level and merged using inner joins to ensure complete data coverage.


## Analysis Scope

- **Geographic unit:** U.S. counties  
- **Time period:** 2022  
- **Housing coverage:** Counties with available Zillow ZHVI data for 2022  
- **Socioeconomic coverage:** Counties with complete ACS 2022 5-year estimates  
- **Exclusions:**  
  - Puerto Rico counties (state FIPS code 72) are excluded to ensure consistency between Zillow and ACS coverage.

The final analysis sample consists of counties with complete housing price and socioeconomic data for 2022.


## Methodological Overview

The analysis follows an exploratory and interpretable modeling approach rather than a predictive or causal framework.

### Exploratory Data Analysis (EDA)
- Examination of variable distributions and skewness  
- Identification of appropriate transformations (e.g., log-transformed housing prices and population)  
- Visualization of bivariate relationships between housing prices and socioeconomic characteristics  
- Assessment of correlations and potential multicollinearity among explanatory variables  

### Stepwise Interpretable Regression
- A sequence of linear regression models is estimated with log-transformed housing prices as the dependent variable.  
- Models are expanded incrementally, starting from simple specifications (e.g., income only) and adding education, population, and demographic controls.  
- Changes in coefficient magnitude and significance across specifications are used to assess robustness and interpretability.

All regression results are interpreted as **conditional associations rather than causal effects**.


## Final Model Specification

The final interpretable regression model is specified as:

log(ZHVI_2022) =
β0
+ β1 · median_income_2022
+ β2 · ba_plus_share_2022
+ β3 · log(1 + population_2022)
+ β4 · avg_household_size_2022
+ β5 · unemployment_rate_2022
+ ε

This specification is treated as the **official final model** for interpretation.

High-school-or-higher attainment (HS+) is excluded from the final specification due to its strong collinearity with bachelor’s degree attainment and is treated as a compositional control in robustness checks.


## Interpretation Strategy

Because the dependent variable is log-transformed, coefficients are interpreted
using a log–linear rule.

Percent change in ZHVI
≈ 100 × (exp(β_k × ΔX_k) − 1)

Effects are evaluated at substantively meaningful unit changes (e.g., +$10,000 income, +10 percentage points in educational attainment) to enhance interpretability.


## Model Diagnostics and Robustness

Several diagnostics and robustness checks are performed, including alternative education specifications:

- Overall model fit (R² ≈ 0.56)
- Residuals versus fitted values
- Assessment of heteroskedasticity
- Multicollinearity diagnostics using Variance Inflation Factors (VIF)
- Robust standard errors (HC3)
- Alternative model specification including high-school-or-higher attainment (HS+) as a robustness check
- Influence diagnostics using Cook’s distance

Key coefficient signs and significance levels remain stable under robust inference, and no individual county exerts disproportionate influence on the estimated coefficients.


## Interpretation Scope and Limitations

- The analysis is **associational, not causal**.
- Results reflect cross-sectional variation in 2022 only.
- County-level aggregation masks within-county heterogeneity.
- Spatial dependence and regional spillovers are not explicitly modeled.
- High multicollinearity among socioeconomic variables requires cautious interpretation of individual coefficients.

These limitations are acknowledged by design and reflect a deliberate tradeoff in favor of transparency, interpretability, and clarity.


## Project Structure

```text
├── data/
│   └── processed/
│       ├── zillow_zhvi_2022.csv
│       └── acs_features_2022_county.csv
├── notebooks/
│   ├── 01_zillow_preprocessing.ipynb
│   ├── 02_census_preprocessing.ipynb
│   ├── 03_housing_price_eda.ipynb
│   └── 04_interpretable_modeling.ipynb
└── README.md

```

Raw input datasets are not included in this repository due to data size and licensing
considerations. All preprocessing steps are fully documented in the notebooks.


## Conclusion

This analysis examined how housing prices vary across U.S. counties in 2022 as a function of key socioeconomic characteristics using an interpretability-focused regression framework.

Three main conclusions emerge from the results.

First, **median household income and educational attainment are the strongest associates of county-level housing prices**. Counties with higher incomes and a larger share of college-educated residents consistently exhibit substantially higher housing values, even after controlling for population size and labor market conditions. These variables explain a large share of cross-county variation in housing prices.

Second, **population size and household structure play secondary but meaningful roles**. More populous counties tend to have higher housing prices, reflecting urban scale effects, while average household size is positively associated with housing values once other factors are held constant. These effects are smaller than those of income and education but remain statistically and substantively relevant.

Third, **labor market conditions, as measured by the unemployment rate, are modestly but consistently associated with housing prices once other socioeconomic characteristics are accounted for**. The estimated effect is small in magnitude relative to income and education, suggesting that unemployment primarily captures residual economic stress rather than acting as a dominant driver of regional housing prices in a cross-sectional setting.

Overall, the final model explains approximately **56% of the variation in log-transformed housing prices across U.S. counties**, which is substantial given the heterogeneity of housing markets and the absence of spatial or temporal structure in the model.

Importantly, these findings describe **conditional associations rather than causal relationships**. The results highlight how housing prices co-vary with correlated dimensions of income, education, urbanization, and demographic structure across regions, providing a transparent and interpretable summary of regional housing price differences in 2022.

