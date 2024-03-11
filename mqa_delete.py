
import traceback
import json
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from typing import Optional
from bson.json_util import dumps
from bson.objectid import ObjectId
from minio_manager import *
from pymongo_get_database import get_database

deleteRouter = APIRouter()

  # api to delete a catalogue or dataset by id
@deleteRouter.delete("/element/{id}")
def delete_analisys(id: str):

  # check if id is valid
  if(len(id) != 24):
    return HTTPException(status_code=400, detail="Id not valid")
  try:
    dbname = get_database()
    collection_name = dbname["mqa"]
    # retrieve the element by id
    result = collection_name.find_one({'_id': ObjectId(id)})
    if result == None:
      return HTTPException(status_code=404, detail="Id not found")
    else:            
        response = collection_name.delete_one({'_id': ObjectId(id)})
        minio_deleteFolder(id)
        if response.deleted_count == 1:
          return {"message": "Deleted successfully"}
        else:
          return {"message": "There was a problem deleting the item"}
  except Exception as e:
    print(traceback.format_exc())
    raise HTTPException(status_code=500, detail="Internal Server Error" + str(e))
  
  
class DeleteParameters(BaseModel):
    index: Optional[str] = None
    date: str

  # api to delete a specifyc analisys from history of a catalogue or dataset by id, and by date and if more than one in the same date, by index
@deleteRouter.delete("/analisys/{id}")
def delete_analisys_spec(id: str, options: DeleteParameters ):
  index = options.index
  date = options.date

  # check if id is valid
  if(len(id) != 24):
    return HTTPException(status_code=400, detail="Id not valid")
  try:
    dbname = get_database()
    collection_name = dbname["mqa"]
    # retrieve the element by id
    result = collection_name.find_one({'_id': ObjectId(id)})
    if result == None:
      return HTTPException(status_code=404, detail="Id not found")
    else:            
        res = json.loads(dumps(result, indent = 4)).get("history")
        if(len(res) == 0):
          return "Empty History"
        # if index is not provided, it deletes all the analisys of that date
        if index == None:
          for i in range(len(res)):
            if res[i]["created_at"][:res[i]["created_at"].rfind(' ')] == date:
              del res[i]
              minio_deleteFile(id, i)
        else:
          # if index is provided, it deletes the analisys of that date and index
          for i in range(len(res)):
            if res[i]["created_at"][:res[i]["created_at"].rfind(' ')] == date and i == int(index):
              del res[i]
              minio_deleteFile(id, i)
        response = collection_name.update_one({'_id': ObjectId(id)},  {'$set': {"history": res}})
        if response.modified_count == 1:
          return {"message": "Deleted successfully"}
        else:
          return {"message": "There was a problem deleting the item"}
  except Exception as e:
    print(traceback.format_exc())
    raise HTTPException(status_code=500, detail="Internal Server Error" + str(e))
  