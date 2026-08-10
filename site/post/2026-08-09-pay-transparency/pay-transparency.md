URL: https://youzhi.netlify.app/post/2026-08-09-pay-transparency/pay-transparency/
Title: Pay-Transparency Mandates in 51.9 Million Job Postings: Measurement, Within-Firm Evidence, and Spillover
Date: 2026-08-09
---

**Abstract.** Twelve US states require employers to publish a pay range in the job advertisement itself. I measure compliance in a corpus of **51,864,055 LinkedIn job postings** collected monthly from February to July 2026, of which 23,970,734 are distinct and 14,250,750 are locatable to a US state. Three findings follow. First, the obvious measure is the wrong one: LinkedIn’s structured salary field records whether an employer used a platform feature, not whether it stated a range, and it understates the mandate’s association with disclosure roughly fivefold. Reading the range out of the description text instead — with an extractor validated against 2,244,205 employer-written labels at 89.8 % precision — raises the raw mandate-minus-no-law gap from 5.7 to **28.4 percentage points**. Second, the gap is not composition. Comparing a single firm with itself across a state line gives **+19.1 pp** in disclosure by any means, and the estimate does not fall when the identical job title at the same employer is held fixed, when the sample is restricted to firms too large for any statutory exemption, or when the comparison is confined to one commuting zone; none of 500 randomly drawn placebo assignments reproduces it. Third, the law travels with the firm: inside no-law states only, firms that also post into a mandate state disclose **13.8 pp** more than matched firms that do not, roughly seven-tenths of the effect measured inside the mandate states themselves. Two null results are reported with equal weight — mandates do not widen posted ranges, and a city-level placebo manufactures a spurious effect. Every estimate is a cross-sectional association rather than a causal effect: the corpus contains no pre-period and no realised wages.

## 1. Introduction {#introduction}

