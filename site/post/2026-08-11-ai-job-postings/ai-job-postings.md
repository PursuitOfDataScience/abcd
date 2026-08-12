URL: https://youzhi.netlify.app/post/2026-08-11-ai-job-postings/ai-job-postings/
Title: Counting Artificial Intelligence in 51.9 Million Job Postings: Measurement, Rotation, and Firm Adoption
Date: 2026-08-11
---

**Abstract.** Public discussion of the artificial-intelligence labour market rests on counts of “AI jobs”, but the counting itself is rarely examined. Using **51,864,055 LinkedIn job postings** collected monthly from February to July 2026 (23,970,734 of them distinct), I show that three quantities routinely conflated differ by a factor of six: **10.4 %** of postings mention AI, **3.8 %** ask the holder to build it, and **1.7 %** are AI jobs by title. Two corrections are needed to get there. Roughly one in seven “AI” postings mentions AI only inside a sentence about how applications are screened, and a single tutoring company accounts for **102 %** of the apparent April surge in AI postings. What survives is a clear rotation: the vocabulary of *building* models is falling and the vocabulary of *using* them is rising, a pattern visible inside individual re-scraped adverts, inside individual firms (**91 %** of the movement is within-firm), and in which AI occupations are posted at all. An AI advert pays **18.7 %** more than the same employer’s other adverts, but only **4.1 %** once the ordinary skills that travel with AI are also held fixed, and the premium is largest where AI is rarest across employers. Firms that begin advertising AI shift their *other* hiring away from entry level by **1 to 2 percentage points**, an estimate correctly signed in **98.6 %** of 288 specifications and separated from ordinary technology adoption by a battery of non-AI placebos, though it is not causally identified.

## 1. Introduction {#introduction}

Almost every claim about artificial intelligence and work depends on a count of AI jobs, and almost none of them says what was counted. The question sounds trivial. It is not. A job advertisement is a document written to attract applicants, and the phrase “artificial intelligence” can appear in it for at least four unrelated reasons: because the job is to build AI systems, because the holder will be expected to use AI tools, because the employer wishes to describe itself as innovative, or because a lawyer has added a paragraph disclosing that AI is used to screen applications. Only the first two are about the job.

This article measures all four in a large corpus and shows that separating them changes the headline number by a third, reverses the direction of several widely quoted trends, and turns one apparent national surge into a single company’s recruitment campaign.

### 1.1 Contribution {#contribution}

Four things, in order of how much I think they matter.

1. **A measurement result.** One in seven postings that mention AI mentions it only in a sentence about the hiring process, and **three in five** postings containing the phrase “artificial intelligence” lose it when such sentences are removed. The contamination is very uneven: it removes 47 % of manufacturing’s apparent AI exposure against 10 % of engineering’s.
2. **A campaign, not a trend.** The April 2026 spike in AI postings is one online tutoring marketplace. Removing gig advertisements removes 102 % of April’s excess over July. The same company is 43 % of the entire AI gig stratum.
3. **A rotation, established three ways.** Language describing the construction of models is falling and language describing the use of models is rising. The result holds in a composition-adjusted concept panel, inside individual adverts that were edited between scrapes, and in a shift-share decomposition showing that **91 %** of it happens inside firms rather than through firms entering and leaving.
4. **Two stress-tested economic results.** The within-firm AI pay premium is positive in **100 %** of 576 specifications, and the shift of adopting firms toward senior hiring is correctly signed in over 98 % of 576 specifications with none significant in the wrong direction.

### 1.2 Terminology {#terminology}

An *AI mention* is a posting whose text contains any of 87 disambiguated AI concepts. An *AI builder* posting names AI engineering work specifically: frameworks, retrieval systems, fine-tuning, agents, model serving, evaluation. An *AI job* is one whose job title says so. *Gig* postings are those whose text advertises hourly, freelance or self-scheduled work. All figures below exclude gig postings unless stated.

## 2. Data {#data}

The corpus is 528 GB of LinkedIn job advertisements scraped monthly between February and July 2026 and acquired by Chicago Booth’s Center for Applied Artificial Intelligence. There are 51,864,055 rows and 23,970,734 distinct postings; the difference is that a posting still live at the next crawl is collected again, which turns out to be useful. Two limitations are structural and apply to everything that follows. These are **posted advertisements**, so no hire, no wage paid and no worker appears anywhere. And nothing is nationally representative: coverage reflects what the crawler reached, and the country mix moves month to month.

