# MegaParse Benchmarks

This document explains the benchmarking methodology, how to run benchmarks locally, and how to interpret the results.

## Methodology

### Similarity Ratio Calculation

The similarity ratio measures how accurately a parser extracts and preserves document content:

1. **Document Preparation**
   - Original document converted to reference markdown
   - Parser output compared against reference
   - Similarity calculated using string comparison algorithms

2. **Scoring Criteria**
   - Text content preservation
   - Structure maintenance (headers, lists)
   - Table formatting accuracy
   - Image reference preservation

### Parser Comparison

Current benchmark results:

| Parser                        | Similarity Ratio | Use Case                    |
| ----------------------------- | --------------- | --------------------------- |
| megaparse_vision              | 0.87            | Complex layouts, images     |
| unstructured_with_check_table | 0.77            | Tables, structured content  |
| unstructured                  | 0.59            | Simple text documents       |
| llama_parser                  | 0.33            | PDF-specific parsing        |

## Running Benchmarks Locally

1. **Setup**
   ```bash
   # Install dependencies
   UV_INDEX_STRATEGY=unsafe-first-match uv pip sync

   # Prepare test documents
   mkdir -p benchmark/test_docs
   cp your_test_docs/* benchmark/test_docs/
   ```

2. **Execute Tests**
   ```bash
   # Run all benchmarks
   python evaluations/script.py

   # Test specific parser
   python evaluations/script.py --parser megaparse_vision
   ```

3. **Add Custom Parser**
   ```python
   # In evaluations/script.py
   class CustomParser(BaseParser):
       def convert(self, file_path: str, strategy: StrategyEnum = StrategyEnum.AUTO) -> str:
           # Your implementation
           pass

   # Add to config
   PARSER_CONFIGS.append({
       "name": "custom_parser",
       "parser": CustomParser(),
       "description": "Your custom parser implementation"
   })
   ```

## Interpreting Results

### Similarity Ratio Components

The similarity ratio (0.0 to 1.0) considers multiple factors:

1. **Content Accuracy (50%)**
   - Text extraction accuracy
   - Character encoding preservation
   - Whitespace handling

2. **Structure Preservation (30%)**
   - Header hierarchy maintenance
   - List formatting
   - Table structure
   - Image placement

3. **Metadata Retention (20%)**
   - Document properties
   - Font information
   - Style attributes

### Performance Thresholds

- **Excellent**: > 0.85
  - Suitable for critical document processing
  - Maintains complex layouts
  - Preserves all content types

- **Good**: 0.70 - 0.85
  - Suitable for general use
  - Minor formatting issues
  - Good content preservation

- **Fair**: 0.50 - 0.70
  - Basic content extraction
  - May lose complex formatting
  - Suitable for simple documents

- **Poor**: < 0.50
  - Significant content loss
  - Structure not preserved
  - Not recommended for production

### Common Issues

1. **Low Similarity Scores**
   - Check input document quality
   - Verify parser configuration
   - Ensure correct strategy selection

2. **Inconsistent Results**
   - Document complexity variation
   - Parser-specific limitations
   - Strategy mismatches

3. **Performance Problems**
   - Resource constraints
   - Large document handling
   - Concurrent processing limits

## Contributing Benchmarks

1. **Add New Test Cases**
   - Place documents in `benchmark/test_docs/`
   - Update reference outputs
   - Document special handling

2. **Improve Methodology**
   - Enhance similarity metrics
   - Add new evaluation criteria
   - Optimize performance

3. **Submit Results**
   - Run complete benchmark suite
   - Document environment details
   - Create pull request with results

## Best Practices

1. **Document Selection**
   - Use representative samples
   - Include edge cases
   - Vary complexity levels

2. **Environment Setup**
   - Clean test environment
   - Consistent dependencies
   - Resource monitoring

3. **Results Reporting**
   - Include all metrics
   - Document anomalies
   - Provide context

For more information on the parsers and their configurations, see the [Architecture Documentation](../ARCHITECTURE.md).
