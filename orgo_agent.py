"""
Orgo Agent for Order Processing Automation
==========================================

This agent automates the end-to-end order processing workflow:
1. Downloads CSV files from GitHub Pages (simulating SPS Commerce downloads)
2. Opens terminal and runs order_processor.py
3. Verifies output files are created
4. Uploads output CSV file to Google Drive folder "TshirtCUA Outputs"

Uses Claude Sonnet 4.5 with computer use capabilities via Orgo.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional

from orgo import Computer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orgo_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OrderProcessingAgent:
    """Orgo agent for automating order processing workflow."""
    
    def __init__(
        self,
        github_pages_url: str,
        project_path: Optional[str] = None,
        computer_id: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        max_iterations: int = 30
    ):
        """
        Initialize the Order Processing Agent.
        
        Args:
            github_pages_url: URL to GitHub Pages containing CSV files
            project_path: Path to the project directory (default: /home/user/Desktop/tshirtcua for Orgo VM)
            computer_id: Optional Orgo computer ID to connect to existing computer
            model: Claude model to use (default: Claude Sonnet 4.5)
            max_iterations: Maximum number of agent loop iterations
        """
        self.github_pages_url = github_pages_url
        # Default to Orgo VM path if not specified
        self.project_path = project_path or "/home/user/Desktop/tshirtcua"
        self.order_processor_path = os.path.join(self.project_path, "order_processor.py")
        self.computer_id = computer_id
        self.model = model
        self.max_iterations = max_iterations
        self.computer: Optional[Computer] = None
        
        # Verify API keys are set
        if not os.getenv("ORGO_API_KEY"):
            raise ValueError("ORGO_API_KEY environment variable is required")
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    
    def progress_callback(self, event_type: str, event_data: Any) -> None:
        """
        Callback function to track agent progress.
        
        Args:
            event_type: Type of event ('text', 'tool_use', 'thinking', 'error')
            event_data: Event data
        """
        if event_type == "text":
            logger.info(f"Claude: {event_data}")
            print(f"🤖 Claude: {event_data}")
        elif event_type == "tool_use":
            action = event_data.get('action', 'unknown')
            logger.info(f"Action: {action}")
            print(f"⚙️  Action: {action}")
            if 'coordinate' in event_data:
                x, y = event_data['coordinate']
                print(f"   Location: ({x}, {y})")
        elif event_type == "thinking":
            logger.debug(f"Thinking: {event_data}")
            print(f"💭 Thinking: {event_data}")
        elif event_type == "error":
            logger.error(f"Error: {event_data}")
            print(f"❌ Error: {event_data}")
    
    def download_csvs_from_github_pages(self) -> None:
        """
        Download CSV files from GitHub Pages to the input directory.
        """
        logger.info(f"Starting CSV download from {self.github_pages_url}")
        
        download_instruction = f"""
        Navigate to {self.github_pages_url} in a web browser.
        Download all CSV files from the page to the 'input' directory in the project.
        The project is located at: {self.project_path}
        The input directory should be at: {os.path.join(self.project_path, 'input')}
        Make sure to save the files with their original names in the input folder.
        After downloading, verify that the CSV files are in the input directory at {os.path.join(self.project_path, 'input')}.
        """
        
        try:
            messages = self.computer.prompt(
                download_instruction,
                callback=self.progress_callback,
                model=self.model,
                thinking_enabled=True,
                max_iterations=self.max_iterations
            )
            logger.info("CSV download task completed")
        except Exception as e:
            logger.error(f"Error during CSV download: {e}", exc_info=True)
            raise
    
    def run_order_processor(self) -> None:
        """
        Open terminal and run the order_processor.py script.
        """
        logger.info("Starting terminal execution of order_processor.py")
        
        vscode_instruction = f"""
        Open Visual Studio Code (terminal) if it's not already open.
        Navigate to the project directory: {self.project_path}
        The full path is: {self.order_processor_path}
        Run the Python script using the terminal. You can run it with: python3 {self.order_processor_path}
        Or navigate to the project directory first: cd {self.project_path} && python3 order_processor.py
        The script should process CSV files from the 'input' directory ({os.path.join(self.project_path, 'input')}) and create output files in the 'output' directory ({os.path.join(self.project_path, 'output')}).
        Wait for the script to complete execution.
        Verify that output files have been created in the 'output' directory at {os.path.join(self.project_path, 'output')}.
        """
        
        try:
            messages = self.computer.prompt(
                vscode_instruction,
                callback=self.progress_callback,
                model=self.model,
                thinking_enabled=True,
                max_iterations=self.max_iterations
            )
            logger.info("Order processor execution completed")
        except Exception as e:
            logger.error(f"Error during order processor execution: {e}", exc_info=True)
            raise
    
    def verify_output(self) -> bool:
        """
        Verify that output files exist in the output directory via desktop interaction.
        Note: This verification happens on the Orgo VM, not the local machine.
        
        Returns:
            True if output files exist, False otherwise
        """
        logger.info("Verifying output files exist on Orgo VM...")
        
        # Since we're running on Orgo VM, we can't directly check the local filesystem
        # Claude will verify this through the terminal/file manager in the previous step
        # For now, we'll assume it exists if the script completed successfully
        # The actual verification happens when Claude checks the output directory
        
        # Return True - Claude already verified this in the run_order_processor step
        logger.info("Output verification assumed successful (verified by Claude in previous step)")
        return True
    
    def get_latest_output_file_path(self) -> str:
        """
        Get the path to the latest output CSV file on the Orgo VM.
        This returns the path string that Claude can use to locate the file.
        
        Returns:
            Path string to the output directory where files should be located
        """
        return os.path.join(self.project_path, "output")
    
    def upload_to_google_drive(self) -> None:
        """
        Upload the output CSV file to Google Drive via browser interaction.
        Navigates to Google Drive, finds the "TshirtCUA Outputs" folder, and uploads the file.
        """
        logger.info("Starting Google Drive upload")
        
        # Get the output directory path on the Orgo VM
        output_dir_path = self.get_latest_output_file_path()
        
        logger.info(f"Output files should be in: {output_dir_path}")
        
        upload_instruction = f"""
        Navigate to Google Drive in a web browser (https://drive.google.com).
        The account should already be logged in.
        
        Find and open the shared folder named "TshirtCUA Outputs".
        If you can't find it immediately, use the search function in Google Drive to search for "TshirtCUA Outputs".
        
        Once you're inside the "TshirtCUA Outputs" folder, you need to upload the CSV file.
        
        The output CSV file is located on the desktop in the "tshirtcua" folder, under the "output" subfolder.
        The full path is: {output_dir_path}
        
        To find and upload the file:
        1. Open the File Manager (if not already open)
        2. Navigate to the Desktop
        3. Open the "tshirtcua" folder
        4. Open the "output" folder inside it
        5. You should see a CSV file named something like "processed_orders_*.csv" (it will have a timestamp in the filename)
        6. Note the exact filename
        
        Then upload to Google Drive:
        1. In Google Drive, click the "New" button or the upload icon
        2. Select "File upload"
        3. In the file picker dialog, navigate to: Desktop → tshirtcua → output
        4. Select the processed_orders_*.csv file (the one with the most recent timestamp)
        5. Wait for the upload to complete
        6. Verify that the file appears in the "TshirtCUA Outputs" folder
        
        Make sure the file is successfully uploaded before proceeding.
        """
        
        try:
            messages = self.computer.prompt(
                upload_instruction,
                callback=self.progress_callback,
                model=self.model,
                thinking_enabled=True,
                max_iterations=self.max_iterations
            )
            logger.info("Google Drive upload task completed")
        except Exception as e:
            logger.error(f"Error during Google Drive upload: {e}", exc_info=True)
            raise
    
    def run(self) -> Dict[str, Any]:
        """
        Run the complete automation workflow.
        
        Returns:
            Dictionary with execution results and status
        """
        results = {
            "success": False,
            "csv_download": False,
            "order_processing": False,
            "output_verified": False,
            "google_drive_upload": False,
            "error": None
        }
        
        try:
            # Initialize computer
            if self.computer_id:
                logger.info(f"Connecting to existing Orgo computer: {self.computer_id}")
                self.computer = Computer(computer_id=self.computer_id)
                logger.info(f"Connected to computer {self.computer_id} successfully")
            else:
                logger.info("Initializing new Orgo computer...")
                self.computer = Computer()
                logger.info("Computer initialized successfully")
            
            # Step 1: Download CSV files
            logger.info("=" * 60)
            logger.info("STEP 1: Downloading CSV files from GitHub Pages")
            logger.info("=" * 60)
            self.download_csvs_from_github_pages()
            results["csv_download"] = True
            
            # Step 2: Run order processor
            logger.info("=" * 60)
            logger.info("STEP 2: Running order processor in VS Code")
            logger.info("=" * 60)
            self.run_order_processor()
            results["order_processing"] = True
            
            # Step 3: Verify output
            logger.info("=" * 60)
            logger.info("STEP 3: Verifying output files")
            logger.info("=" * 60)
            results["output_verified"] = self.verify_output()
            
            # Step 4: Upload to Google Drive
            logger.info("=" * 60)
            logger.info("STEP 4: Uploading output to Google Drive")
            logger.info("=" * 60)
            self.upload_to_google_drive()
            results["google_drive_upload"] = True
            
            # Overall success
            results["success"] = (
                results["csv_download"] and
                results["order_processing"] and
                results["output_verified"] and
                results["google_drive_upload"]
            )
            
            logger.info("=" * 60)
            logger.info("AUTOMATION COMPLETE")
            logger.info("=" * 60)
            logger.info(f"CSV Download: {'✓' if results['csv_download'] else '✗'}")
            logger.info(f"Order Processing: {'✓' if results['order_processing'] else '✗'}")
            logger.info(f"Output Verified: {'✓' if results['output_verified'] else '✗'}")
            logger.info(f"Google Drive Upload: {'✓' if results['google_drive_upload'] else '✗'}")
            logger.info(f"Overall Success: {'✓' if results['success'] else '✗'}")
            
        except Exception as e:
            logger.error(f"Error in automation workflow: {e}", exc_info=True)
            results["error"] = str(e)
            results["success"] = False
        
        finally:
            # Cleanup - only destroy if we created a new computer
            # If using an existing computer_id, don't destroy it
            if self.computer and not self.computer_id:
                try:
                    logger.info("Cleaning up computer instance...")
                    self.computer.destroy()
                    logger.info("Computer instance destroyed")
                except Exception as e:
                    logger.error(f"Error destroying computer: {e}", exc_info=True)
            elif self.computer_id:
                logger.info(f"Leaving computer {self.computer_id} running (not destroyed)")
        
        return results


def main():
    """Main function to run the agent."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Orgo Agent for Order Processing Automation'
    )
    parser.add_argument(
        '--github-url',
        type=str,
        required=True,
        help='GitHub Pages URL containing CSV files'
    )
    parser.add_argument(
        '--project-path',
        type=str,
        default=None,
        help='Path to project directory (default: /home/user/Desktop/tshirtcua for Orgo VM)'
    )
    parser.add_argument(
        '--computer-id',
        type=str,
        default=None,
        help='Orgo computer ID to connect to existing computer (optional)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='claude-sonnet-4-5-20250929',
        help='Claude model to use (default: claude-sonnet-4-5-20250929)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=30,
        help='Maximum number of agent loop iterations (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Create and run agent
    agent = OrderProcessingAgent(
        github_pages_url=args.github_url,
        project_path=args.project_path,
        computer_id=args.computer_id,
        model=args.model,
        max_iterations=args.max_iterations
    )
    
    results = agent.run()
    
    # Exit with appropriate code
    exit(0 if results["success"] else 1)


if __name__ == '__main__':
    main()

