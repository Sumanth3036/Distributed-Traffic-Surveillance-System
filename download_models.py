"""
Download required YOLO models for the traffic surveillance system.
This script downloads the actual model weights that are stored in Git LFS.
"""

import os
import requests
from pathlib import Path

# Model download URLs (from the Git LFS pointers)
MODELS = {
    "helmet_detection.pt": {
        "url": "https://media.githubusercontent.com/media/lohith-kandibanda/Distributed-Traffic-Surveillance-Image-Processing-System-with-Api-Authentication/main/models/helmet_detection.pt",
        "size": 117274914,
        "sha256": "63dd3ccb3bbbb4a9ab5e73ad90447442ca43ec37049029b51b5518ce382c9471"
    },
    "yolo11m.pt": {
        "url": "https://media.githubusercontent.com/media/lohith-kandibanda/Distributed-Traffic-Surveillance-Image-Processing-System-with-Api-Authentication/main/models/yolo11m.pt",
        "size": 40684120,
        "sha256": "c806fe51d7e905336cda56a2e7f08212f7e8a7d06530460f5f8e3050b0e8691f"
    }
}

def download_file(url, destination, expected_size):
    """Download a file with progress indication."""
    print(f"📥 Downloading {destination.name}...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
        
        print(f"\n✅ Downloaded {destination.name} ({downloaded} bytes)")
        
        # Verify size
        actual_size = destination.stat().st_size
        if actual_size != expected_size:
            print(f"⚠️  Warning: Size mismatch. Expected {expected_size}, got {actual_size}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to download {destination.name}: {e}")
        return False

def main():
    # Get models directory
    script_dir = Path(__file__).parent
    models_dir = script_dir / "models"
    
    print("🚀 Starting model download...")
    print(f"📁 Models directory: {models_dir}\n")
    
    # Create models directory if it doesn't exist
    models_dir.mkdir(exist_ok=True)
    
    success_count = 0
    
    for model_name, info in MODELS.items():
        model_path = models_dir / model_name
        
        # Check if file already exists and has correct size
        if model_path.exists():
            current_size = model_path.stat().st_size
            if current_size == info["size"]:
                print(f"✅ {model_name} already exists with correct size. Skipping.")
                success_count += 1
                continue
            else:
                print(f"⚠️  {model_name} exists but size is wrong ({current_size} vs {info['size']}). Re-downloading...")
        
        # Download the model
        if download_file(info["url"], model_path, info["size"]):
            success_count += 1
        
        print()
    
    print("=" * 60)
    if success_count == len(MODELS):
        print("✅ All models downloaded successfully!")
        print("\nYou can now run: docker-compose up --build")
    else:
        print(f"⚠️  Downloaded {success_count}/{len(MODELS)} models")
        print("\nTrying alternative method...")
        print_alternative_instructions()

def print_alternative_instructions():
    """Print manual download instructions."""
    print("\n" + "=" * 60)
    print("📋 ALTERNATIVE: Manual Download Instructions")
    print("=" * 60)
    print("\nIf automatic download fails, manually download from:")
    print("\n1. Helmet Detection Model (117 MB):")
    print("   https://github.com/lohith-kandibanda/Distributed-Traffic-Surveillance-Image-Processing-System-with-Api-Authentication/raw/main/models/helmet_detection.pt")
    print("\n2. YOLOv11m Model (40 MB):")
    print("   https://github.com/lohith-kandibanda/Distributed-Traffic-Surveillance-Image-Processing-System-with-Api-Authentication/raw/main/models/yolo11m.pt")
    print("\nOr use pre-trained YOLO models:")
    print("   - Replace yolo11m.pt with: https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11m.pt")
    print("   - For helmet detection, you may need to train your own or use yolo11n.pt")
    print("=" * 60)

if __name__ == "__main__":
    main()
