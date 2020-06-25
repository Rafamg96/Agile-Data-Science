sudo /usr/share/elasticsearch/bin/elasticsearch start &

sudo docker-compose up &

/home/rafael/Agile_Data_Code_2-master/kafka/bin/zookeeper-server-start.sh /home/rafael/Agile_Data_Code_2-master/kafka/config/zookeeper.properties &

/home/rafael/Agile_Data_Code_2-master/kafka/bin/kafka-server-start.sh /home/rafael/Agile_Data_Code_2-master/kafka/config/server.properties &

spark-submit --packages org.apache.spark:spark-streaming-kafka_2.11:1.6.3 /home/rafael/TFM/app/make_predictions_streaming.py &


