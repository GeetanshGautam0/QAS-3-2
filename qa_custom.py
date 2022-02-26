from typing import *
from dataclasses import dataclass
from qa_enum import *


@dataclass
class HexColor:
    color: str


@dataclass
class LoggingPackage:
    logging_level: LoggingLevel
    data: str
    file_path: str
