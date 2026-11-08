"""4편 예시 규칙 백테스트 (TQQQ, 가상 $20,000) — 규칙대로 vs 첫날 전부 사서 보유.

규칙(4편 예시): 40분할(1회 $500), 종가가 전일 종가 x1.02 이하면 LOC 매수(소수점 버림),
묶음별 매수가 x1.10 이상으로 마감하면 그 묶음 LOC 매도, 현금이 $500 미만이면 매수 멈춤.
수수료·세금·환율은 빼고 계산해요. 가격은 분할 보정된 실제 종가(배당 미반영).
결과: data/backtest_tqqq.json
"""
import json
import math
import os

import yfinance as yf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START_CASH, UNIT, BUY_K, SELL_K = 20000.0, 500.0, 1.02, 1.10
PERIODS = [
    ("최근 1년", "2025-11-01", None),
    ("2022년 하락장", "2022-01-01", "2022-12-31"),
    ("2023년 상승장", "2023-01-01", "2023-12-31"),
    ("2021.11 고점부터 지금까지", "2021-11-01", None),
]


def mdd(vals):
    peak, worst = vals[0], 0.0
    for v in vals:
        peak = max(peak, v)
        worst = min(worst, v / peak - 1)
    return worst


def run(px):
    dates, closes = list(px.index), list(px.values)
    cash, lots, buys, sells, no_cash_days, max_lots = START_CASH, [], 0, 0, 0, 0
    realized = 0.0
    eq, hold = [], []
    hold_qty = math.floor(START_CASH / closes[0])
    hold_cash = START_CASH - hold_qty * closes[0]
    for i, (d, c) in enumerate(zip(dates, closes)):
        if i > 0:
            # 매도 먼저(기간 예약 매도), 그다음 매수
            keep = []
            for q, bp in lots:
                if c >= bp * SELL_K:
                    cash += q * c
                    realized += q * (c - bp)
                    sells += 1
                else:
                    keep.append((q, bp))
            lots = keep
            if c <= closes[i - 1] * BUY_K:
                if cash >= UNIT:
                    q = math.floor(UNIT / c)
                    if q > 0:
                        lots.append((q, c))
                        cash -= q * c
                        buys += 1
                else:
                    no_cash_days += 1
        max_lots = max(max_lots, len(lots))
        eq.append(cash + sum(q for q, _ in lots) * c)
        hold.append(hold_cash + hold_qty * c)
    step = max(1, len(dates) // 40)
    curve = [{"date": dates[i].strftime("%Y-%m-%d"), "rule": round(eq[i]), "hold": round(hold[i]), "close": round(closes[i], 2)}
             for i in list(range(0, len(dates), step)) + [len(dates) - 1]]
    return {
        "start": dates[0].strftime("%Y-%m-%d"), "end": dates[-1].strftime("%Y-%m-%d"), "days": len(dates),
        "price_start": round(closes[0], 2), "price_end": round(closes[-1], 2),
        "price_change_pct": round((closes[-1] / closes[0] - 1) * 100, 1),
        "rule": {"final": round(eq[-1]), "return_pct": round((eq[-1] / START_CASH - 1) * 100, 1),
                 "mdd_pct": round(mdd(eq) * 100, 1), "buys": buys, "sells": sells, "realized": round(realized),
                 "open_lots": len(lots), "max_lots": max_lots, "cash_end": round(cash),
                 "days_wanted_to_buy_but_no_cash": no_cash_days,
                 },
        "hold": {"final": round(hold[-1]), "return_pct": round((hold[-1] / START_CASH - 1) * 100, 1),
                 "mdd_pct": round(mdd(hold) * 100, 1)},
        "curve": curve,
    }


def main():
    df = yf.download("TQQQ", start="2021-10-01", auto_adjust=False, progress=False)
    close = df["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]
    close = close.dropna()
    out = {"rules": {"ticker": "TQQQ", "start_cash": START_CASH, "unit": UNIT, "splits": 40,
                     "buy": "종가 <= 전일 종가 x1.02 (LOC 매수)", "sell": "묶음별 매수가 x1.10 이상 마감 (LOC 매도)",
                     "no_cash": "현금 $500 미만이면 매수 멈춤, 매도만", "excluded": "수수료·세금·환율·배당 제외",
                     "price": "Yahoo Finance 분할 보정 종가", "data_until": close.index[-1].strftime("%Y-%m-%d")},
           "periods": []}
    for name, s, e in PERIODS:
        px = close[s:e] if e else close[s:]
        r = run(px)
        r["name"] = name
        r["rule"].pop("min_cash_pct", None)
        out["periods"].append(r)
        print(f"{name}: {r['start']}~{r['end']} 주가 {r['price_change_pct']}% | 규칙 {r['rule']['return_pct']}% (MDD {r['rule']['mdd_pct']}%, 매수 {r['rule']['buys']} 매도 {r['rule']['sells']}, 현금부족 {r['rule']['days_wanted_to_buy_but_no_cash']}일) | 보유 {r['hold']['return_pct']}% (MDD {r['hold']['mdd_pct']}%)")
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "data", "backtest_tqqq.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
