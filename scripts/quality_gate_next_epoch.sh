#!/bin/bash
"""
Quality Gate Pipeline for Next Epoch
Runs complete validation, deduplication, balancing, and manifest generation
"""

set -e  # Exit on any error

echo "========================================"
echo "QUALITY GATE PIPELINE - NEXT EPOCH"
echo "========================================"
echo "Started: $(date)"
echo ""

# Configuration
INPUT_FILE="${1:-data/unified_instructional_dataset.jsonl}"
OUTPUT_DIR="data/next_epoch"
FINAL_DATASET="$OUTPUT_DIR/final_balanced_dataset.jsonl"
TRAIN_FILE="$OUTPUT_DIR/train.jsonl"
VAL_FILE="$OUTPUT_DIR/val.jsonl"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Input dataset: $INPUT_FILE"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    exit 1
fi

echo "Step 1: Schema Validation"
echo "------------------------"
python scripts/dataset_validation/validate_alpaca_schema.py "$INPUT_FILE"
validation_exit_code=$?

if [ $validation_exit_code -ne 0 ]; then
    echo "Warning: Validation found issues, but continuing..."
else
    echo "✓ Schema validation passed"
fi
echo ""

echo "Step 2: Advanced Deduplication"
echo "------------------------------"
DEDUP_FILE="$OUTPUT_DIR/deduplicated.jsonl"
python scripts/dataset_validation/advanced_dedup.py "$INPUT_FILE" "$DEDUP_FILE" 0.8

if [ ! -f "$DEDUP_FILE" ]; then
    echo "Error: Deduplication failed"
    exit 1
fi
echo "✓ Deduplication completed"
echo ""

echo "Step 3: Dataset Balancing"
echo "------------------------"
python scripts/dataset_validation/assemble_mix.py "$DEDUP_FILE" "$FINAL_DATASET"

if [ ! -f "$FINAL_DATASET" ]; then
    echo "Error: Balancing failed"
    exit 1
fi
echo "✓ Dataset balancing completed"
echo ""

echo "Step 4: Train/Val Split"
echo "----------------------"
python scripts/dataset_validation/assemble_mix.py --split "$FINAL_DATASET" "$TRAIN_FILE" "$VAL_FILE" 0.1

if [ ! -f "$TRAIN_FILE" ] || [ ! -f "$VAL_FILE" ]; then
    echo "Error: Train/Val split failed"
    exit 1
fi
echo "✓ Train/Val split completed"
echo ""

echo "Step 5: Manifest Generation"
echo "---------------------------"
python scripts/dataset_validation/build_manifest.py "$FINAL_DATASET"
echo "✓ Manifest generation completed"
echo ""

echo "Step 6: Final Validation"
echo "-----------------------"
python scripts/dataset_validation/validate_alpaca_schema.py "$FINAL_DATASET"
python scripts/dataset_validation/validate_alpaca_schema.py "$TRAIN_FILE"
python scripts/dataset_validation/validate_alpaca_schema.py "$VAL_FILE"
echo "✓ Final validation completed"
echo ""

echo "Step 7: Summary Report"
echo "---------------------"

# Generate summary table
echo "QUALITY GATE PIPELINE SUMMARY"
echo "=============================="
echo "Completed: $(date)"
echo ""

echo "FILES GENERATED:"
echo "  Final dataset: $FINAL_DATASET ($(wc -l < "$FINAL_DATASET") examples)"
echo "  Training set: $TRAIN_FILE ($(wc -l < "$TRAIN_FILE") examples)"
echo "  Validation set: $VAL_FILE ($(wc -l < "$VAL_FILE") examples)"
echo ""

echo "MANIFESTS AND REPORTS:"
ls -la data/MANIFEST_* data/SUMMARY_* 2>/dev/null || echo "  (Generated in current directory)"
echo ""

echo "STATISTICS FILES:"
find "$OUTPUT_DIR" -name "*.json" -type f | while read file; do
    echo "  $(basename "$file"): $(du -h "$file" | cut -f1)"
done
echo ""

# Calculate reduction statistics
if [ -f "$INPUT_FILE" ] && [ -f "$FINAL_DATASET" ]; then
    original_count=$(wc -l < "$INPUT_FILE")
    final_count=$(wc -l < "$FINAL_DATASET")
    reduction=$((original_count - final_count))
    reduction_percent=$((reduction * 100 / original_count))
    
    echo "PROCESSING STATISTICS:"
    echo "  Original examples: $original_count"
    echo "  Final examples: $final_count"
    echo "  Reduction: $reduction examples ($reduction_percent%)"
    echo ""
fi

echo "NEXT STEPS:"
echo "  1. Review validation reports in $OUTPUT_DIR"
echo "  2. Inspect manifest files for role distribution"
echo "  3. Use $TRAIN_FILE for fine-tuning"
echo "  4. Use $VAL_FILE for validation during training"
echo ""

echo "✓ Quality gate pipeline completed successfully!"
echo ""
echo "Ready for fine-tuning with high-quality, balanced dataset."
