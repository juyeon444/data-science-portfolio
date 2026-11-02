"""Generate the narrative from validated aggregate results; no person-level output."""

def summary_markdown(s,tables):
    def group(name,key):
        return tables[name].set_index('group').loc[key]
    age=group('age','65+')
    fair=group('health','Fair');poor=group('health','Poor')
    inpatient=group('inpatient','Any inpatient stay')
    services=tables['services'].set_index('component')
    payers=tables['payers'].set_index('component')
    return f'''# Why Do Medical Expenditures Concentrate Among a Small Share of Individuals?

AHRQ MEPS HC-251 data describe spending in 2023, the characteristics of people
in the high-expenditure population, and the services and payers that make up
their expenses. These are descriptive comparisons of recorded payments.

## Distribution and concentration

Of {s['raw_n']:,} raw records, {s['positive_weight_n']:,} have a positive annual
person weight; {s['zero_weight_n']:,} zero-weight records are excluded from
person-level population estimates. The weights represent approximately
{s['represented_population']:,.0f} people in the U.S. civilian noninstitutionalized
population. Some people were in scope for only part of the year. Expenditures
are nominal 2023 U.S. dollars; partial-year spending is not annualized.

| Weighted measure | Estimate |
|---|---:|
| Mean annual expenditure | ${s['mean']:,.2f} |
| Median annual expenditure | ${s['median']:,.0f} |
| 90th percentile | ${s['p90']:,.0f} |
| 95th percentile | ${s['p95']:,.0f} |
| 99th percentile | ${s['p99']:,.0f} |
| Zero-spending population share | {s['zero_share']:.2%} |
| Top 1% share of total spending | {s['top1_share']:.2%} |
| Top 5% share of total spending | {s['top5_share']:.2%} |
| Top 10% share of total spending | {s['top10_share']:.2%} |
| Bottom 50% share of total spending | {s['bottom50_share']:.2%} |
| Gini coefficient | {s['gini']:.4f} |

The overall mean's Taylor standard error is ${s['se']:,.2f}; its 95% t interval
is ${s['ci_low']:,.2f}–${s['ci_high']:,.2f} using {s['design_df']} design degrees
of freedom. The other estimates have no confidence intervals in this EDA.

The mean exceeds the median, while a small population share accounts for much
of the spending. Both summaries are useful: the mean relates population size
to total costs, and the median describes a different point in the distribution.
The weighted expenditure total is approximately ${s['total_spending']/1e12:.3f}
trillion for this MEPS target population, not all U.S. national health expenditure.
This pattern does not establish a particular mathematical heavy-tail law.

For comparison, ignoring weights on the same positive-weight records gives a
mean of ${s['unweighted_mean']:,.2f}, a median of ${s['unweighted_median']:,.0f},
and a top-5% spending share of {s['unweighted_top5_share']:.2%}. These are sample
diagnostics, not national estimates.

## Characteristics associated with the top 5%

People aged 65 or older account for {age.population_share:.2%} of the represented
population and {age.top5_population_share:.2%} of the top-5% population allocation.
People reported in fair or poor health in Round 3/1 account for
{fair.population_share+poor.population_share:.2%} of the population and
{fair.top5_population_share+poor.top5_population_share:.2%} of the top allocation.

People with any inpatient stay account for {inpatient.population_share:.2%} of
the population and {inpatient.top5_population_share:.2%} of the top allocation.
Hospital use and annual spending are measured in the same year, and admission
expenses are part of the total. These unadjusted comparisons do not isolate the effect of an admission on
annual costs.

Age, reported health, income, and utilization overlap; they are not independent
contributions that can be added together. Unknown and inapplicable values remain
in labeled categories. For example, negative `AGE23X` codes are not silently
assigned to an age group or removed. See the notebook and aggregate tables for
all categories, including poverty groups. No subgroup significance test is made.

## Services and payment sources

Inpatient care accounts for {services.loc['Inpatient','top5_share']:.2%} of top-5%
spending, compared with {services.loc['Inpatient','overall_share']:.2%} overall.
Prescriptions account for {services.loc['Prescriptions','top5_share']:.2%}, and
office-based care for {services.loc['Office-based','top5_share']:.2%} of top-5%
spending. This breakdown shows which services make up spending, but cannot
separate service prices, frequency, intensity, or medical need.

Private insurance pays {payers.loc['Private','top5_share']:.2%} of top-5% spending,
Medicare {payers.loc['Medicare','top5_share']:.2%}, and out-of-pocket payments
{payers.loc['Out of pocket','top5_share']:.2%}. Payment source is not the same as
insurance enrollment or household financial burden. Service types and payers
are separate decompositions of the same spending and must not be added together.

The service components reconcile exactly with individual totals in this file.
Payer components differ from individual totals by at most
${s['component_max_abs_difference']['payers']:,.0f}, consistent with separate
rounding. Their weighted aggregate difference is
${s['component_weighted_difference']['payers']:,.2f}; no components were rescaled
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
'''
