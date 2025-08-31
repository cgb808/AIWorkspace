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

---
Last updated: $(date)
