import argparse
import requests
import ipaddress
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

API_URL = "https://stat.ripe.net/data/announced-prefixes/data.json"

def fetch_prefixes(asn: int) -> list[str]:
    """Fetch prefixes for a given ASN."""
    params = {"resource": str(asn)}
    try:
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            return [p["prefix"] for p in data.get("data", {}).get("prefixes", [])]
        else:
            logger.error(f"Failed to fetch prefixes for ASN {asn}: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching prefixes for ASN {asn}: {e}")
    return []

def categorize_prefixes(prefixes: list[str], summarize: bool) -> tuple[list[str], list[str]]:
    """Categorize prefixes into IPv4 and IPv6, with optional summarization."""
    v4, v6 = [], []
    for prefix in prefixes:
        try:
            network = ipaddress.ip_network(prefix)
            if isinstance(network, ipaddress.IPv4Network):
                v4.append(network)
            else:
                v6.append(network)
        except ValueError:
            logger.warning(f"Invalid prefix skipped: {prefix}")

    if summarize:
        v4 = list(ipaddress.collapse_addresses(sorted(v4)))
        v6 = list(ipaddress.collapse_addresses(sorted(v6)))

    return [str(net) for net in v4], [str(net) for net in v6]

def write_to_file(filename: Path, prefixes: list[str]) -> None:
    """Write prefixes to a file, overwriting if it exists."""
    with open(filename, "w") as f:
        f.write("\n".join(prefixes))
    logger.info(f"Written {len(prefixes)} prefixes to {filename}")

def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="Fetch and categorize prefixes for a BGP ASN")
    parser.add_argument("asn", type=int, help="BGP ASN to query")
    parser.add_argument("--prefix", metavar="filename", help="Base filename for prefix output (split into v4 and v6)")
    parser.add_argument("--summarize", action="store_true", help="Summarize contiguous subnets")
    args = parser.parse_args()

    # Fetch and categorize prefixes
    logger.info(f"Fetching prefixes for ASN {args.asn}")
    prefixes = fetch_prefixes(args.asn)
    if not prefixes:
        logger.error(f"No prefixes found for ASN {args.asn}")
        return

    v4_prefixes, v6_prefixes = categorize_prefixes(prefixes, args.summarize)

    if args.prefix:
        # Write to separate files
        base = Path(args.prefix)
        write_to_file(base.with_name(base.stem + "-v4.txt"), v4_prefixes)
        write_to_file(base.with_name(base.stem + "-v6.txt"), v6_prefixes)
    else:
        # Output to stdout
        print("\n".join(v4_prefixes))
        print("\n".join(v6_prefixes))

if __name__ == "__main__":
    main()

