#!/usr/bin/env python3
"""
Assessment 4 (NER) Autograder - FIXED VERSION
Evaluates submitted NER models on in-domain and out-of-domain test sets.

This version uses a virtual environment approach to avoid PEP 668 issues.
"""

import json
import sys
import subprocess
import os
from pathlib import Path

# ============================================================================
# AUTO-INSTALL DEPENDENCIES
# ============================================================================
def ensure_dependencies():
    """Install required packages in a virtual environment if needed"""
    required_packages = {
        'torch': 'torch',
        'transformers': 'transformers',
        'seqeval': 'seqeval',
    }
    
    # Check if we're already in a virtual environment or if packages exist
    missing_packages = []
    for import_name, pip_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(pip_name)
    
    if not missing_packages:
        return  # All packages already available
    
    print(f"📦 Installing missing dependencies: {', '.join(missing_packages)}", file=sys.stderr)
    print("⏳ This may take a few minutes on first run...", file=sys.stderr)
    
    # Get the directory where this script lives
    script_dir = Path(__file__).parent.absolute()
    venv_dir = script_dir / '.venv_autograder'
    
    # Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        print(f"🔧 Creating virtual environment at {venv_dir}...", file=sys.stderr)
        try:
            subprocess.run(
                [sys.executable, '-m', 'venv', str(venv_dir)],
                check=True,
                capture_output=True,
                timeout=120
            )
            print("✅ Virtual environment created", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(json.dumps({
                "success": False,
                "error": f"Failed to create virtual environment: {e.stderr.decode()}"
            }))
            sys.exit(1)
        except Exception as e:
            print(json.dumps({
                "success": False,
                "error": f"Failed to create virtual environment: {str(e)}"
            }))
            sys.exit(1)
    
    # Determine the python executable in the venv
    if os.name == 'nt':  # Windows
        venv_python = venv_dir / 'Scripts' / 'python.exe'
        venv_pip = venv_dir / 'Scripts' / 'pip.exe'
    else:  # Unix/Linux/Mac
        venv_python = venv_dir / 'bin' / 'python'
        venv_pip = venv_dir / 'bin' / 'pip'
    
    # Install packages in the virtual environment
    try:
        print(f"📥 Installing packages in virtual environment...", file=sys.stderr)
        install_cmd = [str(venv_pip), 'install'] + missing_packages
        print(f"Running: {' '.join(install_cmd)}", file=sys.stderr)
        
        result = subprocess.run(
            install_cmd,
            capture_output=True,
            text=True,
            timeout=900  # 15 minute timeout
        )
        
        if result.returncode != 0:
            print(json.dumps({
                "success": False,
                "error": f"Failed to install dependencies: {result.stderr}"
            }))
            sys.exit(1)
        
        print("✅ Dependencies installed successfully in virtual environment", file=sys.stderr)
        
        # Re-execute this script using the venv Python
        print(f"🔄 Re-executing script with virtual environment Python...", file=sys.stderr)
        venv_args = [str(venv_python), __file__] + sys.argv[1:]
        os.execv(str(venv_python), venv_args)
        
    except subprocess.TimeoutExpired:
        print(json.dumps({
            "success": False,
            "error": "Installation timed out after 15 minutes"
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"Failed to install dependencies: {str(e)}"
        }))
        sys.exit(1)

# Ensure dependencies are installed BEFORE importing them
ensure_dependencies()

# ============================================================================
# NOW IT'S SAFE TO IMPORT THE PACKAGES
# ============================================================================
import time
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from seqeval.metrics import f1_score, classification_report

def load_jsonl(path):
    """Load JSONL file into list of dicts"""
    with open(path, "r") as f:
        return [json.loads(line) for line in f]

def evaluate_split(test_path, split_name, model, tokenizer, device):
    """Evaluate model on a test split"""
    test_data = load_jsonl(test_path)
    tokens_list = [ex["tokens"] for ex in test_data]
    true_tags = [ex["ner_tags"] for ex in test_data]

    pred_tags = []
    for tokens_ in tokens_list:
        enc = tokenizer(tokens_, is_split_into_words=True,
                        return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            logits = model(**inputs).logits
        preds = logits.argmax(-1).cpu().tolist()[0]

        # Align back to words
        word_ids = enc.word_ids(batch_index=0)
        labels, prev = [], None
        for wid, pid in zip(word_ids, preds):
            if wid is None or wid == prev:
                continue
            labels.append(model.config.id2label[pid])
            prev = wid
        pred_tags.append(labels)

    f1 = f1_score(true_tags, pred_tags)
    print(f"\n=== {split_name.upper()} Evaluation ===", file=sys.stderr)
    print(classification_report(true_tags, pred_tags), file=sys.stderr)
    print(f"{split_name.upper()} Macro F1: {f1:.4f}", file=sys.stderr)
    return f1

def measure_latency(model, tokenizer, device):
    """Measure inference latency"""
    sample = "Nike shoes"
    inputs = tokenizer(sample, return_tensors="pt", truncation=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    # Warm-up
    _ = model(**inputs)
    if device == "cuda":
        torch.cuda.synchronize()
    
    # Timed inference
    t0 = time.time()
    with torch.no_grad():
        _ = model(**inputs)
    if device == "cuda":
        torch.cuda.synchronize()
    latency = round(time.time() - t0, 4)
    
    print(f"\nLatency (s): {latency:.4f}", file=sys.stderr)
    return latency

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: python assessment4_autograder.py <submission_dir>"
        }))
        sys.exit(1)

    submission_dir = sys.argv[1]
    
    # Get script directory for test data
    script_dir = Path(__file__).parent
    test_id_path = script_dir / "data" / "product_ner_test_id.jsonl"
    test_ood_path = script_dir / "data" / "product_ner_train.jsonl"
    
    # Verify test files exist
    if not test_id_path.exists():
        print(json.dumps({
            "success": False,
            "error": f"Test file not found: {test_id_path}"
        }))
        sys.exit(1)
    
    if not test_ood_path.exists():
        print(json.dumps({
            "success": False,
            "error": f"Test file not found: {test_ood_path}"
        }))
        sys.exit(1)
    
    # Look for model directory
    model_dir = Path(submission_dir) / "model"
    if not model_dir.exists():
        # Try submission_dir itself
        model_dir = Path(submission_dir)
    
    if not (model_dir / "config.json").exists():
        print(json.dumps({
            "success": False,
            "error": f"Model not found in {submission_dir}"
        }))
        sys.exit(1)
    
    print(f"🔍 Loading model from: {model_dir}", file=sys.stderr)
    print(f"🧪 Using test files:", file=sys.stderr)
    print(f"   - ID:  {test_id_path}", file=sys.stderr)
    print(f"   - OOD: {test_ood_path}", file=sys.stderr)
    
    try:
        # Load model and tokenizer
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️  Using device: {device}", file=sys.stderr)
        
        try:
            model = AutoModelForTokenClassification.from_pretrained(
                str(model_dir), 
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                trust_remote_code=True
            ).to(device)
        except Exception:
            model = AutoModelForTokenClassification.from_pretrained(
                str(model_dir)
            ).to(device)
        
        tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        
        # Evaluate both splits
        id_f1 = evaluate_split(test_id_path, "id", model, tokenizer, device)
        ood_f1 = evaluate_split(test_ood_path, "ood", model, tokenizer, device)
        
        # Measure latency
        latency = measure_latency(model, tokenizer, device)
        
        # Output results as JSON
        results = {
            "success": True,
            "id_macro_f1": float(id_f1),
            "ood_macro_f1": float(ood_f1),
            "latency_sec": float(latency)
        }
        
        print(json.dumps(results))
        
    except Exception as e:
        import traceback
        print(json.dumps({
            "success": False,
            "error": f"{str(e)}\n{traceback.format_exc()}"
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
