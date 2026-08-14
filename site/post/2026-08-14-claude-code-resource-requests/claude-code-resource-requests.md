URL: https://youzhi.netlify.app/post/2026-08-14-claude-code-resource-requests/claude-code-resource-requests/
Title: Correcting Claude Code's Cluster Resource Requests with slurmwatch: Requested Memory and CPU Cores Against Actual Usage
Date: 2026-08-14
---

Every job submitted to an HPC cluster begins with a guess. The submission script names how much memory the job may use and how many CPU cores it may occupy, the scheduler reserves exactly that, and the job runs. If the guess was far too large, nothing goes wrong. The job completes, writes its output, exits zero, and the reserved-but-untouched memory is quietly unavailable to everybody else for the duration.

[Claude Code](https://www.anthropic.com/claude-code) writes those guesses well enough to be dangerous. It produces correct submission scripts, chains dependent jobs, and diagnoses a failed run from its log. The resource request is the one part it gets consistently, substantially wrong, and it has no way of finding out.

This article measures how wrong, using every job Claude Code submitted on a university cluster during a sustained stretch of machine-learning and data-processing work. It then shows what fixed it, which was not a better prompt but an instrument: [slurmwatch](https://youzhi.netlify.app/post/2026-08-03-slurmwatch/slurmwatch/), a tool that reads a running job’s real usage off the compute node.

## The two numbers this article compares {#the-two-numbers-this-article-compares}

Everything below is one comparison, applied to two resources. It is worth stating in plain terms before any chart appears.

**Memory.** The request is the `--mem` line in the submission script: `--mem=96G` reserves 96 gibibytes. The usage is the highest the job’s memory actually reached at any moment while it ran. If a job asks for 96 and peaks at 6, it held 90 gibibytes that nothing used.

**CPU cores.** The request is `--cpus-per-task`: `--cpus-per-task=8` reserves eight cores. The usage is how many of those cores were genuinely busy. A single-threaded program given eight cores uses one and leaves seven idle.

Both are reported here as a percentage (“this job used 13 % of the memory it requested”) or as a multiple (“this job was given 8 times the cores it used”). Those are the same fact in two directions.

## What slurmwatch is, and why the request needs it {#what-slurmwatch-is-and-why-the-request-needs-it}

The awkward part of the comparison is the second number. The request is written down in the script and trivially available. The usage happens on a compute node, hundreds of metres away, that you never log into, and the only thing that normally comes back is whatever the program chose to print.

[slurmwatch](https://pypi.org/project/slurmwatch/) exists to close that gap. It is a small open-source command-line tool: `sw 12345`, or `sw` with no arguments to let it find your running job, and it displays live in the terminal what that job is doing to the hardware it was given. A companion article, [*slurmwatch: Live Telemetry for HPC Jobs*](https://youzhi.netlify.app/post/2026-08-03-slurmwatch/slurmwatch/), introduces the tool properly and describes its design; this article is the empirical follow-up, and takes only what it needs.

What it needs is four numbers, which `slurmwatch --once --json <jobid>` prints in two seconds and which a script or an agent can read directly:

- **cores actually busy**, which is what `--cpus-per-task` should be sized against;
- **the memory the job genuinely needs**, called the *working set*, and distinct from two other memory figures that are easier to obtain and both misleading, as a later section shows;
- **graphics-card memory occupancy** and **graphics-card activity**, for jobs that use a GPU.

The rest of this article is what those numbers revealed.

## Where the evidence comes from {#where-the-evidence-comes-from}

Claude Code keeps a structured transcript of every session, which preserves the scripts it wrote and every correction its user typed. Slurm’s accounting database independently retains what each job requested and what it recorded. Together these cover **761 job submissions**, which expand to 5,292 allocations once array jobs are counted task by task. Excluding 342 synthetic jobs written to exercise a monitoring tool leaves **4,950**, and restricting to jobs that ran at least two minutes, so that usage figures mean anything, leaves **3,483** allocations across 323 distinct workloads. Every population figure below comes from that set.

For **21 jobs** a slurmwatch snapshot was taken while the job was running. Those 21 are the only jobs here with a trustworthy memory measurement, for a reason the article gets to shortly.

Job names, script names and project names are omitted throughout; workloads are described by what they did.

## How much of each request was used {#how-much-of-each-request-was-used}

[figure: Each bar is a group of jobs, sorted by how much of its request it used. Read the leftmost pair first: 42 % of jobs used a tenth or less of the memory they asked for, against 12 % for cores. Memory is piled up at the left and has essentially no right-hand tail; only 1 % of jobs ever reached 90 % of the memory they reserved. CPU cores are split in two, and the split is informative. The tall bar on the right is thousands of small single-core tasks that asked for one core and kept it busy, which is exactly correct. The bars on the left are the same error as memory, made on a smaller scale: four, six or eight cores requested for work that used one.] Figure 1: Each bar is a group of jobs, sorted by how much of its request it used. Read the leftmost pair first: 42 % of jobs used a tenth or less of the memory they asked for, against 12 % for cores. Memory is piled up at the left and has essentially no right-hand tail; only 1 % of jobs ever reached 90 % of the memory they reserved. CPU cores are split in two, and the split is informative. The tall bar on the right is thousands of small single-core tasks that asked for one core and kept it busy, which is exactly correct. The bars on the left are the same error as memory, made on a smaller scale: four, six or eight cores requested for work that used one.

Over the whole period this adds up to 25,888 gibibyte-hours of memory reserved for work whose peak demand was 10,696, and 3,473 core-hours reserved for work that consumed 963. Both understate the problem, for the reason the next two sections give.

## Why memory goes wrong more than cores {#why-memory-goes-wrong-more-than-cores}

The two resources punish a bad guess very differently, and that difference explains the whole shape of Figure 1.

A job given too few cores runs slowly and finishes. A job given too little memory is killed, and it is killed late: the run looks healthy for an hour, then its memory spikes once and the scheduler destroys it. Over the period, 12 of the 4,950 jobs died that way, 0.24 %. In four of the twelve the recorded peak was at or above ninety per cent of the request, so the request had simply been cut too fine. In the other eight the accounting shows a peak well inside the limit or no peak at all, meaning the fatal spike happened between two samples and was never recorded.

So the incentives are asymmetric. Asking for too little memory destroys hours of work; asking for too much costs nothing anyone will ever mention. Any process optimising against what it can observe will over-request, and it is locally right to.

## Why the easily available memory numbers made it worse {#why-the-easily-available-memory-numbers-made-it-worse}

This is the part I did not expect, and it is the reason a dedicated instrument matters rather than merely being convenient.

Before slurmwatch there were two ways to find out how much memory a job had used, and **both of them report a number larger than the truth**.

- Slurm’s accounting reports `MaxRSS`, the largest memory footprint it sampled. When a job has several processes this adds up pages that the processes *share*, counting the same physical memory once per process.
- The Linux control group that fences the job in reports a lifetime memory peak. That is closer to authoritative, but it includes the *page cache*: copies of files the kernel is holding on the job’s behalf and would give back instantly if anything else wanted them.

Neither is the number that decides whether a job survives. That number is the working set, and it is smaller than both. slurmwatch reports it by subtracting the cache; the other two do not.

[figure: Each dot is one of the 21 measured jobs. Its position is that instrument's memory figure divided by the true requirement slurmwatch measured, so a dot on 1x means the instrument was right. Note the shape of the error rather than its average: most dots sit close to 1x, which is exactly why these numbers look trustworthy, and then a few sit enormously to the right. On one job Slurm's accounting reported 6.95 GiB and the raw control-group counter 15.07 GiB for a job whose real requirement was 0.40 GiB, and that second figure exceeded the job's own 8 GiB limit. The lone dot on the far left is the opposite failure: a long-running placeholder job whose accounting recorded 0.01 GiB while the job was holding 3.99, a figure nothing could be sized from either.] Figure 2: Each dot is one of the 21 measured jobs. Its position is that instrument’s memory figure divided by the true requirement slurmwatch measured, so a dot on 1x means the instrument was right. Note the shape of the error rather than its average: most dots sit close to 1x, which is exactly why these numbers look trustworthy, and then a few sit enormously to the right. On one job Slurm’s accounting reported 6.95 GiB and the raw control-group counter 15.07 GiB for a job whose real requirement was 0.40 GiB, and that second figure exceeded the job’s own 8 GiB limit. The lone dot on the far left is the opposite failure: a long-running placeholder job whose accounting recorded 0.01 GiB while the job was holding 3.99, a figure nothing could be sized from either.

The consequence is the one that matters. Claude Code was not refusing to measure. On several occasions it did measure, with the instruments it had, and sized the request to 1.4 times a figure that was itself several times too large. Sizing carefully to 1.4 times a number that is 17 times too big reserves twenty-four times what the job needs, while following the instruction exactly. No amount of firmer instruction fixes that. Only a different instrument does.

The converse is in the record too, and it is the clearest evidence that the distinction between these numbers is the operative one. A checkpoint-merging step reported a memory footprint of 42.15 GiB while running perfectly well under a 32 GiB limit. The right conclusion is not “raise the limit” but “about 23 GiB of that is a memory-mapped file the kernel will hand back on demand.” The limit stayed at 32 GiB and the job kept working. That judgement is only available to something that can see the two numbers apart.

## What slurmwatch showed on the jobs it measured {#what-slurmwatch-showed-on-the-jobs-it-measured}

[figure: One row per job, sorted by how far the memory request missed. A dot on 1x means the request matched what the job used; the dashed line at 1.4x is the sizing target that was in force. The absolute figures behind the top rows are worth reading: 7.84 GiB reserved for a job that needed 0.05, 47 GiB for one that needed 1.1, and 96 GiB for one that needed 6. Only the bottom six rows meet the memory target, and all six are the same three-GPU training workload measured on six occasions. That is the one workload here whose request had been cut to fit a measurement rather than reasoned out, from 64 GiB down to 56.] Figure 3: One row per job, sorted by how far the memory request missed. A dot on 1x means the request matched what the job used; the dashed line at 1.4x is the sizing target that was in force. The absolute figures behind the top rows are worth reading: 7.84 GiB reserved for a job that needed 0.05, 47 GiB for one that needed 1.1, and 96 GiB for one that needed 6. Only the bottom six rows meet the memory target, and all six are the same three-GPU training workload measured on six occasions. That is the one workload here whose request had been cut to fit a measurement rather than reasoned out, from 64 GiB down to 56.

The clearest single case is the video transcode row. That job asked for sixteen cores and six gibibytes. A slurmwatch reading taken 38 seconds into the run showed 6.0 cores busy and a memory peak of 857 megabytes: 38 % of the cores and 14 % of the memory. It was cancelled and resubmitted with eight cores and two gibibytes, and the second reading showed 5.0 cores busy and 0.61 of 1.96 gibibytes, or 63 % and 31 %. The encoder had never been capable of using sixteen cores; it saturates at five or six however many it is given. No amount of reading the code would have produced that number, and the whole exchange cost about a minute of lost encoding.

## Instruction first, then instrumentation {#instruction-first-then-instrumentation}

Two things were introduced during the period, six days apart, and the order is the argument of this article.

The first was a written rule, placed in the configuration file every session reads: size every request so that actual usage approaches ninety per cent of it, and never round the number up for comfort. It was added after four separate complaints arrived in a single day, and by the end of that day it had acquired a blunt sentence that is still there. Memory is *“the one I keep over-requesting; STOP defaulting to 32/48/96G to be safe.”* At that stage the rule named `MaxRSS` as the way to measure, which is to say it named one of the two numbers that read high.

The second changed the instrument. A slurmwatch reading became mandatory for every job, the four fields to read were named, and the older measurement was explicitly superseded. The operative sentence is *“take a telemetry snapshot and right-size from the real numbers (don’t guess, don’t pad)”*, followed by an instruction to cancel the job and resubmit it if the reading disagrees with the request.

[figure: Only the GPU jobs are shown, because they are the one kind of work present in every week; including the later CPU-only campaigns would confuse a change in behaviour with a change in workload. Both lines fall by roughly a factor of four or five. Two honest qualifications belong with that. The jobs themselves grew, from a median real requirement of 9 GiB in week 1 to 26 GiB in week 6, so part of the closing gap is need rising to meet the request rather than the request falling. And the largest single fall, 9.55x to 3.91x, happens in the week the written rule arrived and before any slurmwatch reading was required. What the instrument plausibly contributed is the second half of the descent, from about 4x to about 1.8x, which is exactly the range the older numbers could not resolve.] Figure 4: Only the GPU jobs are shown, because they are the one kind of work present in every week; including the later CPU-only campaigns would confuse a change in behaviour with a change in workload. Both lines fall by roughly a factor of four or five. Two honest qualifications belong with that. The jobs themselves grew, from a median real requirement of 9 GiB in week 1 to 26 GiB in week 6, so part of the closing gap is need rising to meet the request rather than the request falling. And the largest single fall, 9.55x to 3.91x, happens in the week the written rule arrived and before any slurmwatch reading was required. What the instrument plausibly contributed is the second half of the descent, from about 4x to about 1.8x, which is exactly the range the older numbers could not resolve.

## The corrections, one at a time {#the-corrections-one-at-a-time}

The change is visible in individual edits as well as in the aggregate. The transcripts contain 23 occasions on which Claude Code went back into a submission script it had already written and changed the memory or core request.

[figure: Each arrow runs from the old value to the new one, in the order the rewrites happened. Twenty-one of the twenty-three point downward, several of them steeply: 96 GiB to 48, 96 to 24, 80 to 24, 170 to 120. The two upward arrows are the more interesting ones, and both have the same cause, described below.] Figure 5: Each arrow runs from the old value to the new one, in the order the rewrites happened. Twenty-one of the twenty-three point downward, several of them steeply: 96 GiB to 48, 96 to 24, 80 to 24, 170 to 120. The two upward arrows are the more interesting ones, and both have the same cause, described below.

Both upward arrows are the failure mode of tightening a request, and both took the same form: the request had been sized from a reading of one phase of a job with several phases, and the job was then killed in a later, heavier phase.

In the first, a 32 GiB request carried over from a standard evaluation was killed at a phase that loads a 34.6 GB checkpoint into memory. The request went to 64 GiB, but not before the underlying waste was fixed: the loader had been holding data it no longer needed, and releasing it dropped the peak from about 58 GB to about 46. A slurmwatch reading later showed a 32.9 GiB peak, and the request came back down to 48. In the second, a request cut to 20 GiB from a reading of the training phase was killed during a later checkpoint-merging phase that the reading had never covered.

Neither is an argument against measuring. Both are an argument for measuring a job all the way through rather than at a convenient moment.

## Where the correction did not carry over {#where-the-correction-did-not-carry-over}

[figure: The GPU jobs in the middle group were watched: they were long, expensive, few in number, and a slurmwatch reading was taken while they ran. Both of their requests came down to roughly twice what was needed. The CPU-only campaigns on the right were not watched, and they were submitted under the same written rule. Their core requests are nearly right, because a single-core task obviously needs one core and no measurement is required to know it. Their memory requests are still nearly nine times the recorded peak, because nothing about the job's behaviour reveals what that peak was, and a round 2 or 4 GiB is the safe guess.] Figure 6: The GPU jobs in the middle group were watched: they were long, expensive, few in number, and a slurmwatch reading was taken while they ran. Both of their requests came down to roughly twice what was needed. The CPU-only campaigns on the right were not watched, and they were submitted under the same written rule. Their core requests are nearly right, because a single-core task obviously needs one core and no measurement is required to know it. Their memory requests are still nearly nine times the recorded peak, because nothing about the job’s behaviour reveals what that peak was, and a round 2 or 4 GiB is the safe guess.

This is the point of the whole exercise. The rule applied to every job in Figure 6. It was not being ignored. There was simply no reading to size against, and without one the instruction to avoid over-requesting collides with the instruction to avoid killing the run. The second wins, correctly, every time.

## Why an instrument and not a better prompt {#why-an-instrument-and-not-a-better-prompt}

It is tempting to read all of this as a shortcoming of one tool, fixable with a stronger model or a firmer instruction. The record does not support that, for three reasons.

**The answer is not in the code.** How much memory a program needs depends on the data it is given, the libraries it links, how much file content the kernel decides to cache, and how many worker processes a framework happens to start. None of that is visible in the source. The video encoder that saturates at five cores looks, in its invocation, exactly like one that would use sixteen.

**Success reports nothing.** A job that completes gives back no information about its footprint. A request is written, the job succeeds, and the next request is written by the same reasoning that produced the last one. Nine complaints over the period came from a human reading a dashboard, not from anything Claude Code could have noticed by itself. Seven of the nine arrived in the first three days, which is what a standing instruction is good for; the last two, much later, are what an instruction alone does not reach.

**The easy measurements pointed the wrong way**, as Figure 2 showed. This is the reason Figure 4 falls in two stages: the written rule removed the round numbers, and slurmwatch removed the remaining factor of two.

What closed the gap was making one reading mandatory and naming the four fields to take from it. That is a two-second command against a running job. It converts a question that cannot be answered by reasoning into one that can be answered by looking, which is the entire contribution of the tool.

## Limitations {#limitations}

The population figures for memory rest on Slurm’s `MaxRSS`, which this article has just spent a section criticising. That is unavoidable: it is the only memory figure retained for all 4,950 jobs. Its bias runs one way, and the direction matters. Because `MaxRSS` reads high, the percentages in Figure 1 are upper bounds and the multiples elsewhere are lower bounds. The real gap is wider than reported here, not narrower. Where a slurmwatch figure exists, in Figures 2 and 3, it is used instead.

The 21 measured jobs are not a random sample. They are the jobs somebody thought worth watching, which biases them toward long, expensive and suspicious runs.

Figure 4 cannot separate the effect of the written rule from the effect of the instrument, since the two arrived six days apart while the workload mix was also changing. The claim made is the modest one: the fall from roughly 4x to roughly 1.8x coincides with the instrument and lies in the range the older numbers could not resolve.

Finally, this is one tool, one operator and one cluster. The structural argument generalises, because the absent feedback loop and the misleading memory numbers are properties of Slurm rather than of anything reading it. The particular numbers should not be assumed to.

## Summary {#summary}

Across 761 submissions and 4,950 jobs, Claude Code reserved 25,888 gibibyte-hours of memory for work whose peak demand was 10,696, and 3,473 core-hours for work that consumed 963. The median job used 12.9 % of the memory it asked for. Four jobs in five used under a quarter of it.

A written instruction to stop cut the worst of it, from 9.55 times what was needed to about 4. A mandatory slurmwatch reading took it the rest of the way, to about 1.8. Where no reading was taken, memory requests stayed nearly nine times the recorded peak under the same rule, because without a measurement the safe guess is a large one.

Claude Code is not bad at HPC work. It is blind to one specific quantity; the blindness is a property of the system it works in rather than of its reasoning; and the remedy is a two-second reading rather than a better prompt. That is the case for keeping slurmwatch on the job.
