# VIF and diagnostic correction — 2026-11-01 (America/Phoenix)

## Scope and provenance

Baseline: commit `6ff1e0b5af902ee0c80d1d3d4906c0df1471bfc0`.
The two processed CSVs are inner-joined on county FIPS; the original natural log
ZHVI and log1p population transforms and all five final predictors are retained.
The analysis contains 3,052 unique counties. The correction preserves raw and
processed data, the model specification, and the sample. Full execution checks
the local raw files as well as the processed CSVs.


`tests/original_model_baseline.json` records SHA-256 hashes of the original
processed CSVs and full-precision results obtained by executing the original
notebook model cells before editing. It is a fresh reproduction, not a claim
that historical saved outputs had full precision. Original saved OLS/HC3
summaries agree at displayed precision; historical source/output remain in Git.

## Why the diagnostic changes

In statsmodels 0.14.6, `variance_inflation_factor` fits an auxiliary OLS using the
columns supplied; it does not automatically add an intercept. Dropping `const`
therefore produces regressions through the origin and uncentered R². Those
values are not the centered VIF diagnostic for this intercept-containing model.
The corrected code retains `const` for each auxiliary regression and excludes
only its output row. Equivalently, centered predictor VIFs equal the diagonal
of the inverse predictor correlation matrix; the tests check this independent
calculation and invariance to shifts and changes of units.

| Predictor | Historical uncentered VIF | Corrected centered VIF |
|---|---:|---:|
| median_income_2022 | 40.644744 | 2.673121 |
| ba_plus_share_2022 | 16.981067 | 2.666541 |
| log_population | 70.256602 | 1.542502 |
| avg_household_size_2022 | 58.814741 | 1.257323 |
| unemployment_rate_2022 | 7.361054 | 1.309659 |

The corrected values do not suggest severe multicollinearity under common 5/10
heuristics. These are screening conventions, not a universal acceptance test.
The raw design condition number (~3.28 million) is unit/offset sensitive and is
not sufficient evidence of severe predictor collinearity by itself.

## What does not change

The VIF calculation is downstream of estimation and does not refit or mutate
the final model. Coefficients, OLS/HC3 standard errors and p-values, fitted
values, residuals and R² are unchanged. The regression tests compare to the
pre-edit reproduction and check that the diagnostic does not mutate results.

| Term | Coefficient, before = after | OLS SE | OLS p | HC3 SE | HC3 p |
|---|---:|---:|---:|---:|---:|
| const | 10.26692179 | 0.070474617 | 0 | 0.0791219 | 0 |
| median_income_2022 | 1.162878076e-05 | 5.6442745e-07 | 2.1066985e-88 | 5.8635058e-07 | 2.0015486e-82 |
| ba_plus_share_2022 | 1.681544783 | 0.093687514 | 1.4878241e-68 | 0.11227153 | 5.4785312e-49 |
| log_population | 0.03038466323 | 0.0049399896 | 8.7174345e-10 | 0.0057911961 | 1.6545597e-07 |
| avg_household_size_2022 | 0.2093195604 | 0.027526495 | 3.7915933e-14 | 0.030313894 | 6.0821799e-12 |
| unemployment_rate_2022 | 0.8615786094 | 0.28908618 | 0.0029019427 | 0.31472234 | 0.0062252079 |

R² before = after: 0.562724144445. All five predictor signs are positive;
all HC3 p-values are below 0.05. Displayed zero p-values reflect numerical
underflow, not a probability proven to be exactly zero.

The conclusion changes from “high multicollinearity is a major model limit”
to “this diagnostic does not indicate severe multicollinearity.” It does not
improve fit, reduce uncertainty, establish causality, rank predictor importance,
or validate prediction. Income/education associations remain, with no causal
or economic-mechanism claim added.

## Other diagnostic wording corrected

Cook’s D max = 0.0344910157, below 1; however 176 counties exceed 4/n =
0.0013106160. The old claim that no county has disproportionate influence
was stronger than this screening evidence. No deletion/refit test was conducted.
The residual plot alone does not establish absence of functional-form issues or
quantify heteroskedasticity, so that wording was narrowed.

The final unemployment coefficient is +0.861579 (HC3 p ≈ 0.006225), about
+0.87% home value per +1 percentage point. In the existing HS+ alternative,
it remains positive (~0.6902, OLS p ≈ 0.018). These checks do not demonstrate
a sign reversal or residual-economic-stress mechanism. The notebook and summaries
now distinguish this evidence from interpretation. Spatial dependence, omitted
variables, county aggregation and ACS measurement uncertainty remain limitations;
HC3 does not resolve all of them.

## Initial verification — VIF correction

From the repository root:

```sh
python 01_housing_price_analysis/diagnostics.py
python -m unittest discover -s 01_housing_price_analysis/tests -v
```

Environment: Python 3.12.14, NumPy 2.2.6, pandas
2.3.3, statsmodels 0.14.6; existing local virtual environment,
no dependency upgrade. Test execution and notebook execution are recorded below.
The recorded checks are regression tests and notebook execution; an independent
statistical review is not recorded.

Initial validation: 7/7 tests passed and notebook 04 completed all 37 cells
without error outputs. Two earlier execution attempts failed during kernel setup
because of an invalid configuration argument and unavailable local-port access;
the subsequent run completed. Neither failure was in a model calculation.
The later HS+ description change affected Markdown only. No deletion/refit
sensitivity analysis was performed.

## Data validation and diagnostic updates — 2026-11-01

