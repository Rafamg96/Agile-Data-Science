from flask import Flask, render_template, request
from pymongo import MongoClient
from bson import json_util
import config
import json
import pandas as pd
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, CDSView, GroupFilter, HoverTool, Legend
from bokeh.palettes import Category20_20 as palette
import itertools  
from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter, Select
from bokeh.models.callbacks import CustomJS
from bokeh.layouts import column
#Con la vieja versión
from pyelasticsearch import ElasticSearch
#COn la nueva versión
#from elasticsearch import Elasticsearch
import sys, os, re
import search_helpers
import predict_utils

# Set up Flask and Mongo
app = Flask(__name__)

#Para el modo docker-compose
#client = MongoClient("mongodb://mongodb:27017")
#Para el modo sin docker-compose
client = MongoClient()

RECORDS_PER_PAGE=15
#Para el modo docker-compose
#ELASTIC_URL='http://elasticsearch:9200/'
#Para el modo sin docker-compose
ELASTIC_URL='http://localhost:9200/agile_data_science'

#Con la vieja versión
elastic = ElasticSearch(config.ELASTIC_URL)
#Con la nueva versión
#elastic = Elasticsearch(ELASTIC_URL)
from kafka import KafkaProducer, TopicPartition
#MOdo sin docker compose
producer = KafkaProducer(bootstrap_servers=['localhost:9092'],api_version=(0,10))
#Modo docker compose
#producer = KafkaProducer(bootstrap_servers=['kafka:9092'],api_version=(0,10))
PREDICTION_TOPIC = 'flight_delay_classification_request'

import uuid

def create_area_graph(df,x,y,title='Titulo',x_axis_type="linear",x_axis_label='Eje X', y_axis_label='Eje Y', line_width=2, plot_height=1000, plot_width=1000):

    source=ColumnDataSource(df)
    
    plot = figure(title= title , 
        x_axis_label= x_axis_label, 
        y_axis_label= y_axis_label, 
        plot_width =plot_width,
        plot_height =plot_height,
        x_axis_type=x_axis_type)
    
    
        
    plot.line(x=x, y=y, line_width = line_width, source=source)
    #plot.varea(x=x, y1=y,y2=0, source=source, muted_alpha=0.2)
    
    
    
    return plot


def get_navigation_offsets(offset1, offset2, increment):
  offsets = {}
  offsets['Next'] = {'top_offset': offset2 + increment, 'bottom_offset': 
  offset1 + increment}
  offsets['Previous'] = {'top_offset': max(offset2 - increment, 0), 
 'bottom_offset': max(offset1 - increment, 0)} # Don't go < 0
  return offsets

# Strip the existing start and end parameters from the query string
def strip_place(url):
  try:
    p = re.match('(.+)[?]start=.+&end=.+', url).group(1)
  except AttributeError as e:
    return url
  return p

def process_search(results):
  records = []
  total = 0
  if results['hits'] and results['hits']['hits']:
    total = results['hits']['total']
    hits = results['hits']['hits']
    for hit in hits:
      record = hit['_source']
      records.append(record)
  return records, total



@app.route("/flights/delays/predict/classify_realtime/response/<unique_id>")
def classify_flight_delays_realtime_response(unique_id):
  """Serves predictions to polling requestors"""

  prediction = \
    client.agile_data_science.flight_delay_classification_response.find_one(
      {
        "UUID": unique_id
      }
    )

  response = {"status": "WAIT", "id": unique_id}
  if prediction:
    response["status"] = "OK"
    response["prediction"] = prediction

  return json_util.dumps(response)



@app.route("/flights/delays/predict_kafka")
def flight_delays_page_kafka():
  """Serves flight delay prediction page with polling form"""

  form_config = [
    {'field': 'DepDelay', 'label': 'Departure Delay'},
    {'field': 'Carrier'},
    {'field': 'FlightDate', 'label': 'Date'},
    {'field': 'Origin'},
    {'field': 'Dest', 'label': 'Destination'},
  ]

  return render_template(
   'flight_delays_predict_kafka.html', form_config=form_config
  )

@app.route("/flights/delays/predict/classify_realtime", methods=['POST'])
def classify_flight_delays_realtime():

  # Define the form fields to process
  """POST API for classifying flight delays"""
  api_field_type_map = \
    {
      "DepDelay": float,
      "Carrier": str,
      "FlightDate": str,
      "Dest": str,
      "FlightNum": str,
      "Origin": str
    }

  # Fetch the values for each field from the form object
  api_form_values = {}
  for api_field_name, api_field_type in api_field_type_map.items():
    api_form_values[api_field_name] = request.form.get(
      api_field_name, type=api_field_type
    )

  # Set the direct values, which excludes Date
  prediction_features = {}
  for key, value in api_form_values.items():
    prediction_features[key] = value

  # Set the derived values
  prediction_features['Distance'] = predict_utils.get_flight_distance(
    client, api_form_values['Origin'],
    api_form_values['Dest']
  )

  # Turn the date into DayOfYear, DayOfMonth, DayOfWeek
  date_features_dict = predict_utils.get_regression_date_args(
    api_form_values['FlightDate']
  )
  for api_field_name, api_field_value in date_features_dict.items():
    prediction_features[api_field_name] = api_field_value

  # Add a timestamp
  prediction_features['Timestamp'] = predict_utils.get_current_timestamp()

  # Create a unique ID for this message
  unique_id = str(uuid.uuid4())
  prediction_features['UUID'] = unique_id

  message_bytes = json.dumps(prediction_features).encode()
  producer.send(PREDICTION_TOPIC, message_bytes)

  response = {"status": "OK", "id": unique_id}
  return json_util.dumps(response)


