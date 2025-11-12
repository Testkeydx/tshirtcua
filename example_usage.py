"""
Example usage of the OrderProcessor class.

This script demonstrates how to use the OrderProcessor programmatically
and how to add SKU information for descriptions and ink colors.
"""

from order_processor import OrderProcessor
import pandas as pd

def example_basic_usage():
    """Basic usage example."""
    print("="*60)
    print("Example 1: Basic Usage")
    print("="*60)
    
    # Initialize processor
    processor = OrderProcessor(input_dir='input', output_dir='output')
    
    # Process all CSV files in input directory
    validated_df, aggregated_df, final_df = processor.process_orders()
    
    print(f"\nProcessed {len(validated_df)} rows")
    print(f"Created {len(aggregated_df)} unique SKU-Size combinations")
    print(f"Final output has {len(final_df)} SKUs")
    print("\nCheck the 'output' directory for results!")


def example_with_sku_info():
    """Example with SKU descriptions and ink colors."""
    print("\n" + "="*60)
    print("Example 2: With SKU Information")
    print("="*60)
    
    # Define SKU information (descriptions and ink colors)
    sku_info = {
        'TEE-101': {
            'description': 'T-Shirt V-Neck',
            'ink_color': 'Black'
        },
        'TEE-205': {
            'description': 'Long Sleeve',
            'ink_color': 'White'
        },
        'HOOD-330': {
            'description': 'Hoodie Full Zip',
            'ink_color': 'Gray'
        },
    }
    
    processor = OrderProcessor(input_dir='input', output_dir='output')
    
    # Process with SKU info
    validated_df, aggregated_df, final_df = processor.process_orders(
        sku_info=sku_info,
        output_prefix='orders_with_info'
    )
    
    print("\nFinal output preview:")
    print(final_df.head())
    print("\nCheck the 'output' directory for results!")


def example_specific_files():
    """Example processing specific files."""
    print("\n" + "="*60)
    print("Example 3: Process Specific Files")
    print("="*60)
    
    # Specify exact files to process
    csv_files = [
        'input/order1.csv',
        'input/order2.csv',
        'input/order3.csv'
    ]
    
    processor = OrderProcessor(input_dir='input', output_dir='output')
    
    try:
        validated_df, aggregated_df, final_df = processor.process_orders(
            csv_files=csv_files,
            output_prefix='specific_orders'
        )
        print(f"\nSuccessfully processed {len(csv_files)} files")
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Make sure the specified files exist!")


def example_step_by_step():
    """Example showing each step individually."""
    print("\n" + "="*60)
    print("Example 4: Step-by-Step Processing")
    print("="*60)
    
    processor = OrderProcessor(input_dir='input', output_dir='output')
    
    # Step 1: Combine files
    combined_df = processor.combine_csv_files()
    print(f"\nStep 1: Combined {len(combined_df)} rows")
    
    # Step 2: Concatenate SKU-Size
    concatenated_df = processor.concatenate_sku_size(combined_df)
    print(f"Step 2: Created concatenated SKUs")
    print(concatenated_df[['Vendor Style', 'Size', 'Concatenated SKU']].head())
    
    # Step 3: Validate
    validated_df = processor.validate_and_correct_data(concatenated_df)
    print(f"\nStep 3: Validated data")
    review_count = (validated_df['Validation_Status'] == 'REVIEW').sum()
    print(f"  - {review_count} rows need review")
    
    # Step 4: Aggregate
    aggregated_df = processor.aggregate_orders(validated_df)
    print(f"\nStep 4: Aggregated to {len(aggregated_df)} unique combinations")
    print(aggregated_df.head())
    
    # Step 5: Final format
    final_df = processor.create_final_format(aggregated_df)
    print(f"\nStep 5: Created final format with {len(final_df)} SKUs")
    print(final_df.head())


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ORDER PROCESSOR - EXAMPLE USAGE")
    print("="*60)
    
    # Run examples (comment out any you don't want to run)
    try:
        example_basic_usage()
    except Exception as e:
        print(f"\nExample 1 failed: {e}")
    
    try:
        example_with_sku_info()
    except Exception as e:
        print(f"\nExample 2 failed: {e}")
    
    try:
        example_specific_files()
    except Exception as e:
        print(f"\nExample 3 failed: {e}")
    
    try:
        example_step_by_step()
    except Exception as e:
        print(f"\nExample 4 failed: {e}")
    
    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)

