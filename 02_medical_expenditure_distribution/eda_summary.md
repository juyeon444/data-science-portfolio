# Why Do Medical Expenditures Concentrate Among a Small Share of Individuals?

AHRQ MEPS HC-251 data describe spending in 2023, the characteristics of people
in the high-expenditure population, and the services and payers that make up
their expenses. These are descriptive comparisons of recorded payments.

## Distribution and concentration

Of 18,919 raw records, 18,463 have a positive annual
person weight; 456 zero-weight records are excluded from
person-level population estimates. The weights represent approximately
334,530,273 people in the U.S. civilian noninstitutionalized
population. Some people were in scope for only part of the year. Expenditures
are nominal 2023 U.S. dollars; partial-year spending is not annualized.

| Weighted measure | Estimate |
|---|---:|
| Mean annual expenditure | $7,487.26 |
| Median annual expenditure | $1,583 |
| 90th percentile | $18,330 |
| 95th percentile | $34,150 |
| 99th percentile | $93,443 |
| Zero-spending population share | 14.45% |
| Top 1% share of total spending | 20.09% |
| Top 5% share of total spending | 48.67% |
| Top 10% share of total spending | 65.23% |
| Bottom 50% share of total spending | 2.89% |
| Gini coefficient | 0.7805 |

The overall mean's Taylor standard error is $173.37; its 95% t interval
is $7,144.82–$7,829.70 using 157 design degrees
of freedom. The other estimates have no confidence intervals in this EDA.

The mean exceeds the median, while a small population share accounts for much
of the spending. Both summaries are useful: the mean relates population size
to total costs, and the median describes a different point in the distribution.
The weighted expenditure total is approximately $2.505
trillion for this MEPS target population, not all U.S. national health expenditure.
This pattern does not establish a particular mathematical heavy-tail law.

For comparison, ignoring weights on the same positive-weight records gives a
mean of $8,535.66, a median of $1,879,
and a top-5% spending share of 46.87%. These are sample
diagnostics, not national estimates.

## Characteristics associated with the top 5%

People aged 65 or older account for 17.91% of the represented
population and 39.89% of the top-5% population allocation.
People reported in fair or poor health in Round 3/1 account for
11.42% of the population and
36.21% of the top allocation.

People with any inpatient stay account for 6.43% of
the population and 55.59% of the top allocation.
Hospital use and annual spending are measured in the same year, and admission
expenses are part of the total. These unadjusted comparisons do not isolate the effect of an admission on
annual costs.

Age, reported health, income, and utilization overlap; they are not independent
contributions that can be added together. Unknown and inapplicable values remain
in labeled categories. For example, negative `AGE23X` codes are not silently
assigned to an age group or removed. See the notebook and aggregate tables for
all categories, including poverty groups. No subgroup significance test is made.

## Services and payment sources

Inpatient care accounts for 35.94% of top-5%
spending, compared with 22.21% overall.
Prescriptions account for 25.55%, and
office-based care for 15.74% of top-5%
spending. This breakdown shows which services make up spending, but cannot
separate service prices, frequency, intensity, or medical need.

Private insurance pays 43.47% of top-5% spending,
Medicare 33.98%, and out-of-pocket payments
7.01%. Payment source is not the same as
insurance enrollment or household financial burden. Service types and payers
are separate decompositions of the same spending and must not be added together.

The service components reconcile exactly with individual totals in this file.
Payer components differ from individual totals by at most
$4, consistent with separate
rounding. Their weighted aggregate difference is
$5,793,184.72; no components were rescaled
to force agreement. Reconciliation checks cover component totals, not every potential source of
measurement error.

## Interpretation and limitations

Concentration coincides with differences in age, reported health, and inpatient
utilization, and with a larger inpatient share of high-expenditure spending.
These characteristics are compared separately, without adjustment for one
another. The results describe associations and spending composition rather than
causal explanations.

Only the overall mean has design-based sampling uncertainty here. Quantiles,
concentration, Gini, subgroup comparisons, and component shares are point
estimates. Partial-year exposure, excluded institutionalized populations,
health-status timing, and reported/imputed expenditures limit interpretation.
There is no predictive model, causal adjustment, trimming, or winsorization.

Top groups use weighted population and fractional allocation within boundary
ties. AHRQ reports that allocate whole persons at boundaries use a different rule,
so comparisons require accounting for this difference and the data year. See the
[analysis definitions and sources](analysis_plan.md),
[EDA notebook](notebooks/02_distribution_and_composition.ipynb), and
[aggregate results](outputs/summary.json) for methods and values.
