
import traceback
import json
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel
from typing import Optional
from bson.json_util import dumps
from datetime import datetime
from bson.objectid import ObjectId
from pymongo_get_database import get_database

getRouter = APIRouter()

  # api to get the last results of a catalogue or dataset analisys by id
@getRouter.get("/analisys/{id}")
def get_results(id: str):
  if(len(id) != 24):
    return HTTPException(status_code=400, detail="Id not valid")
  try:
    dbname = get_database()
    collection_name = dbname["mqa"]
    result = collection_name.find_one({'_id': ObjectId(id)})
    if result == None:
      return HTTPException(status_code=404, detail="Not Found")
    else:
      res = json.loads(dumps(result, indent = 4)).get("history")
      if(len(res) == 0):
        return "Empty History"
      return res[len(res)-1]
  except Exception as e:
    print(traceback.format_exc())
    raise HTTPException(status_code=500, detail="Internal Server Error" + str(e))
  

class Parameters(BaseModel):
    parameters: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

# api to get the selected history results of a catalogue or dataset analisys by id and filter the results by parameters
# if user want to get a specific result, must provide at least start_date
@getRouter.post("/analisys/{id}")
def get_results_spec(id: str, options: Parameters ):
  parameters = options.parameters
  start_date = options.start_date
  end_date = options.end_date

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
      res = json.loads(dumps(result, indent = 4))
      type = res.get("type")
      res = res.get("history")
      if(len(res) == 0):
        return "Empty History"
      if parameters == "":
        return res[len(res)-1]
      else:
        # remove spaces from parameters and split them by comma
        parameters = parameters.replace(" ", "")
        attributes = parameters.split(",")
        class Object(object):
          pass
        response = {}
        response[type] = []
        # if start_date and end_date are provided, convert them to datetime format
        # check if only start_date is provided, or both or none. if only end_date is provided, return error
        if start_date != None and end_date != None:
          datetime_start = datetime.strptime(start_date, '%d/%m/%Y')
          datetime_end = datetime.strptime(end_date, '%d/%m/%Y')
        elif start_date != None and end_date == None:
          datetime_start = datetime.strptime(start_date, '%d/%m/%Y')
        elif start_date == None and end_date != None:
          return HTTPException(status_code=404, detail="Invalid date range")
        counter = 0
        # iterate over the history results and filter them by date and parameters
        for i in range(len(res)):
          date_to_compare = datetime.strptime(res[i]["created_at"][:res[i]["created_at"].rfind(' ')], '%d/%m/%Y')
          # case with date range
          if start_date != None and end_date != None:
            # filter by date
            # when the date is in the range, it adds the result to the response, but first check if in parameters there is at least one "datasets" and/or "distribution" and add the empty list to the response for later use
            if date_to_compare >= datetime_start and date_to_compare <= datetime_end:
              counter += 1
              response[type].append({})
              response[type][counter-1]['created_at'] = res[i]["created_at"]
              if "datasets" in parameters and "distribution" not in parameters:
                response[type][counter-1]["datasets"] = []
                for dataset in res[i][type]["datasets"]:
                  response[type][counter-1]["datasets"].append({})
              if "distribution" in parameters:
                response[type][counter-1]["datasets"] = []
                for dataset in res[i][type]["datasets"]:
                  response[type][counter-1]["datasets"].append({"distributions": []})
                  for distribution in dataset["distributions"]:
                    response[type][counter-1]["datasets"][len(response[type][counter-1]["datasets"])-1]["distributions"].append({})
              # filter by parameters
              # If at distribution level, the parameter are for example: datasets.distributions.title, so it split the string and check the length
              for attr in attributes:
                finder = attr.split(".")
                if len(finder) == 1:
                  response[type][counter-1][finder[0]] = res[i][type][finder[0]]
                elif len(finder) == 2:
                  datasets = res[i].get(type).get("datasets")
                  for index, dataset in enumerate(datasets):
                    response[type][counter-1]["datasets"][index][finder[1]] = dataset[finder[1]]
                elif len(finder) == 3:
                  datasets = res[i].get(type).get("datasets")
                  for i, dataset in enumerate(datasets):
                    distributions = dataset.get("distributions")
                    for index, distribution in enumerate(distributions):
                      response[type][counter-1]["datasets"][i]["distributions"][index][finder[2]] = distribution[finder[2]]
          # case with only start_date
          elif start_date != None and end_date == None :
            # filter by date
            # when the date is in the range, it adds the result to the response, but first check if in parameters there is at least one "datasets" and/or "distribution" and add the empty list to the response for later use
            if date_to_compare >= datetime_start:
              counter += 1
              response[type].append({})
              response[type][counter-1]['created_at'] = res[i]["created_at"]
              if "datasets" in parameters and "distribution" not in parameters:
                response[type][counter-1]["datasets"] = []
                for dataset in res[i][type]["datasets"]:
                  response[type][counter-1]["datasets"].append({})
              if "distribution" in parameters:
                response[type][counter-1]["datasets"] = []
                for dataset in res[i][type]["datasets"]:
                  response[type][counter-1]["datasets"].append({"distributions": []})
                  for distribution in dataset["distributions"]:
                    response[type][counter-1]["datasets"][len(response[type][counter-1]["datasets"])-1]["distributions"].append({})
              # filter by parameters
              # If at distribution level, the parameter are for example: datasets.distributions.title, so it split the string and check the length
              for attr in attributes:
                finder = attr.split(".")
                if len(finder) == 1:
                  response[type][counter-1][finder[0]] = res[i][type][finder[0]]
                elif len(finder) == 2:
                  datasets = res[i].get(type).get("datasets")
                  for index, dataset in enumerate(datasets):
                    response[type][counter-1]["datasets"][index][finder[1]] = dataset[finder[1]]
                elif len(finder) == 3:
                  datasets = res[i].get(type).get("datasets")
                  for i, dataset in enumerate(datasets):
                    distributions = dataset.get("distributions")
                    for index, distribution in enumerate(distributions):
                      response[type][counter-1]["datasets"][i]["distributions"][index][finder[2]] = distribution[finder[2]]
          # case with no date range
          else:
            # check if in parameters there is at least one "datasets" and/or "distribution" and add the empty list to the response for later use
            counter += 1
            response[type].append({})
            response[type][counter-1]['created_at'] = res[i]["created_at"]
            if "datasets" in parameters and "distribution" not in parameters:
              response[type][counter-1]["datasets"] = []
              for dataset in res[i][type]["datasets"]:
                response[type][counter-1]["datasets"].append({})
            if "distribution" in parameters:
              response[type][counter-1]["datasets"] = []
              for dataset in res[i][type]["datasets"]:
                response[type][counter-1]["datasets"].append({"distributions": []})
                for distribution in dataset["distributions"]:
                  response[type][counter-1]["datasets"][len(response[type][counter-1]["datasets"])-1]["distributions"].append({})
            # filter by parameters
            # If at distribution level, the parameter are for example: datasets.distributions.title, so it split the string and check the length
            for attr in attributes:
              finder = attr.split(".")
              if len(finder) == 1:
                response[type][counter-1][finder[0]] = res[i][type][finder[0]]
              elif len(finder) == 2:
                datasets = res[i].get(type).get("datasets")
                for index, dataset in enumerate(datasets):
                  response[type][counter-1]["datasets"][index][finder[1]] = dataset[finder[1]]
              elif len(finder) == 3:
                datasets = res[i].get(type).get("datasets")
                for i, dataset in enumerate(datasets):
                  distributions = dataset.get("distributions")
                  for index, distribution in enumerate(distributions):
                    response[type][counter-1]["datasets"][i]["distributions"][index][finder[2]] = distribution[finder[2]]
                
                
        return response
  except Exception as e:
    print(traceback.format_exc())
    raise HTTPException(status_code=500, detail="Internal Server Error" + str(e))
  

  
#api to get all id's of catalogues and datasets
@getRouter.get("/all")
def get_all():
  try:
    dbname = get_database()
    collection_name = dbname["mqa"]
    result = collection_name.find({})
    if result == None:
      return HTTPException(status_code=404, detail="Not Found")
    else:
      res = json.loads(dumps(result, indent = 4))
      response = []
      for el in res:
        if el["type"] == "catalogue":
          response.append({"id": str(el["_id"]["$oid"]), "type": el["type"], "title": el["title"], "creation_date": el["creation_date"]})
        else:
           response.append({"id": str(el["_id"]["$oid"]), "type": el["type"], "title": el["title"], "creation_date": el["creation_date"]})
      return response
  except Exception as e:
    print(traceback.format_exc())
    raise HTTPException(status_code=500, detail="Internal Server Error" + str(e))
