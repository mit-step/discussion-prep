import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from db import get_conn, drop_warrants

drop_warrants(get_conn())
print("dropped")