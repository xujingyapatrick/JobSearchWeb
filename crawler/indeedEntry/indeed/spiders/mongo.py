from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.indeed
collection = db.indeed_collection
