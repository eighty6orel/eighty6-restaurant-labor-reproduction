# Live data directory

Live API pulls and rebuilt panels land here and are **gitignored**.

| Path | Contents |
|------|----------|
| `raw/` | JSON pages from `GET /v1/qcew/employment` |
| `extracts/` | Combined QCEW slice and MW panel written by the scripts |
| `cache/` | Optional client cache |

Nothing in those folders should be committed. Fixtures used by CI live in `../fixtures/`.

```text
python scripts/01_pull_qcew.py
python scripts/02_build_panel.py
python scripts/03_build_mw.py
```

Requires `E86_API_KEY` and, for the full county panel, a **Pro** plan.
