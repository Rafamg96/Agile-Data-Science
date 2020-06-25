import pymongo
import pymongo_spark
from pyspark.sql.functions import desc

APP_NAME = "Introducing PySpark"

# If there is no SparkSession, create the environment
try:
  sc and spark
except NameError as e:
  import findspark
  findspark.init()
  import pyspark
  import pyspark.sql

  sc = pyspark.SparkContext()

  spark = pyspark.sql.SparkSession(sc).builder.appName(APP_NAME).getOrCreate()

print("PySpark initialized...")

pymongo_spark.activate()



# Load the parquet file
on_time_dataframe = spark.read.parquet('../data/on_time_performance.parquet')
on_time_dataframe.registerTempTable("on_time_dataframe")


# Flights by month json

total_flights_by_month = spark.sql(
  """SELECT INT(Month), INT(Year), COUNT(*) AS total_flights
  FROM on_time_dataframe
  GROUP BY INT(Year), INT(Month)
  ORDER BY INT(Year), INT(Month)"""
)

flights_chart_data = total_flights_by_month.rdd.map(lambda row: row.asDict())
flights_chart_data.saveToMongoDB('mongodb://localhost:27017/agile_data_science.flights_by_month')

#Flights delays weekly
flight_delay_weekly = spark.sql("""SELECT INT(DayOfWeek), avg(CarrierDelay) as AvgCarrierDelay
    FROM on_time_dataframe 
    GROUP BY INT(DayOfWeek)
    ORDER BY INT(DayOfWeek)
""")

as_dict = flight_delay_weekly.rdd.map(lambda x: x.asDict())
as_dict.saveToMongoDB('mongodb://localhost:27017/agile_data_science.flights_delay_weekly')

#Airports busy top 20
airport_flights = on_time_dataframe.groupBy(["Origin", "Dest"]).count()
sorted_airport_flights = airport_flights.orderBy(desc("count"))
top_20_airport_flights = sorted_airport_flights.limit(20)

airports_rdd = top_20_airport_flights.rdd.map(lambda x: x.asDict())
airports_rdd.saveToMongoDB('mongodb://localhost:27017/agile_data_science.busy_airports')


# Flights
flights = on_time_dataframe.rdd.map(
    lambda x: 
  {
      'Carrier': x.Carrier, 
      'FlightDate': x.FlightDate, 
      'FlightNum': x.FlightNum, 
      'Origin': x.Origin, 
      'Dest': x.Dest, 
      'TailNum': x.TailNum
  }
)

flights_per_airplane = flights\
  .map(lambda record: (record['TailNum'], [record]))\
  .reduceByKey(lambda a, b: a + b)\
  .map(lambda tuple:
      {
        'TailNum': tuple[0], 
        'Flights': sorted(tuple[1], key=lambda x: (x['FlightNum'], x['FlightDate'], x['Origin'], x['Dest']))
      }
    )

from pyspark.sql import SQLContext, Row
#Obtenemos un df del rdd
my_df = flights_per_airplane.map(lambda l: Row(**dict(l))).toDF()
#Registramos la tabla del df
my_df.registerTempTable("flightsPerAirPlane")

a=spark.sql("""SELECT * from flightsPerAirPlane
    limit 4898
""")

flights_per_airplane_reduced = a.rdd.map(lambda x: x.asDict())
flights_per_airplane_reduced.saveToMongoDB('mongodb://localhost:27017/agile_data_science.flights_per_airplane')

#Aviones por aerolinea
carrier_airplane = spark.sql(
  "SELECT DISTINCT Carrier, TailNum FROM on_time_dataframe"
)

tuple_pair = carrier_airplane.rdd.map(
    lambda nameTuple: (nameTuple[0], [nameTuple[1]])
)

reduced_pairs = tuple_pair.reduceByKey(lambda a, b: a + b)

final_records = reduced_pairs.map(lambda tuple:
      {
        'Carrier': tuple[0], 
        'TailNumbers': sorted(
          filter(
            lambda x: x is not None and x != '', tuple[1] # empty string tail numbers were 
                                        # getting through
            )
          ),
        'FleetCount': len(tuple[1])
      }
    )

final_records.saveToMongoDB(
  'mongodb://localhost:27017/agile_data_science.airplanes_per_carrier'
)

#Images
images_records = spark.read.json('../data/airliners_images.jsonl')
images_records = images_records.rdd.map(lambda x: x.asDict())
images_records.saveToMongoDB('mongodb://localhost:27017/agile_data_science.airplane_images')

#Flight information
faa_tail_number_inquiry = spark.read.json('../data/faa_tail_number_inquiryRAFA.jsonl')
desc_rdd = faa_tail_number_inquiry.rdd.map(lambda x: {'TailNum': x.TailNum, 'Description': x.asDict()})
desc_rdd.saveToMongoDB('mongodb://localhost:27017/agile_data_science.flights_per_airplane_v2')

#Airlines
airlines = spark.read.json('../data/our_airlines_with_wiki.jsonl')
airlines=airlines.rdd.map(lambda x: {'CarrierCode':x.CarrierCode, 'Name':x.Name, 'domain':x.domain, 'logo_url':x.logo_url, 'summary':x.summary, 'url':x.url})
airlines.saveToMongoDB('mongodb://localhost:27017/agile_data_science.airlines')


#Manufacter totals

airplanes = spark.read.json('../data/resolved_airplanes.json')

airplanes.registerTempTable("airplanes")

#
# Same with sub-queries
#
relative_manufacturer_counts = spark.sql("""SELECT
  Manufacturer,
  COUNT(*) AS Total,
  ROUND(
    100 * (
      COUNT(*)/(SELECT COUNT(*) FROM airplanes)
    ),
    2
  ) AS PercentageTotal
FROM
  airplanes
GROUP BY
  Manufacturer
ORDER BY
  Total DESC, Manufacturer
LIMIT 10"""
)
relative_manufacturer_counts.show(30) # show top 30

#
# Now get these things on the web
#
relative_manufacturer_counts_dict = relative_manufacturer_counts.rdd.map(lambda row: row.asDict())
grouped_manufacturer_counts = relative_manufacturer_counts_dict.groupBy(lambda x: 1)


grouped_manufacturer_counts.saveToMongoDB(
  'mongodb://localhost:27017/agile_data_science.airplane_manufacturer_totals'
)



#Distancias (Importante para Kafka)
import sys, os, re

# Load the on-time Parquet file
on_time_dataframe = spark.read.parquet('../data/on_time_performance.parquet')
on_time_dataframe.registerTempTable("on_time_performance")

origin_dest_distances = spark.sql("""
  SELECT Origin, Dest, AVG(Distance) AS Distance
  FROM on_time_performance
  GROUP BY Origin, Dest
  ORDER BY Distance DESC
""")
origin_dest_distances = origin_dest_distances.distinct()

origin_dest_distances.repartition(1).write.mode("overwrite").json("../data/origin_dest_distances.json")
os.system("rm ../data/origin_dest_distances.jsonl")
os.system("cat ../data/origin_dest_distances.json/part* > ../data/origin_dest_distances.jsonl")
# Import our enriched airline data as the 'airlines' collection
%%bash
mongo agile_data_science --quiet --eval 'db.origin_dest_distances.drop()'
mongoimport -d agile_data_science -c origin_dest_distances --file ../data/origin_dest_distances.jsonl
mongo agile_data_science --quiet --eval 'db.origin_dest_distances.ensureIndex({Origin: 1, Dest: 1})'



