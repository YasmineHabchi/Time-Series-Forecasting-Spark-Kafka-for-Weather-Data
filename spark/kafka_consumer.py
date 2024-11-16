from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

spark = SparkSession.builder \
    .appName("KafkaStructuredStreaming") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

kafka_bootstrap_servers = 'localhost:9092'
kafka_topic = 'weather_kafka_topic'

json_schema = StructType([
    StructField("datetime", TimestampType(), True),
    StructField("name", StringType(), True),
    StructField("country", StringType(), True),
    StructField("latitude", DoubleType(), True),
    StructField("longitude", DoubleType(), True),
    StructField("timezone", StringType(), True),
    StructField("max_temp_c", DoubleType(), True),
    StructField("min_temp_c", DoubleType(), True),
    StructField("avg_temp_c", DoubleType(), True),
    StructField("max_wind_mph", DoubleType(), True),
    StructField("avg_visibility_km", DoubleType(), True),
    StructField("avg_humidity", DoubleType(), True),
    StructField("uv_index", DoubleType(), True),
])

# Read data from Kafka topic as a streaming DataFrame
raw_data_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", kafka_topic) \
    .load()

# Convert the value column from Kafka into a string
raw_data_stream = raw_data_stream.selectExpr("CAST(value AS STRING)")

# Parse the JSON data and apply the schema
structured_data_stream = raw_data_stream.select(
    from_json(col("value"), json_schema).alias("data")
).select("data.*")

# Define the Delta Lake storage path
delta_path = "../delta_lake/delta_lake_table"  # Replace with your actual Delta Lake storage path

# Write the streaming DataFrame to Delta Lake
query = structured_data_stream.writeStream \
    .outputMode("append") \
    .format("delta") \
    .option("checkpointLocation", "../delta_lake/checkpoint") \
    .start(delta_path)

# Await termination of the query
query.awaitTermination()
