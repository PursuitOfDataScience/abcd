URL: https://youzhi.netlify.app/post/2026-08-09-pay-transparency/pay-transparency/
Title: Pay-Transparency Mandates in 51.9 Million Job Postings: Measurement, Within-Firm Evidence, and Spillover
Date: 2026-08-09
---

Twelve US states now require an employer to publish a pay range in the job advertisement itself. The laws are recent, they were adopted one at a time, and the natural question — whether they actually changed what employers write down — has been hard to answer for a mundane reason: the answer lives in the text of job advertisements, and job advertisements are not a dataset anyone keeps.

This article uses one. Chicago Booth’s Center for Applied AI acquired **51,864,055 LinkedIn job postings**, crawled monthly from February to July 2026, which deduplicate to **23,970,734 distinct postings**, of which **14,250,750 are locatable to a US state**. That is large enough to compare a single employer with itself on two sides of a state line, and to hold the *identical job title* fixed while doing so.

Three findings follow, and the first is a warning about measurement rather than a result about law.

1. **The obvious way to measure disclosure is wrong, and wrong in a way that hides most of the effect.** LinkedIn publishes a structured salary field. Treating it as “the employer disclosed pay” understates the mandate’s effect by a factor of five, because the field mostly measures whether an employer used LinkedIn’s salary widget, not whether it stated a range.
2. **Read the range out of the description text instead and the effect is large and robust.** Within a single firm, comparing its mandate-state postings against its own no-law-state postings, disclosure by any means is **19.1 percentage points** higher. It survives holding the exact job title at the same employer fixed, restricting to firms too large for any statutory exemption to apply, and comparing across a state line inside a single commuting zone.
3. **The law reaches firms in states that do not have one.** Inside no-law states only, firms that also post into at least one mandate state disclose **13.8 pp** more than matched firms that do not — roughly seven-tenths of the effect measured inside the mandate states themselves. An accounting that counts only what happens inside the twelve states misses most of a second effect of similar size.

Every number here is measured on this corpus. Nothing is simulated, and the two things this data cannot support — a time series, and a claim about wages actually paid — are stated plainly at the end.

## Why this has to be a cross-section {#why-this-has-to-be-a-cross-section}

A reader who knows this literature will ask for an event study: watch disclosure jump at the month a mandate takes effect. That design is unavailable here, and it is worth showing why before presenting one that is not.

[figure: Each bar begins when that state's posting mandate took effect. The shaded band is the crawl window.
Every mandate was already in force before the first snapshot, so the corpus contains no pre-period.] Figure 1: Each bar begins when that state’s posting mandate took effect. The shaded band is the crawl window. Every mandate was already in force before the first snapshot, so the corpus contains no pre-period.

The corpus also has no usable internal clock. `job_posted_date` is not recorded when the posting appears; it is re-derived at every crawl from a relative string such as “2 weeks ago”.

`{r fig-drift, fig.height=4.2, fig.cap="Positive means the later crawl described the posting as newer than the earlier crawl did — which is not how time works. The field is a scraping artefact, not an event date."} med <- 6 ggplot(drift_raw, aes(days_lower + 1, share)) + geom_col(aes(fill = days_lower < 0), width = 1.9) + geom_vline(xintercept = med, linetype = "dashed", color = ink_primary, linewidth = 0.5) + annotate("text", x = med + 2.5, y = 13.0, label = "median +6 days", hjust = 0, size = 3.0, color = ink_primary) + annotate("text", x = -57, y = 11.5, label = "reported as\nOLDER\n21.6%", hjust = 0, size = 3.0, lineheight = 0.95, color = pal[["orange"]]) + annotate("text", x = 40, y = 11.5, label = "reported as\nNEWER\n64.8%", hjust = 0, size = 3.0, lineheight = 0.95, color = pal[["blue"]]) + scale_fill_manual(values = c(`TRUE` = pal[["orange"]], `FALSE` = pal[["blue"]]), guide = "none") + scale_x_continuous(breaks = seq(-60, 60, 20), labels = function(x) ifelse(x > 0, paste0("+", x, "d"), paste0(x, "d"))) + scale_y_continuous(labels = function(x) paste0(x, "%")) + labs(title = "The one date field in the corpus is rewritten at every crawl", subtitle = "Change in a posting’s reported posting date between two consecutive monthly crawls", x = "change in reported posting date", y = "share of observations", caption = "27,893,319 consecutive observations of the same posting. A field that moves in both directions\ncannot date anything, and the column that would have been a timestamp is 100% null.") + theme(panel.grid.major.x = element_blank())`

