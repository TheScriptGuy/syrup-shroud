import argparse
import sys
import re
import traceback

from typing import Dict
from file_operations import FileOperations
from custom_logger import CustomLogger
from ip_validator import IPValidator
from statistics_tracker import StatisticsTracker
from ip_lookup import IPLookup
from display_data import DisplayData

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Parse file for IP addresses')
    parser.add_argument('file', help='File to parse')
    parser.add_argument('regex', help='Regular expression to match lines')
    parser.add_argument('--separator', default=',', help='Field separator (default: comma)')
    parser.add_argument('--column', type=int, required=True, help='Column number to check for IP (0-based)')
    parser.add_argument('--lstrip', help='Text to strip from left of column value')
    parser.add_argument('--rstrip', help='Text to strip from right of column value')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    parser.add_argument('--output', help='Output JSON file for results')
    parser.add_argument('--ripedb', help='RIPE database cache file')
    parser.add_argument('--sort_by', default="IP Count,Total Entries",
                   help='Sort order (comma-separated): BGP ASN, IP Count, Total Entries')
    return parser.parse_args()

def main():
    args = parse_arguments()
    logger = CustomLogger(__name__, 'DEBUG' if args.debug else 'INFO')
    stats_tracker = StatisticsTracker() if args.stats else None
    
    try:
        file_ops = FileOperations(args.file)
        ip_validator = IPValidator()
        ip_lookup = IPLookup(logger, args.ripedb)
        ip_counts: Dict[str, int] = {}
        
        # Phase 1: Parse file and collect IPs
        if stats_tracker:
            stats_tracker.start_line_processing()
        logger.info("Phase 1: Collecting IP addresses")
        pattern = re.compile(args.regex)
        
        for line_count, line in enumerate(file_ops.read_file(), 1):
            if stats_tracker:
                stats_tracker.update_line_count(line_count, logger)
                
            if pattern.search(line.strip()):
                if args.separator == ' ':
                    fields = re.split(r'\s+', line.strip())  # Splitting on one or more spaces
                else:
                    fields = line.strip().split(args.separator)
                if len(fields) > args.column:
                    potential_ip = fields[args.column].strip()
                    if args.lstrip and potential_ip.startswith(args.lstrip):
                        potential_ip = potential_ip[len(args.lstrip):]
                    if args.rstrip and potential_ip.endswith(args.rstrip):
                        potential_ip = potential_ip[:-len(args.rstrip)]
                    if ip_validator.validate_ip(potential_ip)[0]:
                        ip_counts[potential_ip] = ip_counts.get(potential_ip, 0) + 1
       
        if stats_tracker:
            stats_tracker.stop_line_processing()
        
        # Phase 2: Perform ASN lookups
        if stats_tracker:
            stats_tracker.start_lookup_processing()
        
        logger.info("Phase 2: Performing ASN lookups")
        ip_data = {}
        lookup_counter = 0
        for ip in ip_counts:
            lookup_counter += 1
            if stats_tracker:
                stats_tracker.update_lookup_count(lookup_counter, logger)
            asn_info = ip_lookup.lookup_ip(ip)
            ip_data[ip] = {
                'count': ip_counts[ip],
                'asn': asn_info.get('asn') if asn_info else None,
                'description': asn_info.get('asn_description') if asn_info else None
        }
        if stats_tracker:
            stats_tracker.stop_lookup_processing()

        # Output results
        print(f"Found {len(ip_data)} unique IPs with {sum(ip_counts.values())} total hits")
        
        # Display final stats
        if stats_tracker:
            final_stats = stats_tracker.get_final_stats()
            print("\nLine Processing Statistics:")
            print(f"Total time: {final_stats['line_processing']['total_time_seconds']} seconds")
            print(f"Total lines: {final_stats['line_processing']['total_lines']}")
            print(f"Average rate: {final_stats['line_processing']['average_rate']} lines/second")
            print("\nLookup Processing Statistics:")
            print(f"Total time: {final_stats['lookup_processing']['total_time_seconds']} seconds")
            print(f"Total lookups: {final_stats['lookup_processing']['total_lookups']}")
            print(f"Average rate: {final_stats['lookup_processing']['average_rate']} lookups/second")       

        if args.output:
            file_ops.write_json(ip_data, args.output)
        else:
            # Display results
            display = DisplayData(ip_data)
            display.display_asn_table(sort_by=args.sort_by)

            
        ip_lookup.save_cache()
            
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error occurred:\n{error_trace}\nError message: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
