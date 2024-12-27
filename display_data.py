from typing import Dict, List
from prettytable import PrettyTable

class DisplayData:
    """Handles data display formatting and presentation."""

    SORT_COLUMNS = {
        "BGP ASN": lambda x: x[0],
        "IP Count": lambda x: x[1]['ip_count'],
        "Total Entries": lambda x: x[1]['total_hits']
    }

    def __init__(self, ip_data: Dict[str, Dict]):
        self.ip_data = ip_data
        self.asn_data = self._group_by_asn()

    def _group_by_asn(self) -> Dict[str, Dict]:
        """Group IP data by ASN."""
        asn_grouped = {}
        for ip, details in self.ip_data.items():
            asn = details.get('asn', 'Unknown')
            if asn not in asn_grouped:
                asn_grouped[asn] = {
                    'description': details.get('description', 'Unknown'),
                    'ip_count': 0,
                    'total_hits': 0,
                    'ips': []
                }
            asn_grouped[asn]['ip_count'] += 1
            asn_grouped[asn]['total_hits'] += details['count']
            asn_grouped[asn]['ips'].append(ip)
        return asn_grouped

    def display_asn_table(self, sort_by: str = "IP Count,Total Entries", max_sample_ips: int = 3) -> None:
        """Display ASN information in formatted table."""
        table = PrettyTable()
        table.field_names = ["BGP ASN", "BGP Description", "IP Count",
                           "Total Entries", "Sample IPs"]

        sort_fields = [field.strip() for field in sort_by.split(',')]
        sorted_data = sorted(
            self.asn_data.items(),
            key=lambda x: tuple(self.SORT_COLUMNS[field](x) for field in sort_fields),
        reverse=True
        )
        for asn, data in sorted_data:
            table.add_row([
                asn,
                data['description'],
                data['ip_count'],
                data['total_hits'],
                ', '.join(sorted(data['ips'])[:max_sample_ips])
            ])

        table.align = 'l'
        table.max_width = 100
        print(table)