Even if the dates held still, the outcome variable does not.

```{r fig-coverage, fig.height=3.7, fig.cap=“The structured field’s coverage is a property of the crawl, not of employer behaviour. Any disclosure series computed from these six months would be dominated by this line.”} cv <- cov_raw %>% mutate(pct = 100 * with_range / rows)

ggplot(cv, aes(month, pct, group = 1)) + geom_line(linewidth = 1.0, color = pal[[“blue”]]) + geom_point(size = 2.6, color = pal[[“blue”]]) + geom_text(aes(label = sprintf(“%.1f%%”, pct)), vjust = -1.25, size = 3.0, color = ink_secondary) + scale_y_continuous(limits = c(0, 24), labels = function(x) paste0(x, “%”)) + labs(title = “Salary coverage halves over the six snapshots”, subtitle = “Share of rows carrying a structured salary range, by crawl month”, x = NULL, y = “rows with a structured range”, caption = “A disclosure trend computed from this corpus would mostly measure the crawler. This is the secondevery estimate in this article is cross-sectional.”) + theme(panel.grid.major.x = element_blank())

```
What the corpus is excellent for is the opposite design: a very large cross-section in which the same
employer can be observed writing advertisements under two different legal regimes at the same moment.

## What LinkedIn's salary field actually measures

The structured field is not one object. Alongside a range, LinkedIn records a provenance string:
either *"This range is provided by \<employer\>"*, which is the employer's own number, or *"Retrieved
from the description."*, which is LinkedIn's own inference from the text. These are different things,
and pooling them roughly doubles apparent disclosure.

Neither is the same as an employer stating a range in the advertisement. A firm that writes
"\$95,000–\$115,000 per year" in its description and never touches LinkedIn's structured widget is
complying with the law and is invisible to the field.

