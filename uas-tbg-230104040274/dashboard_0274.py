import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pyspark.sql import SparkSession
from sklearn.linear_model import LinearRegression
import numpy as np

# ─── Configuration ────────────────────────────────────────────────────────────
BASE_DIR     = os.path.abspath(os.path.dirname(__file__))
OUTPUT_TOTAL = os.path.join(BASE_DIR, "output", "patient_total")
OUTPUT_TIME  = os.path.join(BASE_DIR, "output", "patient_time")
OUTPUT_ML    = os.path.join(BASE_DIR, "output", "ml_data")

ROOMS = ["ICU", "Emergency", "Pharmacy"]

st.set_page_config(
    page_title="Smart Hospital Monitoring",
    page_icon="hospital",
    layout="wide"
)


@st.cache_resource(show_spinner=False)
def get_spark():
    spark = (
        SparkSession.builder
        .appName("HospitalDashboard")
        .config("spark.driver.memory", "1g")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark


@st.cache_data(show_spinner=False)
def load_data():
    spark = get_spark()

    df_total = spark.read.parquet(OUTPUT_TOTAL).toPandas()
    df_time  = spark.read.parquet(OUTPUT_TIME).toPandas()
    df_ml    = spark.read.parquet(OUTPUT_ML).toPandas()

    df_time["window_start"] = pd.to_datetime(df_time["window_start"])

    return df_total, df_time, df_ml


def train_model(df_ml, room):
    subset = df_ml[df_ml["room"] == room].copy()
    if subset.empty or len(subset) < 2:
        return None, None

    X = subset[["hour"]].values
    y = subset["avg_patients"].values

    model = LinearRegression()
    model.fit(X, y)

    hours_pred = np.arange(0, 24).reshape(-1, 1)
    predictions = model.predict(hours_pred)
    predictions = np.clip(predictions, 5, 80)

    df_pred = pd.DataFrame({
        "hour":             hours_pred.flatten(),
        "predicted_patients": predictions
    })

    return model, df_pred


def main():
    st.title("Smart Hospital Monitoring System")
    st.caption("NIM: 230104040274 | Teknologi Big Data - TI23B | UAS Semester Genap 20252")
    st.divider()

    # ─── Load Data ────────────────────────────────────────────────────────────
    try:
        df_total, df_time, df_ml = load_data()
    except Exception as e:
        st.error(
            "Parquet files not found. "
            "Run main_uas_0274.py first to generate the data."
        )
        st.stop()

    # ─── Sidebar Filter ───────────────────────────────────────────────────────
    st.sidebar.title("Filter")
    selected_rooms = st.sidebar.multiselect(
        "Pilih Ruangan",
        options=ROOMS,
        default=ROOMS
    )

    if not selected_rooms:
        st.warning("Pilih minimal satu ruangan dari sidebar.")
        st.stop()

    # ─── KPI Section ──────────────────────────────────────────────────────────
    st.subheader("KPI Total Pasien")

    df_filtered_total = df_total[df_total["room"].isin(selected_rooms)]
    grand_total       = int(df_filtered_total["total_patients"].sum())

    kpi_cols = st.columns(len(selected_rooms) + 1)

    kpi_cols[0].metric(
        label="Total Semua Ruangan",
        value=f"{grand_total:,}"
    )

    for i, room in enumerate(selected_rooms):
        row = df_filtered_total[df_filtered_total["room"] == room]
        val = int(row["total_patients"].values[0]) if not row.empty else 0
        kpi_cols[i + 1].metric(label=room, value=f"{val:,}")

    st.divider()

    # ─── Trend Chart ──────────────────────────────────────────────────────────
    st.subheader("Tren Pasien per 15 Menit")

    df_filtered_time = df_time[df_time["room"].isin(selected_rooms)].copy()
    df_filtered_time = df_filtered_time.sort_values("window_start")

    fig_trend = px.line(
        df_filtered_time,
        x="window_start",
        y="avg_patients",
        color="room",
        markers=True,
        labels={
            "window_start": "Waktu",
            "avg_patients": "Rata-rata Pasien",
            "room":         "Ruangan"
        },
        title="Rata-rata Jumlah Pasien per Interval 15 Menit"
    )
    fig_trend.update_layout(
        hovermode="x unified",
        legend_title_text="Ruangan"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    # ─── AI Prediction ────────────────────────────────────────────────────────
    st.subheader("Prediksi Jumlah Pasien Berdasarkan Jam (Linear Regression)")

    pred_col1, pred_col2 = st.columns([2, 1])

    with pred_col2:
        st.markdown("**Pilih Parameter Prediksi**")
        pred_room = st.selectbox(
            "Ruangan",
            options=[r for r in ROOMS if r in selected_rooms]
        )
        pred_hour = st.slider("Jam Prediksi", min_value=0, max_value=23, value=10)

    with pred_col1:
        model, df_pred = train_model(df_ml, pred_room)

        if model is not None:
            point_pred = float(model.predict([[pred_hour]])[0])
            point_pred = max(5, min(80, point_pred))

            # Actual data for selected room
            df_actual = df_ml[df_ml["room"] == pred_room].copy()

            fig_pred = go.Figure()

            fig_pred.add_trace(go.Scatter(
                x=df_actual["hour"],
                y=df_actual["avg_patients"],
                mode="markers",
                name="Data Aktual",
                marker=dict(size=8, color="#1f77b4")
            ))

            fig_pred.add_trace(go.Scatter(
                x=df_pred["hour"],
                y=df_pred["predicted_patients"],
                mode="lines",
                name="Garis Regresi",
                line=dict(color="#ff7f0e", width=2)
            ))

            fig_pred.add_trace(go.Scatter(
                x=[pred_hour],
                y=[point_pred],
                mode="markers",
                name=f"Prediksi Jam {pred_hour:02d}:00",
                marker=dict(size=14, color="red", symbol="star")
            ))

            fig_pred.update_layout(
                title=f"Prediksi Pasien Ruangan {pred_room}",
                xaxis_title="Jam",
                yaxis_title="Jumlah Pasien",
                hovermode="x unified"
            )

            st.plotly_chart(fig_pred, use_container_width=True)

    if model is not None:
        st.info(
            f"Ruangan **{pred_room}** pada jam **{pred_hour:02d}:00** "
            f"diprediksi memiliki **{point_pred:.1f} pasien** "
            f"(R2 Score: {model.score(df_ml[df_ml['room']==pred_room][['hour']], df_ml[df_ml['room']==pred_room]['avg_patients']):.4f})"
        )

    st.divider()

    # ─── Peak Hour Analysis ───────────────────────────────────────────────────
    st.subheader("Analisis Jam Pasien Tertinggi")

    peak_data = []
    for room in selected_rooms:
        subset = df_ml[df_ml["room"] == room]
        if subset.empty:
            continue
        peak_row = subset.loc[subset["avg_patients"].idxmax()]
        peak_data.append({
            "Ruangan":           room,
            "Jam Puncak":        f"{int(peak_row['hour']):02d}:00",
            "Rata-rata Pasien":  round(peak_row["avg_patients"], 2),
        })

    if peak_data:
        df_peak = pd.DataFrame(peak_data)

        fig_peak = px.bar(
            df_peak,
            x="Ruangan",
            y="Rata-rata Pasien",
            color="Ruangan",
            text="Jam Puncak",
            title="Jam Puncak per Ruangan"
        )
        fig_peak.update_traces(textposition="outside")
        st.plotly_chart(fig_peak, use_container_width=True)

        st.dataframe(df_peak, use_container_width=True, hide_index=True)

    st.caption("Smart Hospital Monitoring System | Big Data Pipeline: Sensor Data - Spark ETL - Parquet - AI - Dashboard")


if __name__ == "__main__":
    main()
