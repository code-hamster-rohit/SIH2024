from pymongo import MongoClient
import gridfs

uri = "mongodb+srv://rohitkumarpatna1008:Sih2024@sih2024.gnkym.mongodb.net/?retryWrites=true&w=majority&appName=SIH2024"
client = MongoClient(uri)

db = client.SIH2024
fs = gridfs.GridFS(db)