<div class="figure" style="text-align: center">
<img src="pay-transparency_files/figure-html/fig-measures-1.png" alt="Four progressively broader definitions of the same concept, each measured over all 14,250,750 US
postings. The bold figure at the right of each group is the mandate-minus-no-law gap." width="100%" />
<p class="caption">(\#fig:fig-measures)Four progressively broader definitions of the same concept, each measured over all 14,250,750 US
postings. The bold figure at the right of each group is the mandate-minus-no-law gap.</p>
</div>

The gap the researcher reports is a property of the definition chosen, and it ranges from 5.7 pp to
28.4 pp over the same postings and the same laws. The remainder of this article uses the broadest
honest definition — a range in the structured field *or* a salary-context range in the description
text — and the next section is about earning the right to use it.

## Extracting pay from 133 GB of description text, and validating it

The extractor is deliberately unglamorous: a regular-expression pass over every dollar figure in all
51,864,055 descriptions, which classifies each figure by the words around it, infers the pay period,
and annualises. The classification step is the one that matters, because a job advertisement is full of
dollar figures that are not pay.

```{r fig-extract, fig.height=4.0, fig.cap="Only the salary-context figures are treated as disclosure. A signing bonus, a tuition-aid ceiling and
a 401(k) match all quote dollars, and a measure that counted them would report disclosure where there
is none."}
lab <- c(salary = "salary context\n(counted as disclosure)",
 unknown = "unclassifiable", bonus = "next to a bonus",
 tuition = "next to tuition", other = "other context")
ex <- ext_raw %>%
 mutate(kind = ifelse(ctx == "salary", "counted", "discarded"),
 lab = factor(lab[ctx], levels = rev(lab)),
 pct = 100 * n / sum(n))

ggplot(ex, aes(n / 1e6, lab, fill = kind)) +
 geom_col(width = 0.68) +
 geom_text(aes(label = paste0(comma(n), " ", sprintf("%.1f%%", pct))),
 hjust = -0.06, size = 3.0, color = ink_secondary) +
 scale_fill_manual(values = c(counted = pal[["aqua"]], discarded = base_col),
 guide = "none") +
 scale_x_continuous(limits = c(0, 6.6), labels = function(x) paste0(x, "M")) +
 labs(title = "Most dollar figures in a job advertisement are not pay",
 subtitle = "The 5,737,434 postings whose structured salary field is empty but whose description quotes a range",
 x = "postings", y = NULL,
 caption = "Of 20,238,602 postings with no structured range, 28.3% quote a dollar range somewhere. Classifying\neach figure by its surrounding words is what separates a salary from a signing bonus or tuition aid.") +
 theme(panel.grid.major.y = element_blank(),
 axis.text.y = element_text(size = rel(0.92)))
```

The interesting part is that this corpus can validate the extractor against itself, at a scale no hand audit could reach. **2,244,205 US postings carry both an employer-supplied structured range and the description text that range was typed into.** Those are labelled examples, produced by employers rather than by the researcher.

[figure: Scored against 2,244,205 postings that carry both a structured range and the description it was typed
into. Precision is conditional on the extractor returning a range; recall is over all labelled
postings.] Figure 2: Scored against 2,244,205 postings that carry both a structured range and the description it was typed into. Precision is conditional on the extractor returning a range; recall is over all labelled postings.

Two threats deserve explicit treatment.

**Circularity.** LinkedIn renders its own salary widget into the page. If that rendered text reached the description column, the text measure would be a restatement of the structured field rather than an independent reading of it.

```{r fig-echo, fig.height=4.3, fig.cap=“If the extractor were reading LinkedIn’s own widget back to itself, the rate in the lower panel would be far higher on the left than on the right. It is not.”} ec <- tribble( ~grp, ~v, ~facet, “All rows”, 0.78, “Share of rows carrying LinkedIn’s rendered widget text”, “Rows carrying a dollar figure”, 2.85, “Share of rows carrying LinkedIn’s rendered widget text”, “Postings WITH a structured range”, 0.98, “The same rate, split by whether the structured field is filled”, “Postings WITHOUT a structured range”, 0.76, “The same rate, split by whether the structured field is filled” ) %>% mutate(grp = fct_inorder(grp) %>% fct_rev(), facet = fct_inorder(facet))

ggplot(ec, aes(v, grp, fill = facet)) + geom_col(width = 0.6) + geom_text(aes(label = sprintf(“%.2f%%”, v)), hjust = -0.15, size = 3.05, color = ink_secondary) + facet_wrap(~facet, ncol = 1, scales = “free_y”) + scale_fill_manual(values = c(pal[[“violet”]], pal[[“yellow”]]), guide = “none”) + scale_x_continuous(limits = c(0, 3.6), labels = function(x) paste0(x, “%”)) + labs(title = “The text measure is not a restatement of the structured field”, subtitle = “LinkedIn renders its own salary widget into the page; if that text reached the description, thewould be circular”, x = NULL, y = NULL, caption = “Lower panel from a 40,000-row check. The rate barely moves with the structured field, so the widgetis not what the extractor is reading. Measured, not assumed.”) + theme(panel.grid.major.y = element_blank(), axis.text.y = element_text(size = rel(0.92)))

```
**Recall, not precision, is the binding limitation.** The extractor finds a correct range 89.8% of the
time when it finds one, but it recovers only 58.4% of the ranges known to exist. This corpus cannot
decompose the shortfall: an employer who fills in the structured widget without repeating the number in
the description is indistinguishable from a range the extractor failed to read. Either way the
consequence is the same and it runs in a known direction — every disclosure level reported here is a
**lower bound**, and every gap is attenuated toward zero.

How much does the instrument matter? A cruder first version of this measure was a simple yes/no flag
that only fired on comma-formatted numbers or an explicit hourly rate. Substituting the validated
extractor for it, holding every design below fixed, is a clean test of how much measurement error costs.

<div class="figure" style="text-align: center">
<img src="pay-transparency_files/figure-html/fig-flag-1.png" alt="The same designs estimated twice, changing only how a pay range in the description is detected.
Switching to the validated extractor raises every estimate by 3.8 to 4.4 percentage points, because
the flag it replaces missed a third of the ranges that were present." width="100%" />
<p class="caption">(\#fig:fig-flag)The same designs estimated twice, changing only how a pay range in the description is detected.
Switching to the validated extractor raises every estimate by 3.8 to 4.4 percentage points, because
the flag it replaces missed a third of the ranges that were present.</p>
</div>

One by-product deserves its own figure, because it determines how much statistical power the designs
below have.

<div class="figure" style="text-align: center">
<img src="pay-transparency_files/figure-html/fig-sample-1.png" alt="Postings whose pay range can be annualised, by where the range was found. The text-recovered
observations are not a subset of the structured ones; they are postings that never used the widget." width="100%" />
<p class="caption">(\#fig:fig-sample)Postings whose pay range can be annualised, by where the range was found. The text-recovered
observations are not a subset of the structured ones; they are postings that never used the widget.</p>
</div>

## The raw gap, and why it cannot be the answer

Start with the comparison a reader would make first: put the states side by side.

<div class="figure" style="text-align: center">
<img src="pay-transparency_files/figure-html/fig-states-1.png" alt="Each point is a state, placed by the narrow measure horizontally and the broad measure vertically.
Mandate states sit high on both, but the groups overlap, and states differ in industry, firm and
occupation mix as well as in law." width="100%" />
<p class="caption">(\#fig:fig-states)Each point is a state, placed by the narrow measure horizontally and the broad measure vertically.
Mandate states sit high on both, but the groups overlap, and states differ in industry, firm and
occupation mix as well as in law.</p>
</div>

Two things are visible here. On the broad measure the two legal regimes barely overlap: every mandate
state discloses more than every no-law state. On the structured measure they overlap freely, and several
no-law states outrank mandate states outright — the same measurement point as before, now at the level of
individual jurisdictions. The six disclose-on-request states, which require a range only after a
conditional offer, sit 1.4 pp above the no-law group, which is the right answer for a placebo.

None of that settles anything, because a cross-state comparison is confounded by everything else that
differs across states. California is not Mississippi with a different statute: it has a different
industry mix, different firms and different occupations, all of which move disclosure on their own.

The fix available in this corpus is to stop comparing states and compare a firm with itself.

## Within-firm evidence

The estimator is a within-group treated-minus-control difference: every firm that posts in both a
mandate state and a no-law state contributes its own difference, weighted by the smaller of its two
side counts, so a firm with 4,000 postings in one state and three in the other cannot dominate.
Standard errors are computed across firms.

The concern this design does not by itself answer is occupation. A hospital chain posting nurses in
Texas and engineers in California is being compared with itself across two different jobs. So the
grouping is tightened step by step, ending at the same employer advertising the *same exact job title*
on both sides of the border.

<div class="figure" style="text-align: center">
<img src="pay-transparency_files/figure-html/fig-withinfirm-1.png" alt="Points are the within-group gap; bars span two standard errors either side. The grouping tightens from
the top row downward. The bottom row is a placebo: disclose-on-request states impose no posting duty,
and show essentially nothing on the structured measure." width="100%" />
<p class="caption">(\#fig:fig-withinfirm)Points are the within-group gap; bars span two standard errors either side. The grouping tightens from
the top row downward. The bottom row is a placebo: disclose-on-request states impose no posting duty,
and show essentially nothing on the structured measure.</p>
</div>

Holding the identical job title at the same employer fixed does not reduce the estimate — it raises it
slightly, to +3.78 pp structured and +18.55 pp by any means. Occupation composition inside the firm is
not the mechanism.

### The employer-size objection

Nine of the twelve mandates bind only above an employee-count threshold, from four employees in New
York to fifty in Hawaii, and this corpus has no employee count. Applying the mandate wherever it
nominally covers a state therefore introduces measurement error of unknown sign.

Two answers. First, restrict to firms that posted 500 or more jobs in six months, which are above
fifty employees with near certainty: the estimate is **+3.62 pp**, indistinguishable from the
all-firms figure. Second, and more informative, turn the threshold into a falsification test. If the
thresholds bind, the gap must grow with firm size *faster* in high-threshold states than in states
that cover every employer.

<div class="figure" style="text-align: center">
<img src="pay-transparency_files/figure-html/fig-gradient-1.png" alt="Within-firm gap in employer-supplied disclosure by firm posting volume, splitting the mandate side
by statutory threshold while holding the no-law control side common. If thresholds bound, the
high-threshold line would rise steeply from left to right. It does not." width="100%" />
<p class="caption">(\#fig:fig-gradient)Within-firm gap in employer-supplied disclosure by firm posting volume, splitting the mandate side
by statutory threshold while holding the no-law control side common. If thresholds bound, the
high-threshold line would rise steeply from left to right. It does not.</p>
</div>

There is no gradient and no threshold pattern. Small firms in high-threshold states — nominally exempt
— show as large a gap as anyone else. Two readings are consistent with this and the data cannot
separate them: firms adopt a single national posting policy rather than conditioning on each state's
statute, or posting volume is too weak a proxy for employee count to detect the threshold. Either way,
the correction one might have wanted is not needed.

### One labour market, two legal regimes

A within-firm comparison still spans different local labour markets. The sharpest available design
narrows to a single commuting zone: **26 metropolitan areas straddle a mandate state and a no-law
state**, covering 2,330,018 postings.

<div class="figure" style="text-align: center">
<img src="pay-transparency_files/figure-html/fig-metro-1.png" alt="Metropolitan areas with at least 1,000 postings on each side of the legal border, ordered by size.
Each line connects the no-law share to the mandate share within the same metro. Point size is the
number of postings on the smaller side, which is what the pooled estimate weights by." width="100%" />
<p class="caption">(\#fig:fig-metro)Metropolitan areas with at least 1,000 postings on each side of the legal border, ordered by size.
Each line connects the no-law share to the mandate share within the same metro. Point size is the
number of postings on the smaller side, which is what the pooled estimate weights by.</p>
</div>

```{r fig-metrogap, fig.height=4.0, fig.cap="The border designs sit on either side of the all-US within-firm estimate rather than collapsing
toward zero, which is what a labour-market explanation would require."}
mg <- tribble(
 ~design, ~outcome, ~gap, ~se,
 "Within firm (all US)", "y_emp", 3.62, 0.53,
 "Within metro", "y_emp", 4.54, 0.70,
 "Within firm and metro", "y_emp", 3.22, 0.51,
 "Within firm (all US)", "y_any4", 19.07, 0.97,
 "Within metro", "y_any4", 20.30, 1.76,
 "Within firm and metro", "y_any4", 15.97, 0.90
) %>%
 mutate(design = factor(design, levels = rev(c("Within firm (all US)", "Within metro",
 "Within firm and metro"))),
 ref = design == "Within firm (all US)",
 outcome = factor(recode(outcome, y_emp = "Employer-supplied range",
 y_any4 = "Disclosed by any means"),
 levels = c("Employer-supplied range", "Disclosed by any means")))

ggplot(mg, aes(gap, design, color = ref)) +
 geom_errorbarh(aes(xmin = gap - 2 * se, xmax = gap + 2 * se), height = 0,
 linewidth = 0.9) +
 geom_point(size = 3.0) +
 geom_text(aes(label = sprintf("%+.2f", gap)), vjust = -1.15, size = 2.85,
 show.legend = FALSE) +
 facet_wrap(~outcome, scales = "free_x") +
 scale_x_continuous(expand = expansion(mult = c(0.16, 0.16)),
 labels = function(x) paste0(x, " pp")) +
 scale_color_manual(values = c(`TRUE` = ink_muted, `FALSE` = pal[["blue"]]),
 guide = "none") +
 labs(title = "Narrowing to one labour market does not remove the gap",
 subtitle = "Grey is the all-US within-firm estimate for reference; blue restricts to the 26 border metros",
 x = NULL, y = NULL,
 caption = "Bars span two standard errors either side. “Within firm and metro” is the same employer advertising\non both sides of one legal border. The two panels use different scales.") +
 theme(panel.grid.major.y = element_blank())
```

Narrowing to one commuting zone leaves the structured-field gap slightly *larger* and the broad gap slightly smaller, and both remain far from zero. Whatever the border is picking up, it is not a difference between labour markets.

### How surprising is this? Randomisation inference {#how-surprising-is-this-randomisation-inference}

The on-request placebo is one null. A sharper one asks what a gap of this size looks like when the “mandate” is fictional: draw twelve fake mandate states at random from the forty-five jurisdictions without an on-request law, recompute the entire within-firm estimate, and repeat five hundred times.

[figure: Distribution of the within-firm gap under 500 random assignments of twelve fake mandate states,
requiring 20 postings per side as the real estimate here does. The vertical dashed line marks the real
assignment; the panels are on different scales.] Figure 3: Distribution of the within-firm gap under 500 random assignments of twelve fake mandate states, requiring 20 postings per side as the real estimate here does. The vertical dashed line marks the real assignment; the panels are on different scales.

The placebo distributions are centred on zero and their extremes fall well short of the real estimate, so the result is not an artefact of twelve states happening to differ from thirty-three in some way a within-firm comparison cannot absorb.

## The result that is about policy rather than about identification {#the-result-that-is-about-policy-rather-than-about-identification}

Within-firm differencing removes spillover by construction: if a firm exposed to a mandate somewhere changes its posting policy everywhere, that change is differenced away. So the policy-relevant question has to be asked separately, and it is the one a legislator would actually ask. Does a mandate change behaviour in states that never passed one?

Restrict attention to postings in no-law states only. Compare firms that also post into at least one mandate state against firms that do not, matching on state × industry × firm-size cells so the comparison is not simply national firms against local ones.

[figure: Inside no-law states only. Points are the raw disclosure shares of the two groups of firms; the bold
label is the difference after matching on state, industry and firm size, with two standard errors
either side. Matching moves the raw difference very little, in either direction.] Figure 4: Inside no-law states only. Points are the raw disclosure shares of the two groups of firms; the bold label is the difference after matching on state, industry and firm size, with two standard errors either side. Matching moves the raw difference very little, in either direction.

A firm exposed to a posting mandate anywhere discloses **13.8 pp more in states with no law at all** — against a within-firm cross-border estimate of 19.1 pp on the same outcome. Counting disclosure only inside the twelve mandate states therefore misses an effect not much smaller than the one it counts.

The caveat is real and belongs in the same breath: this is an association, not a causal estimate. Firms choose which states to enter, and a national employer differs from a local one in ways matching on state, industry and size does not capture. A clean spillover design needs the timing of a firm’s entry into a mandate state, which this corpus does not contain.

## Two negative results {#two-negative-results}

Negative results are the part of an empirical exercise most likely to go unreported and most likely to be useful, so both are stated with the same weight as the findings above.

**Mandates do not produce wider, less informative ranges.** This is the standard compliance-quality worry: told to publish a range, an employer publishes “$40,000 to $400,000”.

[figure: Width of an employer-supplied range relative to its midpoint. Mandated ranges look narrower in the
raw comparison, and within firm the difference vanishes.] Figure 5: Width of an employer-supplied range relative to its midpoint. Mandated ranges look narrower in the raw comparison, and within firm the difference vanishes.

The raw ordering runs the opposite way to the worry, and within firm it disappears entirely. There is no evidence of range inflation under a mandate, and none of improvement either — the compliance-quality concern is simply not visible in this corpus, in either direction.

**City-level designs pick up composition.** Several ordinances are often listed as city posting mandates and are not. Philadelphia’s is a salary-*history* ban, which places no duty on the advertisement, so it should show nothing.

[figure: Philadelphia against the rest of Pennsylvania, neither of which has a posting mandate. The structured
measure behaves correctly and shows nothing; the broad measure manufactures an effect.] Figure 6: Philadelphia against the rest of Pennsylvania, neither of which has a posting mandate. The structured measure behaves correctly and shows nothing; the broad measure manufactures an effect.

The spurious estimate is roughly two-fifths the size of the genuine within-firm one — large enough to be mistaken for a real effect by anyone who had not checked. This is not an argument against the broad measure, which is validated and which the structured measure cannot replace. It is an argument against assigning treatment at city level in this corpus, where a large city differs from its own state in industry and firm composition far more than it differs in law.

## What this cannot say {#what-this-cannot-say}

- **These are posted advertisements.** No hire is observed, no wage is paid, and no worker appears in the data. Nothing here speaks to whether posted ranges match realised pay, or to the wage effects of transparency, which is the question most of the literature is actually about.
- **This is a cross-section, not an event study.** All twelve mandates predate the first snapshot. The estimates are differences in the level of disclosure under two regimes at one moment; they are not estimates of a change over time, and they inherit whatever selection puts a firm in one state rather than another. The within-firm and within-metro designs narrow that selection considerably; they do not eliminate it.
- **Every level is a lower bound.** The text measure recovers 58.4% of ranges known to exist, so disclosure is understated throughout and the gaps are attenuated.
- **Coverage is shaped by the crawler.** The corpus is what Bright Data’s `discovery_input` reached, which became markedly more targeted across the window. Nothing here is nationally representative, and no month-over-month magnitude should be read from it.
- **The spillover result is an association.** Firms self-select into mandate states.

## What would settle it {#what-would-settle-it}

The design this corpus makes visible but cannot execute is a before-and-after. Every component it needs now exists and has been validated on the full corpus: the extractor, the statutory coding, the within-firm estimator, the metro crosswalk. What is missing is time. Continued monthly collection turns each estimate above from a difference in levels into an event study on the same firms with the same instrument, and would do so for any state that adopts a mandate inside that window.

That is a recommendation about collection rather than about analysis, and it is the most useful thing this exercise produced. The measurement lesson generalises further: on any corpus of this kind, the structured field is a record of which employers used a platform feature, and the text is the record of what they were willing to say. Those are not the same variable, and only one of them is the object the law addresses.

## Reproducibility and access {#reproducibility-and-access}

- **Data.** LinkedIn job postings crawled via Bright Data, acquired by [Chicago Booth’s Center for
Applied
AI](https://www.chicagobooth.edu/research/center-for-applied-artificial-intelligence/stories/2026/caai-new-datasets). No derived extract is published here; every figure reports aggregates only.
- **Measurement.** Every figure above is generated from artifacts written by a single job over the full corpus; the extractor, the within-group estimator and the randomisation loop are the same code that produced the project’s internal findings. The 500 randomisation draws plotted above are embedded in the source of this page rather than referenced, so the figures are reproducible without access to the underlying postings.
- **Statutory coding.** Twelve posting-mandate states (CO, CA, WA, NY, HI, DC, MD, IL, MN, NJ, VT, MA), six disclose-on-request states used as a placebo (CT, NV, RI, OH, SC, LA), and thirty-three states with neither. Cincinnati, Toledo and Philadelphia are frequently listed as city posting mandates and are not: the first two require a pay scale on request after a conditional offer, and Philadelphia’s ordinance is a salary-history ban. Philadelphia is therefore used as a placebo above; Cincinnati and Toledo cannot be tested, because Ohio is an on-request state and is excluded from the control group.
