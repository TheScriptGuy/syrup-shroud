import asyncio
import re
from .log_parser import LogParser
from .ip_address_validator import IPAddressValidator
from .asn_lookup import ASNLookup
from .subnet_mapper import SubnetMapper
from .data_aggregator import DataAggregator
from .data_output import DataOutput

class LogProcessor:
    """
    Orchestrates the log processing flow.
    """

    def __init__(self, 
                 parser: LogParser, 
                 validator: IPAddressValidator, 
                 lookup: ASNLookup, 
                 mapper: SubnetMapper, 
                 aggregator: DataAggregator, 
                 output: DataOutput
                 ):
        self.parser = parser
        self.validator = validator
        self.lookup = lookup
        self.mapper = mapper
        self.aggregator = aggregator
        self.output = output

    async def process_log(
        self, log_file: str, regex_pattern: str, **kwargs
    ):
        tail = kwargs.get('tail', 0)
        sort_by = kwargs.get('sort_by', "IP Count")
        separator = kwargs.get('separator', " ")
        column = kwargs.get('column', 7)

        lines_to_process = self.parser.read_last_lines(log_file, tail) if tail > 0 else open(log_file).readlines()
        line_counter = 0
        for line in lines_to_process:
            if re.search(regex_pattern, line):
                fields = self.parser.parse_line(line.strip(), separator)
                if len(fields) > column:
                    # Get the IP Address from the column
                    ip_address = fields[column]

                    # Check IP is valid and that it is not part of exclusion list
                    if not self.validator.is_valid_ip(ip_address) or self.validator.is_excluded_ip(ip_address):
                        continue

                    # Get the ASN for the IP address
                    asn_info = self.mapper.find_asn_for_ip(ip_address)

                    # If nothing could be found (ASN has not been downloaded)
                    if not asn_info:
                        # Lookup the ASN information for the IP
                        whois_result = self.lookup.get_asn_info(ip_address)
                        # If there is no error with the lookup.
                        if 'error' not in whois_result:
                            # Extract the ASN and Description from whois result
                            asn, description = whois_result['asn'], whois_result['asn_description']
                            # Get all the subnets for the ASN
                            subnets = await self.mapper.fetch_subnets(int(asn))
                            # Add subnets to be tracked and in future reduce number of API queries.
                            self.mapper.add_subnets(subnets, asn, description)
                        else:
                            continue
                    else:
                        asn = asn_info[0]
                        description = asn_info[1]

                    self.aggregator.add_entry(asn, description, ip_address)
            
            line_counter += 1
            if line_counter % 10000 == 0:
                print(f"Lines processed - {line_counter}")
            if line_counter % 10000 == 0:
                print(f"IPv4 - {len(self.mapper.subnet_asn_map['ipv4'])}, IPv6 - {len(self.mapper.subnet_asn_map['ipv6'])}")
