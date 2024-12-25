"""Script to download required NLTK resources."""

import nltk


def download_nltk_resources():
    """Download required NLTK resources."""
    resources = [
        "punkt",
        "punkt_tab",
        "averaged_perceptron_tagger",
        "averaged_perceptron_tagger_eng",
        "maxent_ne_chunker",
        "words",
        "stopwords",
    ]
    for resource in resources:
        print(f"Downloading {resource}...")
        nltk.download(resource)


if __name__ == "__main__":
    download_nltk_resources()
