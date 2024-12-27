import ipaddress
from typing import Tuple, Optional

class IPValidator:
    """Class to validate and categorize IP addresses."""
    
    def __init__(self):
        """Initialize the IP validator."""
        self.invalid_count = 0
        self.max_invalid_attempts = 2
    
    def validate_ip(self, ip_string: str) -> Tuple[bool, Optional[str]]:
        """Validate if a string is an IP address and determine its version.
        
        Args:
            ip_string (str): String to validate as IP address
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, ip_version)
            where ip_version is either 'IPv4', 'IPv6', or None if invalid
        """
        try:
            ip_obj = ipaddress.ip_address(ip_string.strip())
            return True, 'IPv6' if isinstance(ip_obj, ipaddress.IPv6Address) else 'IPv4'
        except ValueError:
            self.invalid_count += 1
            if self.invalid_count >= self.max_invalid_attempts:
                raise ValueError("Could not find any valid IP addresses in the initial data")
            return False, None
