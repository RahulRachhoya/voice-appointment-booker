"""Deploy hf_demo/ to Hugging Face Spaces.

Usage:
    python deploy_hf.py --token YOUR_HF_TOKEN

Or set HF_TOKEN environment variable:
    HF_TOKEN=hf_xxx python deploy_hf.py
"""

import argparse
import os
import sys
from pathlib import Path


def deploy(token: str) -> None:
    """Create the HF Space and upload hf_demo/ files."""
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    repo_id = "RahulRachhoya/voice-appointment-booker"

    print(f"Creating Space: {repo_id}")
    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="gradio",
        exist_ok=True,
        private=False,
    )
    print("Space created (or already exists).")

    hf_demo_dir = Path(__file__).parent / "hf_demo"
    for file_path in hf_demo_dir.iterdir():
        if file_path.is_file():
            print(f"Uploading {file_path.name}...")
            api.upload_file(
                path_or_fileobj=str(file_path),
                path_in_repo=file_path.name,
                repo_id=repo_id,
                repo_type="space",
            )

    print("\nDeployment complete!")
    print(f"View your Space at: https://huggingface.co/spaces/{repo_id}")
    print("\nRemember to add secrets in Space Settings:")
    print("  GROQ_API_KEY")
    print("  ELEVENLABS_API_KEY")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy to HF Spaces")
    parser.add_argument("--token", default=os.getenv("HF_TOKEN", ""), help="HF API token")
    args = parser.parse_args()

    if not args.token:
        print("ERROR: No HF token found.")
        print("Get a token from https://huggingface.co/settings/tokens")
        print("Then run: python deploy_hf.py --token hf_YOUR_TOKEN")
        sys.exit(1)

    deploy(args.token)
