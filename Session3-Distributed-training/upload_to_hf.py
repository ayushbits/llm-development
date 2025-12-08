#!/usr/bin/env python3
"""
Upload preprocessed Hindi data to Hugging Face Hub

This solves the GitHub 100MB file size limit by hosting large files on HF.

Usage:
    # First, login to Hugging Face
    huggingface-cli login
    
    # Then upload
    python upload_to_hf.py --dir hindi_data_large --repo ayushbits/hindi-gpt-workshop-data
"""

import argparse
import os
from pathlib import Path
from huggingface_hub import HfApi, create_repo


def upload_to_huggingface(data_dir, repo_id, private=False):
    """Upload preprocessed data to Hugging Face Hub"""
    
    print("=" * 80)
    print("UPLOAD TO HUGGING FACE HUB")
    print("=" * 80)
    print(f"Source directory: {data_dir}")
    print(f"Destination repo: {repo_id}")
    print(f"Private: {private}")
    print("=" * 80)
    
    # Verify data directory exists
    if not os.path.exists(data_dir):
        raise ValueError(f"Directory not found: {data_dir}")
    
    # Check for required files
    required_files = [
        "hindi_text_document.bin",
        "hindi_text_document.idx",
        "hindi_tokenizer.model"
    ]
    
    print("\n📋 Checking files...")
    for filename in required_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024**2)
            print(f"   ✅ {filename} ({size_mb:.1f} MB)")
        else:
            print(f"   ❌ {filename} NOT FOUND!")
            raise FileNotFoundError(f"Required file missing: {filename}")
    
    # Create repository
    print(f"\n🔧 Creating Hugging Face repository...")
    try:
        create_repo(
            repo_id=repo_id,
            repo_type="dataset",
            private=private,
            exist_ok=True
        )
        print(f"   ✅ Repository created: https://huggingface.co/datasets/{repo_id}")
    except Exception as e:
        print(f"   ℹ️  Repository may already exist: {e}")
    
    # Upload files
    print(f"\n📤 Uploading files to Hugging Face Hub...")
    print(f"   This may take a few minutes depending on file size...")
    
    api = HfApi()
    
    for filename in required_files:
        filepath = os.path.join(data_dir, filename)
        print(f"\n   Uploading {filename}...")
        
        api.upload_file(
            path_or_fileobj=filepath,
            path_in_repo=filename,
            repo_id=repo_id,
            repo_type="dataset",
        )
        
        print(f"   ✅ {filename} uploaded")
    
    # Upload README
    readme_content = f"""# Hindi GPT Workshop Data

Preprocessed Hindi text data for LLM training workshop.

## Files

- `hindi_text_document.bin`: Training data in Megatron format
- `hindi_text_document.idx`: Index file for training data
- `hindi_tokenizer.model`: SentencePiece tokenizer

## Usage

```python
from huggingface_hub import hf_hub_download

# Download all files
for filename in ["hindi_text_document.bin", "hindi_text_document.idx", "hindi_tokenizer.model"]:
    hf_hub_download(
        repo_id="{repo_id}",
        filename=filename,
        local_dir="./data",
        repo_type="dataset"
    )
```

## Dataset Info

- Source: Hindi Wikipedia
- Format: Megatron-LM binary format
- Tokenizer: SentencePiece (30K vocab)
- Optimized for: NVIDIA Megatron-Bridge training

## Workshop

This data is prepared for the LLM Development workshop.
See: https://github.com/ayushbits/llm-development
"""
    
    readme_path = os.path.join(data_dir, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"\n   Uploading README.md...")
    api.upload_file(
        path_or_fileobj=readme_path,
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="dataset",
    )
    print(f"   ✅ README.md uploaded")
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ UPLOAD COMPLETE!")
    print("=" * 80)
    print(f"\n🌐 Dataset URL: https://huggingface.co/datasets/{repo_id}")
    print(f"\n📝 Participants can download with:")
    print(f"""
from huggingface_hub import hf_hub_download

for filename in ["hindi_text_document.bin", "hindi_text_document.idx", "hindi_tokenizer.model"]:
    hf_hub_download(
        repo_id="{repo_id}",
        filename=filename,
        local_dir="./data",
        repo_type="dataset"
    )
""")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Upload Hindi data to Hugging Face Hub")
    parser.add_argument(
        "--dir",
        required=True,
        help="Directory containing preprocessed data (e.g., hindi_data_large)"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Hugging Face repository ID (e.g., ayushbits/hindi-gpt-workshop-data)"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Make repository private"
    )
    
    args = parser.parse_args()
    
    # Check if logged in to Hugging Face
    print("\n🔐 Checking Hugging Face authentication...")
    try:
        api = HfApi()
        user_info = api.whoami()
        print(f"   ✅ Logged in as: {user_info['name']}")
    except Exception as e:
        print(f"   ❌ Not logged in to Hugging Face!")
        print(f"\n   Please run: huggingface-cli login")
        print(f"   Or set HF_TOKEN environment variable")
        return
    
    # Upload
    upload_to_huggingface(args.dir, args.repo, args.private)


if __name__ == "__main__":
    main()

