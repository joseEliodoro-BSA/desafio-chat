from pymongo import AsyncMongoClient


client = AsyncMongoClient("mongodb", port=27017)
db = client.chat


user_collection = db.get_collection("users")
chats_collection = db.get_collection("chats")
