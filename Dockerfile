FROM python:3.11.10-slim-bullseye

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get upgrade && apt-get install -y \
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

COPY . .

RUN pip install uv
RUN UV_INDEX_STRATEGY=unsafe-first-match uv pip install --no-cache --system -e ./libs/megaparse
RUN UV_INDEX_STRATEGY=unsafe-first-match uv pip install --no-cache --system -e ./libs/megaparse_sdk

RUN playwright install --with-deps
RUN python3 - -m nltk.downloader all

EXPOSE 8000
CMD ["uvicorn", "megaparse.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