## 3. What is actually being counted {#what-is-actually-being-counted}

### 3.1 The words that break {#the-words-that-break}

Matching AI vocabulary in employer-written prose is harder than it looks, and this corpus is not monolingual: the language detector splits it across 88 labels, 34 of them carrying at least a thousand postings. Five failures were large enough to change results and are worth stating because any replication will hit them.

`LLM` is the Master of Laws degree: 385,286 postings carry legal-degree language. `Transformer` is a piece of electrical plant, so the concept is matched only as “transformer model” or “transformer architecture”, which leaves 3,692 postings rather than orders of magnitude more. `Copilot` is the person in an aircraft’s right-hand seat. `Claude`, `Gemini`, `Llama` and `Mistral` are a French given name, a zodiac sign, a farm animal and a wind; each is counted only when the document contains independent AI evidence elsewhere, a rule that a 200-case hand audit found correct **99.0 %** of the time. Lowercase `ai` is the Italian preposition, which is why the acronym is matched case-sensitively: in Italian the case-insensitive rate is **6.4 times** the case-sensitive one.

The reverse errors matter too. An early version of the title classifier scored *AML Manager* (anti-money-laundering) and *HTML Developer* as AI jobs, from a missing word boundary, and *ML06*, an internal grade code, from a lookahead that excluded letters but not digits.

### 3.2 The paragraph that is not about the job {#the-paragraph-that-is-not-about-the-job}

The largest problem was invisible to the hand-built vocabulary and was found by an open-vocabulary pass that ranked all 470,498 candidate terms by how much they distinguish an AI posting from a non-AI one. Among the strongest markers were `hiring decisions`, `may use`, `we may` and `made by`. Those are not skills. They are this paragraph:

“We may use artificial intelligence (AI) tools to support parts of the hiring process, such as reviewing applications, analyzing resumes, or assessing responses. These tools assist our recruitment team but do not replace human judgment. Final hiring decisions are ultimately made by humans.”

A warehouse advertisement carrying that sentence contains the words “artificial intelligence” and “AI tools” and is therefore counted as an AI posting. Re-running the scanner over all 51.9 million documents with such sentences removed shows how much of the headline this is.

[figure: For each job function, the share of its AI postings that mention AI only inside a sentence about how applications are screened. Removing those sentences alone takes the corpus AI-mention rate from 13.61 % to 11.62 %, which is 14.6 % of all AI postings. Postings that mention AI only this way carry a within-firm pay premium of -1.55 % (standard error 1.91), that is, none at all.] Figure 1: For each job function, the share of its AI postings that mention AI only inside a sentence about how applications are screened. Removing those sentences alone takes the corpus AI-mention rate from 13.61 % to 11.62 %, which is 14.6 % of all AI postings. Postings that mention AI only this way carry a within-firm pay premium of -1.55 % (standard error 1.91), that is, none at all.

Nearly half of manufacturing’s apparent AI exposure is a recruiting-compliance paragraph. Any claim that AI has reached the factory floor, if it is built on counting mentions, has to clear this first. The correction validates itself on pay: postings that mention AI *only* this way show no within-firm pay premium at all, a precisely estimated zero, while removing them raises the premium for everything else.

### 3.3 One company’s campaign {#one-companys-campaign}

The second correction is larger and stranger. Advertisements that read as gig work (hourly rate, freelance, self-scheduled) are 14.8 % of the corpus but were **35.7 %** of April’s AI postings.

[figure: AI-mention rate among postings appearing for the first time in each month, as measured and after removing gig advertisements. April exceeds July by 4.14 percentage points as measured; with gig postings excluded July is 0.07 points higher instead, so the removal accounts for the whole of the gap. A single employer, an online tutoring marketplace, accounts for 215,439 postings, which is 43.4 % of the entire AI gig stratum.] Figure 2: AI-mention rate among postings appearing for the first time in each month, as measured and after removing gig advertisements. April exceeds July by 4.14 percentage points as measured; with gig postings excluded July is 0.07 points higher instead, so the removal accounts for the whole of the gap. A single employer, an online tutoring marketplace, accounts for 215,439 postings, which is 43.4 % of the entire AI gig stratum.

