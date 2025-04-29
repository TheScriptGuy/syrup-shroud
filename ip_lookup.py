import ipaddress
import json
import aiohttp
import asyncio
from typing import Dict, Optional, Set
from pathlib import Path
from ipwhois import IPWhois
from custom_logger import CustomLogger

class IPLookup:
    """Handles IP address lookups, ASN information, and RIPE database interactions."""
    
    RIPE_API_URL = "https://stat.ripe.net/data/announced-prefixes/data.json"

    # Excluded subnets as strings (faster comparison to API results)
    EXCLUDED_IPV4_PREFIXES = {
        "0.0.0.0/0"
    }

    EXCLUDED_IPV6_PREFIXES = {
        "::/0"
    }

    def __init__(self, logger: CustomLogger, ripe_db_file: Optional[str] = None):
        self.logger = logger
        self.ripe_db_file = Path(ripe_db_file) if ripe_db_file else None
        # Structure: {asn: {'description': str, 'ipv4': set(), 'ipv6': set()}}
        self.asn_data = {}
        # Structure: {ip_network: (asn, description)}
        self.subnet_cache = {'ipv4': {}, 'ipv6': {}}
        self.load_cache()

    def load_cache(self) -> None:
        """Load cached RIPE database if exists."""
        if not self.ripe_db_file or not self.ripe_db_file.exists():
            return
        self.logger.debug(f"Loading RIPE database {self.ripe_db_file}")
        with self.ripe_db_file.open('r') as f:
            data = json.load(f)
            self.asn_data = {
                asn: {
                    'description': info['description'],
                    'ipv4': set(info['ipv4']),
                    'ipv6': set(info['ipv6'])
                }
                for asn, info in data.items()
            }
            
            # Rebuild subnet cache
            for asn, info in self.asn_data.items():
                for subnet in info['ipv4']:
                    self.subnet_cache['ipv4'][ipaddress.ip_network(subnet)] = (asn, info['description'])
                for subnet in info['ipv6']:
                    self.subnet_cache['ipv6'][ipaddress.ip_network(subnet)] = (asn, info['description'])

    def save_cache(self) -> None:
        if not self.ripe_db_file:
            return
        
        data = {}
        for asn, info in self.asn_data.items():
            data[asn] = {
                'description': info['description'],
                'ipv4': list(self._summarize_subnets(info['ipv4'])),
                'ipv6': list(self._summarize_subnets(info['ipv6']))
            }
    
        self.logger.debug(f"Writing summarized cache to file: {self.ripe_db_file}")
        with self.ripe_db_file.open('w') as f:
            json.dump(data, f, indent=4)

    def fetch_subnets(self, asn: str) -> Dict:
        """Synchronous version of subnet fetching."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self._async_fetch_subnets(asn))
        loop.close()
        return result

    async def _async_fetch_subnets(self, asn: str) -> Dict:
        """Fetch subnets from RIPE API."""
        try:
            self.logger.debug(f"ASN{asn} - Downloading subnets for BGP ASN")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.RIPE_API_URL}?resource={asn}") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.logger.debug(f"ASN{asn} - Got response from RIPE API")
                        subnets = [prefix["prefix"] for prefix in data["data"]["prefixes"]]
                        if subnets:
                            self.logger.debug(f"ASN{asn} - I found {len(subnets)} subnets in response")
                        return self._categorize_subnets(subnets)
        except Exception as e:
            self.logger.debug(f"ASN{asn} - Error fetching subnets - {e}")
        return {"ipv4": set(), "ipv6": set()}


    def _summarize_subnets(self, subnets: Set[str]) -> Set[str]:
        """
        Summarize contiguous subnets into larger CIDR blocks,
        excluding overly broad subnets like 0.0.0.0/0 and ::/0.
        """
        if not subnets:
            return set()

        networks = []
        for subnet in subnets:
            if subnet in self.EXCLUDED_IPV4_PREFIXES or subnet in self.EXCLUDED_IPV6_PREFIXES:
                self.logger.debug(f"Excluding subnet {subnet} from summarization")
                continue

            try:
                network = ipaddress.ip_network(subnet)
                networks.append(network)
            except ValueError:
                self.logger.debug(f"Skipping invalid subnet during summarization: {subnet}")
                continue

        return {str(net) for net in ipaddress.collapse_addresses(networks)}


    def _categorize_subnets(self, subnets: list) -> Dict:
        """
        Categorize subnets into IPv4 and IPv6, excluding invalid or overly broad entries.
        """
        result = {"ipv4": set(), "ipv6": set()}
        for subnet in subnets:
            subnet = subnet.strip()
        
            if subnet in self.EXCLUDED_IPV4_PREFIXES or subnet in self.EXCLUDED_IPV6_PREFIXES:
                self.logger.debug(f"Excluding subnet {subnet} during categorization")
                continue

            try:
                network = ipaddress.ip_network(subnet)
                key = 'ipv6' if isinstance(network, ipaddress.IPv6Network) else 'ipv4'
                result[key].add(subnet)
            except ValueError:
                self.logger.debug(f"Skipping invalid subnet format: {subnet}")
                continue
        return result


    def lookup_ip(self, ip_address: str) -> Optional[Dict]:
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Define excluded ranges
            ipv4_excluded = [
                "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",  # Private
                "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16",  # Special-use
                "224.0.0.0/4", "255.255.255.255/32"  # Multicast/Broadcast
            ]
            ipv6_excluded = [
                "fc00::/7",    # Unique Local Address
                "fe80::/10",   # Link Local Address
                "ff00::/8",    # Multicast
                "::/128",      # Unspecified
                "::1/128"      # Loopback
            ]
            
            # Check if IP is in excluded ranges
            excluded_ranges = ipv4_excluded if isinstance(ip, ipaddress.IPv4Address) else ipv6_excluded
            for excluded in excluded_ranges:
                if ip in ipaddress.ip_network(excluded):
                    self.logger.debug(f"IP {ip_address} is in excluded range {excluded}")
                    return None
            
            cache_key = 'ipv6' if isinstance(ip, ipaddress.IPv6Address) else 'ipv4'
            
            self.logger.debug(f"Searching for IP {ip_address}")
            
            # Check subnet cache first
            for network, (asn, description) in self.subnet_cache[cache_key].items():
                if ip in network:
                    self.logger.debug(f"Found {ip_address} in cache: ASN {asn}, Desc {description}")
                    return {'asn': asn, 'asn_description': description}  # Changed key to asn_description
            
            self.logger.debug(f"Did not find IP {ip_address} in cache")

            # If not in cache, perform WHOIS lookup
            self.logger.debug(f"Performing whois lookup for IP {ip_address}")
            whois_result = self._whois_lookup(ip_address)
            if whois_result:
                self.logger.debug(f"Got whois result for {ip_address}")
                asn = whois_result['asn']
                if asn not in self.asn_data:
                    self.logger.debug(f"Could not find existing ASN {asn} in self.asn_data")
                    self.logger.debug(f"Getting subnets for ASN {asn}")
                    subnets = self.fetch_subnets(asn)
                    self.asn_data[asn] = {
                        'description': whois_result['asn_description'],
                        'ipv4': subnets['ipv4'],
                        'ipv6': subnets['ipv6']
                    }
                    self.logger.debug(f"Updating subnet cache with {len(self.asn_data[asn]['ipv4'])} IPv4 subnets and {len(self.asn_data[asn]['ipv6'])} subnets")
                    self._update_subnet_cache(asn)
                return whois_result
        except Exception as e:
            print(f"Error looking up IP {ip_address}: {e}")
        return None

    def _whois_lookup(self, ip_address: str) -> Optional[Dict]:
        """Perform WHOIS lookup for IP address."""
        try:
            ip_whois = IPWhois(ip_address)
            result = ip_whois.lookup_rdap(asn_methods=['whois'])
            return {
                'asn': result.get('asn'),
                'asn_description': result.get('asn_description', '').split(',')[0].strip().lower()
            }
        except Exception:
            return None

    def _update_subnet_cache(self, asn: str) -> None:
        """Update subnet cache with new ASN information."""
        info = self.asn_data[asn]
        for subnet in info['ipv4']:
            self.subnet_cache['ipv4'][ipaddress.ip_network(subnet)] = (asn, info['description'])
        for subnet in info['ipv6']:
            self.subnet_cache['ipv6'][ipaddress.ip_network(subnet)] = (asn, info['description'])
