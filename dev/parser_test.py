import sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.append(str(HERE / "../utils"))

from parsers import parse_title

title = "David Bowie- 01 Speed of Life"

parsed = parse_title(title, False)

pass