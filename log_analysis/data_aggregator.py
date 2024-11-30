from collections import defaultdict, deque
from typing import Dict, Tuple, List

class DataAggregator:
    """
    Aggregates data for summarization and reporting.
    """

    def __init__(self):
        # Counter structure: {(ASN, Description): {ips, sample_ips, total_entries}}
        self.asn_ip_counter = defaultdict(lambda: {
            "ips": set(),
            "sample_ips": deque(maxlen=3),
            "total_entries": 0
        })

    def add_entry(self, asn: str, description: str, ip_address: str) -> None:
        """
        Adds an IP address entry under a specific ASN.

        Args:
            asn (str): ASN number.
            description (str): ASN description.
            ip_address (str): The IP address to add.
        """
        asn_data = self.asn_ip_counter[(asn, description)]
        asn_data["total_entries"] += 1
        if ip_address not in asn_data["ips"]:
            asn_data["ips"].add(ip_address)
            asn_data["sample_ips"].append(ip_address)

    def summarize(self, sort_by: str) -> List[Tuple]:
        """
        Generates a summary of the collected data.

        Args:
            sort_by (str): Column to sort by ('IP Count' or 'Total Entries').

        Returns:
            List[Tuple]: Summary data ready for output.
        """
        summary_data = [
            (asn, description, len(data["ips"]), data["total_entries"], ", ".join(data["sample_ips"]))
            for (asn, description), data in self.asn_ip_counter.items()
        ]
        if sort_by == "IP Count":
            summary_data.sort(key=lambda x: (-x[2], -x[3]))
        elif sort_by == "Total Entries":
            summary_data.sort(key=lambda x: (-x[3], -x[2]))
        return summary_data

