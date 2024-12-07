import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, Dict, Tuple, List
import ipaddress
import json
import aiohttp

class SubnetMapper:
    """
    Manages the mapping of subnets to ASN and descriptions.
    Caches subnets locally to minimize external API calls.
    """
    RIPE_API_URL = "https://stat.ripe.net/data/announced-prefixes/data.json"

    def __init__(self, ripedb: str):
        """
        Initialize the SubnetMapper class.
        Manages the subnet-to-ASN mapping and supports dynamic updates.
        """
        # Shared data structure
        self.subnet_asn_map = {"ipv4": {}, "ipv6": {}}
        self.lock = threading.Lock()
        self.match_found = threading.Event()

        self.ripedb = ripedb

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

    def add_subnets(self, subnets: Dict, asn: str, description: str) -> None:
        """
        Add subnets dynamically to the mapping.
        Updates are protected with a lock to ensure thread safety.

        Args:
            subnets (Dict): Subnets grouped by IPv4 and IPv6.
            asn (str): The ASN associated with the subnets.
            description (str): The description of the ASN.
        """
        with self.lock:
            for ip_version, cidr_list in subnets.items():
                for cidr in cidr_list:
                    subnet = ipaddress.ip_network(cidr)
                    if subnet not in self.subnet_asn_map[ip_version]:
                        self.subnet_asn_map[ip_version][subnet] = (asn, description)

    def find_asn_for_ip(self, ip_address: str) -> Optional[Tuple[str, str]]:
        """
        Check if an IP belongs to a subnet in the mapping.

        Args:
            ip_address (str): The IP address to check.

        Returns:
            Optional[Tuple[str, str]]: ASN and description if found, else None.
        """
        ip = ipaddress.ip_address(ip_address)
        ip_version = "ipv4" if isinstance(ip, ipaddress.IPv4Address) else "ipv6"

        # Check against subnets
        with self.lock:
            for subnet, asn_info in self.subnet_asn_map[ip_version].items():
                if ip in subnet:
                    return asn_info
        return None

    def search_ip_with_threads(self, ip_address: str, thread_count: int = 20) -> Optional[Tuple[str, str]]:
        """
        Search for an IP across subnets using a thread pool.

        Args:
            ip_address (str): The IP to search for.
            thread_count (int): Number of threads in the pool.

        Returns:
            Optional[Tuple[str, str]]: ASN and description if found, else None.
        """
        # Reset match event for a fresh search
        self.match_found.clear()

        # Prepare partitions
        ip = ipaddress.ip_address(ip_address)
        ip_version = "ipv4" if isinstance(ip, ipaddress.IPv4Address) else "ipv6"

        with self.lock:
            subnets = list(self.subnet_asn_map[ip_version].items())
        
        # Divide subnets into chunks for threads
        chunk_size = len(subnets) // thread_count or 1
        subnet_chunks = [subnets[i:i + chunk_size] for i in range(0, len(subnets), chunk_size)]

        def search_chunk(chunk: List[Tuple[ipaddress.IPv4Network, Tuple[str, str]]]):
            for subnet, asn_info in chunk:
                if self.match_found.is_set():
                    return None  # Stop if match is already found
                if ip in subnet:
                    self.match_found.set()  # Notify other threads
                    return asn_info
            return None

        # Execute search in a thread pool
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [executor.submit(search_chunk, chunk) for chunk in subnet_chunks]

            for future in futures:
                result = future.result()
                if result:
                    # Cancel remaining tasks
                    for f in futures:
                        f.cancel()
                    return result

        return None

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
                result["ipv4"].append(ip_network)
            elif isinstance(ip_network, ipaddress.IPv6Network):
                result["ipv6"].append(ip_network)

        for ip_version in ["ipv4", "ipv6"]:
            # result[ip_version] = list(str(ipaddress.collapse_addresses(sorted(result[ip_version]))))
            result[ip_version] = [str(net) for net in ipaddress.collapse_addresses(sorted(result[ip_version]))]

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
