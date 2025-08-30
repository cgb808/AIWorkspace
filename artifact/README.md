# artifact/ Directory

Purpose: Central location for generated or derived artifacts that are not hand-authored source code.

Subdirectories:
- `knowledge-graph/` – Snapshots: `memory_snapshot.json`, `memory_remaining_tasks.json`, entity/edge exports.
- `analysis/` – Generated workspace / structural analysis reports, probes, layout summaries.
- (add others as needed: `benchmarks/`, `exports/`, etc.)

Conventions:
- Large binary artifacts should be `.gitignore`d unless explicitly version-controlled.
- Snapshot JSON files should include a timestamp or be placed in a dated folder if multiple versions.
- Do not place raw model weights here (use `models/`); keep this focused on metadata + analytic outputs.

Maintenance:
- Periodically prune stale analysis files (>30d) to reduce repository noise.

Last updated: 2025-08-30<!-- Directory Index: artifact/ -->
# artifact/ Generated Artifacts

Purpose: Persist generated knowledge graph snapshots, processed outputs, or derived indices.

Retention: Clean up stale artifacts to avoid repository bloat.