from ..db.mongoConnect import get_collection
from bson import ObjectId

async def process_image(data: dict): 
    print("Processed image!")
    return None 