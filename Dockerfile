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

COPY requirements.lock  pyproject.toml README.md ./
COPY libs/megaparse/pyproject.toml libs/megaparse/README.md libs/megaparse/
COPY libs/megaparse_sdk/pyproject.toml libs/megaparse_sdk/README.md libs/megaparse_sdk/

RUN pip install uv
RUN uv pip install --no-cache --system -r requirements.lock

RUN playwright install --with-deps
RUN python3 - -m nltk.downloader all

COPY . .

RUN uv pip install --no-cache --system /app/libs/megaparse /app/libs/megaparse_sdk

EXPOSE 8000
CMD ["uvicorn", "megaparse.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
