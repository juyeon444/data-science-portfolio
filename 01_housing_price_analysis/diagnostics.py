"""Reproduce the unchanged final model and intercept-aware VIF diagnostics."""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from preprocessing import read_county_csv, merge_counties

FEATURES = ['median_income_2022', 'ba_plus_share_2022', 'log_population',
            'avg_household_size_2022', 'unemployment_rate_2022']


def load_sample(processed=None):
    processed = Path(processed or Path(__file__).parent / 'data' / 'processed')
    zillow = read_county_csv(processed / 'zillow_zhvi_2022.csv')
    acs = read_county_csv(processed / 'acs_features_2022_county.csv')
    df = merge_counties(zillow, acs)
    df['log_zhvi'] = np.log(df['zhvi_2022'])
    df['log_population'] = np.log1p(df['population_2022'])
    if not np.isfinite(df[['log_zhvi'] + FEATURES].to_numpy()).all():
        raise ValueError('Model sample contains missing or nonfinite values')
    return df


def population_doubling_effect(beta, population):
    """Exact fitted log1p-population contrast for P -> 2P, in percent."""
    population = np.asarray(population, dtype=float)
    if not np.isfinite(population).all() or (population <= 0).any():
        raise ValueError('Population must be finite and positive')
    return 100 * np.expm1(beta * (np.log1p(2 * population) - np.log1p(population)))


def centered_vif(design):
    """Keep the fitted model intercept in every auxiliary regression.

    Exclude only its reported row. No recentering or refitting of the final
    housing model is performed. Requires a named, unit intercept.
    """
    if 'const' not in design or not np.all(design['const'].to_numpy() == 1):
        raise ValueError('A unit const column is required')
    if not np.isfinite(design.to_numpy(dtype=float)).all():
        raise ValueError('Design must be finite')
    features = design.drop(columns='const')
    if (features.nunique() < 2).any():
        raise ValueError('Predictors must vary')
    return pd.DataFrame({'Variable': features.columns,
                         'VIF': [variance_inflation_factor(design.to_numpy(),
                                 design.columns.get_loc(name)) for name in features]})


def fit_final(df):
    return sm.OLS(df['log_zhvi'], sm.add_constant(df[FEATURES]), missing='raise').fit()


if __name__ == '__main__':
    df = load_sample()
    model = fit_final(df)
    X = pd.DataFrame(model.model.exog, columns=model.model.exog_names)
    table = centered_vif(X)
    # Historical computation, reproduced explicitly; not the corrected diagnostic.
    no_const = X.drop(columns='const')
    table['historical_uncentered_VIF'] = [variance_inflation_factor(no_const.to_numpy(), i)
                                         for i in range(no_const.shape[1])]
    print(table.to_string(index=False))
    print(model.summary())
    robust = model.get_robustcov_results(cov_type='HC3')
    print(pd.DataFrame({'coef': model.params, 'OLS_SE': model.bse, 'OLS_p': model.pvalues,
                        'HC3_SE': robust.bse, 'HC3_p': robust.pvalues}).to_string())
    cooks = model.get_influence().cooks_distance[0]
    print({'n': len(df), 'R2': model.rsquared, 'max_Cook_D': cooks.max(),
           'Cook_D_above_4_n': int((cooks > 4 / len(df)).sum())})
