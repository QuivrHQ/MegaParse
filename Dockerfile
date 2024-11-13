# Using a slim version for a smaller base image
FROM python:3.11.6-slim-bullseye


WORKDIR /app

# Install runtime dependencies
RUN apt-get clean && apt-get update && apt-get install -y \
    libgeos-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    binutils \
    curl \
    git \
    autoconf \
    automake \
    build-essential \
    libtool \
    python-dev \
    build-essential \
    wget \
    gcc \
    # Additional dependencies for document handling
    libmagic-dev \
    poppler-utils \
    tesseract-ocr \
    libreoffice \
    libpq-dev \
    pandoc && \
    rm -rf /var/lib/apt/lists/* && apt-get clean

COPY requirements.lock  pyproject.toml README.md ./
COPY megaparse/sdk/pyproject.toml megaparse/sdk/README.md megaparse/sdk/


RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock

RUN playwright install --with-deps && \
    python -c "from unstructured.nlp.tokenize import download_nltk_packages; download_nltk_packages()" && \
    python -c "import nltk;nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng')" && \
    python -c "from unstructured.partition.model_init import initialize; initialize()"


ENV PYTHONPATH="/app:/app/megaparse/sdk"

COPY . .
EXPOSE 8000

CMD ["uvicorn", "megaparse.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
