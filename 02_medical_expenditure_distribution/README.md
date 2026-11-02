# Why Do Medical Expenditures Concentrate Among a Small Share of Individuals?

This project uses AHRQ's MEPS 2023 Full Year Consolidated File (HC-251) to examine
medical expenditure concentration among the U.S. civilian noninstitutionalized
population. It compares the distribution of spending, characteristics associated
with high expenditures, and the services and payers that make up those expenses.

The analysis describes associations with high expenditures and their spending
composition. It does not estimate causal effects or optimize predictions. The mean remains useful for
spending per person and total costs; the median, quantiles, zero-spending share,
and concentration shares describe other aspects of the distribution.

Read the [EDA summary](eda_summary.md) for the results.

## Analysis

- [Data understanding](notebooks/01_data_overview.ipynb) defines `TOTEXP23`, coverage, and interpretation.
- [Distribution and composition EDA](notebooks/02_distribution_and_composition.ipynb) contains executed weighted tables and plots.
- [Analysis definitions](analysis_plan.md) specify the population, weights, quantiles, top-group boundaries, uncertainty, component reconciliation, and official sources.
- [Aggregate outputs](outputs/summary.json) and CSV tables preserve the calculated values. The notebook also saves four figures under `outputs/`.

Population estimates use `PERWT23F > 0`, retaining zero spenders. Top groups are
weighted population fractions with proportional allocation within expenditure
ties. The overall mean has a Taylor-design 95% confidence interval using `VARSTR`
and `VARPSU`; other results are descriptive point estimates. High-cost records
are retained. Unknown demographic/health codes are labeled rather than dropped.
Original source files are preserved, and the local person-level extraction
cache is excluded from Git alongside raw data.

## Reproduce

Use the repository's existing Python environment and dependencies. The loader
streams the original workbook with Python's standard XML/ZIP libraries, so an
additional Excel-reading package is not required. The first run takes longer
because it extracts the selected columns; later runs use a hash-validated local
cache. Raw inputs are not included in Git.

```sh
python 02_medical_expenditure_distribution/analysis.py
python -m unittest discover -s 02_medical_expenditure_distribution/tests -v
python 02_medical_expenditure_distribution/verify_notebooks.py
```

The raw input is `data/raw/h251.xlsx`, downloaded from
[AHRQ's HC-251 release](https://meps.ahrq.gov/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-251).
The notebook runner requires it, refreshes both notebooks, checks source hashes
and aggregate reconciliation, and records verification in `outputs/validation.json`.