Pay transparency has become one of the most widely adopted labour-market regulations of the past decade. [Cullen (2024)](https://www.aeaweb.org/articles?id=10.1257/jep.38.1.153) reports that 71 % of OECD countries have enacted some form of transparency policy since 2000. Research has concentrated on two families: rules letting coworkers learn each other’s pay, and rules requiring firms to publish gender pay-gap statistics. The measured effects are neither uniform nor uniformly favourable. [Cullen and
Pakzad-Hurson (2023)](https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA19788) show theoretically and empirically that transparency weakens individual bargaining power and lowers average wages by about 2 %. [Mas (2017)](https://www.journals.uchicago.edu/doi/abs/10.1086/693137) finds that publishing municipal salaries in California cut top managers’ compensation by roughly 7 % and raised their quit rate by 75 %. On gender gaps the record is mixed: [Baker et al.
(2023)](https://www.aeaweb.org/articles?id=10.1257/app.20210141) find that Canadian disclosure laws narrowed the faculty gender gap by 20–40 %, [Bennedsen et al.
(2022)](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13136) find a 2 pp narrowing in Denmark driven by slower male wage growth, and [Gulyas, Seitz and Sinha
(2023)](https://www.aeaweb.org/articles?id=10.1257/pol.20210128) find a precise zero in Austria.

This article concerns a third and newer family: **posting mandates**, which regulate the advertisement rather than the employment relationship. A posting mandate is unusual among labour regulations in that compliance is directly observable, because the required disclosure is a piece of public text. That makes the first-order question empirical and, in principle, simple: do employers actually do it?

In practice the question is hard for a mundane reason. The answer lives in the text of job advertisements, and job advertisements are not a dataset anyone keeps. The closest existing study is [Arnold, Quach and Taska (2025)](https://www.nber.org/papers/w34480), who use Burning Glass postings to show that Colorado’s 2021 mandate raised the share of postings containing salary information by about 30 pp — with substantial non-compliance — and that wages rose 1.3–3.6 %. [Batra, Michaud and Mongey
(2023)](https://www.nber.org/papers/w31984) document the other side of the same coin: online job posts contain very little wage information to begin with.

### 1.1 Contribution {#contribution}

I add three things, in order of how much I think they matter.

1. **A measurement result that changes the answer.** Job-posting corpora expose a structured salary field, and it is the natural thing to count. It is the wrong thing to count. On this corpus the structured field puts the mandate-minus-no-law gap at 5.7 pp; reading the range out of the description text puts it at 28.4 pp. The field measures platform-feature adoption, not disclosure. Section 4 documents this and validates the replacement against labels the corpus generates itself.
2. **A within-firm design at a scale that permits holding the job fixed.** With 23.97 M distinct postings I can compare a single employer with itself across a legal border while holding its *exact job title* constant, restrict to firms above any statutory size threshold, and narrow to a single commuting zone in the manner of [Dube, Lester and Reich
(2010)](https://direct.mit.edu/rest/article/92/4/945/57855/Minimum-Wage-Effects-Across-State-Borders). The estimate survives all three.
3. **A spillover estimate.** Within-firm differencing removes spillovers by construction, so they have to be asked about separately — and they are what a legislator would want to know. Firms exposed to a mandate somewhere disclose substantially more in states that have no mandate at all.

The article inherits a methodological posture from the job-postings literature, in which [Hershbein and
Kahn (2018)](https://www.aeaweb.org/articles?id=10.1257/aer.20161570) and [Deming and Kahn
(2018)](https://www.journals.uchicago.edu/doi/abs/10.1086/694106) established that posting text is usable measurement rather than anecdote. It also inherits that literature’s central limitation: these are *posted* advertisements, and no hire, no wage paid and no worker appears anywhere in the data.

### 1.2 Terminology {#terminology}

*Disclosure* means a pay range visible to a reader of the advertisement. *Mandate states* are the twelve with a posting mandate; *no-law states* are the thirty-three with neither a posting mandate nor a disclose-on-request rule. The six *on-request states*, which require a range only after a conditional offer, are held out as a placebo group rather than used as controls.

## 2. Institutional setting {#institutional-setting}

A posting mandate requires the pay range to appear in the advertisement itself. Nine of the twelve bind only above an employee-count threshold, from four employees in New York to fifty in Hawaii, and the effective dates span five years.

[figure: Effective date of each state posting mandate, with its statutory employer-size threshold.
Every mandate was already in force before the first snapshot, so the corpus contains no pre-period and
no event study is available.] Figure 1: Effective date of each state posting mandate, with its statutory employer-size threshold. Every mandate was already in force before the first snapshot, so the corpus contains no pre-period and no event study is available.

This is the first constraint on what can be estimated here, and it belongs before any result: every mandate predates the crawl window, so nothing in this article is a before-and-after comparison.

## 3. Data {#data}

### 3.1 The corpus {#the-corpus}

The data are LinkedIn job postings scraped from publicly accessible pages via Bright Data and acquired by Chicago Booth’s Center for Applied AI: **51,864,055 rows** across six monthly snapshots, February to July 2026, deduplicating to **23,970,734 distinct postings**, of which **14,250,750** carry a parsable US state. Each posting carries a title, an employer identifier, a location, a structured salary field and the full advertisement text.

Two properties of the crawl bear directly on the design, and both argue against using the time dimension.

### 3.2 Why the design is cross-sectional {#why-the-design-is-cross-sectional}

The corpus has no reliable clock. Its one date field, `job_posted_date`, is not recorded when the posting appears; it is re-derived at each crawl from a relative string such as “2 weeks ago”.

[figure: Change in a posting's reported posting date between two consecutive monthly crawls, over
27,893,319 consecutive observations. Positive means the later crawl described the posting as newer than
the earlier crawl did, which is not how time works.] Figure 2: Change in a posting’s reported posting date between two consecutive monthly crawls, over 27,893,319 consecutive observations. Positive means the later crawl described the posting as newer than the earlier crawl did, which is not how time works.

A field that moves in both directions cannot date anything, and the column that would have served as a timestamp is 100 % null. Even if the dates held still, the structured outcome variable does not.

[figure: Share of rows carrying a structured salary range, by crawl month. The decline is a property of
the crawl rather than of employer behaviour, so any disclosure series computed from these six months
would be dominated by it.] Figure 3: Share of rows carrying a structured salary range, by crawl month. The decline is a property of the crawl rather than of employer behaviour, so any disclosure series computed from these six months would be dominated by it.

Together, Figures 1–3 rule out an event study and rule out a trend. What remains is the design this corpus is unusually good for: a very large cross-section in which the same employer is observed writing advertisements under two legal regimes at the same moment.

## 4. Measuring disclosure {#measuring-disclosure}

### 4.1 The structured field is not disclosure {#the-structured-field-is-not-disclosure}

LinkedIn exposes a structured salary field, and alongside any range it records a provenance string: either *“This range is provided by ⟨employer⟩”*, which is the employer’s own number, or *“Retrieved from the description.”*, which is LinkedIn’s own inference from the text. These are different objects, and pooling them roughly doubles apparent disclosure.

Neither is the same as an employer stating a range. A firm that writes “$95,000–$115,000 per year” in its description and never touches the structured widget is complying with the law and is invisible to the field. This is the concrete form of the problem [Batra, Michaud and Mongey
(2023)](https://www.nber.org/papers/w31984) describe: the machine-readable wage fields of job-posting data are sparse, and sparse in ways correlated with the platform rather than the employer.

[figure: Share of US postings disclosing pay under four progressively broader definitions, by state law
group. The bold figure at the right of each group is the mandate-minus-no-law gap; it ranges from 5.7 to
28.4 pp over the same postings and the same laws.] Figure 4: Share of US postings disclosing pay under four progressively broader definitions, by state law group. The bold figure at the right of each group is the mandate-minus-no-law gap; it ranges from 5.7 to 28.4 pp over the same postings and the same laws.

The estimated effect of a mandate is therefore a property of the definition chosen. The rest of this article uses the broadest defensible definition — a range in the structured field *or* a salary-context range in the description text — and the remainder of this section earns the right to use it.

### 4.2 Extraction {#extraction}

The extractor is deliberately unglamorous: a regular-expression pass over every dollar figure in all 51,864,055 descriptions, which classifies each figure by its surrounding words, infers the pay period and annualises. The classification step is the one that matters, because a job advertisement is full of dollar figures that are not pay.

[figure: Context classification of the dollar ranges found in postings whose structured salary field is
empty. Only salary-context ranges count as disclosure; signing bonuses, tuition-aid ceilings and
unclassifiable figures are discarded.] Figure 5: Context classification of the dollar ranges found in postings whose structured salary field is empty. Only salary-context ranges count as disclosure; signing bonuses, tuition-aid ceilings and unclassifiable figures are discarded.

### 4.3 Validation against employer-written labels {#validation-against-employer-written-labels}

Hand-auditing a few hundred postings is the usual standard. This corpus can do better, because it contains its own labels: **2,244,205 US postings carry both an employer-supplied structured range and the description text that range was typed into.** These are labelled examples produced by employers rather than by the researcher, and they outnumber a hand audit by four orders of magnitude.

[figure: Extractor performance against 2,244,205 postings carrying both a structured range and the
description it was typed into. Precision is conditional on the extractor returning a range; recall is
over all labelled postings.] Figure 6: Extractor performance against 2,244,205 postings carrying both a structured range and the description it was typed into. Precision is conditional on the extractor returning a range; recall is over all labelled postings.

Two threats deserve explicit treatment.

**Circularity.** LinkedIn renders its own salary widget into the page. Were that rendered text to reach the description column, the text measure would restate the structured field rather than read the advertisement independently.

[figure: Prevalence of LinkedIn's rendered widget text in the description column. If the extractor were
reading the widget back to itself, the rate in the lower panel would be far higher on the left than on
the right.] Figure 7: Prevalence of LinkedIn’s rendered widget text in the description column. If the extractor were reading the widget back to itself, the rate in the lower panel would be far higher on the left than on the right.

**Recall, not precision, is the binding limitation.** The extractor returns a correct range 89.8 % of the time when it returns one, but recovers only 58.4 % of the ranges known to exist. This corpus cannot decompose the shortfall: an employer who fills the structured widget without repeating the number in the description is indistinguishable from a range the extractor failed to read. The consequence is the same either way and its direction is known — **every disclosure level reported below is a lower bound, and every gap is attenuated toward zero** by measurement error in the outcome.

### 4.4 What the instrument is worth {#what-the-instrument-is-worth}

A cruder first version of this measure was a yes/no flag that fired only on comma-formatted numbers or an explicit hourly rate. Substituting the validated extractor for it, holding every design fixed, prices the measurement error directly.

[figure: The same within-firm designs estimated twice, changing only how a pay range in the description
is detected. The superseded flag has a 9.4 % false-positive and a 35.9 % false-negative rate against the
same 2.24 million labels.] Figure 8: The same within-firm designs estimated twice, changing only how a pay range in the description is detected. The superseded flag has a 9.4 % false-positive and a 35.9 % false-negative rate against the same 2.24 million labels.

A by-product matters for wage work on this corpus, and for the statistical power of everything below.

[figure: US postings with an annualisable pay range, by where the range was found. The text-recovered
observations are not a subset of the structured ones; they are postings that never used the widget.] Figure 9: US postings with an annualisable pay range, by where the range was found. The text-recovered observations are not a subset of the structured ones; they are postings that never used the widget.

## 5. Empirical strategy {#empirical-strategy}

Let \(g\) index a comparison group — a firm, a firm × job-title cell, or a metropolitan area. Within group \(g\), let \(n^T_g\) and \(n^C_g\) count postings in mandate and no-law states, and let \(\bar y^T_g\) and \(\bar y^C_g\) be the corresponding disclosure rates. The estimator is the weighted mean of within-group differences,

\[\widehat{\Delta} \;=\; \frac{\sum_g w_g \, d_g}{\sum_g w_g}, \qquad d_g \;=\; \bar y^T_g - \bar y^C_g, \qquad w_g \;=\; \min\!\left(n^T_g,\; n^C_g\right),\]

with the standard error taken across groups,

\[\widehat{\mathrm{se}}^{\,2} \;=\; \frac{\sum_g w_g^2\left(d_g - \widehat{\Delta}\right)^2}{\left(\sum_g w_g\right)^2}.\]

Weighting by the *smaller* of the two side counts is the point of the design. A firm with four thousand postings in one state and three in the other contributes almost nothing, so the estimate is not driven by firms that barely straddle the border. Only groups with postings on both sides enter at all, which is what makes the comparison within-firm rather than between-firm.

The identifying assumption is not that mandate and no-law states are alike — Section 6.1 shows they are not — but that within an employer, and where stated within the same job title and the same commuting zone, the decision to publish a range differs across the border because of the law rather than because of something else that also changes at the state line. Sections 6.2–6.5 probe that assumption from four directions. None of these designs recovers a causal effect: all twelve mandates predate the data, so what is estimated throughout is a cross-sectional association under progressively tighter conditioning.

## 6. Results {#results}

### 6.1 The raw cross-state comparison, and why it cannot be the answer {#the-raw-cross-state-comparison-and-why-it-cannot-be-the-answer}

Start with the comparison a reader would make first.

[figure: Disclosure by state on the narrow measure (horizontal) and the broad measure (vertical);
point area is the state's posting count. Mandate states sit high on both, and the broad measure separates
the two regimes almost completely.] Figure 10: Disclosure by state on the narrow measure (horizontal) and the broad measure (vertical); point area is the state’s posting count. Mandate states sit high on both, and the broad measure separates the two regimes almost completely.

Two things are visible. On the broad measure the regimes barely overlap: every mandate state discloses more than every no-law state. On the structured measure they overlap freely, and several no-law states outrank mandate states outright — the measurement point of Section 4, restated at the level of individual jurisdictions. The six on-request states sit 1.4 pp above the no-law group, which is the right answer for a group facing no posting duty.

None of that settles anything, because a cross-state comparison is confounded by everything else that differs across states. California is not Mississippi with a different statute: it has a different industry mix, different firms and different occupations, each of which moves disclosure on its own.

### 6.2 Within firm, and within the same job {#within-firm-and-within-the-same-job}

The concern the within-firm design does not by itself answer is occupation. A hospital chain posting nurses in Texas and engineers in California is being compared with itself across two different jobs. The grouping is therefore tightened in steps, ending at the same employer advertising the *same exact job title* on both sides of the border.

[figure: Within-group gap in disclosure, mandate minus no law, as the comparison group is tightened
from the top row downward. Bars span two standard errors either side. The bottom row is a placebo:
disclose-on-request states impose no posting duty.] Figure 11: Within-group gap in disclosure, mandate minus no law, as the comparison group is tightened from the top row downward. Bars span two standard errors either side. The bottom row is a placebo: disclose-on-request states impose no posting duty.

Holding the identical job title at the same employer fixed does not reduce the estimate; it raises it slightly, to +3.78 pp on the structured measure and +18.55 pp by any means. Occupation composition inside the firm is not the mechanism.

### 6.3 The employer-size threshold does not bind {#the-employer-size-threshold-does-not-bind}

Nine mandates apply only above an employee-count threshold, and the corpus has no employee count. Applying the mandate wherever it nominally covers a state therefore introduces measurement error of unknown sign in the *treatment*. Two responses.

First, restrict to firms that posted 500 or more jobs in six months, which exceed fifty employees with near certainty; the estimate is **+3.62 pp**, indistinguishable from the all-firms figure. Second, and more informative, turn the threshold into a falsification test: if thresholds bind, the gap must grow with firm size *faster* in high-threshold states than in states covering every employer.

[figure: Within-firm gap in employer-supplied disclosure by the firm's own posting volume, splitting
the mandate side by statutory threshold while holding the no-law control side common. A binding threshold
would tilt the 25–50 employee line upward to the right.] Figure 12: Within-firm gap in employer-supplied disclosure by the firm’s own posting volume, splitting the mandate side by statutory threshold while holding the no-law control side common. A binding threshold would tilt the 25–50 employee line upward to the right.

There is no gradient and no threshold pattern; small firms in high-threshold states, nominally exempt, show as large a gap as anyone else. Two readings are consistent with this, and the data cannot separate them. Either firms adopt a single national posting policy rather than conditioning on each state’s statute, or posting volume is too weak a proxy for employee count to detect the threshold. The first is not an exotic hypothesis: [Hazell et al. (2022)](https://www.nber.org/papers/w30623) find that 40–50 % of a job’s posted wages are *identical* across a firm’s locations, which is national wage setting of exactly the kind a national posting policy would accompany. Either way, the correction one might have wanted is not needed.

### 6.4 One labour market, two legal regimes {#one-labour-market-two-legal-regimes}

A within-firm comparison still spans different local labour markets. The sharpest available design narrows to a single commuting zone, following the contiguous-border logic of [Dube, Lester and Reich
(2010)](https://direct.mit.edu/rest/article/92/4/945/57855/Minimum-Wage-Effects-Across-State-Borders): **26 metropolitan areas straddle a mandate state and a no-law state**, covering 2,330,018 postings.

[figure: Disclosure on each side of the legal border, for metros with at least 1,000 postings on both
sides. Point area is postings on the smaller side, which is the weight the pooled estimate gives that
metro.] Figure 13: Disclosure on each side of the legal border, for metros with at least 1,000 postings on both sides. Point area is postings on the smaller side, which is the weight the pooled estimate gives that metro.

[figure: Border-design estimates against the all-US within-firm estimate. The border designs sit on
either side of it rather than collapsing toward zero, which is what a labour-market explanation of the gap
would require.] Figure 14: Border-design estimates against the all-US within-firm estimate. The border designs sit on either side of it rather than collapsing toward zero, which is what a labour-market explanation of the gap would require.

Narrowing to one commuting zone leaves the structured-field gap slightly larger and the broad gap slightly smaller, and both remain far from zero. Whatever the border is picking up, it is not a difference between labour markets.

### 6.5 Randomisation inference {#randomisation-inference}

The on-request placebo is one null. A sharper one asks what a gap of this size looks like when the mandate is fictional: draw twelve fake mandate states at random from the forty-five jurisdictions without an on-request law, recompute the entire within-firm estimate, and repeat five hundred times. This is randomisation inference in the sense of [Young
(2019)](https://academic.oup.com/qje/article-abstract/134/2/557/5195544), and it tests a sharp null that the clustered standard errors above do not.

[figure: Distribution of the within-firm gap under 500 random assignments of twelve fake mandate
states, requiring 20 postings per side as the real estimate does. The vertical dashed line marks the real
assignment; the panels are on different scales.] Figure 15: Distribution of the within-firm gap under 500 random assignments of twelve fake mandate states, requiring 20 postings per side as the real estimate does. The vertical dashed line marks the real assignment; the panels are on different scales.

The placebo distributions are centred on zero and their extremes fall well short of the real estimate, so the result is not an artefact of twelve states differing from thirty-three in some way a within-firm comparison cannot absorb.

## 7. Spillovers: the law travels with the firm {#spillovers-the-law-travels-with-the-firm}

Within-firm differencing removes spillovers by construction. If a firm exposed to a mandate somewhere changes its posting policy everywhere, that change is differenced away — which means the designs above are if anything conservative, and that the policy-relevant question has to be asked separately.

Restrict attention to postings in no-law states only. Compare firms that also post into at least one mandate state against firms that do not, matching on state × industry × firm-size cells so the comparison is not simply national firms against local ones.

[figure: Disclosure inside no-law states only, split by whether the firm also posts into a mandate
state. Points are raw shares; the bold label is the difference after matching on state, industry and firm
size, with two standard errors either side.] Figure 16: Disclosure inside no-law states only, split by whether the firm also posts into a mandate state. Points are raw shares; the bold label is the difference after matching on state, industry and firm size, with two standard errors either side.

A firm exposed to a posting mandate anywhere discloses **13.8 pp more in states with no law at all**, against a within-firm cross-border estimate of 19.1 pp on the same outcome. An accounting that counts only what happens inside the twelve mandate states therefore misses most of a second effect of similar size. This is the closest thing here to a policy magnitude, and it is consistent with the mechanism [Arnold,
Quach and Taska (2025)](https://www.nber.org/papers/w34480) emphasise, in which always-posting firms and incumbent workers are affected beyond the directly regulated margin.

The caveat belongs in the same breath: this is an association, not a causal estimate. Firms choose which states to enter, and a national employer differs from a local one in ways that matching on state, industry and size does not capture. A clean spillover design needs the timing of a firm’s entry into a mandate state, which this corpus does not contain.

## 8. Two null results {#two-null-results}

Negative results are the part of an empirical exercise most likely to go unreported and most likely to be useful, so both are given the same weight as the findings above.

### 8.1 Mandates do not widen posted ranges {#mandates-do-not-widen-posted-ranges}

The standard compliance-quality worry is that an employer told to publish a range publishes “$40,000 to $400,000”. The concern is not idle: [Cullen and Pakzad-Hurson
(2023)](https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA19788) give a mechanism by which firms respond strategically to being observed rather than simply complying.

[figure: Mean width of an employer-supplied pay range relative to its midpoint, by law group. Within
firm the mandate-minus-no-law difference is -0.33 pp with a standard error of 0.35, a precise zero.] Figure 17: Mean width of an employer-supplied pay range relative to its midpoint, by law group. Within firm the mandate-minus-no-law difference is -0.33 pp with a standard error of 0.35, a precise zero.

The raw ordering runs opposite to the worry, and within firm it disappears entirely. There is no evidence of range inflation under a mandate and none of improvement either. On this margin the corpus returns a precise zero, which is a more useful answer than a noisy one in either direction.

### 8.2 City-level treatment assignment picks up composition {#city-level-treatment-assignment-picks-up-composition}

Several ordinances are frequently listed as city posting mandates and are not. Philadelphia’s is a salary-*history* ban, which places no duty on the advertisement, so it should show nothing.

[figure: Philadelphia against the rest of Pennsylvania, neither of which has a posting mandate. The
structured measure behaves correctly and shows nothing; the broad measure manufactures an effect.] Figure 18: Philadelphia against the rest of Pennsylvania, neither of which has a posting mandate. The structured measure behaves correctly and shows nothing; the broad measure manufactures an effect.

The spurious estimate is roughly two-fifths the size of the genuine within-firm one — large enough to be mistaken for a real effect by anyone who had not checked. This is not an argument against the broad measure, which is validated and which the structured measure cannot replace. It is an argument against assigning treatment at city level in this corpus, where a large city differs from its own state in industry and firm composition far more than it differs in law.

## 9. Limitations {#limitations}

- **These are posted advertisements.** No hire is observed, no wage is paid, and no worker appears in the data. Nothing here speaks to whether posted ranges match realised pay, or to the wage effects of transparency, which is the question most of the literature — [Cullen and Pakzad-Hurson
(2023)](https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA19788), [Mas
(2017)](https://www.journals.uchicago.edu/doi/abs/10.1086/693137), [Arnold, Quach and Taska
(2025)](https://www.nber.org/papers/w34480) — is actually about.
- **Cross-section, not event study.** All twelve mandates predate the first snapshot (Figure 1). The estimates are differences in the *level* of disclosure under two regimes at one moment, and they inherit whatever selection puts a firm in one state rather than another. The within-firm, within-title and within-metro designs narrow that selection considerably; they do not eliminate it.
- **Every level is a lower bound.** The text measure recovers 58.4 % of ranges known to exist, so disclosure is understated throughout and the gaps are attenuated toward zero.
- **Coverage is shaped by the crawler.** The corpus is what Bright Data’s discovery configuration reached, and that configuration became markedly more targeted across the window. Nothing here is nationally representative, and no month-over-month magnitude should be read from it.
- **No gender dimension.** The transparency literature is largely about pay gaps between groups of workers. A posting contains no worker, so that question cannot be posed on this data at all.
- **The spillover result is an association.** Firms self-select into mandate states.

## 10. Conclusion {#conclusion}

The headline number in a compliance study of a posting mandate is a measurement choice before it is an empirical result. On the same 14.25 million postings and the same twelve statutes, the mandate-minus-no-law gap is 5.7 pp if disclosure means “the employer filled in the platform’s salary widget” and 28.4 pp if it means “a reader of the advertisement can see a pay range”. The second is the object the law addresses. Any study of posting mandates that counts a structured field is measuring feature adoption, and will understate compliance by something like a factor of five.

Conditional on measuring the right thing, the association is large and hard to dislodge. It survives being confined to one employer, one job title, one commuting zone and one firm-size class, and no random assignment of twelve placebo states comes near it. It also extends past the border: firms exposed to a mandate anywhere disclose substantially more where no mandate applies, which means the reach of these statutes is understated by designs that look only inside the states that passed them.

What the corpus cannot do is turn any of this into a causal estimate, because every mandate was already in force when collection began. The pipeline for that estimate now exists and has been validated on the full corpus — the extractor, the statutory coding, the within-group estimator, the metro crosswalk. What is missing is time. Continued monthly collection converts each estimate above from a difference in levels into an event study on the same firms with the same instrument, and would do so for any state that adopts a mandate inside that window. That is a recommendation about collection rather than about analysis, and it is the most useful thing this exercise produced.

The measurement lesson generalises beyond this policy. On any corpus of this kind, a platform’s structured fields record which employers used the platform’s features, and the text records what those employers were willing to say. Those are not the same variable, and only one of them is the object a disclosure law addresses.

## References {#references}

Arnold, D., S. Quach, and B. Taska (2025). “The Impact of Pay Transparency in Job Postings on the Labor Market.” *NBER Working Paper* 34480. [https://www.nber.org/papers/w34480](https://www.nber.org/papers/w34480)

Baker, M., Y. Halberstam, K. Kroft, A. Mas, and D. Messacar (2023). “Pay Transparency and the Gender Gap.” *American Economic Journal: Applied Economics* 15(2), 157–183. [https://www.aeaweb.org/articles?id=10.1257/app.20210141](https://www.aeaweb.org/articles?id=10.1257/app.20210141)

Batra, H., A. Michaud, and S. Mongey (2023). “Online Job Posts Contain Very Little Wage Information.” *NBER Working Paper* 31984. [https://www.nber.org/papers/w31984](https://www.nber.org/papers/w31984)

Bennedsen, M., E. Simintzi, M. Tsoutsoura, and D. Wolfenzon (2022). “Do Firms Respond to Gender Pay Gap Transparency?” *Journal of Finance* 77(4), 2051–2091. [https://onlinelibrary.wiley.com/doi/10.1111/jofi.13136](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13136)

Cullen, Z. B. (2024). “Is Pay Transparency Good?” *Journal of Economic Perspectives* 38(1), 153–180. [https://www.aeaweb.org/articles?id=10.1257/jep.38.1.153](https://www.aeaweb.org/articles?id=10.1257/jep.38.1.153)

Cullen, Z. B., and B. Pakzad-Hurson (2023). “Equilibrium Effects of Pay Transparency.” *Econometrica* 91(3), 765–802. [https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA19788](https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA19788)

Deming, D., and L. B. Kahn (2018). “Skill Requirements across Firms and Labor Markets: Evidence from Job Postings for Professionals.” *Journal of Labor Economics* 36(S1), S337–S369. [https://www.journals.uchicago.edu/doi/abs/10.1086/694106](https://www.journals.uchicago.edu/doi/abs/10.1086/694106)

Dube, A., T. W. Lester, and M. Reich (2010). “Minimum Wage Effects Across State Borders: Estimates Using Contiguous Counties.” *Review of Economics and Statistics* 92(4), 945–964. [https://direct.mit.edu/rest/article/92/4/945/57855/Minimum-Wage-Effects-Across-State-Borders](https://direct.mit.edu/rest/article/92/4/945/57855/Minimum-Wage-Effects-Across-State-Borders)

Gulyas, A., S. Seitz, and S. Sinha (2023). “Does Pay Transparency Affect the Gender Wage Gap? Evidence from Austria.” *American Economic Journal: Economic Policy* 15(2), 236–255. [https://www.aeaweb.org/articles?id=10.1257/pol.20210128](https://www.aeaweb.org/articles?id=10.1257/pol.20210128)

Hazell, J., C. Patterson, H. Sarsons, and B. Taska (2022). “National Wage Setting.” *NBER Working Paper* 30623. [https://www.nber.org/papers/w30623](https://www.nber.org/papers/w30623)

Hershbein, B., and L. B. Kahn (2018). “Do Recessions Accelerate Routine-Biased Technological Change? Evidence from Vacancy Postings.” *American Economic Review* 108(7), 1737–1772. [https://www.aeaweb.org/articles?id=10.1257/aer.20161570](https://www.aeaweb.org/articles?id=10.1257/aer.20161570)

Mas, A. (2017). “Does Transparency Lead to Pay Compression?” *Journal of Political Economy* 125(5), 1683–1721. [https://www.journals.uchicago.edu/doi/abs/10.1086/693137](https://www.journals.uchicago.edu/doi/abs/10.1086/693137)

Young, A. (2019). “Channeling Fisher: Randomization Tests and the Statistical Insignificance of Seemingly Significant Experimental Results.” *Quarterly Journal of Economics* 134(2), 557–598. [https://academic.oup.com/qje/article-abstract/134/2/557/5195544](https://academic.oup.com/qje/article-abstract/134/2/557/5195544)

## Data and code availability {#data-and-code-availability}

- **Data.** LinkedIn job postings crawled via Bright Data, acquired by [Chicago Booth’s Center for Applied
AI](https://www.chicagobooth.edu/research/center-for-applied-artificial-intelligence/stories/2026/caai-new-datasets). No derived extract is published here; every figure reports aggregates only.
- **Measurement.** Every figure is generated from artifacts written by a single job over the full corpus. The 500 randomisation draws plotted in Figure 15, and the tabulations behind every other figure, are embedded in the source of this page rather than referenced, so the figures are reproducible without access to the underlying postings.
- **Statutory coding.** Twelve posting-mandate states (CO, CA, WA, NY, HI, DC, MD, IL, MN, NJ, VT, MA), six disclose-on-request states used as a placebo (CT, NV, RI, OH, SC, LA), and thirty-three states with neither. Cincinnati, Toledo and Philadelphia are frequently listed as city posting mandates and are not: the first two require a pay scale on request after a conditional offer, and Philadelphia’s ordinance is a salary-history ban. Philadelphia is used as a placebo in Section 8.2; Cincinnati and Toledo cannot be tested, because Ohio is an on-request state and is excluded from the control group.
