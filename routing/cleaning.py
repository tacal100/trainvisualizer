import pandas as pd, pathlib, shutil
data_dir = pathlib.Path("public/data")
for p in data_dir.glob("*.csv"):
    df = pd.read_csv(p)
    # Define "empty" as all values NaN or blank after strip
    def col_all_empty(series):
        return series.isna().all() or series.astype(str).str.strip().replace({"nan":""}).eq("").all()
    to_drop = [c for c in df.columns if col_all_empty(df[c])]
    if to_drop:
        df.drop(columns=to_drop).to_csv(p, index=False)
        print(f"{p.name}: dropped {len(to_drop)} -> {to_drop}")
