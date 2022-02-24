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





app = FastAPI()

async def google_scrape(query):
    response = {}
    start = datetime.now()
    url = f"https://www.google.com/search?q={query}"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    headings = soup.find_all(['h3'])
    for i in headings:
        if i.find_parent('a'):
            title = i.find('div').text
            url = i.find_parent('a').get("href").replace("/url?q=", '').split("&sa")[0]
            response[url] = title

    end = datetime.now()
    print(end - start)
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
    start = datetime.now()
    response = await google_scrape(query)
    print(response)
    for url in list(response.keys()):
        print(url)
        url_domain = urlparse(f'{url}').netloc
        query = [i for i in conn.local.domain.find({"domain": url_domain})]
        if query:
            response.pop(url)
    end = datetime.now()
    data = {}
    if keyword:
        for title,url in response.items():
            matching = process.extractOne(keyword, [urlparse(f'{url}').netloc])
            data[(matching[-1], url)] = title
        sorted_keys = sorted([*data], reverse=True)
        print(data)
        response = {data[x]: x[1] for x in sorted_keys}
    print(end - start)
    return response


