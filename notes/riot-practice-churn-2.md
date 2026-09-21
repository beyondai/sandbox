#initial prompt:
Problem: too many players are drfiting away. figure out who's staying and who is leaving.
Data is available in data/riot-synthetic/synthetic-data/data/lifecycle/

#to-prd:
Q1 answer is good. currently we can only set up simple rules for promotion. too late.
Q2 input: right stakeholders. no need to design down stream api's. let's focus
on ml model performance.
#Note to skill improvements: user plans to use a note.md file to track inputs,
instead of directly type in claude, this is god for logs, changes, etc.
The user will label the sections, so the skill should read the information in
that section, and also, only consider incremental info.

Q3: agreed
Q4: batch-job, but share the info about how long it takes to run with how much data
#info for skill improvement: the note input and claude ui input can be mixed. long input go in the doc, short input will through claude ui. The key thing is
user just want to keep a single long-living doc for the entire session for
long inputs.