import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="ニュース重要度スコア可視化", layout="wide")

st.title("ニュース重要度スコア可視化アプリ")
st.caption("GitHubに置いたCSVを自動で読み込みます")


from pathlib import Path

CSV_PATH = Path("相関係数を出す数値のグラフ.csv")

if not CSV_PATH.exists():
    st.error("CSVファイルが見つかりません")
    st.stop()

df = pd.read_csv(CSV_PATH)


# 列名ゆらぎ吸収
rename = {}
for c in df.columns:
    cl = str(c).strip().lower()
    if cl in ["date", "day", "name", "日付"]:
        rename[c] = "Date"
    elif cl in ["value.jpy", "usdjpy", "usd/jpy", "rate", "value"]:
        rename[c] = "USDJPY"
    elif cl in ["sentiment", "emotion", "score", "感情の値", "感情"]:
        rename[c] = "Sentiment"
    elif cl in ["newscount", "news_count", "count", "news"]:
        rename[c] = "NewsCount"
df = df.rename(columns=rename)

need = {"Date", "USDJPY", "Sentiment"}
missing = need - set(df.columns)
if missing:
    st.error(f"CSVに必要な列が足りません: {missing}")
    st.info("列名を Date, USDJPY, Sentiment にして保存し直してください。")
    st.write("今CSVに入っている列名：", list(df.columns))
    st.stop()

if "NewsCount" not in df.columns:
    df["NewsCount"] = 1

# 型整形
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["USDJPY"] = pd.to_numeric(df["USDJPY"], errors="coerce")
df["Sentiment"] = pd.to_numeric(df["Sentiment"], errors="coerce")
df["NewsCount"] = pd.to_numeric(df["NewsCount"], errors="coerce")

df = df.dropna(subset=["Date","USDJPY","Sentiment"]).sort_values("Date").reset_index(drop=True)

# 前日比
df["FX_Change"] = df["USDJPY"].diff()
df["FX_AbsChange"] = df["FX_Change"].abs().fillna(0)

# スコア部品
df["S_strength"] = df["Sentiment"].abs()
df["S_volume"] = (1 + df["NewsCount"].clip(lower=0)) ** 0.5
df["S_fxmove"] = df["FX_AbsChange"]

def minmax(s):
    s = s.astype(float)
    if s.max() == s.min():
        return s * 0
    return (s - s.min()) / (s.max() - s.min())

df["N_strength"] = minmax(df["S_strength"])
df["N_volume"]   = minmax(df["S_volume"])
df["N_fxmove"]   = minmax(df["S_fxmove"])

st.sidebar.header("重み（合計は自動で1に調整）")
w1 = st.sidebar.slider("感情の強さ", 0.0, 1.0, 0.45, 0.05)
w2 = st.sidebar.slider("ニュース量",  0.0, 1.0, 0.35, 0.05)
w3 = st.sidebar.slider("市場の動き", 0.0, 1.0, 0.20, 0.05)
ws = max(w1 + w2 + w3, 1e-9)
w1, w2, w3 = w1/ws, w2/ws, w3/ws
df["Importance"] = (100*(w1*df["N_strength"] + w2*df["N_volume"] + w3*df["N_fxmove"])).round(1)

def label(x):
    if x >= 75: return "🔴 要注意"
    if x >= 50: return "🟠 注意"
    if x >= 25: return "🟡 様子見"
    return "🟢 影響小"
df["Alert"] = df["Importance"].apply(label)

# ===== 表示 =====
col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("時系列")
    fig = plt.figure()
    ax = plt.gca()
    ax.plot(df["Date"], df["USDJPY"], label="USD/JPY")
    ax.set_ylabel("USD/JPY")
    ax2 = ax.twinx()
    ax2.plot(df["Date"], df["Sentiment"], linestyle="--", label="Sentiment")
    ax2.plot(df["Date"], df["Importance"], linestyle=":", label="Importance(0-100)")
    ax2.set_ylabel("Sentiment / Importance")
    lines, labels_ = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels_ + labels2, loc="upper left")
    st.pyplot(fig)

with col2:
    st.subheader("重要日 Top10")
    st.dataframe(
        df.sort_values("Importance", ascending=False).head(10)[
            ["Date","USDJPY","Sentiment","NewsCount","FX_Change","Importance","Alert"]
        ],
        use_container_width=True
    )

st.subheader("全データ")
st.dataframe(
    df[["Date","USDJPY","Sentiment","NewsCount","FX_Change","Importance","Alert"]],
    use_container_width=True
)


CSV_PATH = Path("相関係数を出す数値のグラフ.csv")


if CSV_PATH.exists():
    df = pd.read_csv(CSV_PATH)
    st.success(f"CSV読み込みOK: {CSV_PATH}")
    st.dataframe(df, use_container_width=True)
else:
    st.error(f"CSVが見つからない: {CSV_PATH}")
    st.write("GitHubのリポジトリに data フォルダとCSVがあるか確認してね。")



