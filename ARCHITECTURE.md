# MegaParse Architecture

This document provides a comprehensive overview of the MegaParse system architecture, including component relationships, data flow, and core implementation details.

## System Components

### 1. Core Parser Library (megaparse)

The core library provides the fundamental parsing capabilities:

```
libs/megaparse/
├── src/megaparse/
│   ├── parser/           # Parser implementations
│   │   ├── base.py      # Abstract base parser
│   │   ├── unstructured_parser.py
│   │   ├── megaparse_vision.py
│   │   ├── llama.py
│   │   └── doctr_parser.py
│   ├── api/             # FastAPI application
│   │   └── app.py       # API endpoints
│   └── checker/         # Format utilities
```

### 2. Client SDK (megaparse_sdk)

The SDK provides a high-level interface for API interaction:

```
libs/megaparse_sdk/
├── src/megaparse_sdk/
│   ├── client/          # API client implementation
│   └── schema/          # Data models and configurations
```

### 3. FastAPI Interface

The API layer exposes parsing capabilities as HTTP endpoints:

- `/v1/file`: File upload and parsing
- `/v1/url`: URL content extraction and parsing
- `/healthz`: Health check endpoint

## Data Flow

1. **Document Input**
   ```
   Client → SDK → API → Parser Library
   ```
   - Client submits document through SDK
   - SDK validates and sends to API
   - API routes to appropriate parser
   - Parser processes and returns results

2. **Parser Selection**
   ```
   Input → Strategy Selection → Parser Assignment → Processing
   ```
   - Input type determines available strategies
   - Strategy influences parser selection
   - Parser processes according to strategy

## Core Classes and Flow

### MegaParse Class

The central orchestrator managing the parsing workflow:

```python
class MegaParse:
    def __init__(self, parser: BaseParser):
        self.parser = parser

    def load(self, file_path: str, strategy: StrategyEnum = StrategyEnum.AUTO) -> str:
        # 1. Validate input
        # 2. Select strategy
        # 3. Process document
        # 4. Format output
```

### Parser Hierarchy

```
BaseParser (Abstract)
├── UnstructuredParser
│   └── Basic document parsing
├── MegaParseVision
│   └── AI-powered parsing (GPT-4V)
├── LlamaParser
│   └── Enhanced PDF parsing
└── DoctrParser
    └── OCR-based parsing
```

### Strategy Selection

The `StrategyEnum` determines parsing behavior:

- `AUTO`: Automatic strategy selection based on input
- `FAST`: Optimized for speed (simple documents)
- `HI_RES`: Maximum accuracy (complex documents)

## Implementation Details

### Parser Selection Logic

1. **Input Analysis**
   - File type detection
   - Content complexity assessment
   - Available parser evaluation

2. **Strategy Application**
   - AUTO: Selects optimal parser
   - FAST: Prioritizes UnstructuredParser
   - HI_RES: Prefers MegaParseVision/LlamaParser

### Error Handling

The system implements multiple error handling layers:

1. **SDK Level**
   - Input validation
   - Connection error handling
   - Rate limiting management

2. **API Level**
   - Request validation
   - Authentication
   - Resource management

3. **Parser Level**
   - Format-specific error handling
   - Processing error recovery
   - Output validation

## Deployment Architecture

### Docker Support

Two deployment options:

1. **Standard Image**
   ```yaml
   # Basic parsing capabilities
   docker compose up
   ```

2. **GPU-Enabled Image**
   ```yaml
   # Enhanced processing with GPU support
   docker compose -f docker-compose.gpu.yml up
   ```

### API Server

- FastAPI application
- Uvicorn ASGI server
- Interactive documentation at `/docs`
- Health monitoring at `/healthz`

## Extension Points

### Custom Parser Implementation

Extend `BaseParser` for custom parsing logic:

```python
class CustomParser(BaseParser):
    def convert(self, file_path: str, strategy: StrategyEnum) -> str:
        # Custom implementation
        pass

    async def aconvert(self, file_path: str, strategy: StrategyEnum) -> str:
        # Async implementation
        pass
```

### Strategy Customization

Create custom strategies by extending `StrategyEnum`:

```python
class CustomStrategy(StrategyEnum):
    CUSTOM = "custom"
    # Define behavior in parser implementation
```
