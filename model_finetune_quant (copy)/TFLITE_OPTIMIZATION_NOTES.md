<!-- Source: Docs/TFLITE_OPTIMIZATION_NOTES.md -->
# TFLite Optimization Notes

Strategies:

1.  Post-training quantization (dynamic range, int8 full, float16).  
2.  Operator fusion (Conv+BN+ReLU).  
3.  Sparsity-aware conversion (structured pruning).  
4.  Delegate usage: NNAPI, GPU, XNNPACK.  
5.  Model slimming: reduce sequence length + embedding dims.

Deployment Checklist:

*   Validate numerical drift vs FP32 baseline.  
*   Benchmark on target device (latency p50/p95, memory).  
*   Fallback path if delegate unavailable.  
*   Provide A/B gating via feature flag.
