import argparse
import asyncio
from log_analysis.log_parser import LogParser
from log_analysis.ip_address_validator import IPAddressValidator
from log_analysis.asn_lookup import ASNLookup
from log_analysis.subnet_mapper import SubnetMapper
from log_analysis.data_aggregator import DataAggregator
from log_analysis.data_output import DataOutput
from log_analysis.log_processor import LogProcessor

def main():
    # Argument parser setup
    parser = argparse.ArgumentParser(description="Parse log file and extract matching lines.")
    parser.add_argument("log_file", type=str, help="Path to the log file.")
    parser.add_argument("regex_pattern", type=str, help="Regex pattern to match lines in the log file.")
    parser.add_argument("--tail", type=int, default=0, help="Number of lines to process from the end of the file.")
    parser.add_argument("--sort_by", type=str, choices=["IP Count", "Total Entries"], default="IP Count",
                        help="Column to sort by in the summary (default: 'IP Count').")
    parser.add_argument("--separator", type=str, default=" ", help="Field separator in the log file (default: space).")
    parser.add_argument("--column", type=int, default=7, help="Column index (0-based) to extract IP address (default: 7).")
    parser.add_argument("--json", type=str, help="File path to output JSON data. Suppresses stdout output.")
    parser.add_argument("--ripedb", type=str, help="Used previously saved mapping data")
    args = parser.parse_args()

    # Instantiate the modular classes
    parser = LogParser()
    validator = IPAddressValidator()
    lookup = ASNLookup()
    mapper = SubnetMapper(args.ripedb if args.ripedb else None)
    aggregator = DataAggregator()
    output = DataOutput()

   
    # Create the log processor instance
    processor = LogProcessor(parser, validator, lookup, mapper, aggregator, output)

    # Extract log_file and regex_pattern explicitly, pass the rest as **kwargs
    log_file = args.log_file
    regex_pattern = args.regex_pattern

    # Run the log processing task
    result = asyncio.run(processor.process_log(
        log_file=log_file,
        regex_pattern=regex_pattern,
        **{k: v for k, v in vars(args).items() if k not in ['log_file', 'regex_pattern', 'ripedb']}
    ))

    # Handle JSON output
    if args.json:
        output.write_json(args.json, aggregator.asn_ip_counter)
    else:
        # Default output to stdout
        summary_data = aggregator.summarize(args.sort_by)
        headers = ["BGP ASN", "BGP Description", "IP Count", "Total Entries", "Sample IPs"]
        output.print_table(summary_data, headers)
    
    if args.ripedb:
        # Lets write the contents of the subnets to file
        mapper.write_subnets_to_file(args.ripedb)

if __name__ == "__main__":
    main()

