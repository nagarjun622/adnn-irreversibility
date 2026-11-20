# Do AI Agents Know Which Actions Cannot Be Undone?

ADNN course project (Option 1)

We test whether two open-weight LLMs (Qwen2.5-7B-Instruct, Llama-3.1-8B-Instruct) represent
and use the difference between reversible, partially reversible and irreversible actions.

- **RQ1** Can a linear probe on hidden states read the reversibility label? (with controls and ablations)
- **RQ2** Can the model say the label when asked directly?
- **RQ3** Does an agent act more carefully before irreversible actions (66 paired tasks)? Gap = K − A.

## Headline results
- Probes decode the label inside one environment (about 0.96 balanced accuracy) but do not transfer across environments (0.30–0.34).
- Asked directly, the models are weak (3-class balanced accuracy 0.43 Qwen, 0.45 Llama).
- Neither agent asked before an irreversible action (A = 0.00). Knowledge K: Qwen 0.833, Llama 0.258.

Full numbers and discussion: `docs/ADNN_Option1_Report.pdf`.

## Repository layout
| Path | Content |
|---|---|
| `config.py`, `probe_utils.py` | seeds (SEED=42), model names, probe helpers |
| `sandbox.py`, `sandbox_text.py` | text sandbox simulator and labelling rules |
| `sw_labeller.py` | ScienceWorld action labelling |
| `data/all_pairs.jsonl` | 2,129 labelled (state, action) pairs (see `docs/DATA_CARD.md`) |
| `data/rq3_tasks.jsonl` | 66 paired RQ3 tasks |
| `data/label_check_raterA.csv`, `label_check_raterB.csv` | label check, 100 pairs, two **automated** raters |
| `demo/irreversibility_replay.html` | step-by-step replay of the saved delete_00 episodes for both models (open in a browser) |
| `logs/` | raw model outputs for RQ2 and RQ3 |
| `results/` | all result CSVs and figures |
| `docs/` | report, data card, contribution log, slides |

## Reproduce
1. Open the Colab notebook (GPU runtime, e.g. T4), mount Drive, `pip install -r requirements.txt`.
2. Set your Hugging Face token as a Colab secret named `HF_TOKEN` (never commit it). Accept the Llama 3.1 licence on Hugging Face.
3. Run the notebook cells in order. Each stage saves to Drive and skips work already done, so it can be resumed.
4. All seeds are fixed (`SEED = 42`). GPU non-determinism can change numbers in the third decimal.

Tested versions are pinned in `requirements.txt`.

## Licences
Code: MIT (see LICENSE). Data: synthetic or ScienceWorld-generated. Models keep their own licences
(Qwen2.5: Apache-2.0, Llama 3.1: Llama 3.1 Community License). Verify before publishing.
