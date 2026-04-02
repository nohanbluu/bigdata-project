from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://nohanbluu_db_user:iCoQlXNctEOSxCFP@cluster0.3e2jqxm.mongodb.net/?appName=Cluster0"

client = MongoClient(uri, server_api=ServerApi('1'))
try:
    client.admin.command('ping')
    print("BERHASIL terhubung ke MongoDB Atlas!")
except Exception as e:
    print(f"GAGAL: {e}")