1. **Population contrast:** The former +3.085099% was for a +1 change in
   log population, despite the prose describing doubling. Notebook 04 now uses
   the exact contrast `log1p(2P) - log1p(P)` at the sample median P = 26,791.
   The fitted relative change is **+2.128381354%**. This changes the reported
   contrast, not the population coefficient (0.03038466323) or model.
2. **Available-month means:** Notebook 01 retains the original averaging policy,
   explicitly checks the twelve month-end columns, and reports observed counts.
   The processed Zillow table contains 3,021 complete-year and 40 eleven-month
   counties. The final sample contains 3,012 complete-year and the same 40
   eleven-month counties. Twelve raw rows have no observed 2022 values and are
   excluded as before. No month was imputed and no county was newly removed.
3. **Measurement periods:** README, Executive Summary and notebook descriptions
   distinguish Zillow 2022 from ACS 2018–2022 five-year period estimates.
   Imperfect period alignment is now explicit. The ACS period is documented by
   the [Census Bureau](https://www.census.gov/programs-surveys/acs/news/data-releases/2022/release.html).
4. **Education missingness:** Shared validation rejects missing/nonfinite/negative
   education components before calculating shares; missing counts cannot become
   zero through skip-NA sums. Synthetic complete, partially missing and wholly
   missing inputs are tested, including execution of the actual Census notebook
   function. The existing raw education inputs have no missing components, so
   their processed values remain unchanged.
5. **County keys and joins:** ACS extraction requires county summary level
   `0500000US` rather than accepting any five-digit suffix. Shared loading rejects
   null, malformed, duplicate and excluded keys, preserves leading zeros, and
   enforces one-to-one joins in both EDA and modeling. The historical final sample
   is preserved. These checks validate structure, not every geographic boundary.
6. **Real notebook regression coverage:** Tests now execute the actual modeling
   cells, checking predictor names, sample size and keys, coefficients, OLS/HC3
   inference, fit, predictions and residuals against the pre-edit baseline.
   `verify_notebooks.py` additionally executes all four notebooks in fresh kernels
   and checks their results. It fails explicitly if the unpublished raw inputs
   are unavailable. Existing processed outputs are verified without rewriting
   their bytes. Unit/regression tests require only public processed data.
7. **EDA display and interpretation:** Six significant digits replace fixed
   three-decimal formatting, so income coefficients no longer appear as zero.
   The EDA no longer attributes an untested economic mechanism to unemployment;
   it distinguishes bivariate correlation from conditional or causal importance,
   and points to the corrected final-model VIFs.

### Regression and notebook validation

- **17 unit/regression tests passed**, including the actual Census and modeling
  notebook functions/cells and boundary cases.
- **All four notebooks executed successfully**: 21 + 30 + 45 + 37 = 133 original
  cells, plus a temporary validation cell per notebook. No error outputs remain.
- Original sample **n = 3,052**, R² **0.562724144445**, coefficients, OLS/HC3
  inference, predictions/residuals and corrected VIFs remain consistent with the
  baseline. Predictions/residuals are compared with those implied by the original
  reproduced coefficient vector on the same design, not an archived historical
  per-county predictions file.
- Raw and processed data hashes were identical before and after full execution;
  **37 data files** were checked. The seven public processed CSV hashes also
  match `original_model_baseline.json`.
- Execution timestamp, notebook counts and data hashes are recorded in
  `tests/notebook_validation.json`. The runner checks key numeric/period statements
  in README and Executive Summary; the seven changes were also reviewed for prose
  consistency. These checks do not claim automated semantic verification of all prose.
- No complete-year-only or deletion/refit sensitivity result, predictive-performance
  gain, causal conclusion or new model was introduced.

Reproduce from the repository root with the existing Python environment:

```sh
python -m unittest discover -s 01_housing_price_analysis/tests -v
python 01_housing_price_analysis/verify_notebooks.py --write
```

## Documentation updates

The documentation uses consistent definitions for the measured variables,
processing steps, and fitted contrasts. Statistical results are unchanged.

1. Notebook definitions and the EDA plot title now consistently describe the
   mean of available monthly ZHVI values in 2022.
2. The education section states that missing or invalid counts raise an error
   before shares are calculated, rather than saying such rows are removed.
3. The Zillow output section distinguishes checking existing files from creating
   missing outputs. The EDA distinguishes selecting overlapping counties from
   checking for missing values.
4. The README opens with the 3,052-county sample, predictors, and measurement
   periods, then explains the interpretation-focused purpose.
5. General claims about transparency, reliability, and deliberate tradeoffs were
   replaced with descriptions of the output, checks, and interpretation limits.
6. The Executive Summary separates data coverage from regression findings and
   explains HC3 when it first appears.
7. Current findings appear in the README and summary; calculation history is
   linked to this record. Initial and follow-up verification are labeled
   separately. Historical values and unperformed sensitivity checks remain
   documented, and no new conclusions were added.
8. The interpretation section describes percentages as changes in exponentiated
   fitted log values, distinguishing them from causal effects and changes in
   mean dollar home values.

Verification after these edits: all 17 unit/regression tests passed, and all four
notebooks executed successfully in fresh kernels (133 original cells, plus the
runner’s temporary validation cells). Raw and processed files were unchanged
byte for byte. The model specification, coefficient estimates, OLS/HC3 inference,
fitted values, residuals, R², and corrected VIFs still match the original model
baseline. All Python source files are unchanged; the only executable notebook
source change is the EDA plot title. README and Executive Summary figures were
also compared with recalculated model fit, unemployment contrasts and p-values,
the exact population-doubling contrast, the HS+ alternative, and Cook’s distance.
The refreshed execution record is `tests/notebook_validation.json`.

The documentation update preserved data and model calculations. No additional
sensitivity analysis was performed.
