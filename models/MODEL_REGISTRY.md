# Model Registry

This folder is CryptoShield AI's model registry: the labelled archive of
every trained model, so any version can be compared, restored, or rolled
back if a newer model underperforms (see the AI Risk Assessment, "Model
Performance Risk").

## Versioning convention

Each trained model is saved as a pair of files, produced by
`utils/model_registry.save_model_version()`:

```
model_v{N}.joblib          - the trained scikit-learn model
model_v{N}_metrics.json    - the metrics that version achieved
```

The shared TF-IDF vectorizer produced by the data pipeline is saved
separately as `tfidf_vectorizer.joblib`. If the pipeline's preprocessing
changes in a way that changes the vectorizer, regenerate it and note the
change in the registry log below.

`best_model.joblib` is a copy (not a symlink, for portability) of whichever
versioned model is currently deployed in the Streamlit app. Only update it
via `utils/model_registry.promote_to_best()`, after the new version has
been reviewed and meets the success criteria from the project proposal:

- Recall >= 85%
- Precision >= 75%
- F1-score >= 80%
- ROC-AUC >= 0.85

## Registry log

Update this table every time a new model version is saved.

| Version | Date | Model type | Accuracy | Precision | Recall | F1 | ROC-AUC | Notes |
|---|---|---|---|---|---|---|---|---|
| v1 | | | | | | | | |

## Rollback procedure

If a newly promoted model underperforms in review:

1. Confirm the previous version's file (`model_v{N-1}.joblib`) is still present.
2. Run `utils.model_registry.rollback_to(N-1)`.
3. Note the rollback and the reason in the registry log above.
