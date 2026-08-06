import pandas as pd
from pathlib import Path

base = Path(r"C:\Users\moham\Documents\L'Oreal")
for p in sorted(base.glob("DLL_INVENTORY*.xlsx")):
    xl = pd.ExcelFile(p)
    print("===", p.name, "sheets:", xl.sheet_names)
    for sh in xl.sheet_names:
        df = pd.read_excel(p, sheet_name=sh, nrows=5)
        print(" sheet", sh, "cols:", list(df.columns), "nrows_preview", len(df))
        print(df.head(3).to_string())
    full = pd.read_excel(p)
    print(" full_rows:", len(full))
    print()
