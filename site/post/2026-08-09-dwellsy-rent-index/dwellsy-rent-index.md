URL: https://youzhi.netlify.app/post/2026-08-09-dwellsy-rent-index/dwellsy-rent-index/
Title: A Repeat-Rent Index From Rental Listings: External Validation, and the Limits of a Truncation Explanation
Date: 2026-08-09
---

Housing is the largest single expense in most household budgets, and shelter carries roughly a third of the weight of the United States consumer price index, yet the official measurement of it is deliberately slow. The CPI’s rent of primary residence samples what tenants actually pay, including the large majority who are in the middle of a lease and whose rent will not change this month. That is the correct object for a cost-of-living index and the wrong object for anyone who needs to know what the rental market is doing now.

Online listings offer the opposite trade-off. An advertised rent is visible the day it is posted, but it is an *asking* price: no lease has been signed, no tenant is observed, and the set of units advertised is whatever the platform happens to index. The question this article takes up is whether a listings-based index can nevertheless be made to behave — whether it tracks the established series, whether it leads them, and whether the ways in which it fails can be diagnosed rather than merely disclosed.

The answer turns out to be split, and the split is the point. On **timing** the index validates decisively. On **level** it is wrong by roughly ten percentage points of cumulative growth over five years, and the explanation that the data documentation itself proposes — that the sample is truncated — is testable, is tested here, and accounts for about one per cent of the discrepancy.

## The data {#the-data}

The source is a corpus of United States rental listings supplied by Dwellsy and acquired by the Center for Applied Artificial Intelligence at Chicago Booth: 12,796,708 de-duplicated listings from 2020 to 2026, a separate log of 24.3 million timestamped rent revisions, and a 101-week panel. Three properties of it govern everything below.

**These are asking prices.** No lease is signed and no tenant is observed. Coverage is whatever Dwellsy indexes, which is not a probability sample of the housing stock.

**The listing is the wrong unit of analysis.** Dwellsy expires listings automatically after 120 days, which splits one marketing episode for one apartment into several listing records. Measuring rent growth across listing records therefore mixes genuine price change with an administrative rule. The remedy is to work at the level of the *unit* — a specific apartment at a specific address — and to compare a unit only with itself.

**The rents are filtered, not clipped.** Dwellsy retains listings between $500 and $20,000 per month. Listings outside that range are *absent* from the data rather than winsorized to the boundary, so the number that were dropped is unknowable from the file. This is the property that the second half of the article is about.

## Holding the apartment fixed {#holding-the-apartment-fixed}

The estimator is the repeat-sales design of Bailey, Muth and Nourse, transplanted from house prices to rents. Rather than compare the average rent this month against the average rent last month — which moves whenever the *mix* of advertised units changes — it uses only apartments observed twice, and asks how much the rent on that same apartment changed between the two dates. Every fixed characteristic of the unit, observed or not, differences out. A national index is then the set of monthly values that best reconciles all such pairs at once.

Matching is deliberately strict: consecutive listings at the same address identifier, the same bedroom count, floor area within five per cent, and a discarded tail of implausible changes. That yields 5,775,959 matched pairs with a median gap of five months.

Two refinements matter. The first is that pairs are not equally informative: the longer a unit sits between two listings, the further its rent can drift from the market for reasons peculiar to that unit. Treating a fifty-month pair as though it were as precise as a one-month pair over-weights exactly the noisiest observations, and Case and Shiller’s three-stage procedure corrects for it by modelling the variance and re-estimating by generalised least squares.

[figure: Standard deviation of the repeat-sales residual by the gap between the two listings of a pair. The generalised least squares stage weights each pair by the inverse of this fitted variance. The dip at nine to twelve months is the annual lease cycle: pairs almost exactly a year apart are unusually well behaved.] Figure 1: Standard deviation of the repeat-sales residual by the gap between the two listings of a pair. The generalised least squares stage weights each pair by the inverse of this fitted variance. The dip at nine to twelve months is the annual lease cycle: pairs almost exactly a year apart are unusually well behaved.

The second refinement is that a repeat-sales index is only identified in months that actually contain pairs.

