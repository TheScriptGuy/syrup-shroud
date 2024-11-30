from ipwhois import IPWhois
from typing import Optional

class ASNLookup:
    """
    Handles WHOIS lookups and ASN-related information retrieval.
    """

    @staticmethod
    def get_asn_info(ip_address: str) -> Optional[dict]:
        """
        Fetches ASN information for an IP address using WHOIS.

        Args:
            ip_address (str): The IP address to lookup.

        Returns:
            Optional[dict]: ASN information including ASN number and description.
        """
        try:
            ip_whois = IPWhois(ip_address)
            result = ip_whois.lookup_rdap(asn_methods=['whois'])
            return {
                'asn': result.get('asn'),
                'asn_description': result.get('asn_description').split(',')[0].strip().lower()
            }
        except Exception as e:
            return {"error": str(e)}

