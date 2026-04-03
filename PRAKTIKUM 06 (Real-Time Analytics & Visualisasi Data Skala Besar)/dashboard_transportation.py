import streamlit as st
import time
import sys
import os
import plotly.graph_objects as go

# ==========================
# MODULE PATH
# ==========================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from analytics import transportation_analytics as ta
from alerts import transportation_alert as alert

# ==========================
# CONFIG
# ==========================
DATA_PATH = "data/serving/transportation"
REFRESH_INTERVAL = 5

st.set_page_config(
    page_title="Smart Transportation",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================
# THEME
# ==========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

    :root {
        --bg-primary: #0a0e17;
        --bg-card: #111827;
        --bg-card-hover: #1a2233;
        --border: #1f2937;
        --text-primary: #e5e7eb;
        --text-secondary: #9ca3af;
        --text-muted: #6b7280;
        --accent: #60a5fa;
        --accent-dim: rgba(96,165,250,0.12);
        --danger: #f87171;
        --danger-dim: rgba(248,113,113,0.1);
        --success: #34d399;
    }

    .stApp {
        font-family: 'IBM Plex Sans', -apple-system, sans-serif;
        background-color: var(--bg-primary);
    }

    #MainMenu, footer, header { visibility: hidden; }

    /* ---- HEADER ---- */
    .hdr {
        background: var(--bg-card);
        border-bottom: 1px solid var(--border);
        padding: 1rem 1.75rem;
        margin: -1rem -1rem 1.25rem -1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .hdr-left h1 {
        color: var(--text-primary);
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.2px;
    }
    .hdr-left span {
        color: var(--text-muted);
        font-size: 0.72rem;
        letter-spacing: 0.3px;
    }
    .hdr-right {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .live-dot {
        width: 7px; height: 7px;
        background: var(--success);
        border-radius: 50%;
        animation: blink 1.8s infinite;
    }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
    .live-label {
        color: var(--success);
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    /* ---- METRIC GRID ---- */
    .m-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.25rem;
    }
    .m-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-top: 2px solid var(--accent);
        padding: 1rem 1.25rem;
    }
    .m-card .m-label {
        color: var(--text-muted);
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.35rem;
    }
    .m-card .m-value {
        color: var(--text-primary);
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* ---- ALERT ---- */
    .alert-row {
        background: var(--danger-dim);
        border: 1px solid rgba(248,113,113,0.25);
        border-left: 3px solid var(--danger);
        padding: 0.6rem 1rem;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .alert-row .a-dot {
        width: 6px; height: 6px;
        background: var(--danger);
        border-radius: 50%;
        flex-shrink: 0;
    }
    .alert-row .a-text {
        color: var(--danger);
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* ---- SECTION ---- */
    .sec {
        color: var(--text-secondary);
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin: 1.5rem 0 0.6rem 0;
    }

    /* ---- SEPARATOR ---- */
    .sep {
        border: none;
        border-top: 1px solid var(--border);
        margin: 1.25rem 0;
    }

    /* ---- INFO ---- */
    .info-row {
        background: var(--accent-dim);
        border: 1px solid rgba(96,165,250,0.2);
        border-left: 3px solid var(--accent);
        padding: 0.6rem 1rem;
        color: var(--accent);
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* ---- HIDE STREAMLIT ELEMENTS ---- */
    .stDeployButton { display: none; }
    div[data-testid="stToolbar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ==========================
# PLOTLY THEME
# ==========================
PLT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#111827",
    font=dict(family="IBM Plex Sans", color="#9ca3af", size=11),
    margin=dict(l=45, r=15, t=10, b=40),
    xaxis=dict(gridcolor="#1f2937", zerolinecolor="#1f2937", linecolor="#1f2937"),
    yaxis=dict(gridcolor="#1f2937", zerolinecolor="#1f2937", linecolor="#1f2937"),
    height=280,
)

BLUE = "#60a5fa"
BLUE_FILL = "rgba(96,165,250,0.08)"

# ==========================
# LOOP
# ==========================
if "c" not in st.session_state:
    st.session_state.c = 0

placeholder = st.empty()

while True:
    st.session_state.c += 1
    k = st.session_state.c

    with placeholder.container():

        # HEADER
        st.markdown("""
        <div class="hdr">
            <div class="hdr-left">
                <h1>Smart Transportation | Real-Time Analytics</h1>
                <span>Big Data Optimized · Modul 6 Praktikum</span>
            </div>
            <div class="hdr-right">
                <div class="live-dot"></div>
                <span class="live-label">Live</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # LOAD DATA
        df = ta.load_data(DATA_PATH)
        if df.empty:
            st.markdown('<div class="info-row">Waiting for streaming data...</div>', unsafe_allow_html=True)
            time.sleep(REFRESH_INTERVAL)
            continue

        df = ta.preprocess(df)
        df_sample = df.tail(1000)

        # METRICS
        try:
            m = ta.compute_metrics(df)
            peak = ta.detect_peak_hour(df)
        except Exception:
            m = {"total_trips": 0, "total_fare": 0, "top_location": "-"}
            peak = None

        peak_str = f"{peak}:00" if peak is not None else "—"
        fare_str = f"{int(m['total_fare']):,}".replace(",", ".")

        st.markdown(f"""
        <div class="m-grid">
            <div class="m-card">
                <div class="m-label">Total Trips</div>
                <div class="m-value">{m['total_trips']}</div>
            </div>
            <div class="m-card">
                <div class="m-label">Total Fare (IDR)</div>
                <div class="m-value">{fare_str}</div>
            </div>
            <div class="m-card">
                <div class="m-label">Top Location</div>
                <div class="m-value">{m['top_location']}</div>
            </div>
            <div class="m-card">
                <div class="m-label">Peak Hour</div>
                <div class="m-value">{peak_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ALERTS
        try:
            al = alert.generate_alert(df)
            if al:
                st.markdown('<div class="sec">Alerts</div>', unsafe_allow_html=True)
                for a in al:
                    st.markdown(f'<div class="alert-row"><div class="a-dot"></div><div class="a-text">{a}</div></div>', unsafe_allow_html=True)
        except Exception:
            pass

        st.markdown('<hr class="sep">', unsafe_allow_html=True)

        # TRAFFIC WINDOW
        st.markdown('<div class="sec">Traffic Volume | Window Aggregation (1 min)</div>', unsafe_allow_html=True)
        try:
            tw = ta.traffic_per_window(df)
            if tw is not None and not tw.empty:
                f1 = go.Figure(go.Scatter(
                    x=tw.index, y=tw.values,
                    mode="lines", line=dict(color=BLUE, width=1.5),
                    fill="tozeroy", fillcolor=BLUE_FILL
                ))
                f1.update_layout(**PLT, xaxis_title="Time", yaxis_title="Trips/min")
                st.plotly_chart(f1, key=f"a{k}")
        except Exception as e:
            st.warning(str(e))

        st.markdown('<hr class="sep">', unsafe_allow_html=True)

        # FARE + VEHICLE
        c1, c2 = st.columns(2, gap="medium")

        with c1:
            st.markdown('<div class="sec">Revenue by Location</div>', unsafe_allow_html=True)
            try:
                fd = ta.fare_per_location(df_sample)
                if not fd.empty:
                    shade = ["#60a5fa","#93c5fd","#bfdbfe","#dbeafe","#eff6ff"][:len(fd)]
                    f2 = go.Figure(go.Bar(
                        x=fd.index, y=fd.values,
                        marker=dict(color=shade),
                        text=[f"{v:,.0f}" for v in fd.values],
                        textposition="outside",
                        textfont=dict(color="#9ca3af", size=9),
                    ))
                    f2.update_layout(**PLT, xaxis_title="Location", yaxis_title="Fare (IDR)")
                    st.plotly_chart(f2, key=f"b{k}")
            except Exception as e:
                st.warning(str(e))

        with c2:
            st.markdown('<div class="sec">Vehicle Distribution</div>', unsafe_allow_html=True)
            try:
                vd = ta.vehicle_distribution(df_sample)
                if not vd.empty:
                    shade2 = ["#60a5fa","#93c5fd","#bfdbfe"][:len(vd)]
                    f3 = go.Figure(go.Bar(
                        x=vd.index, y=vd.values,
                        marker=dict(color=shade2),
                        text=vd.values, textposition="outside",
                        textfont=dict(color="#9ca3af", size=10),
                    ))
                    f3.update_layout(**PLT, xaxis_title="Type", yaxis_title="Count")
                    st.plotly_chart(f3, key=f"c{k}")
            except Exception as e:
                st.warning(str(e))

        st.markdown('<hr class="sep">', unsafe_allow_html=True)

        # MOBILITY TREND
        st.markdown('<div class="sec">Mobility Trend | Downsampled (10s)</div>', unsafe_allow_html=True)
        try:
            mt = ta.mobility_trend(df_sample)
            if not mt.empty:
                f4 = go.Figure(go.Scatter(
                    x=mt.index, y=mt.values,
                    mode="lines", line=dict(color=BLUE, width=1.5),
                    fill="tozeroy", fillcolor=BLUE_FILL
                ))
                f4.update_layout(**PLT, xaxis_title="Time", yaxis_title="Fare (IDR)")
                st.plotly_chart(f4, key=f"d{k}")
        except Exception as e:
            st.warning(str(e))

        st.markdown('<hr class="sep">', unsafe_allow_html=True)

        # ANOMALY
        st.markdown('<div class="sec">Anomaly Detection</div>', unsafe_allow_html=True)
        try:
            anom = ta.detect_anomaly(df_sample)
            if not anom.empty:
                st.dataframe(anom.tail(20), hide_index=True, key=f"e{k}")
            else:
                st.markdown('<div class="info-row">No anomalies in current window</div>', unsafe_allow_html=True)
        except Exception as e:
            st.warning(str(e))

        st.markdown('<hr class="sep">', unsafe_allow_html=True)

        # LIVE TABLE
        st.markdown('<div class="sec">Live Trip Data (Last 50)</div>', unsafe_allow_html=True)
        st.dataframe(df_sample.tail(50), hide_index=True, key=f"f{k}")

    time.sleep(REFRESH_INTERVAL)
