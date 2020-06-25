# Agile_Data_Code_2

### Manual Install

Intall the following requirements:

flask==1.1.1
Jinja2==2.10.3  
bokeh==1.4.0
pandas==0.24.2
pymongo==3.9.0
urllib3==1.25.6
pyelasticsearch==1.4.1
elasticsearch==7.7.1
beautifulsoup4==4.7.1
ipython==6.4.0
kafka-python==1.4.7
requests==2.22.0
scipy==1.1.0
selenium==3.14.1
wikipedia==1.4.0
findspark==1.3.0
iso8601==0.1.12

### Manual Execution
Execute Elasticsearch
sudo /usr/share/elasticsearch/bin/elasticsearch start
Execute MongoDB
mongod --dbpath /home/rafael/TFM/mongodb/data/db/ &
Execute Kafka
kafka/bin/zookeeper-server-start.sh kafka/config/zookeeper.properties
kafka/bin/kafka-server-start.sh kafka/config/server.properties
Execute sparkstreaming
spark-submit --packages org.apache.spark:spark-streaming-kafka_2.11:1.6.3 /home/rafael/TFM/app/make_predictions_streaming.py 
Execute webapp
python app/app.py
