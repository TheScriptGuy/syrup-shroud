import csv
import re
from typing import List

class LogParser:
    """
    Parses log files and extracts relevant fields.
    """

    @staticmethod
    def parse_line(line: str, separator: str) -> List[str]:
        """
        Parses a log line into fields using the specified separator.

        Args:
            line (str): The log line to parse.
            separator (str): Field separator.

        Returns:
            List[str]: Parsed fields.
        """
        if separator == " ":
            return re.split(r'\s+', line.strip())
        elif separator == "\t":
            return line.strip().split("\t")
        else:
            return next(csv.reader([line], delimiter=separator))

    @staticmethod
    def read_last_lines(filename: str, num_lines: int) -> List[str]:
        """
        Reads the last N lines from a file.

        Args:
            filename (str): Path to the log file.
            num_lines (int): Number of lines to read from the end.

        Returns:
            List[str]: Last N lines from the file.
        """
        with open(filename, 'rb') as f:
            f.seek(0, 2)
            buffer = bytearray()
            pointer_location = f.tell()
            lines_found = 0

            while pointer_location >= 0 and lines_found < num_lines:
                f.seek(pointer_location)
                pointer_location -= 1
                byte = f.read(1)
                if byte == b'\n':
                    lines_found += 1
                buffer.extend(byte)

            lines = buffer[::-1].decode(errors='ignore').strip().split('\n')
            return lines[-num_lines:] if num_lines > 0 else lines

