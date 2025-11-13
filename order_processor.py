"""
SPS Commerce Order Processing Automation
=========================================

This script automates the processing of shirt orders downloaded from SPS Commerce:
1. Combines multiple CSV order files into one
2. Concatenates Vendor Style and Size into SKU-Size format
3. Validates and corrects size errors/missing data
4. Aggregates quantities by unique SKU-Size combinations
5. Outputs final formatted CSV for printing

Author: Automation Script
Date: 2025
"""

import pandas as pd
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

# Google Drive API imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('order_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SizeValidator:
    """Handles size validation, correction, and standardization."""
    
    # Standard size mappings (normalize variations to standard format)
    SIZE_MAPPINGS = {
        # Standard sizes
        'XS': ['xs', 'extra small', 'extra-small', 'x-small'],
        'S': ['s', 'small'],
        'M': ['m', 'medium', 'med'],
        'L': ['l', 'large'],
        'XL': ['xl', 'extra large', 'extra-large', 'x-large'],
        '2XL': ['2xl', 'xxl', '2x', 'xx-large', '2xl', 'double xl'],
        '3XL': ['3xl', 'xxxl', '3x', 'triple xl'],
        '4XL': ['4xl', 'xxxxl', '4x'],
    }
    
    # Reverse mapping for quick lookup
    SIZE_LOOKUP = {}
    for standard, variants in SIZE_MAPPINGS.items():
        for variant in variants:
            SIZE_LOOKUP[variant.lower()] = standard
    
    @classmethod
    def normalize_size(cls, size: str) -> Optional[str]:
        """
        Normalize a size string to standard format.
        
        Args:
            size: Size string (e.g., 'M', 'med', 'Medium', 'm')
            
        Returns:
            Standardized size (e.g., 'M') or None if invalid
        """
        if pd.isna(size) or size == '':
            return None
        
        size_str = str(size).strip().upper()
        
        # Direct match
        if size_str in cls.SIZE_MAPPINGS.keys():
            return size_str
        
        # Check variations
        size_lower = str(size).strip().lower()
        if size_lower in cls.SIZE_LOOKUP:
            return cls.SIZE_LOOKUP[size_lower]
        
        # Try to extract size from common patterns
        # Handle numeric sizes like "2XL" or "2 XL"
        numeric_match = re.match(r'(\d+)\s*xl', size_lower)
        if numeric_match:
            num = numeric_match.group(1)
            if num == '2':
                return '2XL'
            elif num == '3':
                return '3XL'
            elif num == '4':
                return '4XL'
        
        # Handle "XXL" variations
        if 'xxl' in size_lower or '2xl' in size_lower:
            return '2XL'
        if 'xxxl' in size_lower or '3xl' in size_lower:
            return '3XL'
        
        logger.warning(f"Could not normalize size: '{size}'")
        return None
    
    @classmethod
    def extract_size_from_sku(cls, sku: str) -> Optional[str]:
        """
        Extract size from a concatenated SKU (e.g., 'TEE-101-M' -> 'M').
        
        Args:
            sku: Concatenated SKU string
            
        Returns:
            Extracted size or None if not found
        """
        if pd.isna(sku) or sku == '':
            return None
        
        sku_str = str(sku).strip()
        
        # Try to extract size from end of SKU (after last dash)
        parts = sku_str.split('-')
        if len(parts) >= 2:
            potential_size = parts[-1].strip()
            normalized = cls.normalize_size(potential_size)
            if normalized:
                return normalized
        
        return None
    
    @classmethod
    def validate_and_correct_row(cls, row: pd.Series, concatenated_sku: str) -> Tuple[str, str]:
        """
        Validate and correct size for a single row.
        
        Args:
            row: DataFrame row with 'Size' column
            concatenated_sku: The concatenated SKU (VendorStyle-Size)
            
        Returns:
            Tuple of (corrected_size, validation_status)
            validation_status: 'OK' or 'REVIEW'
        """
        original_size = row.get('Size', '')
        normalized_size = cls.normalize_size(original_size)
        
        # If size is valid, use it
        if normalized_size:
            return normalized_size, 'OK'
        
        # Try to extract from concatenated SKU
        extracted_size = cls.extract_size_from_sku(concatenated_sku)
        if extracted_size:
            logger.info(f"Extracted size '{extracted_size}' from SKU '{concatenated_sku}' for row with missing/invalid size")
            return extracted_size, 'OK'
        
        # Cannot determine size - needs review
        logger.warning(f"Could not determine size for SKU '{concatenated_sku}', original size: '{original_size}'")
        return original_size if original_size else 'UNKNOWN', 'REVIEW'