@app.route("/airplane/flights/<tail_number>")
def flights_per_airplane_v2(tail_number):
  flights = client.agile_data_science.flights_per_airplane.find_one({'TailNum': tail_number})
  descriptions = client.agile_data_science.flights_per_airplane_v2.find_one({'TailNum': tail_number})
  print(descriptions['Description'])
  if descriptions is None:
    descriptions = []
  images = client.agile_data_science.airplane_images.find_one({'TailNum': tail_number})
  if images is None:
    images = []
  return render_template('flights_per_airplane.html', flights=flights, images=images, descriptions=descriptions['Description'], tail_number=tail_number)


@app.route("/")
def home():
  return render_template('home.html')

@app.route("/Busy_Airports")
def busy_airports():
  collection=client.agile_data_science.busy_airports
  df = pd.DataFrame(list(collection.find()))
  script,div=components(create_area_graph(title='Top 20 Busy Airports',df=df,x='Dest',y='count',x_axis_type="linear",plot_height=500,plot_width=1000,x_axis_label='Destination', y_axis_label='Flights'))
  return render_template('Busy_Airports.html',script=script, div=div)

@app.route("/dashboard")
def dashboard():
  return render_template('dashboard.html')


# Controller: Fetch an airplane entity page
@app.route("/airlines")
@app.route("/airlines/")
def airlines():
  airlines = client.agile_data_science.airplanes_per_carrier.find()
  return render_template('all_airlines.html', airlines=airlines)




# Controller: Fetch an airplane entity page
@app.route("/airlines/<carrier_code>")
def airline2(carrier_code):
  airline_summary = client.agile_data_science.airlines.find_one(
    {'CarrierCode': carrier_code}
  )
  airline_airplanes = client.agile_data_science.airplanes_per_carrier.find_one(
    {'Carrier': carrier_code}
  )
  return render_template(
    'airlines.html',
    airline_summary=airline_summary,
    airline_airplanes=airline_airplanes,
    carrier_code=carrier_code
  )

#Airplanes
@app.route("/airplanes")
@app.route("/airplanes/")
def search_airplanes():

  search_config = [
    {'field': 'TailNum', 'label': 'Tail Number'},
    {'field': 'Owner', 'sort_order': 0},
    {'field': 'OwnerState', 'label': 'Owner State'},
    {'field': 'Manufacturer', 'sort_order': 1},
    {'field': 'Model', 'sort_order': 2},
    {'field': 'ManufacturerYear', 'label': 'MFR Year'},
    {'field': 'SerialNumber', 'label': 'Serial Number'},
    {'field': 'EngineManufacturer', 'label': 'Engine MFR', 'sort_order': 3},
    {'field': 'EngineModel', 'label': 'Engine Model', 'sort_order': 4}
  ]



  # Pagination parameters
  start = request.args.get('start') or 0
  start = int(start)
  end = request.args.get('end') or config.AIRPLANE_RECORDS_PER_PAGE
  end = int(end)

  # Navigation path and offset setup
  #Como no me coge bien el final de la url lo he metido como remplazo
  if(request.url=="http://localhost:5000/airplanes/"):
    request.url="http://localhost:5000/airplanes/?"
  nav_path = search_helpers.strip_place3(request.url)
  nav_offsets = search_helpers.get_navigation_offsets(
    start, 
    end, 
    config.AIRPLANE_RECORDS_PER_PAGE
  )

  # Build the base of our elasticsearch query
  query = {
    'query': {
      'bool': {
        'must': []}
    },
    'from': start,
    'size': config.AIRPLANE_RECORDS_PER_PAGE
  }

  arg_dict = {}
  for item in search_config:
    field = item['field']
    value = request.args.get(field)
    arg_dict[field] = value
    if value:
      query['query']['bool']['must'].append({'match': {field: value}})

  # Query elasticsearch, process to get records and count
  #Nueva versión
  #results = elastic.search(body=query, index='agile_data_science_airplanes')
  #Vieja versión
  results = elastic.search(query, index='agile_data_science_airplanes')
  airplanes, airplane_count = search_helpers.process_search(results)

  # Persist search parameters in the form template
  return render_template(
    'all_airplanes.html',
    search_config=search_config,
    args=arg_dict,
    airplanes=airplanes,
    airplane_count=airplane_count,
    nav_path=nav_path,
    nav_offsets=nav_offsets,
  )

