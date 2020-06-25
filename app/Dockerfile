FROM python:3.6

ENV FLASK_APP run.py

COPY app.py make_predictions_streaming.py predict_utils.py requirements.txt search_helpers.py config.py .env ./
COPY static static

#install and source ansible
#RUN apt-get update && apt-get install -y proj-bin libgeos-dev libproj-dev

#RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt 

RUN pip install -r requirements.txt

EXPOSE 5000
EXPOSE 9200
EXPOSE 80
#Exponer todos los puertos
#EXPOSE 0-8000
#CMD elasticsearch start
#CMD sudo /usr/share/elasticsearch/bin/elasticsearch start
#CMD wget -qO - https://www.mongodb.org/static/pgp/server-4.2.asc | apt-key add -
#CMD echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.2 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-4.2.list
#CMD apt-get update
#CMD apt-get install -y mongodb-org
#CMD mongod
CMD python app.py
