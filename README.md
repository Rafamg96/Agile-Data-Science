# Agile_Data_Code_2

### Manual Install

For a manual install read Appendix A for further setup instructions. 

Note: You must READ THE MANUAL INSTALL SCRIPT BEFORE RUNNING IT. It does things to your `~/.bashrc` that you should know about. 

Note: You must have Java installed on your computer for these instructions to work. You can find more information about how to install Java here: [https://www.java.com/en/download/help/download_options.xml](https://www.java.com/en/download/help/download_options.xml)

## Downloading Data

Once the server comes up, download the data and you are ready to go. First change directory into the `Agile_Data_Code_2` directory.


Now download the data:
```
./download.sh
```

For the [Introduction to PySpark](http://datasyndrome.com/training) course, run:

```
./intro_download.sh
```

For the [Realtime Predictive Analytics](http://datasyndrome.com/video) video course, or to skip ahead to chapter 8 in the book, run: 

```
ch08/download_data.sh
```

## Running Examples

All scripts run from the base directory, except the web app which runs in ex. `ch08/web/`.

### Jupyter Notebooks

All notebooks assume you have run the jupyter notebook command from the project root directory `Agile_Data_Code_2`. If you are using a virtual machine image (Vagrant/Virtualbox or EC2), jupyter notebook is already running. See directions on port mapping to proceed.

# The Data Value Pyramid

Originally by Pete Warden, the data value pyramid is how the book is organized and structured. We climb it as we go forward each chapter.

![Data Value Pyramid](images/climbing_the_pyramid_chapter_intro.png)

# System Architecture

The following diagrams are pulled from the book, and express the basic concepts in the system architecture. The front and back end architectures work together to make a complete predictive system.

## Front End Architecture

This diagram shows how the front end architecture works in our flight delay prediction application. The user fills out a form with some basic information in a form on a web page, which is submitted to the server. The server fills out some neccesary fields derived from those in the form like "day of year" and emits a Kafka message containing a prediction request. Spark Streaming is listening on a Kafka queue for these requests, and makes the prediction, storing the result in MongoDB. Meanwhile, the client has received a UUID in the form's response, and has been polling another endpoint every second. Once the data is available in Mongo, the client's next request picks it up. Finally, the client displays the result of the prediction to the user! 

This setup is extremely fun to setup, operate and watch. Check out chapters 7 and 8 for more information!

![Front End Architecture](images/front_end_realtime_architecture.png)

## Back End Architecture

The back end architecture diagram shows how we train a classifier model using historical data (all flights from 2015) on disk (HDFS or Amazon S3, etc.) to predict flight delays in batch in Spark. We save the model to disk when it is ready. Next, we launch Zookeeper and a Kafka queue. We use Spark Streaming to load the classifier model, and then listen for prediction requests in a Kafka queue. When a prediction request arrives, Spark Streaming makes the prediction, storing the result in MongoDB where the web application can pick it up.

This architecture is extremely powerful, and it is a huge benefit that we get to use the same code in batch and in realtime with PySpark Streaming.

![Backend Architecture](images/back_end_realtime_architecture.png)

# Screenshots

Below are some examples of parts of the application we build in this book and in this repo. Check out the book for more!

## Airline Entity Page

Each airline gets its own entity page, complete with a summary of its fleet and a description pulled from Wikipedia.

![Airline Page](images/airline_page_enriched_wikipedia.png)

## Airplane Fleet Page

We demonstrate summarizing an entity with an airplane fleet page which describes the entire fleet.

![Airplane Fleet Page](images/airplanes_page_chart_v1_v2.png)

## Flight Delay Prediction UI

We create an entire realtime predictive system with a web front-end to submit prediction requests.

![Predicting Flight Delays UI](images/predicting_flight_kafka_waiting.png)
# Agile-Data-Science