An entirely separate check found the same thing without being told to look. Scoring all 161,535 frequent open-vocabulary terms on persistence, every one of the fourteen largest transient phrases in the corpus comes from this single advertisement: “adaptive instruction”, “subject mastery”, “concepts students commonly struggle”, “explain material”. The phrase “tutor copilot” appears in 258,785 postings. This also explains a result that looked substantive: `Copilot` appears to be *falling* 20 % over the clean window until gig postings are removed, after which it is *rising* 29 %.

The practical consequence is uncomfortable. The window this corpus is usually analysed over begins in April, precisely because February behaves differently. April is the worst month to anchor on for AI.

### 3.4 How much to trust the measure {#how-much-to-trust-the-measure}

Two independent checks. First, the title-based and text-based classifiers were built separately and agree: **97.4 %** of postings whose *title* is an AI role also mention AI in the text, before any boilerplate is stripped, and 93.9 % after. Second, a labelled evaluation set of 873 postings, drawn from 300,000 and over-sampled twelve-fold on disagreements, was scored against a deliberately different reference built from phrases absent from the main vocabulary.

The reference initially implies 84.9 % recall, that is, 1,338 postings out of the 300,000 scanned carry strong independent evidence and are still called non-AI. Reading all 28 sampled cases shows the reference is what is wrong. Nine matched visibly non-AI text: “building our **talent pipeline**”, “the approved **training model** of explain, demonstrate, practice”, “**Late-Model** Equipment”, “building robust **financial models**”. The remaining titles are Kindergarten Paraprofessional, Retail Store Supervisor, Remote Therapist, Senior FP&A Analyst. Exactly one of 28 is a genuine miss, a machine-learning engineering role whose text says “ML driven solutions” and never spells the words out.

“Model” is the dangerous word. Any AI detector built on *build, train or deploy* plus *model* is swamped by finance. Measured against the independent title taxonomy, the text measure misses **2.6 %** of AI-titled postings, and no available fix is worth its cost: promoting the bare `ML` acronym to a qualifying term would add 13,648 postings to recover 711.

## 4. Three numbers, not one {#three-numbers-not-one}

[figure: The corrections, and the three quantities they leave behind, on the same 23,970,734 distinct postings. The blue bar is the same 10.38 % in both panels: the bottom panel starts where the top one ends. Hiring-process sentences account for 1.99 of the 3.24 percentage points removed, company blurb and benefits sentences for 0.71, gig advertisements for the remaining 0.54. The lower two bars are near-subsets of the blue one rather than strict ones: 93.5 % of building postings and 93.9 % of AI-titled postings also mention AI in their text, so the three together cover 10.72 % of postings.] Figure 3: The corrections, and the three quantities they leave behind, on the same 23,970,734 distinct postings. The blue bar is the same 10.38 % in both panels: the bottom panel starts where the top one ends. Hiring-process sentences account for 1.99 of the 3.24 percentage points removed, company blurb and benefits sentences for 0.71, gig advertisements for the remaining 0.54. The lower two bars are near-subsets of the blue one rather than strict ones: 93.5 % of building postings and 93.9 % of AI-titled postings also mention AI in their text, so the three together cover 10.72 % of postings.

The two panels are one chain, and the blue bar appears in both: the corrected mention rate of **10.38 %** is where the first panel ends and what the second panel breaks apart. It is lower than the 13.61 % above it because it is the same measure after the two corrections, not a wider one. Within it, building and AI-titled postings are near-subsets rather than strict ones, because a posting can name a vector database or a fine-tuning framework without ever using a word general enough to count as an AI mention. That accounts for about one in fifteen of each.

The gap between the top and bottom bars is the whole difficulty. Mentioning AI is common; being an AI job is rare. Reading the position of the mention in the document confirms the distinction is real rather than an artefact of thresholds: in postings classified as AI-building the first AI word appears **5 %** of the way through the text, because it is what the job is, and it is named inside a bullet point 79 % of the time. In postings classified as a passing mention it appears **34 %** of the way through and reaches a bullet only 31 % of the time.

