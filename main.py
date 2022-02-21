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


app = FastAPI()

def google_scrape(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    return soup.title.text

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
    query = (f"https://www.google.com/search?q={query}%20{keyword}")
    for url in search(query, stop=10):
        if not [i for i in conn.local.domain.find({"domain": url})]:
            try:
                a = google_scrape(url)
                response[a] = url
            except Exception as e:
                pass
    return response

