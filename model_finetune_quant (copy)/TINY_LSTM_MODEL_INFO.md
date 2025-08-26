<!-- Source: Docs/TINY_LSTM_MODEL_INFO.md -->
## TinyLSTM Model

**Proposal:** Create a stable TinyLSTM embedding model for very fast inference inside our product.

**TINY LSTM
Model for Embeddings or Sentiment**

1.  **Define the Task & Data**  
    *   Task: Sentiment classification or embedding generation.  
    *   Data sources:  
        *   Sentiment: IMDB, SST-2, Twitter Sentiment.  
        *   Embeddings: SNLI, STS, AllNLI, or domain-specific corpora.

2.  **Tokenization & Vocabulary**  
    *   Use a subword tokenizer like SentencePiece or BPE.  
    *   Limit vocab size (5k - 15k) to reduce embedding table size.

3.  **Model Architecture**  
    *   Embedding size: 128 or 256.  
    *   LSTM hidden size: 256–512 depending on performance vs speed.  
    *   Layers: 1–2 LSTM layers.  
    *   Optional: Bidirectional LSTM for richer context.  
    *   Add LayerNorm after embeddings or LSTM output to stabilize training.

4.  **Pooling Strategy (for embeddings)**  
    *   Mean pooling over time steps.  
    *   [CLS]-style learned token (prepend special token; use its hidden state).  
    *   Max pooling (try but may lose nuance).  

5.  **Regularization**  
    *   Dropout: 0.1–0.3.  
    *   Weight decay: small (e.g., 1e-5).  
    *   Gradient clipping: 1.0.  

6.  **Loss Functions**  
    *   Sentiment: Cross-entropy.  
    *   Embeddings: Contrastive (InfoNCE / NT-Xent), Cosine similarity loss, or Triplet loss.

7.  **Optimization**  
    *   Optimizer: AdamW.  
    *   LR schedule: Warmup (5%) then cosine decay or constant LR.  
    *   Batch size: Start small (32–128) and scale if stable.

8.  **Training Tricks**  
    *   Use mixed precision (fp16/bf16).  
    *   Bucket sequences by length to reduce padding.  
    *   Early stopping on validation similarity or accuracy.  

9.  **Evaluation Metrics**  
    *   Sentiment: Accuracy, F1.  
    *   Embeddings: Spearman/Pearson correlation on STS tasks.  

10. **Deployment Considerations**  
    *   Quantize (int8 or int4) after training for speed.  
    *   Export ONNX or TFLite for edge/mobile.  
    *   Provide simple Python API: `embed(texts: List[str]) -> np.ndarray`.

11. **Stretch Goals**  
    *   Distill from larger model (e.g., MiniLM) using KL divergence or embedding alignment.  
    *   Multi-task training: Sentiment + similarity.

12. **Risks / Mitigations**  
    *   Underfitting: Increase hidden size or add BiLSTM.  
    *   Overfitting: Increase dropout, more data augmentation.

13. **Next Steps**  
    *   Build prototype in PyTorch.  
    *   Run small-scale experiment with 50k sentences.  
    *   Compare vs MiniLM / all-MiniLM-L6-v2 on STS.