## 5. The rotation {#the-rotation}

### 5.1 What is rising and what is falling {#what-is-rising-and-what-is-falling}

Monthly shares are reweighted so that each month has the same industry, function, seniority and language mix as the pooled corpus, which prevents a change in what the crawler collected from masquerading as a change in demand. A concept is reported as moving only if the sign is identical across three different windows and at least 95 % of 1,000 firm-block bootstrap resamples reproduce it.

[figure: Change in the composition-adjusted share of postings between April and July 2026, for the 34 of 87 AI concepts whose direction is stable across three windows and at least 95 % bootstrap-confident. Boilerplate-free, gig-free. The falling set is methods, frameworks, research fields, older model families and the general analytics stack; the rising set is assistants, agents, vendor products and the governance and adoption of AI. Nothing falling names an assistant or an agent, and nothing rising names a training framework.] Figure 4: Change in the composition-adjusted share of postings between April and July 2026, for the 34 of 87 AI concepts whose direction is stable across three windows and at least 95 % bootstrap-confident. Boilerplate-free, gig-free. The falling set is methods, frameworks, research fields, older model families and the general analytics stack; the rising set is assistants, agents, vendor products and the governance and adoption of AI. Nothing falling names an assistant or an agent, and nothing rising names a training framework.

The split is clean in both directions: not one of the 15 falling concepts names an assistant or an agent, and not one of the 19 rising concepts names a training framework. This is not a story about AI shrinking. Over the same window the composite AI-mention series rises **8.5 %** with bootstrap agreement of 1.000. The rotation is in *which* AI words employers use, not in how many postings use one. It is also not a race between builders and users: the two composites move almost identically over the clean window, +8.1 % for builders against +7.9 % for users, and only the user series is sign-stable enough to call.

### 5.2 The same advertisement, edited {#the-same-advertisement-edited}

A posting still live at the next crawl is scraped again, which makes the advertisement its own control: employer, title, function, level and location are fixed by construction, and only the text can move. Of 11,396,051 postings seen more than once, only 7.9 % show any change in length at all. Within that churn, AI concepts are added far more often than removed.

[figure: Net change in the share of the same advertisement carrying each concept, comparing its first and last scrape, on boilerplate-free text. Employer, title, level and location are fixed by construction. The generic analytics stack is the placebo: it is drawn from the same documents and the same scrape process.] Figure 5: Net change in the share of the same advertisement carrying each concept, comparing its first and last scrape, on boilerplate-free text. Employer, title, level and location are fixed by construction. The generic analytics stack is the placebo: it is drawn from the same documents and the same scrape process.

The placebo is the point. A generic technology bundle of SQL, Python and Tableau, drawn from the same documents and subject to the same scraping noise, moves by **-0.02 %**. Responsible-AI language moves by **+5.19 %**. What employers retro-fit into an existing advertisement is not model names: the two fastest insertions are a claim that AI improves efficiency and language about fairness and bias.

### 5.3 Inside firms, not between them {#inside-firms-not-between-them}

The rotation could be the same employers changing their minds, or simply a change in which employers are posting. Over a six-month crawl the second would largely be a sampling story. A shift-share decomposition over the 12,353 firms with at least three AI postings in both February to March and June to July, which together account for about three quarters of AI postings in each period, separates them.

