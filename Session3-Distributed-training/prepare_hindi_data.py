#!/usr/bin/env python3
"""
Prepare Hindi dataset for Megatron-Bridge training

This script:
1. Downloads Hindi text data (Wikipedia or IndicCorp)
2. Trains a SentencePiece tokenizer
3. Converts to Megatron format (.bin/.idx files)

Usage:
    python prepare_hindi_data.py --dataset-size small
    python prepare_hindi_data.py --dataset-size large
"""

import argparse
import os
import json
import subprocess
from pathlib import Path
from datasets import load_dataset


def download_hindi_data(size="small"):
    """Download Hindi text data from Hugging Face"""
    print(f"📥 Downloading Hindi data ({size} size)...")
    
    if size == "small":
        # 10K documents (~50MB final)
        num_samples = 10000
        output_dir = "hindi_data_small"
    else:
        # 100K documents (~500MB final)
        num_samples = 100000
        output_dir = "hindi_data_large"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Download Hindi Wikipedia
    print(f"   Downloading {num_samples} samples from Hindi Wikipedia...")
    dataset = load_dataset(
        "wikimedia/wikipedia",
        "20231101.hi",  # Hindi Wikipedia
        split=f"train[:{num_samples}]",
        trust_remote_code=True
    )
    
    print(f"   Downloaded {len(dataset)} documents")
    
    # Extract text and save as JSONL
    jsonl_path = os.path.join(output_dir, "hindi_text.jsonl")
    txt_path = os.path.join(output_dir, "hindi_text.txt")
    
    print(f"   Saving to {jsonl_path}...")
    
    with open(jsonl_path, 'w', encoding='utf-8') as f_jsonl, \
         open(txt_path, 'w', encoding='utf-8') as f_txt:
        for item in dataset:
            text = item['text'].strip()
            if len(text) > 100:  # Filter very short docs
                # Save JSONL for Megatron
                json.dump({'text': text}, f_jsonl, ensure_ascii=False)
                f_jsonl.write('\n')
                
                # Save plain text for tokenizer training
                f_txt.write(text + '\n')
    
    print(f"   ✅ Saved {jsonl_path} and {txt_path}")
    
    return output_dir, jsonl_path, txt_path


def train_tokenizer(txt_path, output_dir, vocab_size=30000):
    """Train SentencePiece tokenizer for Hindi"""
    print(f"\n🔧 Training SentencePiece tokenizer...")
    print(f"   Vocab size: {vocab_size}")
    print(f"   Input: {txt_path}")
    
    try:
        import sentencepiece as spm
        
        tokenizer_prefix = os.path.join(output_dir, "hindi_tokenizer")
        
        spm.SentencePieceTrainer.train(
            input=txt_path,
            model_prefix=tokenizer_prefix,
            vocab_size=vocab_size,
            character_coverage=0.9995,
            model_type='bpe',
            pad_id=0,
            unk_id=1,
            bos_id=2,
            eos_id=3,
            user_defined_symbols=['<|endoftext|>'],
        )
        
        tokenizer_path = f"{tokenizer_prefix}.model"
        print(f"   ✅ Tokenizer trained: {tokenizer_path}")
        
        return tokenizer_path
        
    except ImportError:
        print("   ❌ SentencePiece not installed!")
        print("   Run: pip install sentencepiece")
        raise


def preprocess_for_megatron(jsonl_path, tokenizer_path, output_dir):
    """Convert to Megatron binary format using preprocess_data.py"""
    print(f"\n⚙️  Converting to Megatron format...")
    
    output_prefix = os.path.join(output_dir, "hindi")
    
    # Check if Megatron-LM is installed
    try:
        import megatron
        megatron_path = Path(megatron.__file__).parent.parent
        preprocess_script = megatron_path / "tools" / "preprocess_data.py"
        
        if not preprocess_script.exists():
            # Try alternative location
            preprocess_script = "Megatron-LM/tools/preprocess_data.py"
    except:
        preprocess_script = "Megatron-LM/tools/preprocess_data.py"
    
    print(f"   Using script: {preprocess_script}")
    print(f"   Input: {jsonl_path}")
    print(f"   Output: {output_prefix}")
    print(f"   Tokenizer: {tokenizer_path}")
    
    # Run Megatron preprocessing
    cmd = [
        "python",
        str(preprocess_script),
        "--input", jsonl_path,
        "--output-prefix", output_prefix,
        "--tokenizer-type", "SentencePieceTokenizer",
        "--tokenizer-model", tokenizer_path,
        "--workers", "8",
        "--append-eod",
    ]
    
    print(f"\n   Running: {' '.join(cmd)}")
    print(f"   This may take a few minutes...\n")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"   ✅ Megatron preprocessing complete!")
        print(f"   Created: {output_prefix}.bin")
        print(f"   Created: {output_prefix}.idx")
        output_prefix += '_text_document'
        # Show file sizes
        bin_size = Path(f"{output_prefix}.bin").stat().st_size / (1024**2)
        idx_size = Path(f"{output_prefix}.idx").stat().st_size / (1024**2)
        print(f"\n   File sizes:")
        print(f"     {output_prefix}.bin: {bin_size:.1f} MB")
        print(f"     {output_prefix}.idx: {idx_size:.1f} MB")
        
        return output_prefix
    else:
        print(f"   ❌ Preprocessing failed!")
        print(f"   Error: {result.stderr}")
        raise RuntimeError("Megatron preprocessing failed")


def main():
    parser = argparse.ArgumentParser(description="Prepare Hindi data for Megatron training")
    parser.add_argument(
        "--dataset-size",
        choices=["small", "large"],
        default="small",
        help="Dataset size: small (~10K docs, 50MB) or large (~100K docs, 500MB)"
    )
    parser.add_argument(
        "--vocab-size",
        type=int,
        default=30000,
        help="Tokenizer vocabulary size"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("HINDI DATA PREPARATION FOR MEGATRON-BRIDGE")
    print("=" * 80)
    print(f"Dataset size: {args.dataset_size}")
    print(f"Vocabulary size: {args.vocab_size}")
    print("=" * 80)
    
    # Step 1: Download data
    output_dir, jsonl_path, txt_path = download_hindi_data(args.dataset_size)
    
    # Step 2: Train tokenizer
    tokenizer_path = train_tokenizer(txt_path, output_dir, args.vocab_size)
    
    # Step 3: Preprocess for Megatron
    output_prefix = preprocess_for_megatron(jsonl_path, tokenizer_path, output_dir)
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ HINDI DATA PREPARATION COMPLETE!")
    print("=" * 80)
    print(f"\n📁 Output directory: {output_dir}/")
    print(f"\n📊 Files created:")
    print(f"   1. {output_prefix}.bin       (training data)")
    print(f"   2. {output_prefix}.idx       (index file)")
    print(f"   3. {tokenizer_path}          (tokenizer)")
    print(f"\n🎯 Ready for Megatron-Bridge training!")
    print(f"\n💡 Next steps:")
    if args.dataset_size == "small":
        print(f"   - Add {output_dir}/ to your git repo")
        print(f"   - Total size: ~50MB (fits in GitHub)")
    else:
        print(f"   - Upload to Hugging Face Hub (too large for git)")
        print(f"   - Run: python upload_to_hf.py --dir {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()

