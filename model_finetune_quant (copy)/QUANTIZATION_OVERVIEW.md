# Quantization Overview (Consolidated)

This folder aggregates internal notes and external references for model fine-tuning and quantization across the project.

Included Topics:

* Gemma (7B) usage profile
* BGE-small retrieval embedding role
* TinyLSTM internal lightweight embedding / sentiment prototype
* TFLite optimization strategies
* Predictive modeling notes (NeuralProphet, feature pipeline)

General Quantization Strategies:

1.  Post-training dynamic range (drop-in, least accuracy risk)
2.  Full integer (int8) with calibration dataset
3.  Weight-only quantization (e.g., GPTQ, AWQ) for LLMs
4.  Mixed precision (FP16/BF16 + INT8 critical layers)
5.  4-bit quantization (QLoRA / NF4) for fine-tuning efficiency

Calibration Dataset Guidance:

* 200 - 500 representative samples often sufficient for int8 PTQ
* Cover edge linguistic constructs (code, markdown, short queries, long docs)

Fine-Tuning Pathways:

* Full fine-tune (rare; expensive)
* LoRA / QLoRA adapters (preferred for rapid iteration)
* Distillation into TinyLSTM for edge or ultra-low latency contexts

Validation Metrics:

* Embedding similarity (STS benchmark or internal retrieval eval set)
* Downstream task accuracy / F1 / MRR / NDCG
* Latency (p50/p95), memory footprint, cold start

Risk Mitigation:

* Keep original fp16 checkpoint pinned
* Run side-by-side retrieval quality diff before promoting quantized model
* Document any notable semantic drift cases

See INDEX.md for original file references.
