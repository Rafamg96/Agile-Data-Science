import sys, os, re
import time

sys.path.append("lib")
import utils

import requests
from bs4 import BeautifulSoup

from random import randint
import warnings                                           
import pandas as pd
import jsonlines
warnings.filterwarnings('ignore')

# Base string to plug in our tail number with a str.format() call
BASE_URL = 'http://registry.faa.gov/aircraftinquiry/NNum_Results.aspx?NNumbertxt={}'

# Fetch the page with selenium/PhantonJS
from selenium import webdriver
#phantomjs_driver = r"C:\Users\RMunoz\Downloads\openssl-1.1.1f.tar\phantomjs-2.1.1-windows\bin\phantomjs.exe"
driver = webdriver.PhantomJS()


# Load tail numbers 
#tail_number_records = pd.read_csv(r"C:\Users\RMunoz\Desktop\Rafael Muñoz González\TFM\TFMPRUEBA\TFM-SolidQ\Origenes de datos\Datos intermedios\new_airplanes.csv",sep=';')
#tail_number_records=tail_number_records['TailNum']
#tail_number_records=tail_number_records.unique()
tail_number_records = utils.read_json_lines_file('../data/tail_numbers.jsonl')
# This is our collection of Aircraft records we will save at the end
aircraft_records = []

# Loop through the tail numbers, fetching
contador=0
for tail_number_record in tail_number_records:
    # The table structure is constant for all pages that contain data
    try:
        print(contador++)
        time.sleep(0.01) # essential to sleep FIRST in loop or you will flood sites
        tail_number = tail_number_record['TailNum']
        url = BASE_URL.format(tail_number)
        print(url)
        # Fetch the page, parse the html
        driver.get(url)

        html = driver.page_source
        soup = BeautifulSoup(html, "lxml")


        aircraft_description = soup.find_all('table')[3]
        craft_tds = aircraft_description.find_all('td')
        serial_number = craft_tds[1].text.strip()
        manufacturer = craft_tds[5].text.strip()
        model = craft_tds[9].text.strip()
        mfr_year = craft_tds[25].text.strip()

        registered_owner = soup.find_all('table')[4]
        reg_tds = registered_owner.find_all('td')
        owner = reg_tds[1].text.strip()
        owner_state = reg_tds[9].text.strip()

        airworthiness = soup.find_all('table')[5]
        worthy_tds = airworthiness.find_all('td')
        engine_manufacturer = worthy_tds[1].text.strip()
        engine_model = worthy_tds[5].text.strip()

        aircraft_record = {
            'TailNum': tail_number,
            'SerialNumber': serial_number,
            'Manufacturer': manufacturer,
            'Model': model,
            'Mfr_Year': mfr_year,
            'Owner': owner,
            'Owner_State': owner_state,
            'Engine_Manufacturer': engine_manufacturer,
            'Engine_Model': engine_model,
          }
        aircraft_records.append(
          aircraft_record
        )
        print(aircraft_record)
        sys.stdout.write(".")
    except:
        sys.stdout.write("#")



utils.write_json_lines_file(aircraft_records, '../data/faa_tail_number_inquiryRAFA.jsonl')
