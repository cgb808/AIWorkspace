## Large Files Removed From Git Tracking

The following large binary / dataset artifacts exceeded GitHub's size or recommended thresholds and were removed from the repository history to allow the project to push cleanly.

They are referenced here so you can restore them locally when needed. Do NOT commit these files back to the repo. They belong either in a separate data storage bucket, an artifacts release, or managed via Git LFS (if later adopted).

| Path | Size (approx) | Description | Suggested Retrieval Source |
|------|---------------|-------------|----------------------------|
| `data/standard/english_standard_dataset.jsonl` | 76–77 MB | Training / instructional dataset (English standard) | Internal data lake / dataset generation pipeline | 
| `whisper/ggml-base.en.bin` | 141–142 MB | Whisper base English model checkpoint (ggml) | Download from official Whisper / ggml model distribution (e.g. https://huggingface.co/ggerganov/whisper.cpp) |

### Recovery Instructions
1. Create needed parent directories if missing:
   ```bash
   mkdir -p data/standard whisper
   ```
2. Place the dataset JSONL back at: `data/standard/english_standard_dataset.jsonl`.
3. Download the Whisper ggml model (base.en) and place it at: `whisper/ggml-base.en.bin`.

### Optional: Using Git LFS (Future)
If you decide these should version under Git LFS:
```bash
git lfs install
git lfs track "data/standard/english_standard_dataset.jsonl" "whisper/ggml-base.en.bin"
git add .gitattributes
```
Then re-add & recommit (not recommended until the team agrees on LFS usage and quotas).

### Rationale
- Keeps initial clone light.
- Avoids GitHub hard 100 MB limit.
- Encourages separation between code and large model/data blobs.

### Do Not Push Policy
These paths are now covered by `.gitignore`. If you accidentally stage them, unstage with:
```bash
git restore --staged data/standard/english_standard_dataset.jsonl whisper/ggml-base.en.bin || true
```

### Current Ignored Large / Generated Artifacts Snapshot

The following additional large or generated files/directories are ignored (patterns from `.gitignore` or implicitly untracked) and should remain local-only:

Ignored dataset/model artifacts:
- `data/downloaded/` (individual large JSONL instructional datasets e.g. orca, narrativeqa, race)
- `data/standard/mathematics_standard_dataset.jsonl`
- `models/test-embed-mini/model.safetensors`
- `models/test-embed-mini-int8/model.safetensors`
- `vendor/whisper.cpp/models/` (e.g. `ggml-small.en.bin`)
- `whisper/ggml-base.en.bin`

Tool / build outputs:
- `node_modules/`
- `vendor/whisper.cpp/build/`
- `vendor/whisper.cpp/examples/**/build/`
- `artifact/knowledge-graph/run-*` and `artifact/knowledge-graph/latest`

Generated analysis & transient artifacts:
- `artifact/analysis/*.json`
- `artifact/analysis/*.txt`

Experimental/Archive (excluded copies):
- `archive/dashboard (copy)/`
- `archive/dashboard_handoff (copy)/`
- `archive/gemma_phi_ui/`
- `archive/model_finetune_quant (copy)/`
- `archive/extracted_zip/`

Virtual env & caches:
- `.venv/`, `venv/`
- `.mypy_cache/`, `.pytest_cache/`
- `__pycache__/`

Large 3D / media assets (examples):
- `scripts/Meet Mira/sharable-bot.glb`
- `scripts/Meet Mira/nsbu-patrick/Patrick.zip`

Other sizeable binaries (tooling):
- `node_modules/supabase/bin/supabase`
- `frontend/dashboard/node_modules/**/esbuild`
- `frontend/dashboard/node_modules/typescript/lib/{typescript,tsserver,tsc}.js`

### Generator / Helper Scripts (Do Not Commit Outputs)
The following scripts create large or transient outputs that should stay ignored; only commit the scripts themselves:
- `scripts/generate_hybrid_dataset.py`
- `scripts/create_methodology_dataset.py`
- `scripts/build_clarify_priority_dataset.py`
- `fine_tuning/training/scripts/build_dataset_manifest.py`
- `fine_tuning/training/scripts/generate_interruption_recovery_dataset.py`
- `scripts/package_training_artifacts.py`

If new large generators are added, add their output directories to `.gitignore` and append to this list.

---
Last updated: $(date)
