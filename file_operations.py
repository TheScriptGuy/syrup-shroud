import json
from typing import Dict, Any
from pathlib import Path

class FileOperations:
    """Class to handle all file-related operations including reading, writing and JSON operations."""
    
    def __init__(self, filename: str):
        """Initialize FileOperations with a filename.
        
        Args:
            filename (str): Path to the file to be processed
        """
        self.filename = Path(filename)
    
    def read_file(self) -> list:
        """Read the file and return its contents as a list of lines.
        
        Returns:
            list: Lines from the file
            
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            PermissionError: If the program lacks permission to read the file
        """
        try:
            with self.filename.open('r') as file:
                return file.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {self.filename} was not found")
        except PermissionError:
            raise PermissionError(f"Permission denied when trying to read {self.filename}")

    def write_json(self, ip_data: Dict[str, Dict], output_file: str) -> None:
        """Transform and write IP data to JSON file."""
        transformed_data = {}

        # Group by ASN and description
        for ip, details in ip_data.items():
            asn = details.get('asn', 'unknown')
            desc = details.get('description', 'unknown')
            key = f"{asn}_{desc}"

            if key not in transformed_data:
                transformed_data[key] = {
                    'total_log_entries': 0,
                    'ips': []
                }

            transformed_data[key]['total_log_entries'] += details['count']
            transformed_data[key]['ips'].append(ip)

        with Path(output_file).open('w') as f:
            json.dump(transformed_data, f, indent=4)
