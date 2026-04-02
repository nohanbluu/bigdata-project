from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("SimpleJob").getOrCreate()

print("========================================")
print("  Spark berhasil dijalankan!")
print(f"  Spark Version: {spark.version}")
print("========================================")

data = [("A", 10), ("B", 20), ("A", 30)]
columns = ["category", "value"]
df = spark.createDataFrame(data, columns)

print("\nData Asli:")
df.show()

print("Hasil Agregasi (groupBy + sum):")
df.groupBy("category").sum("value").show()

spark.stop()
print("SPARK JOB SELESAI - SUKSES!")
