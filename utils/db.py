import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["portfolio"]  # change as needed

def get_collection(name):
    return db[name]
