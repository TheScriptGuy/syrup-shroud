from dataclasses import dataclass
from time import time

@dataclass
class PhaseStats:
    start_time: float = 0.0
    last_update_time: float = 0.0
    items_processed: int = 0
    last_update_items: int = 0

class StatisticsTracker:
    def __init__(self, line_report_interval: int = 100000, lookup_report_interval: int = 100):
        self.line_stats = PhaseStats()
        self.lookup_stats = PhaseStats()
        self.line_report_interval = line_report_interval
        self.lookup_report_interval = lookup_report_interval

    def start_line_processing(self):
        self.line_stats.start_time = time()
        self.line_stats.last_update_time = self.line_stats.start_time

    def stop_line_processing(self):
        self.line_end_time = time()

    def start_lookup_processing(self):
        self.lookup_stats.start_time = time()
        self.lookup_stats.last_update_time = self.lookup_stats.start_time

    def stop_lookup_processing(self):
        self.lookup_end_time = time()

    def update_line_count(self, current_lines: int, logger) -> None:
        self.line_stats.items_processed = current_lines
        if current_lines % self.line_report_interval == 0:
            current_time = time()
            interval_time = current_time - self.line_stats.last_update_time
            lines_processed = current_lines - self.line_stats.last_update_items
            rate = lines_processed / interval_time
            logger.info(f"Processing rate: {rate:.2f} lines/second")
            self.line_stats.last_update_time = current_time
            self.line_stats.last_update_items = current_lines

    def update_lookup_count(self, current_lookups: int, logger) -> None:
        self.lookup_stats.items_processed = current_lookups
        if current_lookups % self.lookup_report_interval == 0:
            current_time = time()
            interval_time = current_time - self.lookup_stats.last_update_time
            lookups_processed = current_lookups - self.lookup_stats.last_update_items
            rate = lookups_processed / interval_time
            logger.info(f"IP Lookup rate: {rate:.2f} lookups/second")
            self.lookup_stats.last_update_time = current_time
            self.lookup_stats.last_update_items = current_lookups

    def get_final_stats(self) -> dict:
        line_processing_time = self.lookup_stats.start_time - self.line_stats.start_time
        lookup_processing_time = time() - self.lookup_stats.start_time
        
        return {
            "line_processing": {
                "total_time_seconds": round(line_processing_time, 2),
                "total_lines": self.line_stats.items_processed,
                "average_rate": round(self.line_stats.items_processed / line_processing_time, 2)
            },
            "lookup_processing": {
                "total_time_seconds": round(lookup_processing_time, 2),
                "total_lookups": self.lookup_stats.items_processed,
                "average_rate": round(self.lookup_stats.items_processed / lookup_processing_time, 2)
            }
        }
