# quick boilerplate to get into the db

import json
import sqlite3
from pathlib import Path
from src.pv_sources import initialize_db, pull_source, gather_ioc_info


db_path = Path(__file__).parent / 'data' / 'LCLS_PV.db'
print(db_path)
conn = sqlite3.connect(db_path)
c = conn.cursor()

with open(db_path.parent / 'ioc_info.json', 'r') as f:
    ioc_info = json.load(f)
