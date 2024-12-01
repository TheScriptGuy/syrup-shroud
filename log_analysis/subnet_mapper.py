import aiohttp
import ipaddress
import json
import sys
from typing import Dict, Tuple, Optional, List

class SubnetMapper:
    """
    Manages the mapping of subnets to ASN and descriptions.
    Caches subnets locally to minimize external API calls.
    """

    RIPE_API_URL = "https://stat.ripe.net/data/announced-prefixes/data.json"

    def __init__(self, ripedb: str):
        """Initialize the SubnetMapper class."""
        # Set the RIPE database file.
        self.ripedb = ripedb

        # Initialize the subnet_asn_map
        self.subnet_asn_map = {}
        
        # Set an empty dict for both IPv4 and IPv6 addresses.
        for ip_type in ["ipv4", "ipv6"]:
            self.subnet_asn_map[ip_type]: Dict[str, Tuple[str, str]] = {}
        
        if self.ripedb:
            # We need to load the database first
            self.get_subnets_from_file(self.ripedb)

    def get_subnets_from_file(self, filename: str) -> dict:
        """
        Load the contents of a file into self.subnet_asn_map..
        Converts subnet keys from strings to ip_network objects.

        :param filename: The name of the file to load data from.
        """
        # Attempt to open the file
        try:
            with open(filename, 'r') as file:
                data = json.load(file)

            # Convert subnet keys back to ip_network objects
            self.subnet_asn_map = {"ipv4": {ipaddress.ip_network(subnet): asn for subnet, asn in data["ipv4"].items()},
                                   "ipv6": {ipaddress.ip_network(subnet): asn for subnet, asn in data["ipv6"].items()}
                                   }

        except FileNotFoundError:
            print(f"File {filename} not found.")
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from {filename}.")
        except ValueError as e:
            print(f"Failed to convert data in {filename}: {e}")

    def find_asn_for_ip(self, ip_address: str) -> Optional[Tuple[str, str]]:
        """
        Finds the ASN and description for a given IP address from the cached subnets.

        Args:
            ip_address (str): The IP address to check.

        Returns:
            Optional[Tuple[str, str]]: (ASN, description) if found, None otherwise.
        """
        ip = ipaddress.ip_address(ip_address)
        
        # Lets look in our subnet_asn_map
        # Check to see whether its an IPv4 address or an IPv6 address
        if isinstance(ip, ipaddress.IPv4Network):
            for subnet, asn_info in self.subnet_asn_map["ipv4"].items():
                if ip in ipaddress.ip_network(subnet):
                    return asn_info
        elif isinstance(ip, ipaddress.IPv6Network):
            for subnet, asn_info in self.subnet_asn_map["ipv6"].items():
                if ip in address.ip_network(subnet):
                    return asn_info

        # We didn't find anything
        return None

    def add_subnets(self, subnets: Dict, asn: str, description: str) -> None:
        """
        Adds new subnets to the cache.

        Args:
            subnets (Dict): Dict List of subnet CIDR strings.
            asn (str): The ASN associated with the subnets.
            description (str): The description of the ASN.
        """
        for ip_version in subnets:
            for subnet in subnets[ip_version]:
                if subnet not in self.subnet_asn_map[ip_version]:
                    self.subnet_asn_map[ip_version][subnet] = (asn, description)


    @staticmethod
    def split_ipv4_ipv6(ip_networks: list) -> dict:
        """
        Separates a list of ip_network objects into IPv4 and IPv6 subnets.
    
        :param networks: List of ip_network objects
        :return: Dictionary with "ipv4" and "ipv6" as keys and lists of ip_network objects as values
        """
        result = {"ipv4": [], "ipv6": []}

        for network in ip_networks:
            ip_network = ipaddress.ip_network(network)
            if isinstance(ip_network, ipaddress.IPv4Network):
                result["ipv4"].append(network)
            elif isinstance(ip_network, ipaddress.IPv6Network):
                result["ipv6"].append(network)
        return result

    async def fetch_subnets(self, asn: int) -> Dict:
        """
        Fetches subnets for a given ASN from the RIPE API if not already cached.

        Args:
            asn (int): The ASN for which to fetch subnets.

        Returns:
            Dict: Dict list of both IPv4 and IPv6 subnets (CIDR strings) for the ASN.
        """
        asn_str = str(asn)  # Ensure ASN is a string for comparison
        subnets = []
        separate_subnets = {"ipv4": {}, "ipv6": {}}

        # Check if the ASN's subnets are already cached
        result = {
            "ipv4": [
                subnet for subnet, asn_info in self.subnet_asn_map.get("ipv4", {}).items() if asn_info[0] == asn_str
            ],
            "ipv6": [
                subnet for subnet, asn_info in self.subnet_asn_map.get("ipv6", {}).items() if asn_info[0] == asn_str
            ],
        }

        # Only return if there's something in the result
        if result["ipv4"] or result["ipv6"]:
            return result
        
        # If not cached, fetch subnets from the RIPE API
        try:
            params = {"resource": str(asn)}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.RIPE_API_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        subnets = [prefix["prefix"] for prefix in data.get("data", {}).get("prefixes", [])]
                        separate_subnets = self.split_ipv4_ipv6(subnets)
                        return separate_subnets
                    else:
                        print(f"Error: RIPE API returned status {response.status} for ASN {asn}.")
                        return {"ipv4": {}, "ipv6": {}}
        except Exception as e:
            print(f"Error fetching subnets for ASN {asn}: {e}")
            return {"ipv4": {}, "ipv6": {}}

    def write_subnets_to_file(self) -> None:
        """
        Write the contents of self.subnet_asn_map to a file in JSON format.
        Converts subnet keys (ip_network objects) to strings.
        
        :param filename: The name of the file to write the data to.
        """
        try:
            # Convert ip_network objects to strings for JSON serialization
            data_to_write = {"ipv4": {str(subnet): asn for subnet, asn in self.subnet_asn_map["ipv4"].items()},
                             "ipv6": {str(subnet): asn for subnet, asn in self.subnet_asn_map["ipv6"].items()}
                            }

            # Write to file
            with open(self.ripedb, 'w') as file:
                json.dump(data_to_write, file, indent=4)

            print(f"Subnet-ASN map successfully written to {self.ripedb}")
        except Exception as e:
            print(f"Failed to write subnet-asn map to {self.ripedb}: {e}")    
