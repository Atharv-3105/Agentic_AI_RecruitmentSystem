import pymongo
from pymongo.collection import Collection
from bson.objectid import ObjectId
from typing import Optional

from core.config import MONGODB_CONNECTION, DB_NAME

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            
            try:
                cls._instance.client = pymongo.MongoClient(MONGODB_CONNECTION)
                cls._instance.db = cls._instance.client[DB_NAME]
                
                #Collections
                cls._instance.resumes = cls._instance.db["resumes"]
                cls._instance.jds = cls._instance.db["jds"]
                cls._instance.screenings = cls._instance.db["screenings"]
                print("-"*10,"MongoDB connection successful", "-"*10)
            except pymongo.errors.ConnectionFailure as e:
                print("-"*10, "MongoDB connection failed", "-"*10)
                cls._instance = None
            
            return cls._instance
    
    def get_collection(self, name: str) -> Optional[Collection]:
        return getattr(self, name, None)

#Create Instance of our Database
db_instance = Database()

#This function will store document into the DB and return a Unique_ID for it
def add_document(collection_name: str, data: dict)-> str:
    collection = db_instance.get_collection(collection_name)
    data_to_insert = data.copy()
    result = collection.insert_one(data_to_insert)
    return str(result.inserted_id)

#This function will fetch a stored document from the DB using the Unique_ID
def get_document(collection_name: str, doc_id: str)-> Optional[dict]:
    try:
        collection = db_instance.get_collection(collection_name)
        doc = collection.find_one({"_id": ObjectId(doc_id)})
        if doc:
            doc["_id"] = str(doc["_id"]) #Convert ObjectId to string for JSON 
        return doc

    except Exception:
        return None
    