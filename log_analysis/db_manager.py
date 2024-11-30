import os
import json
from ipaddress import ip_network
from datetime import datetime, timedelta

# Constants
DEFAULT_RIPEDB_PATH = "./ripedb.json"
MAX_DB_AGE_DAYS = 30


class DBManager:
    def __init__(self, db_path=DEFAULT_RIPEDB_PATH):
        self.db_path = db_path
        self.database = {"last_updated": None, "data": {}}
        self.modified = False

    def load_database(self):
        """Loads the database from the JSON file."""
        if not os.path.exists(self.db_path):
            return  # No database file; proceed with empty structure.

        try:
            with open(self.db_path, "r") as db_file:
                data = json.load(db_file)

            # Validate structure
            if not isinstance(data, dict) or "last_updated" not in data or "data" not in data:
                raise ValueError("Malformed database")

            last_updated = datetime.strptime(data["last_updated"], "%Y-%m-%d")
            if datetime.now() - last_updated > timedelta(days=MAX_DB_AGE_DAYS):
                return  # Data too old; proceed with empty structure.

            # Convert subnet strings to ip_network objects
            for asn, details in data["data"].items():
                details["subnets"] = [ip_network(subnet) for subnet in details["subnets"]]

            self.database = data

        except (ValueError, KeyError, json.JSONDecodeError) as e:
            print(f"Error loading database: {e}")
            exit(1)

    def save_database(self):
        """Saves the database back to the JSON file if modified."""
        if not self.modified:
            return

        self.database["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        data_to_save = {
            "last_updated": self.database["last_updated"],
            "data": {
                "asn": {
                    "description": details["description"],
                    "subnets": [str(subnet) for subnet in details["subnets"]],
                }
                for asn, details in self.database["data"].items()
            },
        }

        with open(self.db_path, "w") as db_file:
            json.dump(data_to_save, db_file, indent=4)

    def has_changed(self):
        """Returns whether the database has been modified."""
        return self.modified

    def update_asn(self, asn, description, subnets):
        """Updates the database with a new ASN and subnets."""
        if asn not in self.database["data"]:
            self.database["data"][asn] = {"description": description, "subnets": subnets}
            self.modified = True
        else:
            existing_subnets = self.database["data"][asn]["subnets"]
            new_subnets = [subnet for subnet in subnets if subnet not in existing_subnets]
            if new_subnets:
                self.database["data"]["asn"]["subnets"].extend(new_subnets)
                self.modified = True

