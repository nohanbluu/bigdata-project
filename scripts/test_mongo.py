from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# GANTI URI DI BAWAH DENGAN CONNECTION STRING MONGODB ATLAS KAMU
uri = "mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/?appName=Cluster0"

client = MongoClient(uri, server_api=ServerApi('1'))
try:
    client.admin.command('ping')
    print("BERHASIL terhubung ke MongoDB Atlas!")
except Exception as e:
    print(f"GAGAL: {e}")
