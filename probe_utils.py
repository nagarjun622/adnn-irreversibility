import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score
from config import *

CLASSES = ["reversible", "partial", "irreversible"]
PROBE_C = 0.01          # one fixed regularisation strength for every probe


def load_all(model_tag="qwen7b", position="last"):
    """Rows (dataframe) and hidden states (N x layers x hidden) in the same order."""
    data = pd.read_json(DATA_DIR + "/all_pairs.jsonl", lines=True)
    ids = json.load(open(f"{HIDDEN_DIR}/{model_tag}_all_ids.json"))
    assert list(data["id"]) == ids, "row order does not match the hidden states"
    H = np.load(f"{HIDDEN_DIR}/{model_tag}_all_{position}.npy", mmap_mode="r")
    return data, H


def make_labels(data, mode="3class"):
    if mode == "3class":                       # 0 reversible, 1 partial, 2 irreversible
        return data["label"].map({c: i for i, c in enumerate(CLASSES)}).values
    return (data["label"] != "reversible").astype(int).values   # binary: 1 = cannot be fully undone


def get_scores(y, pred, proba, classes):
    out = {"bal_acc": balanced_accuracy_score(y, pred),
           "macro_f1": f1_score(y, pred, average="macro")}
    try:
        if len(classes) == 2:
            out["auroc"] = roc_auc_score(y, proba[:, 1])
        else:
            out["auroc"] = roc_auc_score(y, proba, multi_class="ovr", labels=list(classes))
    except ValueError:
        out["auroc"] = np.nan
    return out


def fit_eval(Xtr, ytr, Xte, yte):
    """Standardise, fit an L2 logistic regression, score on the test rows."""
    scaler = StandardScaler().fit(Xtr)
    clf = LogisticRegression(C=PROBE_C, max_iter=300, random_state=SEED)
    clf.fit(scaler.transform(Xtr), ytr)
    Xte_s = scaler.transform(Xte)
    pred = clf.predict(Xte_s)
    proba = clf.predict_proba(Xte_s)
    return get_scores(yte, pred, proba, clf.classes_), pred


def layer_sweep(data, H, y, split_col, layers, shuffle=False, train_mask=None):
    """One probe per layer. shuffle=True gives the shuffled-label control."""
    train = (data[split_col] == "train").values
    test = ~train
    if train_mask is not None:
        train = train & train_mask
    rows = []
    for layer in layers:
        X = np.asarray(H[:, layer, :], dtype=np.float32)
        ytr = y[train].copy()
        if shuffle:
            np.random.RandomState(SEED + layer).shuffle(ytr)
        scores, _ = fit_eval(X[train], ytr, X[test], y[test])
        rows.append({"layer": layer, "split": split_col, **scores})
    return pd.DataFrame(rows)
