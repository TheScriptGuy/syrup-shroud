import ipaddress
from typing import Optional

class IPAddressValidator:
    """
    Validates and categorizes IP addresses.
    """

    @staticmethod
    def is_valid_ip(ip_address: str) -> bool:
        """
        Checks if a string is a valid IP address.

        Args:
            ip_address (str): The IP address to validate.

        Returns:
            bool: True if the IP address is valid, False otherwise.
        """
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_excluded_ip(ip_address: str) -> bool:
        """
        Checks if the IP address is in a reserved or special-use range.

        Args:
            ip_address (str): The IP address to check.

        Returns:
            bool: True if the IP is in an excluded range, False otherwise.
        """
        excluded_ranges = [
            "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",  # Private ranges
            "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16",  # Special-use
            "224.0.0.0/4", "255.255.255.255/32"  # Multicast and Broadcast
        ]

        ip = ipaddress.ip_address(ip_address)
        return any(ip in ipaddress.ip_network(cidr) for cidr in excluded_ranges)

    @staticmethod
    def is_public_ip(ip_address: str) -> bool:
        """
        Checks if an IP address is public.

        Args:
            ip_address (str): The IP address to check.

        Returns:
            bool: True if the IP address is public, False otherwise.
        """
        ip = ipaddress.ip_address(ip_address)
        return not ip.is_private and not IPAddressValidator.is_excluded_ip(ip_address)

