# Interpretable Analysis of U.S. County-Level Housing Prices (2022)

## Problem Statement

This project examines how income, education, population, household size, and
unemployment are associated with home values across **3,052 U.S. counties**.
It pairs Zillow home values for 2022 with ACS estimates covering 2018–2022.

The regression describes these associations while holding the other predictors
constant and measures how much variation in log home values the predictors
explain together. The analysis focuses on interpretation; it does not estimate
causal effects or optimize predictive accuracy.


## Data Sources

This project combines county-level housing price data from Zillow with socioeconomic and demographic indicators from the U.S. Census Bureau’s American Community Survey (ACS).

### Zillow Housing Data
- **Source:** Zillow Research  
- **Dataset:** County-level Zillow Home Value Index (ZHVI)  
- **File:** `County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`  
- **Description:** Monthly home value estimates for U.S. counties  
- **Processing:** Available monthly ZHVI values in 2022 are averaged for each county (`zhvi_2022`); missing months are not imputed.

### American Community Survey (ACS)
- **Source:** U.S. Census Bureau (data.census.gov)  
- **Survey:** ACS 2018–2022 5-Year Estimates (2022 release vintage)
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
  - `zhvi_2022`: Available-month mean Zillow Home Value Index for 2022

- **Analysis target:**  
  - `log_zhvi = log(zhvi_2022)`

A logarithmic transformation is applied to housing prices because the raw ZHVI distribution is highly right-skewed. The log transformation reduces the influence of extremely high-priced counties, improves linearity in regression models, and allows coefficients to be interpreted approximately in percentage terms.


## Feature Variables

County-level socioeconomic characteristics derived from the ACS are used as explanatory variables. All features are aligned using standardized 5-digit county FIPS codes.

### Core Feature Candidates
- **`median_income_2022`**  
  Median household income (USD, inflation-adjusted)

- **`ba_plus_share_2022`**  
  Share of the population aged 25 or older with a bachelor’s degree or higher

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
- All features are constructed at the county level and merged using validated one-to-one inner joins to select overlapping counties.


## Analysis Scope

- **Geographic unit:** U.S. counties  
- **Measurement periods:** Zillow 2022; ACS 2018–2022
- **Housing coverage:** Counties with available Zillow ZHVI data for 2022  
- **Socioeconomic coverage:** Counties with complete ACS 2018–2022 5-year period estimates
- **Exclusions:**  
  - Puerto Rico counties (state FIPS code 72) are excluded to ensure consistency between Zillow and ACS coverage.

The final analysis sample has **3,052 counties**, selected by the intersection of
3,061 processed Zillow counties and 3,143 processed ACS counties. Nine Zillow
counties and 91 ACS counties fall outside this intersection. Inner joins do not
establish complete national coverage.

