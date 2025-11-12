# SPS Commerce Order Processing Automation

Automated processing pipeline for shirt orders downloaded from SPS Commerce. This script combines multiple order CSV files, validates and corrects data, and aggregates quantities for printing.

## Features

1. **Combine Multiple CSV Files**: Automatically combines all CSV files from SPS Commerce into one dataset
2. **SKU-Size Concatenation**: Creates standardized `VendorStyle-Size` format
3. **Intelligent Data Validation**: 
   - Corrects common size typos and variations (e.g., "med" → "M", "xl" → "XL")
   - Extracts size from concatenated SKU if size column is missing
   - Flags rows requiring manual review
4. **Quantity Aggregation**: Sums quantities for unique SKU-Size combinations
5. **Final Format Output**: Creates printer-ready format with size columns

## Installation

1. Install Python 3.8 or higher
2. (Recommended) Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Place your CSV files in the `input` directory, then run:

```bash
python order_processor.py
```

The script will:
- Read all CSV files from the `input` directory
- Process and validate the data
- Save outputs to the `output` directory

### Process Specific Files

```bash
python order_processor.py --files input/order1.csv input/order2.csv input/order3.csv
```

### Custom Input/Output Directories

```bash
python order_processor.py --input-dir /path/to/orders --output-dir /path/to/results
```

### Custom Output Prefix

```bash
python order_processor.py --output-prefix murdoch_orders
```

## Input Format

The input CSV files should have the following columns:
- `Quantity`: Number of items ordered
- `Vendor Style`: The SKU/vendor style code (e.g., "TEE-101")
- `Size`: Size of the item (e.g., "M", "L", "XL")

Example:
```csv
Quantity,Vendor Style,Size
2,TEE-101,M
1,TEE-101,L
3,TEE-205,S
```

## Output Files

The script generates three output files:

1. **`*_validated_*.csv`**: Validated data with corrected sizes and validation status
   - Columns: `Final SKU`, `Final Size`, `Quantity`, `Validation_Status`, `Original_Vendor_Style`, `Original_Size`
   - Rows marked `REVIEW` in `Validation_Status` need manual attention

2. **`*_aggregated_*.csv`**: Aggregated quantities by unique SKU-Size
   - Columns: `Full SKU (SKU-Size)`, `Total Quantity`, `Size`, `Validation_Status`

3. **`*_final_*.csv`**: Printer-ready format with size columns
   - Columns: `SKU`, `Description`, `Ink Color`, `XS`, `S`, `M`, `L`, `XL`, `2XL`, etc.
   - Quantities are distributed across size columns

## Size Standardization

The script automatically normalizes size variations to standard formats:
- `XS`, `S`, `M`, `L`, `XL`, `2XL`, `3XL`, `4XL`

Common corrections:
- "med" → "M"
- "medium" → "M"
- "xl" → "XL"
- "xxl" → "2XL"
- "2xl" → "2XL"

## Error Handling

- Missing sizes are extracted from the concatenated SKU when possible
- Invalid sizes are flagged for manual review
- All processing steps are logged to `order_processing.log`
- Rows requiring review are marked in the `Validation_Status` column

## Example Workflow

1. Download all order CSV files from SPS Commerce
2. Place them in the `input` directory (or specify with `--input-dir`)
3. Run the script: `python order_processor.py`
4. Check the `output` directory for:
   - Validated data (review any rows marked "REVIEW")
   - Aggregated quantities
   - Final printer-ready format
5. Review the log file `order_processing.log` for any warnings

## Integration with SKU Information

To add descriptions and ink colors to the final output, you can modify the script to include a `sku_info` dictionary:

```python
sku_info = {
    'TEE-101': {'description': 'T-Shirt V-Neck', 'ink_color': 'Black'},
    'TEE-205': {'description': 'Long Sleeve', 'ink_color': 'White'},
    'HOOD-330': {'description': 'Hoodie Full Zip', 'ink_color': 'Gray'},
}

processor = OrderProcessor()
validated_df, aggregated_df, final_df = processor.process_orders(sku_info=sku_info)
```

## Troubleshooting

### No CSV files found
- Ensure CSV files are in the `input` directory
- Check file extensions are `.csv` (case-sensitive)
- Use `--files` to specify exact file paths

### Validation errors
- Check `order_processing.log` for detailed error messages
- Review rows marked `REVIEW` in the validated output
- Manually correct any problematic rows and re-run

### Missing columns
- Ensure input CSV files have: `Quantity`, `Vendor Style`, `Size`
- Column names are case-sensitive

## Logging

All processing steps are logged to `order_processing.log` and displayed in the console. Check this file for:
- File loading status
- Validation warnings
- Aggregation summaries
- Error messages

## Orgo Agent Automation

This project includes an automated agent that uses Orgo and Claude Sonnet 4.5 to automate the entire order processing workflow.

### Prerequisites

1. **Orgo API Key**: Sign up at [orgo.ai](https://orgo.ai) to get your API key
2. **Anthropic API Key**: Get your API key from [Anthropic Console](https://console.anthropic.com)
3. **Set Environment Variables**:

```bash
export ORGO_API_KEY=your_orgo_api_key
export ANTHROPIC_API_KEY=your_anthropic_api_key
```

Or create a `.env` file in the project root:
```
ORGO_API_KEY=your_orgo_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Using the Orgo Agent

The agent automates the complete workflow:
1. Downloads CSV files from GitHub Pages (simulating SPS Commerce downloads)
2. Opens VS Code and runs `order_processor.py`
3. Verifies output files are created

**Basic Usage**:

```bash
python orgo_agent.py --github-url https://your-username.github.io/your-repo/
```

**Advanced Options**:

```bash
python orgo_agent.py \
  --github-url https://your-username.github.io/your-repo/ \
  --project-path /path/to/project \
  --model claude-sonnet-4-5-20250929 \
  --max-iterations 30
```

### Agent Features

- **Claude Sonnet 4.5**: Uses the latest Claude model with computer use capabilities
- **Extended Thinking**: Enabled for better reasoning and decision-making
- **Progress Tracking**: Real-time callbacks show what the agent is doing
- **Error Handling**: Comprehensive error handling with cleanup
- **Output Verification**: Automatically verifies that output files are created

### Agent Workflow

1. **Initialization**: Connects to Orgo virtual desktop
2. **CSV Download**: Navigates to GitHub Pages and downloads all CSV files to `input/` directory
3. **VS Code Execution**: Opens VS Code, navigates to project, and runs `order_processor.py`
4. **Verification**: Checks that output files exist in `output/` directory
5. **Cleanup**: Properly destroys the computer instance

### Logging

The agent logs all activities to `orgo_agent.log` and displays progress in the console. Check the log file for:
- Agent actions and decisions
- Tool usage (clicks, typing, etc.)
- Errors and warnings
- Execution results

### Troubleshooting

**API Key Errors**:
- Ensure both `ORGO_API_KEY` and `ANTHROPIC_API_KEY` are set
- Verify keys are valid and have sufficient credits/quota

**Download Issues**:
- Verify the GitHub Pages URL is accessible
- Check that CSV files are available on the page
- Ensure the agent can access the internet

**VS Code Execution Issues**:
- Make sure VS Code is installed on the virtual desktop
- Verify `order_processor.py` exists in the project directory
- Check that Python is installed and accessible

**Output Verification Fails**:
- Review `orgo_agent.log` for execution errors
- Check that `order_processor.py` ran successfully
- Verify output directory permissions

## License

This script is provided as-is for internal use.

