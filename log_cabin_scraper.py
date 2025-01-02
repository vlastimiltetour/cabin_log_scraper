# -*- coding: utf-8 -*-

import email
import base64
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
from datetime import datetime
import requests

def return_cabin_overview():
  training_data = False

  if training_data:
    base_url = '/content/main.mhtml'
  else:

    base_url = 'https://www.sreality.cz/hledani/prodej/domy/chalupy/trutnov'


  # basic variables
  count = 0
  cabin_data = []
  price_history_data = []
  url_list = [base_url]


  # get the number of ads
  if training_data:
    soup = parse_cabin_file(base_url)
  else:
    page = requests.get(base_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    #'https://www.sreality.cz/hledani/prodej/domy/chalupy/trutnov?strana=2']
    number_of_ads_raw = soup.find("p", class_="MuiTypography-root MuiTypography-body1 css-43c7n8").text
    number_match = re.search(r'(\d+)', number_of_ads_raw)
    number_of_ads = int(number_match.group(0)) if number_match else None
    number_of_pages = round(number_of_ads / 21)

  for i in range(number_of_pages+1):
    paginated_url = f"{base_url}?strana={i}"
    url_list.append(paginated_url)

  for url in url_list:

    if training_data:
      pass

    else:
      page = requests.get(url)
      soup = BeautifulSoup(page.content, 'html.parser')

    cabin_root = soup.find_all("div", class_="MuiBox-root css-n6y9a7")

    for cabin in cabin_root:

      try:
        id_raw_url = cabin.find_previous("a", class_="MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineAlways css-vpeef3").get("href")

        match = re.search(r'(\d+)$', id_raw_url)
        id = int(match.group(0)) if match else None
        url = id_raw_url if id_raw_url else None

        title_tag = cabin.find("p", class_="MuiTypography-root MuiTypography-body1 css-mjbyyl")
        title = title_tag.text if title_tag else 'title not found'

        location = cabin.find("p", class_="MuiTypography-root MuiTypography-body1 css-mjbyyl").find_next_sibling("p").text

        raw_price = cabin.find("p", class_="MuiTypography-root MuiTypography-body1 css-2bjqts").text


        if (raw_price == 'Cenanavyžádání') or (raw_price == 'Cena na vyžádání'):
          raw_price = 0
          price = 0

        else:
          price_regex_remove_czk = raw_price.replace('Kč', '')
          price_regex_remove_irrelevant = re.sub(r'\(.*$', '', price_regex_remove_czk)
          price_regex_remove_blanks = re.sub(r'\s+', '', price_regex_remove_irrelevant)

          if type(price_regex_remove_blanks) == str:
            price = 0
          else:
            price = int(price_regex_remove_blanks)

        square_meters_regex = re.findall(r'\d+', title)
        num1 = int(square_meters_regex[0])
        num2 = int(square_meters_regex[1])

        square_meters = num1 + num2

        price_per_m2 = price / square_meters

        timestamp = datetime.today()

        cabin_data.append({
            'ID':id,
            'Title': title,
            'm2': square_meters,
            'Location': location,
            'url': url,
        })

        price_history_data.append({
            'cabin_ID': id,
            'Price': price,
            'Timestamp': timestamp,
            'Price_m2': price_per_m2,
        })


      except Exception as e:
        print('this is an error', e)



  cabin_data_df = pd.DataFrame(cabin_data)
  price_history_data_df = pd.DataFrame(price_history_data)

  return cabin_data_df, price_history_data_df


# This is a chunk of code only to test connection - rarely to be used
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

def test_connection():
  uri = "mongodb+srv://vtetour:913YeRIC00Che49O@cluster0.2bbgf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

  # Create a new client and connect to the server
  client = MongoClient(uri, server_api=ServerApi('1'))

  # Send a ping to confirm a successful connection
  try:
      client.admin.command('ping')
      return "Pinged your deployment. You successfully connected to MongoDB!"
  except Exception as e:
      return print(e)

from pymongo import MongoClient
import pandas as pd

# Replace with your MongoDB connection string
MONGO_URI = "mongodb+srv://vtetour:913YeRIC00Che49O@cluster0.2bbgf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Connect to MongoDB
client = MongoClient(MONGO_URI)

db = client['log_cabin_scraper']  # Replace 'your_database' with your database name
cabins_collection = db['cabins']  # Collection for cabins_df
price_history_collection = db['price_history']  # Collection for price_history_df

# Get DataFrames
cabins_df, price_history_df = return_cabin_overview()

# Convert DataFrames to a list of dictionaries
cabins_data = cabins_df.to_dict('records')
price_history_data = price_history_df.to_dict('records')

# Insert cabins data
if cabins_data:
    result_cabins = cabins_collection.insert_many(cabins_data)
    print(f"Inserted {len(result_cabins.inserted_ids)} documents into 'cabins' collection.")

# Insert price history data
if price_history_data:
    result_price_history = price_history_collection.insert_many(price_history_data)
    print(f"Inserted {len(result_price_history.inserted_ids)} documents into 'price_history' collection.")


from pymongo import MongoClient
import pandas as pd

def read_mongo_db(id=None):

  # Replace with your MongoDB connection string
  MONGO_URI = "mongodb+srv://vtetour:913YeRIC00Che49O@cluster0.2bbgf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

  # Connect to MongoDB
  client = MongoClient(MONGO_URI)

  db = client['log_cabin_scraper']  # Replace 'your_database' with your database name
  cabins_collection = db['cabins']  # Collection for cabins_df
  price_history_collection = db['price_history']  # Collection for price_history_df

  mongo_cabin_data = list(cabins_collection.find())

  mongo_cabin_df = pd.DataFrame(mongo_cabin_data)

  mongo_price_history_data = list(price_history_collection.find())

  mongo_price_history_df = pd.DataFrame(mongo_price_history_data)
  mongo_price_history_df.head()
  mongo_price_history_df.rename(columns={"cabin_ID": "ID"}, inplace=True)

  merged_df = mongo_cabin_df.merge(mongo_price_history_df, on='ID', how='inner')


  if id == None:
    return merged_df

  return merged_df[merged_df['ID'] == id].sort_values('Timestamp')
  #return mongo_cabin_df

def calculate_price_diff(group):
  if len(group) < 2:
    return 0

  return group.iloc[0]['Price'] - group.iloc[1]['Price']


def show_data_highlights():
  df = read_mongo_db(None)

  price_diff_df = (
        df.groupby("ID")
        .apply(calculate_price_diff)
        .reset_index(name="Price_Difference")
    )

  
  return price_diff_df

def dashboard():
  df = read_mongo_db(None)
  df_sorted = df.sort_values(by=['ID', 'Timestamp'], ascending=[True, False])
  df_filtered_recent_data = df_sorted.drop_duplicates(subset=['ID'], keep='first')
  df_filtered_recent_data = df_filtered_recent_data.reset_index(drop=True)

  mean = round(df_filtered_recent_data['Price'].mean())
  stdev = round(df_filtered_recent_data['Price'].std())

  print('Average is:', mean)
  print('STDEV is', stdev)

  no_of_cabins = df_filtered_recent_data["ID"].nunique()
  #top locations
  top_5_expensive = df_filtered_recent_data.nlargest(5, 'Price')[['Title','Location', 'm2', 'Price', 'Price_m2', 'url']]
  #df.sort_values(by=['col1'])
  top_5_cheap = df_filtered_recent_data[df_filtered_recent_data['Price'] > 0]
  top_5_cheapest = top_5_cheap.nsmallest(5, 'Price')[['Title','Location', 'm2', 'Price', 'Price_m2','url']]

  top_5_m2 = df_filtered_recent_data.nlargest(5, 'Price_m2')[['Title','Location', 'm2', 'Price', 'Price_m2', 'url']]
  bottom_5_m2 = df_filtered_recent_data[df_filtered_recent_data['Price_m2'] > 0]
  bottom_5_m2 = bottom_5_m2.nsmallest(5, 'Price_m2')[['Title','Location', 'm2', 'Price', 'Price_m2','url']]
  # top 5 diffs
  return no_of_cabins, mean, stdev, top_5_expensive, top_5_cheapest, top_5_m2, bottom_5_m2

no_of_cabins, mean, stdev, top_5_expensive, top_5_cheapest, top_5_m2, bottom_5_m2 = dashboard()

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Email configuration
subject = "Scraping Pozemků"
sender = "v.tetour@gmail.com"
recipients = ["vlkscraper@outlook.com", "v.tetour@gmail.com", 'zuzanak36@gmail.com']
password = "hyhe qdhx ntsu cvqs"

def send_email(subject, sender, recipients, password):
    # Create email message container
    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    # Get dashboard data
    no_of_cabins, mean, stdev, top_5_expensive, top_5_cheapest, top_5_m2, bottom_5_m2 = dashboard()

    # Convert DataFrames to HTML
    html_content = f"""
    <html>
        <body>
            <h2>Dashboard Highlights</h2>
            <p>Number of Unique Cabins: <strong>{no_of_cabins}</strong></p>
            <p>Average price {mean}</p>
            <h3>Top 5 Most Expensive Cabins</h3>
            {top_5_expensive.to_html(index=False, escape=False)}
            <h3>Top 5 Cheapest Cabins</h3>
            {top_5_cheapest.to_html(index=False, escape=False)}
            <h3>Top 5 Most Expensive per m2</h3>
            {top_5_m2.to_html(index=False, escape=False)}
            <h3>Top 5 Cheapest per m2</h3>
            {bottom_5_m2.to_html(index=False, escape=False)}
            <h3>Zuza chce hlídat tyhle dva:</h3>
            TBD
        </body>
    </html>
    """

    # Attach HTML content
    html_part = MIMEText(html_content, "html")
    msg.attach(html_part)

    # Send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")

send_email(subject, sender, recipients, password)
