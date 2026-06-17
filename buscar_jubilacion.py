import pandas as pd

df = pd.read_csv("data/clean/enaho_2024_clean.csv",
                 encoding="utf-8", low_memory=False)

candidatas = [c for c in df.columns if any(
    x in c.upper() for x in [
        'JUBIL', 'ONP', 'AFP', 'PENSION',
        'RETIRO', 'CTS', 'P550', 'P551',
        'P552', 'INGPENSION', 'INGJUB'
    ]
)]

print(f"Variables encontradas: {len(candidatas)}")
for col in candidatas:
    print(f"\n{col}:")
    print(df[col].value_counts(dropna=False).head(5))
