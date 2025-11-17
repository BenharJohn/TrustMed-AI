"""
Script to download the mimic_ex dataset from Hugging Face
"""
import os
from datasets import load_dataset

def download_mimic_ex():
    print("Downloading mimic_ex dataset from Hugging Face...")
    print("This may take a few minutes depending on your connection speed.\n")

    try:
        # Load the dataset from Hugging Face
        dataset = load_dataset("Morson/mimic_ex")

        # Create output directory
        output_dir = "./dataset/mimic_ex"
        os.makedirs(output_dir, exist_ok=True)

        # Save the dataset
        print(f"Saving dataset to {output_dir}...")
        dataset.save_to_disk(output_dir)

        print(f"\n✓ Dataset successfully downloaded to {output_dir}")
        print(f"Dataset info:")
        print(f"  - Splits: {list(dataset.keys())}")
        for split_name, split_data in dataset.items():
            print(f"  - {split_name}: {len(split_data)} examples")

    except Exception as e:
        print(f"✗ Error downloading dataset: {e}")
        print("\nYou can manually download from: https://huggingface.co/datasets/Morson/mimic_ex")
        return False

    return True

if __name__ == "__main__":
    success = download_mimic_ex()
    exit(0 if success else 1)
