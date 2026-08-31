# Trainer/reference material

This folder contains trainer-facing quality checks and interpretation guidance.

- `reference_checks.md` lists exact local-data checks and qualitative Earth Engine checks for the six practicals.
- Student notebooks remain clean: no saved execution outputs and no hidden answer cells.

For an internet/API outage during teaching, use the student-facing fallback material under `fallback/`.

Before travel, trainers should also render the six notebooks with:

```bash
python scripts/build_trainer_references.py
```

Review the generated HTML before using it as fallback material.
