import random
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, avg, window, hour
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from sklearn.linear_model import LinearRegression
import numpy as np
import os

# ─── Configuration ────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_TOTAL = os.path.join(BASE_DIR, "output", "patient_total")
OUTPUT_TIME  = os.path.join(BASE_DIR, "output", "patient_time")
OUTPUT_ML    = os.path.join(BASE_DIR, "output", "ml_data")

ROOMS        = ["ICU", "Emergency", "Pharmacy"]
DURATION_MIN = 120
INTERVAL_MIN = 1


def create_spark_session():
    spark = (
        SparkSession.builder
        .appName("SmartHospitalMonitoring")
        .config("spark.driver.memory", "1g")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def generate_data(spark):
    schema = StructType([
        StructField("timestamp",     TimestampType(), False),
        StructField("room",          StringType(),    False),
        StructField("patient_count", IntegerType(),   False),
    ])

    start_time = datetime(2026, 6, 11, 8, 0, 0)
    records = []

    for minute in range(DURATION_MIN):
        ts = start_time + timedelta(minutes=minute * INTERVAL_MIN)
        for room in ROOMS:
            patient_count = random.randint(5, 80)
            records.append((ts, room, patient_count))

    df = spark.createDataFrame(records, schema=schema)
    return df


def process_data(spark, df):
    df.createOrReplaceTempView("hospital_data")

    # 1. Total patients per room
    df_total = df.groupBy("room").agg(
        spark_sum("patient_count").alias("total_patients")
    )

    # 2. Patient trend per 15 minutes
    df_time = (
        df.groupBy(
            window(col("timestamp"), "15 minutes").alias("time_window"),
            col("room")
        )
        .agg(avg("patient_count").alias("avg_patients"))
        .select(
            col("time_window.start").alias("window_start"),
            col("time_window.end").alias("window_end"),
            col("room"),
            col("avg_patients")
        )
        .orderBy("window_start", "room")
    )

    # 3. ML dataset based on hour
    df_ml = (
        df.withColumn("hour", hour(col("timestamp")))
        .groupBy("hour", "room")
        .agg(avg("patient_count").alias("avg_patients"))
        .orderBy("hour", "room")
    )

    return df_total, df_time, df_ml


def save_parquet(df_total, df_time, df_ml):
    df_total.write.mode("overwrite").parquet(OUTPUT_TOTAL)
    df_time.write.mode("overwrite").parquet(OUTPUT_TIME)
    df_ml.write.mode("overwrite").parquet(OUTPUT_ML)

    print("Parquet files saved successfully.")
    print(f"  patient_total : {OUTPUT_TOTAL}")
    print(f"  patient_time  : {OUTPUT_TIME}")
    print(f"  ml_data       : {OUTPUT_ML}")


def train_model(spark):
    df_ml = spark.read.parquet(OUTPUT_ML).toPandas()

    results = {}
    for room in ROOMS:
        subset = df_ml[df_ml["room"] == room]
        if subset.empty:
            continue

        X = subset[["hour"]].values
        y = subset["avg_patients"].values

        model = LinearRegression()
        model.fit(X, y)

        score = model.score(X, y)
        results[room] = {
            "model":       model,
            "r2_score":    round(score, 4),
            "coefficient": round(float(model.coef_[0]), 4),
            "intercept":   round(float(model.intercept_), 4),
        }

    print("\nLinear Regression Training Results:")
    for room, info in results.items():
        print(f"  {room} - R2: {info['r2_score']}, "
              f"coef: {info['coefficient']}, intercept: {info['intercept']}")

    return results


def analyze_peak_hours(spark):
    df_ml = spark.read.parquet(OUTPUT_ML).toPandas()

    print("\nPeak Hour Analysis per Room:")
    for room in ROOMS:
        subset = df_ml[df_ml["room"] == room]
        if subset.empty:
            continue
        peak_row  = subset.loc[subset["avg_patients"].idxmax()]
        peak_hour = int(peak_row["hour"])
        peak_val  = round(peak_row["avg_patients"], 2)
        print(f"  {room} - Peak at {peak_hour:02d}:00 with avg {peak_val} patients")


def main():
    print("Smart Hospital Monitoring System - UAS TBG TI23B")
    print(f"NIM: 230104040274")
    print("-" * 50)

    spark = create_spark_session()

    print("Generating sensor data...")
    df = generate_data(spark)
    print(f"Total records generated: {df.count()}")

    print("\nRunning Spark transformations...")
    df_total, df_time, df_ml = process_data(spark, df)

    print("\nTotal patients per room:")
    df_total.show()

    print("Patient trend per 15 minutes (sample):")
    df_time.show(10, truncate=False)

    print("ML dataset by hour (sample):")
    df_ml.show(10)

    print("\nSaving to Parquet...")
    save_parquet(df_total, df_time, df_ml)

    print("\nTraining AI model...")
    train_model(spark)

    analyze_peak_hours(spark)

    spark.stop()
    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()
