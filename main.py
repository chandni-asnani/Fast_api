from fastapi import FastAPI, Path
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import re
from db.connections import conn
from models.domain import Domain
from db.queries import FetchData
from bson import ObjectId
import logging
from urllib.parse import urlparse
from datetime import datetime
from fuzzywuzzy import process



# =================== Using Google search and BeautifulSoup library ============= 

app = FastAPI()

async def google_scrape(url):
    start = datetime.now()
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    end = datetime.now()
    print(end - start)
    return soup.title.text

async def output(url_domain, response, url):
    # start = datetime.now()
    query = [i for i in conn.local.domain.find({"domain": url_domain})]
    # end = datetime.now()
    # print(end - start)
    if not query:
        try:
            a = await google_scrape(url)
            response[a] = url
        except Exception as e:
            logging.error(str(e))
    return response

@app.get("/blacklisted_domain_list")
def get_domain_list():
    try:
        return FetchData.fetchblacklisteddomains()
    except Exception as e:
        logging.error(str(e))



@app.post("/add_blacklisted_domain")
def create_domain(data:Domain):
    message = "Domain Already Exists"
    try:
        if not [i for i in conn.local.domain.find({"domain": data.domain})]:
            conn.local.domain.insert_one(dict(data))
            message = "Created Successfully"
    except Exception as e:
        logging.error(str(e))
    return message

@app.delete("/delete_blacklisted_domain")
async def delete_domain(data:Domain):
    message = "Domain Does not Exists"
    try:
        if  [i for i in conn.local.domain.find({"domain": data.domain})]:
            conn.local.domain.find_one_and_delete(dict(data))
            message = "Deleted Successfully"
    except Exception as e:
        logging.error(str(e))
    return message



@app.get("/search/{query}")
async def google_query(query,keyword=None):
    response = {}
    search_results = search(query, stop=10)
    start = datetime.now()


    for url in search_results:
        url_domain = urlparse(f'{url}').netloc
        response = await output(url_domain, response, url)
    end = datetime.now()
    data = {}
    if keyword:
        for title,url in response.items():
            matching = process.extractOne(keyword, [urlparse(f'{url}').netloc])
            data[(matching[-1], url)] = title
        # data = dict(map(lambda x:((process.extractOne(keyword, [urlparse(f'{x[0]}').netloc])[-1], x[0]),x[-1]), response.items()))
        sorted_keys = sorted([*data], reverse=True)
        print(data)
        response = {data[x]: x[1] for x in sorted_keys}
    print(end - start)
    return response