[figure: A pair is dated by its second listing, so the count is mechanically zero at the start of the window and thin for the first half-year; the index is reported from 2021-01 for that reason. The upward drift thereafter is the panel accumulating history, not a rising re-listing rate.] Figure 2: A pair is dated by its second listing, so the count is mechanically zero at the start of the window and thin for the first half-year; the index is reported from 2021-01 for that reason. The upward drift thereafter is the panel accumulating history, not a rising re-listing rate.

## Validation, part one: does it track? {#validation-part-one-does-it-track}

The comparison series are Zillow’s ZORI, which is also an asking-rent measure built from listings, and the CPI’s rent of primary residence, which is contract rent paid by sitting tenants. The prediction stated before looking was that ZORI should track closely and that the CPI should *not* — and specifically that agreement with the CPI at zero lag would be evidence of a problem rather than of success, because the two series measure different things at different points in a tenancy.

[figure: All three series are indexed to 100 in January 2021. The Dwellsy index reaches its peak and turns over well before either comparison series does; the CPI, which is contract rent paid by all tenants rather than the rent asked of new ones, is still climbing when asking rents have been flat for a year.] Figure 3: All three series are indexed to 100 in January 2021. The Dwellsy index reaches its peak and turns over well before either comparison series does; the CPI, which is contract rent paid by all tenants rather than the rent asked of new ones, is still climbing when asking rents have been flat for a year.

The shapes agree and the timing does not, which is exactly the intended result. Correlation in levels is uninformative here because all three series trend upward; the demanding test is the correlation of month-to-month *changes*, and the informative statistic is the lag at which that correlation is maximised.

