import json
from typing import Dict, Tuple


class DataOutput:
    """
    Handles the formatting and output of data.
    """

    @staticmethod
    def print_table(data: list, headers: list) -> None:
        """
        Prints a formatted table to stdout.

        Args:
            data (list): Data rows.
            headers (list): Column headers.
        """
        from tabulate import tabulate
        if data:
            table = tabulate(data, headers=headers, tablefmt="pretty", colalign=("left", "left", "right", "right", "left"))
            print(table)
        else:
            print("No matching data found.")

    @staticmethod
    def write_json(file_path: str, asn_ip_data: Dict[Tuple[str, str], Dict]) -> None:
        """
        Writes the data to a JSON file.

        Args:
            file_path (str): Path to the output JSON file.
            asn_ip_data (dict): Aggregated ASN and IP data.
        """
        json_data = {
            f"{asn}_{description}": {
                "total_log_entries": data["total_entries"],
                "ips": list(data["ips"]),  # Include all IPs
            }
            for (asn, description), data in asn_ip_data.items()
        }

        with open(file_path, "w") as f:
            json.dump(json_data, f, indent=4)
        print(f"JSON output written to {file_path}")