Zillow is summarized over available months in **2022**; ACS covariates are
**2018–2022 period estimates**, not 2022 single-year measurements. The periods
are not identical. In the final sample, **3,012 counties have twelve observed
Zillow months and 40 have eleven**. The model uses the original available-month
averages and county sample. A complete-year-only sensitivity analysis has
not been performed.
The Census Bureau documents the period in its [2022 ACS release](https://www.census.gov/programs-surveys/acs/news/data-releases/2022/release.html).


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

```text
log(ZHVI_2022) =
β0
+ β1 · median_income_2022
+ β2 · ba_plus_share_2022
+ β3 · log(1 + population_2022)
+ β4 · avg_household_size_2022
+ β5 · unemployment_rate_2022
+ ε
```

This is the final model used for interpretation.

High-school-or-higher attainment (HS+) is evaluated in an alternative specification.
The VIFs reported below apply to the five-predictor final model; they do not
diagnose collinearity in the HS+ alternative.


## Interpretation Strategy

Because the dependent variable is log-transformed, coefficients are interpreted
using a log–linear rule.

Percent change in ZHVI
≈ 100 × (exp(β_k × ΔX_k) − 1)

Fitted contrasts are evaluated at meaningful unit changes, such as +$10,000 income
and +10 percentage points in educational attainment. For population doubling,
the exact change in `log1p(P)` is `log1p(2P) - log1p(P)`, evaluated at the sample
median population in the notebook. The fitted relative change is about **+2.128%**.
These percentages describe changes in exponentiated fitted log values; they do
not estimate causal effects or changes in mean dollar home values. The
[correction record](diagnostic_correction.md) explains the earlier population
contrast and its replacement.


## Model Diagnostics and Robustness

Several diagnostics and robustness checks are performed, including alternative education specifications:

- Overall model fit (R² ≈ 0.56)
- Residuals versus fitted values
- Assessment of heteroskedasticity
- Multicollinearity diagnostics using Variance Inflation Factors (VIF)
- Robust standard errors (HC3)
- Alternative model specification including high-school-or-higher attainment (HS+) as a robustness check
- Influence diagnostics using Cook’s distance

All five predictor coefficients are positive and statistically significant at
the 5% level using HC3 standard errors. Predictor VIFs range from **1.26 to 2.67**,
below the common screening thresholds of 5 and 10. Cook’s distance reaches
0.03449, and 176 counties exceed the 4/n screening threshold.

VIF auxiliary regressions retain the fitted model’s intercept; only the
intercept’s row is omitted from the reported table. The VIF correction leaves
the regression estimates, standard errors, p-values, predictions, residuals,
and R² unchanged. The [correction record](diagnostic_correction.md) contains
the previous values, the calculation error, and the before-and-after comparisons.


## Interpretation Scope and Limitations

- The analysis is **associational, not causal**.
- The outcome summarizes 2022, but ACS covariates summarize 2018–2022; temporal alignment is imperfect.
- County-level aggregation masks within-county heterogeneity.
- Spatial dependence and regional spillovers are not explicitly modeled.
- Predictor VIFs of 1.26–2.67 do not indicate severe multicollinearity under common 5/10 heuristics; this does not resolve omitted variables, functional form, spatial dependence or measurement uncertainty.
- HC3 addresses heteroskedasticity sensitivity, not spatial dependence or ACS measurement error.
- Influence screening flags observations; deletion/refit sensitivity remains untested.



## Reproducing the corrected diagnostics

From the repository root, using the environment in `requirements.txt`:

```sh
python 01_housing_price_analysis/diagnostics.py
python -m unittest discover -s 01_housing_price_analysis/tests -v
python 01_housing_price_analysis/verify_notebooks.py --write
```

Run notebooks with their notebook directory as the working directory. Shared helpers
validate county identifiers, reject incomplete education counts and retain the original
available-month means. Existing processed files are verified without rewriting them.
The unit/regression tests execute the actual modeling cells and compare the sample,
coefficients, OLS/HC3 inference, fitted values and residuals with the original baseline.
The full runner executes all four notebooks in fresh kernels, checks coverage and
reported document values, verifies raw/processed hashes, and refreshes outputs only
after every notebook passes. It requires the original raw inputs, which are not
published; without them it fails explicitly. Public processed CSVs are sufficient
for the diagnostic script and unit/regression tests.

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
├── preprocessing.py
├── diagnostics.py
├── verify_notebooks.py
├── tests/
├── diagnostic_correction.md
├── executive_summary.md
└── README.md

```

Raw input datasets are not included in this repository due to data size and licensing
considerations. All preprocessing steps are fully documented in the notebooks.


## Conclusion

Income and college attainment are positively associated with county home values
after accounting for the other predictors. Population and average household size
also have positive, statistically significant associations. Their magnitudes
depend on the unit changes used for comparison; the model’s overall fit does
not assign a separate share of explained variation to each predictor.

Unemployment has a smaller association at the reported unit change and varies
with the specification. Its final-model coefficient is 0.8616 (OLS p ≈ 0.0029,
HC3 p ≈ 0.0062), corresponding to about +0.87% ZHVI per +1 percentage point
unemployment. Adding HS+ gives a coefficient of 0.6902 (OLS p ≈ 0.018).
Both coefficients are positive. These results describe a conditional association
and do not identify a suppression effect or an economic mechanism.

The final model explains approximately 56% of the observed variation in log
home values in this sample. It summarizes how home values vary with the five
county characteristics within the measurement periods and limitations described
above. It does not establish causal effects or out-of-sample predictive accuracy.