[figure: Decomposition of the change in each concept group's share among AI postings, February to March against June to July, over the 12,353 firms posting at least three AI advertisements in both periods. The within-firm component is the same employers changing what they ask for; the between-firm component is the reallocation of posting volume across employers; the cross term is the interaction of the two. The four bars sum to the total change, -27.1 points for building and +43.5 for using.] Figure 6: Decomposition of the change in each concept group’s share among AI postings, February to March against June to July, over the 12,353 firms posting at least three AI advertisements in both periods. The within-firm component is the same employers changing what they ask for; the between-firm component is the reallocation of posting volume across employers; the cross term is the interaction of the two. The four bars sum to the total change, -27.1 points for building and +43.5 for using.

Measured against the movement among firms present in both periods, which is the within, between and cross terms together, **91 %** of the fall in building vocabulary and **85 %** of the rise in using vocabulary is the same employers changing what they ask for. Firms entering and leaving the corpus contribute about one percentage point.

### 5.4 And in which jobs are posted {#and-in-which-jobs-are-posted}

The rotation is not only what advertisements say. Crossing the role taxonomy, which sorts AI job titles into nineteen subtypes, with growth shows it in the occupational structure itself.

[figure: Change in each AI job subtype's share of all AI-titled postings, February to March against June to July, with the median advertised salary. Point size is the number of postings. The fifteen subtypes with at least 3,000 postings are shown, including the residual 'AI other' bucket. Seven of the eight shrinking subtypes are model-building occupations; the eighth is internships.] Figure 7: Change in each AI job subtype’s share of all AI-titled postings, February to March against June to July, with the median advertised salary. Point size is the number of postings. The fifteen subtypes with at least 3,000 postings are shown, including the residual ‘AI other’ bucket. Seven of the eight shrinking subtypes are model-building occupations; the eighth is internships.

Machine-learning engineering falls by 4.8 percentage points of all AI jobs and is posted at 0.72 times its earlier rate; AI architecture doubles. Reading the vocabulary that distinguishes each subtype, the growing occupations ask either for governance, transformation and consulting, as AI leadership and AI architecture do, or for agents and assistants, as AI engineering does. The shrinking ones ask for PyTorch, reinforcement learning and quantization. Notably, **AI leadership now advertises a higher median salary than machine-learning engineering**, and the doctorate requirement varies enormously across these jobs: 62 % of AI-research postings ask for one, against 3 % of AI-product postings.

## 6. What AI is worth in an advertisement {#what-ai-is-worth-in-an-advertisement}

### 6.1 Four numbers, not one {#four-numbers-not-one}

Advertised pay is read out of the description text by an extractor validated at 89.8 % precision, which covers 27 % of postings. Each rung below adds a control.

[figure: The AI pay premium at four levels of control, excluding gig postings. Each rung compares an AI advertisement with a non-AI advertisement that is more nearly identical to it. The final rung adds 269 individually named skills from an independent vocabulary.] Figure 8: The AI pay premium at four levels of control, excluding gig postings. Each rung compares an AI advertisement with a non-AI advertisement that is more nearly identical to it. The final rung adds 269 individually named skills from an independent vocabulary.

Roughly three quarters of the raw gap is which employer is hiring. Half of what remains is which function and level the job is. Over half of what survives that is the ordinary bundle of Python, cloud platforms and SQL that travels with AI work. **The irreducible return to AI content itself, holding the employer, the function, the level and 269 named skills fixed, is about 4 %.**

### 6.2 Across employers, the premium is largest where AI is rarest {#across-employers-the-premium-is-largest-where-ai-is-rarest}

[figure: Within-firm AI pay premium against how common AI is in the unit. Orange points are the 22 industries with at least 100,000 postings, of which eight are labelled; their rank correlation is -0.25. The blue line joins quintiles of firms by their own AI intensity, with 95 % intervals; the two least AI-intensive quintiles contain no estimable firm and are absent. The horizontal dashed line marks the corpus-wide within-firm premium of 18.7 %.] Figure 9: Within-firm AI pay premium against how common AI is in the unit. Orange points are the 22 industries with at least 100,000 postings, of which eight are labelled; their rank correlation is -0.25. The blue line joins quintiles of firms by their own AI intensity, with 95 % intervals; the two least AI-intensive quintiles contain no estimable firm and are absent. The horizontal dashed line marks the corpus-wide within-firm premium of 18.7 %.

At an employer where fewer than one posting in a hundred mentions AI, an AI advertisement offers **65 %** more than its neighbours. At an employer where nearly two in five do, it offers **18 %**. The three populated quintiles fall in strict order; the two least AI-intensive quintiles contain no firm that prices enough of both kinds of posting to estimate, so this is a three-point pattern rather than a five-point one.

Across industries the same relationship is present but much weaker, at a rank correlation of **-0.25** over the 22 industries shown. Retail is the extreme case that fits, with the lowest AI share and by far the largest premium, and banking and manufacturing also pay well above the corpus figure at modest AI shares. But the pattern does not hold at the other end: the two smallest premiums belong to government administration and defence, neither of them AI-saturated, and software development sits in the middle of the distribution rather than at the bottom. The firm-level ordering is the evidence here; the industry scatter is consistent with it and no more.

A compensating differential for a scarce skill would produce the firm-level pattern. Rent-sharing would predict the opposite, with the largest premiums at the firms most saturated with AI, and that is not what the quintiles show.

### 6.3 Within the firm, AI raises the floor {#within-the-firm-ai-raises-the-floor}

[figure: AI premium at matched quantiles of the same employer's own pay distribution, averaged over the 4,033 firms that price at least eight AI and eight non-AI postings and weighted by the smaller side. The comparison is entirely within employers, so it is not a composition effect.] Figure 10: AI premium at matched quantiles of the same employer’s own pay distribution, averaged over the 4,033 firms that price at least eight AI and eight non-AI postings and weighted by the smaller side. The comparison is entirely within employers, so it is not a composition effect.

Inside a single employer the AI premium falls by a factor of 2.7 from the bottom of its pay distribution to the top. Whatever AI is doing to advertised pay, it is not fattening the upper tail.

## 7. Firms that begin advertising AI {#firms-that-begin-advertising-ai}

The corpus permits one quasi-longitudinal design. Among 53,197 firms with at least eight postings in February to March and eight in June to July, an *adopter* posted no AI advertisements in the first period and at least one in the last. The outcome is measured on the firm’s **own non-AI postings**, so nothing is mechanical, with firm and industry-by-month fixed effects and standard errors clustered on the firm.

On the 6,500 firms that adopt the boilerplate-free AI measure, the estimate is a shift of **1.2 percentage points** away from entry-level roles and **1.6 points** toward senior ones. Across all 288 variants of the design the entry estimate has a median of 1.7 points, which is the figure quoted in the abstract; the two numbers are the same result at different settings, and Section 7.1 shows the whole distribution. The obvious objection is that this describes any firm adopting any new technology. It does not.

[figure: The same design applied to non-AI technology adoptions. In every row a firm 'adopts' the named concept between February to March and June to July, and the outcome is measured on the firm's postings that do not contain it. Bars show 95 % intervals. The senior panel is the discriminating test.] Figure 11: The same design applied to non-AI technology adoptions. In every row a firm ‘adopts’ the named concept between February to March and June to July, and the outcome is measured on the firm’s postings that do not contain it. Bars show 95 % intervals. The senior panel is the discriminating test.

A firm that starts mentioning Snowflake does not tilt senior. A firm that starts mentioning AI does, with a t-statistic of 4.33 against at most 1.40 for every non-AI placebo. Three further checks point the same way. Matching adopters to controls on baseline entry share, industry and size cuts the baseline imbalance from 9.5 to 1.6 percentage points and moves the estimate from -1.2 to **-2.0**, that is, further from zero rather than toward it. Only 36 of 6,519 AI adopters also adopted the hiring-disclosure paragraph, which rules out the possibility that “adoption” is an applicant-tracking-system upgrade. And the effect scales with how much AI the firm ends up posting.

[figure: Entry-level effect by how much AI the adopting firm ends up posting in the final period, with 95 % intervals. A fifth bin covering firms above 30 % AI contains 436 firms with a standard error of 2.94 and is omitted as uninformative.] Figure 12: Entry-level effect by how much AI the adopting firm ends up posting in the final period, with 95 % intervals. A fifth bin covering firms above 30 % AI contains 436 firms with a standard error of 2.94 and is omitted as uninformative.

### 7.1 Both results under every defensible specification {#both-results-under-every-defensible-specification}

Reporting an estimate at a handful of specifications chosen by the analyst invites the suspicion that others were tried. Both load-bearing results were therefore re-run at every combination of the choices available.

[figure: Both load-bearing results across every defensible combination of analyst choices. Top: the within-firm AI pay premium across 576 specifications, varying the AI measure, gig inclusion, duplicate handling, language, geography, control set and minimum firm size, grouped by control set. Bottom: the entry and senior effects across 576 specifications, varying the treatment measure, gig inclusion, adoption threshold, balance requirement, control set and sample. Light bars span the full range, dark bars the interquartile range where available, and points mark medians.] Figure 13: Both load-bearing results across every defensible combination of analyst choices. Top: the within-firm AI pay premium across 576 specifications, varying the AI measure, gig inclusion, duplicate handling, language, geography, control set and minimum firm size, grouped by control set. Bottom: the entry and senior effects across 576 specifications, varying the treatment measure, gig inclusion, adoption threshold, balance requirement, control set and sample. Light bars span the full range, dark bars the interquartile range where available, and points mark medians.

The pay premium is positive in every one of 576 specifications, and the only analyst choice that moves it materially is how much of function and seniority is absorbed. Restricting the corpus to English-language postings changes the median by 0.003 percentage points. For the hiring shift, 98.6 % of entry specifications are negative and 99.3 % of senior specifications are positive, and **not one of the 576 is statistically significant in the wrong direction**.

### 7.2 What this is, and is not {#what-this-is-and-is-not}

It is not a causal estimate. Firms choose when to start advertising AI; the window is six months; and the difference between adopters and non-adopters was already moving by 1.7 percentage points between February and March, before any adoption is measured. A staggered event study using firms that adopt later as controls does show a clean sign break at the moment of adoption, with pre-period differences running in the *opposite* direction to the estimated effect, which is the reassuring direction for a violation to run. The honest description is a well-identified association with placebo and dose support, not an effect.

## 8. Four things that are not happening {#four-things-that-are-not-happening}

Negative results are cheap to omit and expensive to rediscover, so they are worth stating.

**There is no visible AI talent shortage.** Across 27,323 firms, those posting a higher share of AI advertisements receive *more* applicants per posting, not fewer (rank correlation +0.33). Within firm, function and level, an AI advertisement survives between -0.03 and +0.05 additional monthly snapshots, which is zero on a six-snapshot scale. If AI roles were unusually hard to fill, they would stay open longer and attract fewer applicants. Neither appears.

**The junior end of the AI market is crowded, not empty.**

[figure: Difference in applicant counts between AI and non-AI advertisements at the same firm, function and seniority, with 95 % intervals. Only the usable 26 to 199 applicant band is counted. Median applicants at entry level are 63 for an AI advertisement against 50 for a non-AI one.] Figure 14: Difference in applicant counts between AI and non-AI advertisements at the same firm, function and seniority, with 95 % intervals. Only the usable 26 to 199 applicant band is counted. Median applicants at entry level are 63 for an AI advertisement against 50 for a non-AI one.

**The AI internship collapse is seasonal.** Internship postings inside AI fall 33.8 % between April and July, which reads as the pipeline closing until the control is examined: *all* internship postings fall 31.7 % over the same window. The difference is 2.1 percentage points, which is nothing. The composition adjustment used throughout corrects for industry, function, seniority and language, and there is no calendar control anywhere in this corpus.

**Employers almost never write that AI is replacing anyone.** Across 23,970,734 distinct postings, 277 of them, or 0.001 %, name AI or automation as replacing roles, headcount or staff. The displacement narrative is essentially absent from advertisement text. This is a fact about what employers write, not about what they do.

## 9. Two things that are worth noticing {#two-things-that-are-worth-noticing}

**The junior AI rung is credential-gated rather than closed.** An entry-level AI posting requires a doctorate 8.30 % of the time, which is more often than a *senior* AI posting does (6.36 %) and 6.8 times the entry-level non-AI rate. It says “no degree required” in 2.46 % of cases, against 11.77 % for entry-level non-AI work. Entry-level AI advertisements also carry salary bands 2.3 times wider than entry-level non-AI ones. Employers appear not to have settled either what a junior AI worker should know or what one is worth.

**A new genre of advertisement text obeys the law.** Slightly over one per cent of postings now disclose that AI is used to screen candidates. New York City’s Local Law 144 requires exactly this disclosure of employers hiring into the city, and the rate there is **2.53 %**, against **1.06 %** in the rest of New York State and 1.08 % in the rest of the United States. The disclaimer that no law requires, that the employer does *not* use AI in hiring, sits flat at 0.12 to 0.13 % everywhere. A measure that jumps at the exact jurisdictional boundary of the rule requiring it, while a near-identical measure that no rule requires stays flat, is about as good a validation as observational text offers. Employers also instruct applicants to use AI roughly 27 times more often than they forbid it.

## 10. Limitations {#limitations}

Six months of monthly snapshots is not a business cycle, and every temporal result here is composition-adjusted and sign-tested but still short. These are posted advertisements: no hire, no wage paid and no worker appears. Advertised pay is not paid pay, and the extractor is effectively an English-language and United States instrument, covering 30.3 % of English postings but 0.08 % of German ones and 0.000 % of Swedish ones, so no non-English pay number is usable. Nothing in the corpus is nationally representative. And AI exposure and the wage level are close to the same variable here, with a rank correlation of +0.62 across occupations, so “AI-exposed work shrank” cannot be separated from “high-wage white-collar postings shrank”.

Two analyst-side cautions are worth passing on. The composition reweighting used throughout must not be applied to outcomes defined on seniority, because it reweights away the variation being measured; a first version of the seniority analysis reported the AI entry-level series as rising with bootstrap agreement of 1.000, which was an artefact. And April 2026 over-samples technology industries by 29.6 % relative to the other five months, on top of the gig campaign, which makes it a poor base month for anything correlated with technology.

## 11. How this was computed {#how-this-was-computed}

Nothing here is a sample. Every number above is a full pass over 51,864,055 rows, which is a constraint worth describing because it shaped most of the design decisions.

The raw corpus is **528 GB of uncompressed Parquet in 142 files**, each around 4 GB and internally split into roughly 6,800 row groups. Reading one whole file into memory is not possible on any ordinary machine, so nothing ever does: every pass streams batches of rows and selects only the columns it needs. The first job built two derived tables so that later work would not have to touch the 528 GB again. One is a **4.5 GB column store** holding every field except the two text columns, which answers any question that is not about wording. The other is a **125 GB text store**, the posting identifier plus the description, compressed and verified content-identical to the source. Most of the analysis reads the small one.

Work is organised as **array jobs on a batch scheduler**: one task per Parquet file, up to sixteen at a time, because the bottleneck is a shared filesystem rather than arithmetic. The text was read end to end **thirteen times** in the course of this project, as **1,565 array tasks**, about eleven complete passes over the 125 GB. In total the work ran as **1,787 batch tasks** and consumed **276 core-hours**. It is CPU-only throughout: there is no model to train and no GPU anywhere in the pipeline.

That total is modest, and deliberately so. Two choices account for it.

The first is how the text is matched. The naive way to find 87 concepts in 52 million documents is one large regular expression, and it is orders of magnitude too slow. Instead each document is tokenised once and the concept vocabulary is intersected against the resulting set, which turns a scan over patterns into a hash lookup. Case-sensitive acronyms and the handful of ambiguous vendor names still need real regular expressions, but they run on the small fraction of documents that a cheap prefilter has already flagged.

The second is memory discipline. The median task peaks at **0.6 GiB** and **93 %** stay under 3 GiB, because streaming avoids materialising anything large. The exceptions are the jobs that genuinely need the whole corpus resident at once: the widest, a skill-premium regression holding hundreds of indicator columns over 24 million rows, peaks at **55 GiB**. Two early versions of that pattern were killed outright for running out of memory. The fix in both cases was to preallocate typed arrays rather than concatenate data frames: the step that assembles one row per posting out of 142 parts needs roughly 48 GB the second way and 3 GB the first, for identical output.

The estimation is hand-rolled for an unglamorous reason: the statistics library available here is a broken partial install, so the fixed-effect estimators are written directly against numpy. Absorbing employer fixed effects across hundreds of thousands of firms is done by alternating projections rather than by building a design matrix. The uncertainty figures are resampling rather than formulae: **1,000 firm-block bootstrap draws** behind every trend, and the two specification curves are **1,152 separate regressions**.

### 11.1 Reproduction {#reproduction}

Every figure is generated from tables produced by scripts in the `linkedin-jobs-data` project, which run over the complete corpus rather than a sample. A 33-check self-test re-derives each headline value from the stored artefacts and passes in 79 seconds; the two pre-existing suites for earlier phases of the same project, 49 and 72 checks, remain green. The measurement traps encountered along the way, including all of those in Section 3, are recorded as numbered entries in the project’s conventions document so that the next person to touch this corpus does not have to find them again.
