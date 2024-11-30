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
        if ripedb:
            # We need to load the database first
            self.subnet_asn_map = self.get_subnets_from_file(ripedb)
        else:
            # There is no database to load
            # Cache: maps subnet (CIDR string) to (ASN, ASN description)
            self.subnet_asn_map: Dict[str, Tuple[str, str]] = {}

    @staticmethod
    def get_subnets_from_file(filename: str) -> dict:
        """
        Load the contents of a file into self.subnet_asn_map.
        Converts subnet keys from strings to ip_network objects.

        :param filename: The name of the file to load data from.
        """
        try:
            with open(filename, 'r') as file:
                data = json.load(file)

            # Convert subnet keys back to ip_network objects
            return {ipaddress.ip_network(subnet): asn for subnet, asn in data.items()}
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
        for subnet, asn_info in self.subnet_asn_map.items():
            if ip in ipaddress.ip_network(subnet):
                return asn_info

        # We didn't find anything
        return None

    def add_subnets(self, subnets: List[str], asn: str, description: str) -> None:
        """
        Adds new subnets to the cache.

        Args:
            subnets (List[str]): List of subnet CIDR strings.
            asn (str): The ASN associated with the subnets.
            description (str): The description of the ASN.
        """
        for subnet in subnets:
            if subnet not in self.subnet_asn_map:
                self.subnet_asn_map[subnet] = (asn, description)

    @staticmethod
    def split_ipv4_ipv6(ip_networks: list) -> dict:
        """
        Separates a list of ip_network objects into IPv4 and IPv6 subnets.
    
        :param networks: List of ip_network objects
        :return: Dictionary with "ipv4" and "ipv6" as keys and lists of ip_network objects as values
        """
        result = {"ipv4": [], "ipv6": []}
    
        for network in ip_networks:
            if isinstance(network, ipaddress.IPv4Network):
                result["ipv4"].append(network)
            elif isinstance(network, ipaddress.IPv6Network):
                result["ipv6"].append(network)
    
        return result

    async def fetch_subnets(self, asn: int) -> List[str]:
        """
        Fetches subnets for a given ASN from the RIPE API if not already cached.

        Args:
            asn (int): The ASN for which to fetch subnets.

        Returns:
            List[str]: List of subnets (CIDR strings) for the ASN.
        """
        # Check if the ASN's subnets are already cached
        if any(asn_info[0] == str(asn) for asn_info in self.subnet_asn_map.values()):
            return [subnet for subnet, asn_info in self.subnet_asn_map.items() if asn_info[0] == str(asn)]

        # If not cached, fetch subnets from the RIPE API
        try:
            params = {"resource": str(asn)}
            async with aiohttp.ClientSession() as session:
                async with session.get(self.RIPE_API_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        subnets = [prefix["prefix"] for prefix in data.get("data", {}).get("prefixes", [])]
                        #separate_subnets = self.split_ipv4_ipv6(subnets)
                        return subnets
                    else:
                        print(f"Error: RIPE API returned status {response.status} for ASN {asn}.")
                        return []
        except Exception as e:
            print(f"Error fetching subnets for ASN {asn}: {e}")
            return []

    def write_subnets_to_file(self, filename: str) -> None:
        """
        Write the contents of self.subnet_asn_map to a file in JSON format.
        Converts subnet keys (ip_network objects) to strings.
        
        :param filename: The name of the file to write the data to.
        """
        try:
            # Convert ip_network objects to strings for JSON serialization
            data_to_write = {str(subnet): asn for subnet, asn in self.subnet_asn_map.items()}

            # Write to file
            with open(filename, 'w') as file:
                json.dump(data_to_write, file, indent=4)

            print(f"Subnet-ASN map successfully written to {filename}")
        except Exception as e:
            print(f"Failed to write subnet-asn map to {filename}: {e}")    