[figure: Cross-correlation of month-to-month changes at each lag. A positive lag means the Dwellsy index moves first. Against ZORI the peak sits at one month, the offset expected from ZORI's own smoothing. Against the CPI it sits at eleven months, and the contemporaneous correlation is approximately zero.] Figure 4: Cross-correlation of month-to-month changes at each lag. A positive lag means the Dwellsy index moves first. Against ZORI the peak sits at one month, the offset expected from ZORI’s own smoothing. Against the CPI it sits at eleven months, and the contemporaneous correlation is approximately zero.

This lag is not a discovery. That measured contract rents follow market asking rents with something close to a year’s delay is well established, and it is the reason central-bank analysts watch listings data at all. Recovering the regularity from an index built on different data, by a different method, is evidence that the index is measuring the thing it claims to measure.

The cross-section validates on the same pattern. Restricting to metropolitan areas with at least 25,000 matched pairs and joining to ZORI gives 46 metros, and the two rankings agree closely.

[figure: Each point is a metropolitan area; the diagonal is equality. The rank correlation is 0.92, so the index orders metros almost exactly as ZORI does — but every one of the 46 points lies below the diagonal, which is a systematic level difference and not scatter.] Figure 5: Each point is a metropolitan area; the diagonal is equality. The rank correlation is 0.92, so the index orders metros almost exactly as ZORI does — but every one of the 46 points lies below the diagonal, which is a systematic level difference and not scatter.

### Beyond the 46 metros {#beyond-the-46-metros}

Metropolitan areas are defined on core-based statistical areas, so a metro-only view leaves most of the map blank and says nothing about small-town or rural rental markets. The same matched pairs support a state-level index directly — every state clears five thousand pairs — estimated with the identical Bailey-Muth-Nourse and Case-Shiller procedure used nationally.

[figure: Cumulative growth June 2021 to June 2026, estimated separately for each state on the same matched pairs and the same estimator as the national index. Alaska and Hawaii are estimated and labelled below but are not drawn, as the base map is the lower 48.] Figure 6: Cumulative growth June 2021 to June 2026, estimated separately for each state on the same matched pairs and the same estimator as the national index. Alaska and Hawaii are estimated and labelled below but are not drawn, as the base map is the lower 48.

The states that led the pandemic-era surge are the states that gave it back. Arizona, Colorado, Texas and Nevada sit at the bottom of the distribution over this window, and the Northeast and industrial Midwest at the top — the Sun Belt supply wave arriving after the demand shock that preceded it.

County resolution requires a different estimator. A repeat-sales index needs pairs in enough separate months to chain, and the typical county has a few hundred pairs spread over five years. What *is* identified at that resolution is the duration-weighted mean within-unit growth rate: total log rent change across all matched pairs in the county, divided by the total elapsed time those pairs span. It uses the same pairs and the same unit test, and it is a period-average annual rate rather than a chained index, so it should not be read against the state numbers digit for digit.

[figure: Duration-weighted mean within-unit rent growth per year, 2021 to 2026, for the 1,152 counties with at least 100 matched pairs. Counties in grey have too few pairs or no listings at all. Rents are measured on the same apartment twice, so none of the variation here is composition between counties.] Figure 7: Duration-weighted mean within-unit rent growth per year, 2021 to 2026, for the 1,152 counties with at least 100 matched pairs. Counties in grey have too few pairs or no listings at all. Rents are measured on the same apartment twice, so none of the variation here is composition between counties.

## The problem {#the-problem}

Every point in the cross-section sits below the diagonal, and the national series does the same thing: the index reproduces the shape and the timing of the rent cycle while understating its size. The obvious suspicion is that this is an artefact of holding the unit fixed, since a repeat-rent design deliberately discards everything except units that appear twice. It is not.

[figure: Six ways of measuring the same quantity on the same data, against the two external series. The Dwellsy estimators differ in almost every respect — one holds the unit fixed, one holds the composition fixed, one adjusts for observable quality — and they agree with each other far more closely than any of them agrees with ZORI or the CPI.] Figure 8: Six ways of measuring the same quantity on the same data, against the two external series. The Dwellsy estimators differ in almost every respect — one holds the unit fixed, one holds the composition fixed, one adjusts for observable quality — and they agree with each other far more closely than any of them agrees with ZORI or the CPI.

A repeat-rent index, a fixed-weight median and a quality-adjusted hedonic regression are three different answers to three different questions, and they disagree with one another by about four percentage points. All six land below nineteen per cent while both external series land above twenty-seven. Whatever produces the gap therefore sits upstream of the estimator, in which listings are present in the sample at all.

## The documented suspect {#the-documented-suspect}

Which returns to the rent filter. The $500 to $20,000 bound is a row filter: out-of-range listings were never written to the file. In a repeat-rent design that has a specific and unpleasant consequence, because a pair survives only if **both** of its listings fall inside the band. Consider an apartment advertised at $470 in 2021 and at $560 in 2023. It rose by nineteen per cent, and it contributes nothing to the index, because its first listing was never recorded. The apartment next door, advertised at $520 and then $560, rose by eight per cent and does contribute. At the lower edge of a rising market the filter preferentially deletes the units that rose the most, and the same argument at the upper edge deletes units that rose out of the top of the band.

The prediction that follows is sharp enough to be wrong: attenuation must be **dose-dependent**. Narrowing the band should attenuate the measured index further, from each side independently, and monotonically in how much of the market the band excludes.

Before testing it, the size of the dose has to be estimated, and this is the part that cannot be done from the data alone. The mass outside the band is unobservable by construction. What can be done is to fit a distribution to a region of the observed data that is safely interior — far from both boundaries, so no boundary distortion enters the fit — and extrapolate it outward. Fitting a lognormal to observed rents between $1,000 and $8,000 by maximum likelihood, with the truncation of the fitting window itself accounted for, gives the following picture.

[figure: Observed advertised rents (bars) with a lognormal fitted by maximum likelihood to the interior region between $1,000 and $8,000 (line), extrapolated past both boundaries. The shaded area below $500 is the estimated missing mass. The upper bound is far into the tail and removes essentially nothing.] Figure 9: Observed advertised rents (bars) with a lognormal fitted by maximum likelihood to the interior region between $1,000 and $8,000 (line), extrapolated past both boundaries. The shaded area below $500 is the estimated missing mass. The upper bound is far into the tail and removes essentially nothing.

The median advertised rent is $1,679 and the fifth percentile is $795, so the lower bound sits deep in the left tail and the upper bound is effectively irrelevant — one listing in seven thousand is within ten per cent of it. How much the filter removed depends on the fitting window, and on the year: as the rent distribution shifted right over the window, it pulled away from the lower bound and the filter bit progressively less.

[figure: Estimated share of the underlying rent distribution falling outside the $500-$20,000 band, fitted separately for each year and each of three interior windows. The spread between the three lines is the model uncertainty on a quantity that cannot be observed; the downward slope is the distribution shifting right, away from the lower bound.] Figure 10: Estimated share of the underlying rent distribution falling outside the $500-$20,000 band, fitted separately for each year and each of three interior windows. The spread between the three lines is the model uncertainty on a quantity that cannot be observed; the downward slope is the distribution shifting right, away from the lower bound.

## The test {#the-test}

Whether that is enough to matter is an empirical question, and the ladder answers it. The index was re-estimated on progressively narrower bands: from both sides at once, from the bottom only, and from the top only. Everything else — the pair construction, the unit test, the trim, the Case-Shiller weighting — is held identical, so the only thing that varies between points is how much of the market the band admits.

[figure: Each point is a complete re-estimation of the national index on a narrower band. The mechanism is confirmed: growth falls monotonically as the band excludes more of the market, from both directions, and the slope is estimated precisely. The extrapolation to an unfiltered sample is the open point at the left.] Figure 11: Each point is a complete re-estimation of the national index on a narrower band. The mechanism is confirmed: growth falls monotonically as the band excludes more of the market, from both directions, and the slope is estimated precisely. The extrapolation to an unfiltered sample is the open point at the left.

The prediction holds in every respect. Growth falls monotonically as the band tightens; it falls when the band is tightened from below and, much more weakly, when tightened from above, which is what the shape of the distribution implies it should do; and the relationship is close to linear over the region that matters. Discarding two-fifths of the market costs four percentage points of measured growth, so the mechanism is not merely present but large when the dose is large.

The dose, however, is not large. Removing the estimated 0.71 per cent that the real filter removes moves the index by about a tenth of a percentage point.

[figure: Decomposition of the ten-and-a-half point discrepancy against ZORI. Both mechanical explanations are real and both are negligible; the residual is not a rounding difference but the overwhelming majority of the gap.] Figure 12: Decomposition of the ten-and-a-half point discrepancy against ZORI. Both mechanical explanations are real and both are negligible; the residual is not a rounding difference but the overwhelming majority of the gap.

## The second candidate {#the-second-candidate}

The other mechanical explanation available in this data concerns *which* asking price is being indexed. Every listing has at least two: the price it opened at, and the price it carried when it left the market. The index above uses opening asks. If landlords increasingly marked down while a unit sat, an opening-ask index would miss a growing discount and overstate what tenants faced — or, in the other direction, understate it.

Re-estimating the entire index on the closing ask moves neither the path nor the level enough to matter.

[figure: The same estimator, the same units and the same band, run once on the price each listing opened at and once on the price it carried when it left the market. The two paths are almost indistinguishable, and the five-year totals differ by roughly a fifth of a percentage point.] Figure 13: The same estimator, the same units and the same band, run once on the price each listing opened at and once on the price it carried when it left the market. The two paths are almost indistinguishable, and the five-year totals differ by roughly a fifth of a percentage point.

It is the right check to run and it does not rescue the level either.

That the substitution changes so little is worth a moment, because the two prices are not close to interchangeable at the level of the individual apartment. A separate decomposition on the weekly panel separates the two decisions a landlord makes: the **re-listing step**, which is the new asking price relative to the last asking price of the previous listing at the same unit, and the **within-spell markdown**, which is how far the price is walked down while the unit sits unrented.

[figure: Each point is a metropolitan area. Landlords reset the asking price slightly upward at turnover and then give it back, several times over, while the unit sits. The two channels are positively correlated across metros, so they are not substitutes: soft markets do more of both.] Figure 14: Each point is a metropolitan area. Landlords reset the asking price slightly upward at turnover and then give it back, several times over, while the unit sits. The two channels are positively correlated across metros, so they are not substitutes: soft markets do more of both.

The implication for index construction is real even though it did not move this level: an index built on opening asks observes only the channel that moves *least* when a market cools, and will therefore understate what a prospective tenant actually encounters. It is a reason to publish both, and not a reason to expect either to close a ten-point gap.

## What is left {#what-is-left}

Having eliminated the two explanations that could be tested inside the data, what remains is the one that cannot be tested inside it: **composition**. The Dwellsy sample is whatever Dwellsy indexes. If the platform’s coverage tilts toward market segments, unit types, ownership structures or geographies whose rents rose more slowly than the national aggregate, then every estimator built on it inherits that tilt — which is precisely the pattern observed, with six methodologically unrelated estimators agreeing closely with one another and disagreeing with the outside world. A coverage tilt of this kind is documented elsewhere in this corpus, in its weekly panel, which under-represents large managed communities relative to single-family rentals; whether the listing table underlying this index carries an analogous tilt has not been tested, and cannot be tested without an external benchmark.

The coverage map is the argument in visual form. Half of all counties never appear at all, and the ones that do are not a scaled-down copy of the country.

[figure: Listings per county on a log scale, all counties with any listing at all. The white areas are not places with no rental housing; they are places this platform does not index. Any national aggregate built from this sample weights the shaded counties and ignores the rest.] Figure 15: Listings per county on a log scale, all counties with any listing at all. The white areas are not places with no rental housing; they are places this platform does not index. Any national aggregate built from this sample weights the shaded counties and ignores the rest.

Distinguishing that from the alternative — that ZORI and the CPI are themselves tilted, in the opposite direction — requires an external benchmark at the unit level, which is to say administrative or lease-level data that this project does not have. That is a limit, and it is stated as one.

## What the index is, then {#what-the-index-is-then}

It is a **timing instrument, not a level instrument**, and the two should be reported separately.

As a timing instrument it is validated: it recovers the turning points of the cycle, it moves one month ahead of the leading commercial asking-rent index, it moves roughly eleven months ahead of the CPI’s rent component, and it orders metropolitan areas almost exactly as ZORI does. For anyone who needs to know whether the rental market has turned, several months before the official statistics say so, those properties are the ones that matter.

As a level instrument it is biased downward by about two percentage points a year, the bias is one-sided across all 46 metros, and — the useful part — that bias is now known not to be an artefact of the filter or of the choice of asking price. Publishing the index without that statement attached would be publishing a number that is wrong in a way its own documentation had already guessed at, and wrongly diagnosed.

There is a general lesson in the shape of the result. The dataset’s documentation identified the filter as the leading candidate for the level bias, and the identification was reasonable: the mechanism is genuine, the sign is right, and the effect is estimated here at eighteen standard errors. It was simply two orders of magnitude too small. A plausible mechanism with the correct sign is not evidence of a material effect, and the distance between “this could explain it” and “this does explain it” is a dose-response curve.

## Notes on method and data {#notes-on-method-and-data}

- **Estimator.** Bailey-Muth-Nourse repeat-sales with Case-Shiller three-stage weighting, implemented directly on NumPy. Pair construction, the unit test and the outlier trim are identical across every band in the ladder, so points differ only in the band.
- **The extrapolation is model-dependent.** The mass outside the filter cannot be observed. A lognormal fitted to the interior gives 0.71 per cent; two alternative fitting windows give 0.92 and 0.94 per cent. Even at three times the headline estimate the correction remains under half a percentage point, so the conclusion is not sensitive to the choice, but the quantity itself is an extrapolation and is reported as one.
- **The lead is measured in sample.** Sixty-five months contain essentially one rent cycle. The eleven-month lead against the CPI is consistent with an established regularity, but a claim that it will hold out of sample requires a recursive, real-time evaluation that has not been run here.
- **These remain asking prices.** No lease, no tenant, and no rent paid is observed anywhere in this data.
- **Source.** Dwellsy US rental listings, acquired by the University of Chicago Booth School of Business [Center for Applied Artificial Intelligence](https://www.chicagobooth.edu/research/center-for-applied-artificial-intelligence/stories/2026/caai-new-datasets). No extract of the underlying data is redistributed here; every figure reports aggregate statistics.
