import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT))
from analysis import (weighted_quantile,top_fraction,concentration,lorenz,survey_mean,
                      validate_sample,grouped,SERVICES,PAYERS,check_arrays)


class WeightedAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.y=np.array([0.,10.,10.,100.]);self.w=np.array([1.,2.,3.,4.])

    def test_weighted_quantile_left_inverse(self):
        self.assertEqual(weighted_quantile(self.y,self.w,.5),10)
        self.assertEqual(weighted_quantile(self.y,self.w,.99),100)
        self.assertEqual(weighted_quantile(self.y,self.w,0),0)
        self.assertEqual(weighted_quantile(self.y,self.w,1),100)

    def test_ties_split_equally_and_exact_target_population(self):
        a=top_fraction(self.y,self.w,.5)
        np.testing.assert_allclose(a,[0,.2,.2,1])
        self.assertAlmostEqual(np.dot(a,self.w),5)
        self.assertAlmostEqual(concentration(self.y,self.w,.5),410/450)

    def test_tie_permutation_and_weight_scale_invariance(self):
        idx=[3,2,0,1]
        np.testing.assert_allclose(top_fraction(self.y[idx],self.w[idx],.5),top_fraction(self.y,self.w,.5)[idx])
        self.assertAlmostEqual(concentration(self.y,self.w,.05),concentration(self.y,self.w*3,.05))
        self.assertEqual(weighted_quantile(self.y,self.w,.7),weighted_quantile(self.y,self.w*3,.7))

    def test_full_empty_membership_and_identical_costs(self):
        np.testing.assert_array_equal(top_fraction(self.y,self.w,0),np.zeros(4))
        np.testing.assert_array_equal(top_fraction(self.y,self.w,1),np.ones(4))
        self.assertAlmostEqual(concentration(np.ones(4),self.w,.05),.05)

    def test_zero_and_invalid_values_not_silently_removed(self):
        for y,w in [([-1,1],[1,1]),([np.nan,1],[1,1]),([0,1],[0,1]),([0,1],[1,-1]),([1],[1,1])]:
            with self.assertRaises(ValueError):check_arrays(y,w)
        with self.assertRaises(ValueError):concentration([0,0],[1,1],.05)
        with self.assertRaises(ValueError):lorenz([0,0],[1,1])
        with self.assertRaises(ValueError):top_fraction([1],[1],1.1)
        with self.assertRaises(ValueError):weighted_quantile([1],[1],-.1)

    def test_lorenz_endpoints_and_concentration_complement(self):
        x,l=lorenz(self.y,self.w)
        self.assertEqual((x[0],l[0],x[-1],l[-1]),(0,0,1,1))
        self.assertTrue((np.diff(x)>0).all());self.assertTrue((np.diff(l)>=0).all())
        self.assertAlmostEqual(float(np.interp(.5,x,l)),1-concentration(self.y,self.w,.5))

    def test_taylor_mean_se_hand_calculation(self):
        df=pd.DataFrame({'TOTEXP23':[0.,2.,4.,6.],'PERWT23F':[1.]*4,
                         'VARSTR':[1]*4,'VARPSU':[1,1,2,2]})
        got=survey_mean(df)
        self.assertEqual(got['mean'],3);self.assertEqual(got['se'],2)
        self.assertEqual(got['design_df'],1)
        scaled=survey_mean(df.assign(PERWT23F=df.PERWT23F*5))
        self.assertEqual(scaled['mean'],3);self.assertEqual(scaled['se'],2)
        with self.assertRaises(ValueError):survey_mean(df.assign(VARPSU=1))

    def make_sample(self):
        df=pd.DataFrame({'DUPERSID':['a','b','c','d'],'TOTEXP23':self.y,'PERWT23F':self.w,
                         'VARSTR':[1]*4,'VARPSU':[1,1,2,2]})
        for col in list(SERVICES.values())+list(PAYERS.values()):df[col]=0.
        df['OBVEXP23']=self.y;df['TOTSLF23']=self.y
        return df

    def test_validation_and_zero_weight_exclusion(self):
        df=self.make_sample();df.loc[0,'PERWT23F']=0
        self.assertEqual(len(validate_sample(df)),3)
        with self.assertRaises(ValueError):validate_sample(df.assign(DUPERSID='duplicate'))
        with self.assertRaises(ValueError):validate_sample(df.assign(TOTEXP23=-1))
        with self.assertRaises(ValueError):validate_sample(df.assign(TOTSLF23=1000))
        with self.assertRaises(ValueError):validate_sample(df.assign(VARSTR=-1))

    def test_group_decomposition_reconciles(self):
        df=self.make_sample();df['group']=['A','A','B','B']
        table=grouped(df,'group',top_fraction(df.TOTEXP23,df.PERWT23F,.5))
        self.assertAlmostEqual(table.population_share.sum(),1)
        self.assertAlmostEqual(table.top5_population_share.sum(),1)
        self.assertAlmostEqual(table.spending_share.sum(),1)
        self.assertAlmostEqual(np.dot(table.population_share,table['mean']),np.average(self.y,weights=self.w))

if __name__=='__main__':unittest.main()
