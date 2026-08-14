URL: https://youzhi.netlify.app/post/2026-08-14-claude-code-resource-requests/claude-code-resource-requests/
Title: Claude Code Over-Requests HPC Resources: Measuring the Gap, and Closing It with Live Telemetry
Date: 2026-08-14
---

[Claude Code](https://www.anthropic.com/claude-code) is an extremely capable collaborator on an HPC system. It writes correct submission scripts, chains dependent jobs, diagnoses a crashed run from its log, and recovers a checkpoint without being asked twice. There is one thing it does badly, and it does it consistently: it cannot size the resource request.

Every job carries a request for memory and processor cores, written before the job runs. Nothing ever checks the answer. A job that reserved ninety-six gibibytes and touched six looks, from every direction Claude Code can see, exactly like a job that was sized correctly. Both completed. Both wrote their output. Only one deserved the allocation.

This article measures the gap. Every job discussed here was submitted by Claude Code on a university HPC system running Slurm, during a sustained stretch of machine-learning and data-processing work. The finding is that memory was over-requested by roughly an order of magnitude: the median job used **12.9 %** of the memory it reserved, and four jobs in five used under a quarter. Processor cores fared better but not well, with the median job consuming **53 %** of the core-seconds it was given. In total, 25,888 gibibyte-hours of memory were reserved for work whose peak demand was 10,696, and 3,473 core-hours were reserved for work that consumed 963.

The interesting part is not the size of the error. It is that written instructions to stop, repeated and increasingly blunt, only got about halfway. What closed the rest of the gap was a live measurement from the compute node, taken with [slurmwatch](https://pypi.org/project/slurmwatch/). The argument of this article is that the weakness is structural rather than a deficit of reasoning, and that it is therefore fixed by instrumentation rather than by prompting.

## Where the numbers come from {#where-the-numbers-come-from}

Three records are combined, and they have different weaknesses.

Claude Code keeps a structured transcript of every session, which preserves the scripts it wrote, the tool output it received, and every correction its user typed. Slurm’s accounting database independently retains what each job requested and what it recorded. Together these cover **761 job submissions**, which expand to 5,292 allocations once array jobs are counted task by task. Excluding 342 synthetic jobs written to exercise a monitoring tool leaves **4,950**, and restricting to jobs that ran at least two minutes, so that usage figures mean anything, leaves **3,483** allocations across 323 distinct workloads. Every population statistic below comes from that set.

The third record is live telemetry. For 21 jobs a snapshot was taken with slurmwatch while the job was still running. This reports what Slurm’s accounting cannot: the memory a job genuinely needs, separated from the file cache the kernel is holding on its behalf, and the number of cores actually busy. Those 21 are the only jobs here for which a trustworthy memory figure exists, and the section on instruments explains why that distinction carries so much weight.

Job names, script names and project names are omitted throughout; workloads are described by what they did.

## The population picture {#the-population-picture}

[figure: How much of each request was actually used, across 3,483 job allocations. Memory is concentrated in the leftmost bars: two jobs in five never exceeded a tenth of what they reserved, and four in five stayed under a quarter. Processor cores are bimodal, which is the more encouraging shape. The right-hand spike is arrays of single-core work, where one core was requested and one core ran flat out. The left-hand mass is the same mistake as memory, made on a smaller scale.] Figure 1: How much of each request was actually used, across 3,483 job allocations. Memory is concentrated in the leftmost bars: two jobs in five never exceeded a tenth of what they reserved, and four in five stayed under a quarter. Processor cores are bimodal, which is the more encouraging shape. The right-hand spike is arrays of single-core work, where one core was requested and one core ran flat out. The left-hand mass is the same mistake as memory, made on a smaller scale.

Two features of Figure 1 matter more than the medians.

The first is that memory has no right-hand tail worth speaking of. Exactly 1.0 % of allocations reached ninety per cent of the memory they held. This is not a distribution of estimates scattered around a correct answer; it is a distribution of estimates that were almost never close.

The second is that cores are bimodal, and the two modes have different causes. The spike at 90-100 % is genuine efficiency: large document-processing arrays requested one core per task and ran that core continuously, which is exactly right. The mass below thirty per cent is the familiar error, and it clusters on requests of four, six and eight cores for work that used one.

## The asymmetry that makes memory the harder case {#the-asymmetry-that-makes-memory-the-harder-case}

Requesting too much of either resource is not free. On a shared system a job that reserves memory it will never touch waits longer for a slot and, once running, blocks work that would have used it. But the two resources punish mistakes very differently, and this asymmetry explains the whole shape of Figure 1.

A job given too few cores runs slowly and finishes. A job given too little memory is killed, and it is killed late: after the run has looked healthy for an hour, at the first moment its footprint spikes. Twelve of the 4,950 allocations died this way, 0.24 %. In four of the twelve the recorded peak was at or above ninety per cent of the request, so the sizing had simply been too tight. In the remaining eight the accounting either shows a peak well inside the limit or records no peak at all, which means the fatal spike happened between two samples and was never recorded.

That is the real structure of the problem. The cost of under-requesting memory is a destroyed run; the cost of over-requesting it is invisible. Anything optimising against what it can observe will over-request every time, and it will be locally correct to do so.

## The instruments available, and why they pointed the wrong way {#the-instruments-available-and-why-they-pointed-the-wrong-way}

Before a live monitor was in use, there were two ways to size a memory request, and both of them read high.

Slurm’s accounting reports `MaxRSS`, the largest resident set size it sampled. For a job with several processes this sums shared pages across them, so the same physical page is counted once per process. The Linux control group reports a lifetime memory peak, which is closer to authoritative but includes the page cache: file contents the kernel is holding on the job’s behalf and would release instantly if anything else wanted them. Neither figure is the number that determines whether a job survives. That number is the working set, the memory the job genuinely needs, and it is smaller than both.

[figure: Three instruments reading the same 21 jobs. The horizontal axis is the working set, the figure that actually governs whether a job is killed; the vertical axis is what each of the two older instruments reported for the same job. The dashed line is exact agreement, and 33 of the 42 readings sit above it. Note what the shape of the error is: most points are close to the line, and a handful are enormously above it. The worst case is a factor of 37.7, a job whose true requirement was 0.40 GiB reported by the scheduler as 6.95 GiB and by the raw control-group counter as 15.07 GiB, the latter exceeding the job's own 8 GiB limit. The single point far below the line is a long-lived placeholder whose accounting recorded 0.01 GiB against a measured 3.99.] Figure 2: Three instruments reading the same 21 jobs. The horizontal axis is the working set, the figure that actually governs whether a job is killed; the vertical axis is what each of the two older instruments reported for the same job. The dashed line is exact agreement, and 33 of the 42 readings sit above it. Note what the shape of the error is: most points are close to the line, and a handful are enormously above it. The worst case is a factor of 37.7, a job whose true requirement was 0.40 GiB reported by the scheduler as 6.95 GiB and by the raw control-group counter as 15.07 GiB, the latter exceeding the job’s own 8 GiB limit. The single point far below the line is a long-lived placeholder whose accounting recorded 0.01 GiB against a measured 3.99.

The shape of the disagreement is what makes it dangerous. In the middle of the distribution the older instruments are close to right: the median overstatement is 1.29 times for the scheduler’s figure and 1.05 for the raw control-group counter. On a single-process job holding little cached file data all three numbers agree, which is precisely why the instruments look trustworthy. The failure is in the tail. On the multi-process, file-heavy jobs the scheduler’s figure reaches 2.4, 3.6, 6.9 and 17.4 times the true requirement, and nothing about the reading announces which kind of job it came from.

This is the mechanism behind Figure 1, and it is easy to miss. Claude Code was not refusing to measure. On several occasions it did measure, using the instruments it had, and sized the request to 1.3 or 1.5 times a figure that was itself several times too large. Instructions to measure more carefully cannot fix that. Only a different instrument can.

The converse case is in the record too, and it is the clearest evidence that the distinction is the operative one. A checkpoint-merging step reported a peak resident set of 42.15 GiB while running successfully under a 32 GiB limit. The correct reading of that is not “raise the limit” but “about 23 GiB of that figure is a memory-mapped file the kernel will hand back on demand.” The limit stayed at 32 GiB and the job kept working. That decision is available only to something that knows the two numbers are different, which is exactly what slurmwatch reports and the older instruments do not.

## What a live reading changes {#what-a-live-reading-changes}

Once a monitor was reading the compute node directly, the gap became visible in a single command, and it was large.

[figure: The 21 jobs for which a live reading exists, ordered by how far the memory request missed. A mark on 1x asked for exactly what it used; the dashed line is the sizing target in force. Read the absolute figures behind the top rows: 7.84 GiB reserved for a job needing 0.05, 47.04 for one needing 1.09, 96 for one needing 5.96. Cores are closer to the target but structurally coarse, because the request is an integer and the smallest useful integer is one. Only the bottom six rows meet the memory target, and all six are the same three-card training workload observed on six occasions: the one workload here whose request had been cut to fit a measurement, from 64 GiB to 56 GiB.] Figure 3: The 21 jobs for which a live reading exists, ordered by how far the memory request missed. A mark on 1x asked for exactly what it used; the dashed line is the sizing target in force. Read the absolute figures behind the top rows: 7.84 GiB reserved for a job needing 0.05, 47.04 for one needing 1.09, 96 for one needing 5.96. Cores are closer to the target but structurally coarse, because the request is an integer and the smallest useful integer is one. Only the bottom six rows meet the memory target, and all six are the same three-card training workload observed on six occasions: the one workload here whose request had been cut to fit a measurement, from 64 GiB to 56 GiB.

The clearest single case in the record is the video transcode row of Figure 3. That array requested sixteen cores and six gibibytes. A reading taken 38 seconds into the run returned 6.0 effective cores and a peak of 857 megabytes: 37.6 % of the cores and 13.6 % of the memory. It was cancelled and resubmitted with eight cores and two gibibytes, and the second reading returned 5.0 effective cores and 0.61 of 1.96 gibibytes, or 62.6 % and 30.9 %. The encoder had never been able to use sixteen cores; it saturates at five or six regardless of what it is given. No amount of reasoning about the workload would have produced that number, and the whole exchange cost about a minute of lost encoding.

## Instruction, then instrumentation {#instruction-then-instrumentation}

Two interventions were made, six days apart, and the order of them is the argument of this article.

The first was a written rule, placed in the global configuration file that every session reads: size every request so that actual usage approaches ninety per cent of it, and never pad to a round number. It was added after four separate corrections arrived in a single day, and by the end of that day it had acquired an unusually blunt sentence, which survives in the file. Memory is *“the one I keep over-requesting; STOP defaulting to 32/48/96G to be safe.”* At this stage the rule named `MaxRSS` as the way to measure, which is to say it named an instrument that reads high.

The second changed the instrument. A live snapshot became mandatory for every job, four fields were named, and the older measurement was explicitly superseded. The operative sentence is *“take a telemetry snapshot and right-size from the real numbers (don’t guess, don’t pad)”*, followed by an instruction to cancel and resubmit if the reading disagrees with the request.

[figure: How much more was asked for than was needed, week by week, on the graphics-card workloads. These are shown alone because they are the only workload family present in every week, so the series is not confounded by the arrival of new kinds of work. Both curves fall by roughly a factor of four or five. The first dashed marker is when the written rule was added; the second is when a live measurement became mandatory and the older instrument was retired. The largest single fall precedes the instrument, and the last two weeks are where the two curves converge.] Figure 4: How much more was asked for than was needed, week by week, on the graphics-card workloads. These are shown alone because they are the only workload family present in every week, so the series is not confounded by the arrival of new kinds of work. Both curves fall by roughly a factor of four or five. The first dashed marker is when the written rule was added; the second is when a live measurement became mandatory and the older instrument was retired. The largest single fall precedes the instrument, and the last two weeks are where the two curves converge.

Week 1 is the baseline: a median request of ninety-six gibibytes against a median peak of nine, a factor of 9.55, with eight cores requested for one. By the last two weeks the memory factor is 1.85 and the core factor 2.00. The improvement is real, and two honest qualifications belong with it.

The jobs themselves grew. The median measured peak rises from 8.98 GiB in the first week to 26.01 GiB in the last, so part of the closing gap is need catching up with the request rather than the request coming down to meet need. And the change cannot be attributed to either intervention alone: the largest single fall, 9.55 to 3.91, happens in the week the written rule arrived and before any live monitor was required. What the monitor plausibly supplied is the second half of the descent, from about 4 to about 1.8, which is precisely the range that reasoning cannot reach because the older instruments do not resolve it.

## The record of rewrites {#the-record-of-rewrites}

The corrections are visible individually as well as in aggregate. The transcripts contain 23 unambiguous edits in which a memory or core request was rewritten in a job script that had already been written.

[figure: Every rewrite of a memory or core request in a job script. Each arrow runs from the old value to the new one, in the order the rewrites happened. Twenty-one of the twenty-three point downward, several of them steeply: 96 GiB to 48, 96 GiB to 24, 80 GiB to 24, 170 GiB to 120. The two upward arrows are the informative ones, and both have the same cause.] Figure 5: Every rewrite of a memory or core request in a job script. Each arrow runs from the old value to the new one, in the order the rewrites happened. Twenty-one of the twenty-three point downward, several of them steeply: 96 GiB to 48, 96 GiB to 24, 80 GiB to 24, 170 GiB to 120. The two upward arrows are the informative ones, and both have the same cause.

The two upward arrows deserve their place in the figure, because they are the failure mode of tightening a request. Both have the same shape: the request had been sized from a reading of one phase of a multi-phase job, and the job was then killed in a later, heavier phase.

In the first case a 32 GiB request was carried over from the standard evaluation sizing, and the job was killed at a phase that loads a 34.6 GB checkpoint into memory. The request went to 64 GiB, but not before the underlying waste was fixed: the loader had been holding optimiser state it no longer needed, and releasing it dropped the peak from about 58 GB to about 46 GB. A live reading later returned a 32.9 GiB peak, and the request came back down to 48 GiB. In the second, a request cut to 20 GiB from a reading of the training phase was killed during a later checkpoint-merging phase that the reading had never covered.

Neither is an argument against measuring. Both are an argument for measuring the whole job rather than a convenient moment in it.

## What did not transfer {#what-did-not-transfer}

The correction did not generalise evenly, and the way it failed is the most useful finding here.

[figure: Where the correction held and where it did not. On the graphics-card workloads, the ones under continuous observation, both resources come down to roughly twice what is needed. On the large processor-only campaigns that came later, cores are nearly right at 1.51 times consumption while memory is still 8.77 times the recorded peak. The difference is not competence. It is that a core request is cheap to get wrong and a memory request is not, so the same reasoning, correctly weighing its own risk, keeps padding the one that can destroy a run.] Figure 6: Where the correction held and where it did not. On the graphics-card workloads, the ones under continuous observation, both resources come down to roughly twice what is needed. On the large processor-only campaigns that came later, cores are nearly right at 1.51 times consumption while memory is still 8.77 times the recorded peak. The difference is not competence. It is that a core request is cheap to get wrong and a memory request is not, so the same reasoning, correctly weighing its own risk, keeps padding the one that can destroy a run.

The graphics-card jobs were watched. They were long, expensive, few in number, and a reading was repeatedly taken while they ran. Their memory requests came down to 1.85 times need and stayed there.

The document-processing campaigns were not watched. They were arrays of thousands of short tasks, individually cheap, and no live reading was ever taken for any of them. Their core requests are nearly right, because a single-core task obviously needs a single core and no measurement is required to know it. Their memory requests are still 8.77 times the recorded peak, because nothing in the job’s own behaviour reveals what that peak was, and a round two or four gibibytes is the safe guess.

This is the point of the whole exercise. The rule was in force for all of these jobs. It was not being ignored. There was simply no reading to size against, and in the absence of a reading the instruction to avoid over-requesting collides with the instruction to avoid killing the run. The second one wins, correctly, every time.

## Why an instrument and not better reasoning {#why-an-instrument-and-not-better-reasoning}

It is tempting to read this as a shortcoming of one tool, remediable by a better model or a firmer prompt. The record does not support that reading, for three reasons.

**The information is not in the code.** How much memory a program needs depends on the data it is given, the libraries it links, the file cache the kernel decides to keep, and the number of worker processes a framework happens to spawn. None of this is legible in the source. The video encoder that saturates at five cores looks, in its invocation, exactly like one that would use sixteen.

**The feedback loop is broken by default.** A successful job produces no signal about its footprint. A request is written, the job completes, the transcript records success, and the next request is written from the same reasoning that produced the last one. Nine corrections came from a human reading a dashboard, not from anything Claude Code could have noticed alone. Seven of the nine fell in the first three days; the remaining two, arriving much later, are what a standing instruction does not reach.

**The measurements that were available pointed the wrong way.** This is the finding that surprised me most. Sizing diligently to 1.4 times a `MaxRSS` figure that overstates by a factor of 17 follows the instruction exactly and still reserves twenty-four times what the job needs. Figure 4 shows the fix arriving in two stages for this reason: the rule removed the round numbers, and the instrument removed the remaining factor of two.

What actually closed the gap was making one measurement mandatory and naming the four fields to read: cores actually busy, working-set peak, graphics-card memory occupancy, and graphics-card activity. That is a two-second command against a running job, and it is the whole of what slurmwatch contributes here. It converts a question that cannot be answered by reasoning into one that can be answered by looking.

## Limitations {#limitations}

The population figures for memory rest on Slurm’s `MaxRSS`, which this article has just spent a section criticising. That is unavoidable: it is the only memory figure retained for all 4,950 allocations. Its bias runs one way, and the direction matters for the interpretation. Because `MaxRSS` overstates the true requirement, the utilisation percentages in Figure 1 are upper bounds and the over-request factors elsewhere are lower bounds. The real gap is wider than reported here, not narrower. Where a working-set figure exists, in Figures 2 and 3, it is used instead.

The 21 measured jobs are not a random sample. They are the jobs somebody thought worth watching, which biases them toward long, expensive and suspicious runs.

The weekly series in Figure 4 cannot separate the effect of the written rule from the effect of the instrument, since the two were introduced six days apart in a period when the workload mix was also changing. The claim made is the modest one: the fall from roughly 4 to roughly 1.8 coincides with the instrument and lies in the range the previously available instruments could not resolve.

Finally, all of this comes from one tool, one operator and one cluster. The structural argument generalises, because the broken feedback loop and the misleading instruments are properties of Slurm rather than of anything reading it. The particular numbers should not be assumed to.

## Summary {#summary}

Across 761 job submissions and 4,950 allocations, Claude Code reserved 25,888 gibibyte-hours of memory for work whose peak demand was 10,696, and 3,473 core-hours for work that consumed 963. The median job used 12.9 % of its memory request. Four in five used under a quarter.

A written instruction to stop cut the worst of it, from 9.55 times need to about 4. A mandatory live reading from the compute node took it the rest of the way, to about 1.8. Where no reading was taken, memory requests remained 8.77 times the recorded peak under the same rule, because in the absence of a measurement the risk calculus favours padding, and it is right to.

Claude Code is not bad at HPC work. It is blind to one specific quantity, the blindness is a property of the system it is working in rather than of its reasoning, and the remedy is a two-second reading rather than a better prompt. That is the case for keeping an instrument on the job.