# Controller: Fetch an email and display it
@app.route("/on_time_performance")
def on_time_performance():
  
  carrier = request.args.get('Carrier')
  flight_date = request.args.get('FlightDate')
  flight_num = request.args.get('FlightNum')
  
  flight = client.agile_data_science.on_time_performance.find_one({
    'Carrier': carrier,
    'FlightDate': flight_date,
    'FlightNum': flight_num
  })
  
  return render_template('flight.html', flight=flight)

# Controller: Fetch all flights between cities on a given day and display them
@app.route("/flights/<origin>/<dest>/<flight_date>")
def list_flights(origin, dest, flight_date):

  start = request.args.get('start') or 0
  start = int(start)
  end = request.args.get('end') or config.RECORDS_PER_PAGE
  end = int(end)
  width = end - start

  nav_offsets = get_navigation_offsets(start, end, config.RECORDS_PER_PAGE)

  flights = client.agile_data_science.on_time_performance.find(
    {
      'Origin': origin,
      'Dest': dest,
      'FlightDate': flight_date
    },
    sort = [
      ('DepTime', 1),
      ('ArrTime', 1)
    ]
  )
  flight_count = flights.count()
  flights = flights.skip(start).limit(width)

  return render_template(
    'flights.html', 
    flights=flights, 
    flight_date=flight_date, 
    flight_count=flight_count,
    nav_path=request.path,
    nav_offsets=nav_offsets
  )

@app.route("/total_flights")
def total_flights():
  total_flights = client.agile_data_science.flights_by_month.find({}, 
    sort = [
      ('Year', 1),
      ('Month', 1)
    ])
  return render_template('total_flights.html', total_flights=total_flights)

# Serve the chart's data via an asynchronous request (formerly known as 'AJAX')
@app.route("/total_flights.json")
def total_flights_json():
  total_flights = client.agile_data_science.flights_by_month.find({}, 
    sort = [
      ('Year', 1),
      ('Month', 1)
    ])
  return json_util.dumps(total_flights, ensure_ascii=False)

# Controller: Fetch a flight chart 2.0
@app.route("/total_flights_chart")
def total_flights_chart():
  total_flights = client.agile_data_science.flights_by_month.find({}, 
    sort = [
      ('Year', 1),
      ('Month', 1)
    ])
  return render_template('total_flights_chart.html', total_flights=total_flights)

@app.route("/airplanes/chart/manufacturers.json")
@app.route("/airplanes/chart/manufacturers.json")
def airplane_manufacturers_chart():
  mfr_chart = client.agile_data_science.airplane_manufacturer_totals.find_one()
  return json.dumps(mfr_chart)

@app.route("/flights/search")
@app.route("/flights/search/")
def search_flights():

  # Search parameters
  carrier = request.args.get('Carrier')
  flight_date = request.args.get('FlightDate')
  origin = request.args.get('Origin')
  dest = request.args.get('Dest')
  tail_number = request.args.get('TailNum')
  flight_number = request.args.get('FlightNum')

  # Pagination parameters
  start = request.args.get('start') or 0
  start = int(start)
  end = request.args.get('end') or config.RECORDS_PER_PAGE
  end = int(end)

  print(request.args)
  # Navigation path and offset setup
  nav_path = strip_place(request.url)
  #nav_path=request.path
  nav_offsets = get_navigation_offsets(start, end, config.RECORDS_PER_PAGE)

  # Build the base of our elasticsearch query
  query = {
    'query': {
      'bool': {
        'must': []}
    },
    'sort': [
      {'FlightDate': {'order': 'asc'} },
      '_score'
    ],
    'from': start,
    'size': config.RECORDS_PER_PAGE
  }

  # Add any search parameters present
  if carrier:
    query['query']['bool']['must'].append({'match': {'Carrier': carrier}})
  if flight_date:
    query['query']['bool']['must'].append({'match': {'FlightDate': flight_date}})
  if origin: 
    query['query']['bool']['must'].append({'match': {'Origin': origin}})
  if dest: 
    query['query']['bool']['must'].append({'match': {'Dest': dest}})
  if tail_number: 
    query['query']['bool']['must'].append({'match': {'TailNum': tail_number}})
  if flight_number: 
    query['query']['bool']['must'].append({'match': {'FlightNum': flight_number}})

  # Query elasticsearch, process to get records and count
  #Nueva versión
  #results = elastic.search(body=query,index='agile_data_science_airplanes')
  #Vieja versión
  results= elastic.search(query)
  flights, flight_count = process_search(results)

  # Persist search parameters in the form template
  return render_template(
    'search.html', 
    flights=flights, 
    flight_date=flight_date, 
    flight_count=flight_count,
    nav_path=nav_path,
    nav_offsets=nav_offsets,
    carrier=carrier,
    origin=origin,
    dest=dest,
    tail_number=tail_number,
    flight_number=flight_number
    )


if __name__ == "__main__":
  app.run(
    debug=True,
    host='0.0.0.0'
  )
