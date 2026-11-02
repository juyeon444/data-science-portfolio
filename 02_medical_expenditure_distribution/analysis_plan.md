# Analysis definitions and interpretation

The analysis compares expenditure concentration across demographic and health
characteristics and separates spending by service type and payer. These are
unadjusted descriptive comparisons. They do not isolate causal effects, prices,
service intensity, or unmet medical need. The source is AHRQ's MEPS 2023 Full Year
Consolidated file, HC-251. All amounts are nominal 2023 U.S. dollars.

## Population and data checks

National person-level estimates use `PERWT23F > 0`. Records with zero person
weights are counted and excluded from these estimates, not treated as zero
spenders. Nonfinite or negative weights stop execution. Person identifiers must
be unique. Expenditure fields must be finite and nonnegative; reserved negative
codes are not silently converted to zero or removed.

The target is the U.S. civilian noninstitutionalized population represented by
the annual MEPS weight, including people in scope for only part of the year.
Their spending covers their in-scope time. We do not annualize those observations
or exclude deaths. Thus an annual total is not necessarily twelve months of
individual exposure. Data quality checks compare the raw/positive-weight row
counts and sum of person weights with the HC-251 documentation.

Unknown or inapplicable demographic and health codes remain in a labeled
category in subgroup comparisons. `RTHLTH31` is perceived health at Round 3/1,
not a clinical diagnosis or a consistently timed causal baseline. Health status
can change during the expenditure year. `AGE23X` is the year-end age field;
negative reserved codes are reported as unknown. `POVCAT23` uses the supplied
five-category family-income-to-poverty classification. Admission groups use
`IPDIS23`; they describe utilization and are not causal treatment groups.

## Distribution and concentration

- The weighted mean is `sum(w*y)/sum(w)`. It describes spending per person and
  helps relate population and aggregate spending. It need not describe the
  spending of a typical individual.
- The weighted median and other quantiles are the smallest expenditure values
  whose cumulative population weight reaches the requested fraction. We do not
  interpolate dollar values. Zero spenders stay in these calculations.
- Top 1%, 5%, 10%, and 50% groups are defined by weighted population, ranked by
  total spending. The bottom 50% is the complement of the top 50% allocation.
- Boundary ties are allocated proportionally: if expenditure is equal at the
  threshold, every tied person receives the same inclusion fraction, so selected
  weight equals the target population fraction exactly. This is an accounting
  allocation, not a literal classification of people or a risk score.
- This boundary convention differs from AHRQ Statistical Brief 560, which uses
  whole-person boundary rules. Comparisons with that report must account for
  the different boundary convention and data year.
- The Lorenz curve and Gini coefficient use population weights. Spending shares
  and the Lorenz curve are undefined if total weighted spending is zero; the
  code stops rather than returning zero concentration.
- Nonweighted summaries are shown only as a diagnostic comparison for the same
  positive-weight records. They are not national estimates.

A long right tail or a large mean–median gap is not, by itself, evidence of a
particular mathematical heavy-tail distribution. Tail-law fitting, moment
existence, and tail-index estimation are outside this analysis. `log1p` plots retain zero expenditures;
log-scale appearance is not used to infer a lognormal distribution. High values
are retained unless a separate documented data error is established.

## Exploring what makes up the concentration

The EDA compares population and spending shares, weighted means and medians,
and representation in the top 5% allocation by age, poverty category, reported
health, and inpatient utilization. Each grouping is a separate descriptive view;
age, health, income, and utilization are correlated and their shares must not
be added as independent explanations.

For overall spending and the top 5% allocation, two separate decompositions are
shown: health service types and sources of payment. The service decomposition
uses mutually exclusive totals for office-based, outpatient, emergency,
inpatient, prescription, dental, agency and independent home health, vision,
and other supplies/equipment. Facility and separately billed physician subtotals
are not added again. The payer decomposition excludes collapsed private/TRICARE
and “other” variables when their constituent fields are already included.
Service and payer decompositions are two descriptions of the same dollars,
not additive components of a larger total.

MEPS component amounts are independently rounded. We report maximum person-level
and weighted aggregate differences from `TOTEXP23`, and allow at most $10 of
absolute person-level difference for the ten components in either partition.
Larger differences stop execution for investigation. Components are not rescaled
or forced to match. Small rounding differences can leave shares slightly above
or below 100%.

## Uncertainty and limits

The overall weighted mean has a with-replacement Taylor linearization standard
error using strata `VARSTR` and PSUs `VARPSU`. A 95% t interval uses the number
of PSUs minus the number of strata as its degrees of freedom. A singleton
stratum stops the calculation; no silent singleton adjustment is used. This
accounts for sampling design, not all imputation or measurement uncertainty.

Quantiles, concentration shares, Gini, subgroup comparisons, and component
shares are descriptive point estimates without confidence intervals. They
support descriptions of the observed pattern, not formal significance claims
or proof that differences would persist in another sample. They would require
additional survey-aware variance methods for inference. No predictive model,
causal adjustment, trimming, or winsorization is used.

## Sources

- [AHRQ HC-251 documentation](https://meps.ahrq.gov/mepsweb/data_stats/download_data/pufs/h251/h251doc.shtml): sections 2.4–2.5, 3.3, 3.8, 3.9 and Appendix 3.
- [HC-251 codebook](https://meps.ahrq.gov/data_stats/download_data/pufs/h251/h251cb.pdf): variable definitions and frequencies.
- [AHRQ Statistical Brief 560](https://meps.ahrq.gov/data_files/publications/st560/stat560.shtml): reference concentration methods; it analyzes 2018–2022, not this project's 2023 data.
