# Data card: irreversibility pairs

**What:** 2,129 (state text, action text) pairs, each with a reversibility label:
`reversible`, `partial` (partially reversible), `irreversible`.

| Environment | reversible | partial | irreversible | Total |
|---|---|---|---|---|
| sandbox (text tools: files, email, money) | 650 | 600 | 450 | 1,700 |
| ScienceWorld | 269 | 12 | 148 | 429 |

**Fields:** id, environment, state_text, action_text, label, horizon, source, scenario_id, tool,
group_id, is_minimal_pair, label_h1/h2/h3 (labels for different undo horizons), split_0/1/2 (scenario-based splits).

**How labels were made:** automatically, from simulator rules that search for an undo path
(for example: recycle bin on and file deleted = reversible; email held 60 s = reversible; no undo = irreversible).
ScienceWorld labels come from `sw_labeller.py`.

**Label check:** 100 random pairs (50 per environment) re-labelled by two automated raters following the written guide.
Rater agreement kappa = 0.80; versus automatic labels kappa = 0.76 and 0.67. ScienceWorld is weaker (0.53, 0.44).
**No human annotators were used.** Files: `data/label_check_raterA.csv`, `label_check_raterB.csv`.

**Known limits:** synthetic scenarios; few `partial` examples in ScienceWorld (12); labels reflect the simulator's rules,
which a real system may not share; English only; class balance differs by environment.

**Intended use:** research on probing and agent safety. Not for deciding real-world actions.
**Personal data:** none; all names, emails and amounts are invented.