class OrderProcessor:
    """Main class for processing SPS Commerce orders."""
    
    def __init__(
        self, 
        input_dir: str = 'input', 
        output_dir: str = 'output',
        google_drive_folder_id: Optional[str] = None,
        google_credentials_path: Optional[str] = None
    ):
        """
        Initialize the OrderProcessor.
        
        Args:
            input_dir: Directory containing input CSV files
            output_dir: Directory for output files
            google_drive_folder_id: Optional Google Drive folder ID to upload output files
            google_credentials_path: Path to Google service account credentials JSON file
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.input_dir.mkdir(exist_ok=True)
        self.validator = SizeValidator()
        self.google_drive_folder_id = google_drive_folder_id or os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self.google_credentials_path = google_credentials_path or os.getenv('GOOGLE_CREDENTIALS_PATH')
    
    def combine_csv_files(self, csv_files: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Combine multiple CSV files into a single DataFrame.
        
        Args:
            csv_files: List of CSV file paths. If None, reads all CSV files from input_dir.
            
        Returns:
            Combined DataFrame
        """
        if csv_files is None:
            csv_files = list(self.input_dir.glob('*.csv'))
            if not csv_files:
                raise FileNotFoundError(f"No CSV files found in {self.input_dir}")
        
        logger.info(f"Combining {len(csv_files)} CSV files...")
        
        dataframes = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                logger.info(f"Loaded {len(df)} rows from {csv_file.name}")
                dataframes.append(df)
            except Exception as e:
                logger.error(f"Error reading {csv_file}: {e}")
                continue
        
        if not dataframes:
            raise ValueError("No valid CSV files could be read")
        
        combined_df = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Combined total: {len(combined_df)} rows")
        
        return combined_df
    
    def concatenate_sku_size(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Concatenate Vendor Style and Size columns to create SKU-Size format.
        
        Args:
            df: DataFrame with 'Vendor Style' and 'Size' columns
            
        Returns:
            DataFrame with added 'Concatenated SKU' column
        """
        logger.info("Concatenating Vendor Style and Size...")
        
        # Ensure required columns exist
        required_cols = ['Vendor Style', 'Size']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Create concatenated SKU
        df['Concatenated SKU'] = df['Vendor Style'].astype(str) + '-' + df['Size'].astype(str)
        
        return df
    
    def validate_and_correct_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and correct size data, creating final validated columns.
        
        Args:
            df: DataFrame with 'Concatenated SKU' and 'Size' columns
            
        Returns:
            DataFrame with 'Final SKU', 'Final Size', and 'Validation_Status' columns
        """
        logger.info("Validating and correcting size data...")
        
        results = []
        for idx, row in df.iterrows():
            concatenated_sku = row.get('Concatenated SKU', '')
            final_size, validation_status = self.validator.validate_and_correct_row(
                row, concatenated_sku
            )
            
            # Rebuild final SKU with corrected size
            vendor_style = row.get('Vendor Style', '')
            final_sku = f"{vendor_style}-{final_size}" if vendor_style else concatenated_sku
            
            results.append({
                'Final SKU': final_sku,
                'Final Size': final_size,
                'Validation_Status': validation_status,
                'Quantity': row.get('Quantity', 0),
                'Original_Vendor_Style': vendor_style,
                'Original_Size': row.get('Size', ''),
            })
        
        validated_df = pd.DataFrame(results)
        
        # Log validation summary
        review_count = (validated_df['Validation_Status'] == 'REVIEW').sum()
        ok_count = (validated_df['Validation_Status'] == 'OK').sum()
        logger.info(f"Validation complete: {ok_count} OK, {review_count} need REVIEW")
        
        if review_count > 0:
            logger.warning(f"{review_count} rows require manual review. Check output file.")
        
        return validated_df
    
    def aggregate_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate quantities by unique SKU-Size combinations.
        
        Args:
            df: DataFrame with 'Final SKU' and 'Quantity' columns
            
        Returns:
            Aggregated DataFrame with summed quantities
        """
        logger.info("Aggregating orders by unique SKU-Size combinations...")
        
        # Ensure Quantity is numeric
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(0)
        
        # Group by Final SKU and sum quantities
        aggregated = df.groupby('Final SKU', as_index=False).agg({
            'Quantity': 'sum',
            'Final Size': 'first',  # Keep first size (should be same for same SKU)
            'Validation_Status': lambda x: 'REVIEW' if 'REVIEW' in x.values else 'OK'
        })
        
        aggregated.columns = ['Full SKU (SKU-Size)', 'Total Quantity', 'Size', 'Validation_Status']
        aggregated = aggregated.sort_values('Full SKU (SKU-Size)')
        
        logger.info(f"Aggregated to {len(aggregated)} unique SKU-Size combinations")
        
        return aggregated
    
    def create_final_format(self, aggregated_df: pd.DataFrame, 
                           sku_info: Optional[Dict[str, Dict]] = None) -> pd.DataFrame:
        """
        Create final format with SKU, Description, Ink Color, and size columns.
        
        Args:
            aggregated_df: Aggregated DataFrame with 'Full SKU (SKU-Size)' and 'Total Quantity'
            sku_info: Optional dict mapping SKU to description and ink color
                      Format: {'TEE-101': {'description': 'T-Shirt V-Neck', 'ink_color': 'Black'}}
        
        Returns:
            DataFrame in final format with size columns
        """
        logger.info("Creating final format with size columns...")
        
        # Extract base SKU from Full SKU
        aggregated_df['Base SKU'] = aggregated_df['Full SKU (SKU-Size)'].str.split('-').str[:-1].str.join('-')
        
        # Standard size order
        size_order = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL']
        
        # Create pivot table
        pivot_df = aggregated_df.pivot_table(
            index='Base SKU',
            columns='Size',
            values='Total Quantity',
            aggfunc='sum',
            fill_value=0
        )
        
        # Ensure all size columns exist
        for size in size_order:
            if size not in pivot_df.columns:
                pivot_df[size] = 0
        
        # Reorder columns
        pivot_df = pivot_df[[s for s in size_order if s in pivot_df.columns]]
        
        # Reset index
        pivot_df = pivot_df.reset_index()
        pivot_df.columns.name = None
        
        # Add Description and Ink Color columns
        pivot_df['Description'] = ''
        pivot_df['Ink Color'] = ''
        
        # Fill in SKU info if provided
        if sku_info:
            def get_description(sku):
                return sku_info.get(sku, {}).get('description', '')
            def get_ink_color(sku):
                return sku_info.get(sku, {}).get('ink_color', '')
            
            pivot_df['Description'] = pivot_df['Base SKU'].apply(get_description)
            pivot_df['Ink Color'] = pivot_df['Base SKU'].apply(get_ink_color)
        
        # Rename Base SKU to SKU
        pivot_df = pivot_df.rename(columns={'Base SKU': 'SKU'})
        
        # Reorder columns: SKU, Description, Ink Color, then sizes
        column_order = ['SKU', 'Description', 'Ink Color'] + [s for s in size_order if s in pivot_df.columns]
        pivot_df = pivot_df[column_order]
        
        logger.info(f"Final format created with {len(pivot_df)} SKUs")
        
        return pivot_df
    
    def upload_to_google_drive(self, file_path: Path) -> Optional[str]:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            Google Drive file ID if successful, None otherwise
        """
        if not GOOGLE_DRIVE_AVAILABLE:
            logger.error("Google Drive API libraries not installed. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return None
        
        if not self.google_credentials_path:
            logger.warning("Google credentials path not provided. Skipping Google Drive upload.")
            return None
        
        if not self.google_drive_folder_id:
            logger.warning("Google Drive folder ID not provided. Skipping Google Drive upload.")
            return None
        
        try:
            logger.info(f"Uploading {file_path.name} to Google Drive...")
            
            # Authenticate with service account
            credentials = service_account.Credentials.from_service_account_file(
                self.google_credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            service = build('drive', 'v3', credentials=credentials)
            
            # Prepare file metadata
            file_metadata = {
                'name': file_path.name,
                'parents': [self.google_drive_folder_id] if self.google_drive_folder_id else None
            }
            
            # Upload file
            media = MediaFileUpload(str(file_path), mimetype='text/csv', resumable=True)
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"✓ Successfully uploaded {file_path.name} to Google Drive")
            logger.info(f"  File ID: {file_id}")
            logger.info(f"  View at: https://drive.google.com/file/d/{file_id}/view")
            
            return file_id
            
        except FileNotFoundError:
            logger.error(f"Google credentials file not found: {self.google_credentials_path}")
            return None
        except HttpError as e:
            logger.error(f"Google Drive API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {e}", exc_info=True)
            return None
    
    def process_orders(self, csv_files: Optional[List[str]] = None,
                      sku_info: Optional[Dict[str, Dict]] = None,
                      output_prefix: str = 'processed_orders') -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Complete order processing pipeline.
        
        Args:
            csv_files: List of CSV file paths (optional, reads from input_dir if None)
            sku_info: Optional dict with SKU descriptions and ink colors
            output_prefix: Prefix for output files
            
        Returns:
            Tuple of (validated_df, aggregated_df, final_df)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            # Step 1: Combine CSV files
            combined_df = self.combine_csv_files(csv_files)
            
            # Step 2: Concatenate SKU and Size
            concatenated_df = self.concatenate_sku_size(combined_df)
            
            # Step 3: Validate and correct data
            validated_df = self.validate_and_correct_data(concatenated_df)
            
            # Step 4: Aggregate orders
            aggregated_df = self.aggregate_orders(validated_df)
            
            # Step 5: Create final format
            final_df = self.create_final_format(aggregated_df, sku_info)
            
            # Save only the final output
            final_output = self.output_dir / f'{output_prefix}_{timestamp}.csv'
            
            final_df.to_csv(final_output, index=False)
            logger.info(f"Saved final printer-ready file to {final_output}")
            
            # Step 6: Upload to Google Drive (if configured)
            if self.google_drive_folder_id and self.google_credentials_path:
                logger.info("=" * 60)
                logger.info("STEP 6: Uploading output to Google Drive")
                logger.info("=" * 60)
                file_id = self.upload_to_google_drive(final_output)
                if file_id:
                    logger.info(f"✓ Google Drive upload successful: {file_id}")
                else:
                    logger.warning("Google Drive upload failed or was skipped")
            else:
                logger.info("Skipping Google Drive upload (not configured)")
            
            return validated_df, aggregated_df, final_df
            
        except Exception as e:
            logger.error(f"Error processing orders: {e}", exc_info=True)
            raise


def main():
    """Main function to run the order processor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process SPS Commerce shirt orders')
    parser.add_argument('--input-dir', type=str, default='input',
                       help='Directory containing input CSV files (default: input)')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Directory for output files (default: output)')
    parser.add_argument('--files', nargs='+', type=str,
                       help='Specific CSV files to process (optional)')
    parser.add_argument('--output-prefix', type=str, default='processed_orders',
                       help='Prefix for output files (default: processed_orders)')
    parser.add_argument('--google-drive-folder-id', type=str, default=None,
                       help='Google Drive folder ID to upload output files (optional)')
    parser.add_argument('--google-credentials-path', type=str, default=None,
                       help='Path to Google service account credentials JSON file (optional)')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = OrderProcessor(
        input_dir=args.input_dir, 
        output_dir=args.output_dir,
        google_drive_folder_id=args.google_drive_folder_id,
        google_credentials_path=args.google_credentials_path
    )
    
    # Process orders
    validated_df, aggregated_df, final_df = processor.process_orders(
        csv_files=args.files,
        output_prefix=args.output_prefix
    )
    
    print("\n" + "="*60)
    print("ORDER PROCESSING COMPLETE")
    print("="*60)
    print(f"\nProcessed {len(validated_df)} order rows")
    print(f"Aggregated to {len(aggregated_df)} unique SKU-Size combinations")
    print(f"Final output: {len(final_df)} SKUs ready for printing")
    print(f"\nFinal CSV saved to: {args.output_dir}")
    print("="*60)


if __name__ == '__main__':
    main()

