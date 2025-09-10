import streamlit as st
import pandas as pd
import yfinance as yf

# ----------------------
# Utility Functions
# ----------------------

def get_fx_changes(pairs, period='1d', interval='1h'):
    changes = {}
    for p in pairs:
        try:
            data = yf.download(p, period=period, interval=interval, progress=False)
            if not data.empty:
                last = data['Close'].iloc[-1]
                prev = data['Close'].iloc[0]
                changes[p] = (last - prev) / prev
        except Exception:
            changes[p] = None
    return changes


def compute_currency_strength(changes):
    def pair_to_currencies(pair):
        s = pair.replace('=X', '')
        base, quote = s[:3], s[3:]
        return base, quote

    currencies = ['USD','EUR','JPY','GBP','AUD','CAD','CHF','NZD']
    scores = {c: 0.0 for c in currencies}
    counts = {c: 0 for c in currencies}

    for p, ch in changes.items():
        if ch is None:
            continue
        base, quote = pair_to_currencies(p)
        scores[base] += ch
        counts[base] += 1
        scores[quote] -= ch
        counts[quote] += 1

    for c in scores:
        scores[c] = scores[c]/counts[c] if counts[c] > 0 else 0.0

    return pd.DataFrame.from_dict(scores, orient='index', columns=['Strength']).sort_values(by='Strength', ascending=False)


def build_pair_bias(strength_df):
    pairs = [
        ('EUR','USD'), ('USD','JPY'), ('GBP','USD'), ('AUD','USD'), ('USD','CAD'),
        ('USD','CHF'), ('NZD','USD'), ('EUR','JPY'), ('GBP','JPY'), ('AUD','JPY')
    ]

    bias_data = []
    for base, quote in pairs:
        if base not in strength_df.index or quote not in strength_df.index:
            continue
        diff = strength_df.loc[base, 'Strength'] - strength_df.loc[quote, 'Strength']
        if diff > 0.0005:
            bias = 'Bullish'
        elif diff < -0.0005:
            bias = 'Bearish'
        else:
            bias = 'Neutral'
        bias_data.append({
            'Pair': f"{base}/{quote}",
            'Bias': bias,
            'Strength_Diff': diff
        })

    return pd.DataFrame(bias_data).sort_values(by='Strength_Diff', ascending=False)

# ----------------------
# Streamlit App Layout
# ----------------------

st.set_page_config(page_title="Macro FX Dashboard", layout="wide")
st.title("💱 Macro FX Dashboard (MVP)")

pairs = [
 'EURUSD=X','GBPUSD=X','USDJPY=X','AUDUSD=X','USDCAD=X','USDCHF=X','NZDUSD=X',
 'EURJPY=X','GBPJPY=X','AUDJPY=X'
]

with st.spinner("Fetching FX data..."):
    changes = get_fx_changes(pairs)
    strength_df = compute_currency_strength(changes)
    bias_df = build_pair_bias(strength_df)

# Currency Strength Heatmap
st.subheader("📊 Currency Strength (Relative)")
st.dataframe(strength_df.style.background_gradient(cmap='RdYlGn'))

# Pair Bias Board
st.subheader("📌 Pair Bias Board")
st.dataframe(
    bias_df.style.applymap(
        lambda x: 'color: green' if x=="Bullish" else ('color: red' if x=="Bearish" else 'color: gray'),
        subset=['Bias']
    )
)

st.markdown("---")
st.caption("⚠️ Disclaimer: Demo dashboard for educational purposes only. Data from Yahoo Finance may be delayed.")
