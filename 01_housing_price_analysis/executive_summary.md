# Executive Summary (For General Audience)

### Which characteristics are associated with county housing prices in 2022?

This analysis combines Zillow home values and U.S. Census Bureau ACS data for
3,052 counties. Zillow values summarize available months in 2022, while ACS
characteristics are 2018–2022 five-year period estimates. Of these counties,
3,012 have twelve Zillow months and 40 have eleven. Available months are
averaged without filling in missing months.

Income, college attainment, population, household size, and unemployment each
have positive associations with home values after accounting for the other
predictors. All five are statistically significant at the 5% level using HC3
robust standard errors, which adjust for heteroskedasticity (differences in
error variance across counties). These associations do not establish causes.

The model explains about **56.3% of the observed variation in log home values**
in this sample. This is an in-sample descriptive result, not a measure of
out-of-sample predictive accuracy or a ranking of individual drivers.

The corrected variance inflation factors (VIFs), which measure collinearity
among predictors, range from **1.26 to 2.67**. They do not indicate severe
multicollinearity under common screening rules. The correction leaves the
regression coefficients, statistical significance, and model fit unchanged;
the calculation and previous values are documented in the correction record.

Unemployment has a modest positive conditional association in this specification
(about +0.87% home value per +1 percentage point unemployment). The analysis
does not establish why this association occurs or identify residual economic
stress as its mechanism.

Limitations remain: a single cross-section with different measurement periods,
partial-year housing coverage for 40 counties, county-level aggregation, unmodeled
spatial dependence and ACS measurement uncertainty. Influence screening also
flags counties for further examination. The model has not been refitted after
removing flagged counties to check sensitivity. Low VIF does not remove these limitations.

See the [diagnostic correction record](diagnostic_correction.md) for before/after
values, unchanged model estimates, and verification details.
