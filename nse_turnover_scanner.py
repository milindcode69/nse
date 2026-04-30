import pandas as pd
import requests
import io
import datetime
from datetime import timedelta, timezone

BASE_URL = "https://archives.nseindia.com/products/content/sec_bhavdata_full_{date}.csv"

NSE_HOLIDAYS = {
    '2026-01-26','2026-03-03','2026-03-26','2026-03-31','2026-04-03',
    '2026-04-14','2026-05-01','2026-05-28','2026-06-26','2026-09-14',
    '2026-10-02','2026-10-20','2026-11-10','2026-11-24','2026-12-25'
}
NSE_HOLIDAYS = {datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in NSE_HOLIDAYS}

def get_previous_working_day(d):
    while True:
        d -= datetime.timedelta(days=1)
        if d.weekday() < 5 and d not in NSE_HOLIDAYS:
            return d

def download_bhavcopy(date):
    url = BASE_URL.format(date=date.strftime("%d%m%Y"))
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = df.columns.str.strip()
    return df

def main():
    IST = timezone(timedelta(hours=5, minutes=30))
    today = datetime.datetime.now(IST).date()
    
    day2 = get_previous_working_day(today)
    day1 = get_previous_working_day(day2)

    print("Using NSE dates:", day1, "→", day2)

    df1 = download_bhavcopy(day1)
    df2 = download_bhavcopy(day2)

    df1["SERIES"] = df1["SERIES"].astype(str).str.strip()
    df2["SERIES"] = df2["SERIES"].astype(str).str.strip()

    df1 = df1[df1["SERIES"] == "EQ"]
    df2 = df2[df2["SERIES"] == "EQ"]

    df = pd.merge(df1, df2, on="SYMBOL", suffixes=("_D1", "_D2"))

    df = df[(df["TURNOVER_LACS_D1"] > 7000) & (df["TURNOVER_LACS_D2"] > 7000)]

    df["DELIV_PER_D2"] = pd.to_numeric(df["DELIV_PER_D2"], errors="coerce")

    df["Turnover_Multiple"] = df["TURNOVER_LACS_D2"] / df["TURNOVER_LACS_D1"]
    df["Price_Change_%"] = (
        (df["CLOSE_PRICE_D2"] - df["CLOSE_PRICE_D1"]) / df["CLOSE_PRICE_D1"]
    ) * 100

    df = df[df["Turnover_Multiple"] > 1.5]

    output = pd.DataFrame({
        "Stock": df["SYMBOL"],
        "Date": day2.strftime("%d-%m-%Y"),
        f"Turnover_{day1.strftime('%d%b')}": df["TURNOVER_LACS_D1"].astype(int),
        f"Turnover_{day2.strftime('%d%b')}": df["TURNOVER_LACS_D2"].astype(int),
        f"Close_{day2.strftime('%d%b')}": df["CLOSE_PRICE_D2"].astype(float).round(2),
        "Turnover Multiple": df["Turnover_Multiple"].round(2),
        "Delivery %": df["DELIV_PER_D2"].round(2),
        "Price Change %": df["Price_Change_%"].round(2)
    })

    output = output.sort_values(
        by=f"Turnover_{day1.strftime('%d%b')}",
        ascending=False
    )

    filename = f"turnover_{day2.strftime('%d%m%Y')}.csv"
    output.to_csv(filename, index=False)

    print("\nSaved:", filename)
    print(output.head(10))

if __name__ == "__main__":
    main()
