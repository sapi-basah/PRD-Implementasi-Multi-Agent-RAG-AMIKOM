import os
from huggingface_hub import snapshot_download

def download_e5_model():
    model_id = "Xenova/multilingual-e5-small"
    revision = "761b726dd34fb83930e26aab4e9ac3899aa1fa78"
    
    # Target directory based on Roadmap PDF
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(base_dir, "models", "e5", revision)
    
    print(f"Downloading {model_id} (revision: {revision})")
    print(f"Target directory: {target_dir}")
    
    os.makedirs(target_dir, exist_ok=True)
    
    try:
        # Download specific files required by the Roadmap
        allow_patterns = ["config.json", "tokenizer.json", "tokenizer_config.json", "onnx/model_int8.onnx"]
        
        snapshot_download(
            repo_id=model_id,
            revision=revision,
            local_dir=target_dir,
            local_dir_use_symlinks=False,
            allow_patterns=allow_patterns
        )
        print("\nDownload complete! Model artifacts saved to:")
        print(target_dir)
    except Exception as e:
        print(f"\nError downloading model: {e}")

if __name__ == "__main__":
    download_e5_model()
