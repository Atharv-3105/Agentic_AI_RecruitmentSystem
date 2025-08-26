import pymongo
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("MONGODB_CONNECTION")

try:
    client = pymongo.MongoClient(URL, serverSelectionTimeoutMS=5000)
    client.admin.command('ismaster')
    print("MongoDB connection successfull")

    db_list = client.list_database_names()
    print(f"Databases found:{db_list}")

except ConnectionFailure as e:
    print(f"Coudl not connect to the MongoDB: {e}")