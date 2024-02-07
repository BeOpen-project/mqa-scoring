'''
YODA (Your Open DAta)
EU CEF Action 2019-ES-IA-0121
University of Cantabria
Developer: Johnny Choque (jchoque@tlmat.unican.es)

Fork:
BEOPEN 2023
Developer: Marco Sajeva (sajeva.marco01@gmail.com)
'''

import math
import csv
import re
import traceback
import requests
import json
from rdflib import Graph
from fastapi import BackgroundTasks, FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from pydantic import BaseModel
import logging 
from typing import Optional
from pymongo_get_database import *
from bson.json_util import dumps
from datetime import datetime
from bson.objectid import ObjectId


# load the vocabulary
URL_EDP = 'https://data.europa.eu/api/mqa/shacl/validation/report'
HEADERS = {'content-type': 'application/rdf+xml'}
MACH_READ_FILE = os.path.join('edp-vocabularies', 'edp-machine-readable-format.rdf')
NON_PROP_FILE = os.path.join('edp-vocabularies', 'edp-non-proprietary-format.rdf')
LICENSE_FILE = os.path.join('edp-vocabularies', 'edp-licences-skos.rdf')
ACCESSRIGHTS_FILE = os.path.join('edp-vocabularies', 'access-right-skos.rdf')
MEDIATYPE_FILE_APPLICATION = os.path.join('edp-vocabularies', 'edp-mediatype-application.csv')
MEDIATYPE_FILE_AUDIO = os.path.join('edp-vocabularies', 'edp-mediatype-audio.csv')
MEDIATYPE_FILE_FONT = os.path.join('edp-vocabularies', 'edp-mediatype-font.csv')
MEDIATYPE_FILE_IMAGE = os.path.join('edp-vocabularies', 'edp-mediatype-image.csv')
MEDIATYPE_FILE_MESSAGE = os.path.join('edp-vocabularies', 'edp-mediatype-message.csv')
MEDIATYPE_FILE_MODEL = os.path.join('edp-vocabularies', 'edp-mediatype-model.csv')
MEDIATYPE_FILE_MULTIPART = os.path.join('edp-vocabularies', 'edp-mediatype-multipart.csv')
MEDIATYPE_FILE_TEXT = os.path.join('edp-vocabularies', 'edp-mediatype-text.csv')
MEDIATYPE_FILE_VIDEO = os.path.join('edp-vocabularies', 'edp-mediatype-video.csv')
MEDIATYPE_FILE_VIDEO = os.path.join('edp-vocabularies', 'edp-mediatype-video.csv')

# converts the metric to a string containing just the name of the metric, ex: dct:title
def str_metric(val, g):
  valStr=str(val)
  for prefix, ns in g.namespaces():
    if val.find(ns) != -1:
      metStr = valStr.replace(ns,prefix+":")
      return metStr

# converts the vocabulary to a graph and get the list of available properties
    # "application/rdf+xml"
    # "text/csv"
def load_edp_vocabulary(file, format):
  g = Graph()
  g.parse(file, format=format)
  voc = []
  for sub, pred, obj in g:
    voc.append(str(sub))
  return voc

# send the request to the EDP validator and get the response
def edp_validator(file: str):
  check = False
  try:
    r_edp = requests.post(URL_EDP, data=bytes(file, 'utf-8'), headers=HEADERS)
    r_edp.raise_for_status()
  except requests.exceptions.HTTPError as err:
    print(traceback.format_exc())
    raise SystemExit(err)
  report = json.loads(r_edp.text)
  if valResult(report):
    check = True
  return check

# check if the response of edp validator contains the property "shacl:conforms" and return the value
def valResult(d):
  if 'shacl:conforms' in d:
    return d['shacl:conforms']
  for k in d:
    if isinstance(d[k], list):
      for i in d[k]:
        if 'shacl:conforms' in i:
          return i['shacl:conforms']

# create object and add attributes to avoid some properties are missing
def prepareResponse():
  class Object(object):
    pass
  response = Object()
  
  response.title = ''
  response.accessURL = 400
  response.downloadURL = False
  response.downloadURLResponseCode = 400
  response.format = False
  response.dctFormat_dcatMediaType = False
  response.formatMachineReadable = False
  response.formatNonProprietary = False
  response.license = False
  response.licenseVocabulary = False
  response.mediaType = False
  response.issued = False
  response.modified = False
  response.rights = False
  response.byteSize = False
  return response


def distribution_calc(str):
  mach_read_voc = []
  non_prop_voc = []
  license_voc = []
  
  # distribution object
  response = prepareResponse()

  g = Graph()
  g.parse(data = str)
  
  # load the vocabulary
  try:
    mach_read_voc = load_edp_vocabulary(MACH_READ_FILE,"application/rdf+xml")
    non_prop_voc = load_edp_vocabulary(NON_PROP_FILE,"application/rdf+xml")
    license_voc = load_edp_vocabulary(LICENSE_FILE,"application/rdf+xml")
  except:
    print(traceback.format_exc())
    mach_read_voc = '-1'
    non_prop_voc = '-1'
    license_voc = '-1'

  accessURL_List = []
  downloadURLResponseCode_List = []
  dctFormat_dcatMediaType_List = []

  # iterate over the properties of the distribution and check if they value are good
  # some metrics just check if the property is present
  # others need to check the url or the value of the property
  # others need to check if they are in the vocabulary
  # full list can be found https://data.europa.eu/mqa/methodology?locale=en with relative weights
  for sub, pred, obj in g:
    met = str_metric(pred, g)
    if met == "dct:title" and response.title == '':
      response.title = obj

    elif met == "dcat:accessURL":
      try:
        res = requests.get(obj)
        accessURL_List.append(res.status_code)
      except:
        print(traceback.format_exc())
        accessURL_List.append(400)

    elif met == "dcat:downloadURL":
      response.downloadURL = True
      try:
        res = requests.get(obj)
        downloadURLResponseCode_List.append(res.status_code)
      except:
        print(traceback.format_exc())
        downloadURLResponseCode_List.append(400)
    # in catalogue formats the property dct:MediaTypeOrExtent is inside an empty dct:format tag. The empty tag must be skipped and not counted
    elif (met == "dct:format" and obj != '' and obj != None) or met == "dct:MediaTypeOrExtent":
      response.format = True
      try:
        if (obj) in mach_read_voc:
          response.formatMachineReadable = True
        else:
          response.formatMachineReadable = False
        if (obj) in non_prop_voc:
          response.formatNonProprietary = True
        else:
          response.formatNonProprietary = False
      except:
        print(traceback.format_exc())
        response.formatMachineReadable = False
        response.formatNonProprietary = False
      try:
        g2 = Graph()
        g2.parse(obj, format="application/rdf+xml")
        if (obj, None, None) in g2: 
          dctFormat_dcatMediaType_List.append(True)
        else:
          dctFormat_dcatMediaType_List.append(False)
      except:
        print(traceback.format_exc())
        dctFormat_dcatMediaType_List.append(False)

    elif met == "dct:license":
      response.license = True
      try:
        if (obj) in license_voc:
          response.licenseVocabulary = True
        else:
          response.licenseVocabulary = False
      except:
        print(traceback.format_exc())
        response.licenseVocabulary = False

    elif met == "dcat:mediaType":
      response.mediaType = True
      try:
        # removes the prefix from the url to check if it is in the vocabulary
        mediatype = obj.replace('http://www.iana.org/assignments/media-types/','')
        mediatype = mediatype.replace('https://www.iana.org/assignments/media-types/','')
        found = False
        try:
          vocabularies = [MEDIATYPE_FILE_APPLICATION, MEDIATYPE_FILE_AUDIO, MEDIATYPE_FILE_FONT, MEDIATYPE_FILE_IMAGE, MEDIATYPE_FILE_MESSAGE, MEDIATYPE_FILE_MODEL, MEDIATYPE_FILE_MULTIPART, MEDIATYPE_FILE_TEXT, MEDIATYPE_FILE_VIDEO]
          for voc in vocabularies:
            with open(voc, 'rt') as f:
              reader = csv.reader(f, delimiter=',')
              for row in reader: 
                for field in row:
                  if field ==  mediatype:
                    found = True
                    break
              if found == True:
                break
          if found == True:
            dctFormat_dcatMediaType_List.append(True)
        except:
          print(traceback.format_exc())
          dctFormat_dcatMediaType_List.append(False)
      except:
        print(traceback.format_exc())
        dctFormat_dcatMediaType_List.append(False)

    elif met == "dct:issued":
      response.issued = True

    elif met == "dct:modified":
      response.modified = True

    elif met == "dct:rights":
      response.rights = True

    elif met == "dcat:byteSize":
      response.byteSize = True

  response.accessURL = most_frequent(accessURL_List)
  response.downloadURLResponseCode = most_frequent(downloadURLResponseCode_List)
  temp = True
  for el in dctFormat_dcatMediaType_List:
    if el == False:
      temp = False
      break
  response.dctFormat_dcatMediaType = temp
  return response

# get the most frequent value in a list
def most_frequent(List):
    counter = 0
    if(len(List) == 0):
      return 400
    num = List[0]
    for i in List:
        curr_frequency = List.count(i)
        if(curr_frequency> counter):
            counter = curr_frequency
            num = i
 
    return num

def dataset_calc(dataset_str, pre):

  class Object(object):
    pass
  response = Object()
  response.distributions = []

  accessRights_voc = []
  dt_copy = dataset_str
  # cut off all the tags on datasets level, and leave just the tags on distribution level to analyze them separately
  distribution_start = [m.start() for m in re.finditer('(?=<dcat:distribution>)', dataset_str)]
  distribution_finish = [m.start() for m in re.finditer('(?=</dcat:distribution>)', dataset_str)]
  if len(distribution_start) == len(distribution_finish):
    for index, item in enumerate(distribution_start):
      distr_tag = dataset_str[distribution_start[index]:distribution_finish[index]+20]
      # cut off the distribution tag from the dataset string to obtain just the dataset properties to analyze them separately
      dt_copy = dt_copy.replace(distr_tag, '')
      # variable pre is always required from rdf files and it contains at least the rdf tag: <rdf:RDF ...> and can also contain the xml tag: <?xml version="1.0"?> 
      distribution = pre + '<dcat:Dataset>' + distr_tag + '</dcat:Dataset>' +'</rdf:RDF>'
      response.distributions.append(distribution_calc(distribution))

    dt_copy = dt_copy.replace(dt_copy[dt_copy.rfind('<adms:identifier>'):dt_copy.rfind('</adms:identifier>')+18], '')
    g = Graph()
    g.parse(data = dt_copy)

# sets initial values to avoid some properties are missing
    response.title = ''
    response.issued = 0
    response.modified = False
    response.keyword = False
    response.issuedDataset = False
    response.modifiedDataset = False
    response.theme = False
    response.spatial = False
    response.temporal = False
    response.contactPoint = False
    response.publisher = False
    response.accessRights = False
    response.accessRightsVocabulary = False
    response.accessURL = []
    response.downloadURL = 0
    response.downloadURLResponseCode = []
    response.format = 0
    response.dctFormat_dcatMediaType = 0
    response.formatMachineReadable = 0
    response.formatNonProprietary = 0
    response.license = 0
    response.licenseVocabulary = 0
    response.mediaType = 0
    response.rights = 0
    response.byteSize = 0

    try:
      accessRights_voc = load_edp_vocabulary(ACCESSRIGHTS_FILE,"application/rdf+xml")
    except:
      print(traceback.format_exc())
      accessRights_voc = '-1'
      
    try:
      res = edp_validator(dataset_str)
      if res == True:
        response.shacl_validation = True
      else:
        response.shacl_validation = False
    except:
      print(traceback.format_exc())
      response.shacl_validation = 0


  # iterate over the properties of the datasets and check if they value are good
  # some metrics just check if the property is present
  # others need to check the url or the value of the property
  # others need to check if they are in the vocabulary
  # full list can be found https://data.europa.eu/mqa/methodology?locale=en with relative weights
    for sub, pred, obj in g:
      met = str_metric(pred, g)
      if met == "dct:title" and response.title == '':
        response.title = obj

      elif met == "dct:issued":
        response.issued += 1
        response.issuedDataset = True

      elif met == "dct:modified":
        response.modified = True
        response.modifiedDataset = True

      elif met == "dcat:keyword":
        response.keyword = True

      elif met == "dcat:theme":
        response.theme = True

      elif met == "dct:spatial":
        response.spatial = True

      elif met == "dct:temporal":
        response.temporal = True

      elif met == "dcat:contactPoint":
        response.contactPoint = True

      elif met == "dct:publisher":
        response.publisher = True

      elif met == "dct:accessRights":
        response.accessRights = True
        try:
          if str(obj) in accessRights_voc:
            response.accessRightsVocabulary = True
          else:
            response.accessRightsVocabulary = False
        except:
            print(traceback.format_exc())
            response.accessRightsVocabulary = False
  
    tempArrayDownloadUrl = []
    tempArrayAccessUrl = []
    # iterate over the distributions metrics to count positive values
    for distr in response.distributions:
      if distr.issued == True:
        response.issued += 1
      if distr.downloadURL == True:
        response.downloadURL += 1
      tempArrayDownloadUrl.append(distr.downloadURLResponseCode)
      tempArrayAccessUrl.append(distr.accessURL)
      if distr.license == True:
        response.license += 1
      if distr.licenseVocabulary == True:
        response.licenseVocabulary += 1
      if distr.byteSize == True:
        response.byteSize += 1
      if distr.rights == True:
        response.rights += 1
      if distr.format == True:
        response.format += 1
      if distr.formatMachineReadable == True:
        response.formatMachineReadable += 1
      if distr.formatNonProprietary == True:
        response.formatNonProprietary += 1
      if distr.mediaType == True:
        response.mediaType += 1
      if distr.dctFormat_dcatMediaType == True:
        response.dctFormat_dcatMediaType += 1
      
      # calculate the percentage of positive values for each metric
    response.issued = round(response.issued / (len(response.distributions)+ 1) * 100)
    response.downloadURL = round(response.downloadURL / len(response.distributions) * 100)
    list_unique = (list(set(tempArrayDownloadUrl)))
    # create a list for each response code and gives the percentage of each code
    for el in list_unique:
      response.downloadURLResponseCode.append({"code": el, "percentage": round(tempArrayDownloadUrl.count(el) / len(response.distributions) * 100)})
    list_unique = (list(set(tempArrayAccessUrl)))
    # create a list for each response code and gives the percentage of each code
    for el in list_unique:
      response.accessURL.append({"code": el, "percentage": round(tempArrayAccessUrl.count(el) / len(response.distributions) * 100)})
    response.license = round(response.license / len(response.distributions) * 100)
    response.licenseVocabulary = round(response.licenseVocabulary / len(response.distributions) * 100)
    response.byteSize = round(response.byteSize / len(response.distributions) * 100)
    response.rights = round(response.rights / len(response.distributions) * 100)
    response.format = round(response.format / len(response.distributions) * 100)
    response.formatMachineReadable = round(response.formatMachineReadable / len(response.distributions) * 100)
    response.formatNonProprietary = round(response.formatNonProprietary / len(response.distributions) * 100)
    response.mediaType = round(response.mediaType / len(response.distributions) * 100)
    response.dctFormat_dcatMediaType = round(response.dctFormat_dcatMediaType / (len(response.distributions)*2) * 100)

# modified needs to be checked on both dataset and distribution level, but only needs to be true once, so if it is true on dataset level, it is not necessary to check on distribution level
    if(response.modified == False):
      for distr in response.distributions:
        if distr.modified == True:
          response.modified = True
          break
    
  else:
    return -1
  return response

# find the nth occurrence of a substring in a string
def find_nth(haystack: str, needle: str, n: int) -> int:
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

def main(xml, pre, dataset_start, dataset_finish, url, collection_name, id):

# if the file is a catalogue, it needs to be analyzed on catalogue level, otherwise it needs to be analyzed just on dataset level
  if xml.rfind('<dcat:Catalog ') != -1:

    class Object(object):
      pass
    response = Object()
    response.datasets = []
    response.title = ''

    dt_copy = xml
    # cut off all the tags on catalogue level, and leave just the tags on dataset level to analyze them separately
    for index, item in enumerate(dataset_start):
      # variable pre is always required from rdf files and it contains at least the rdf tag: <rdf:RDF ...> and can also contain the xml tag: <?xml version="1.0"?> 
      dataset = pre + xml[dataset_start[index]:dataset_finish[index]+15] + '</rdf:RDF>'
      result = dataset_calc(dataset, pre)
      response.datasets.append(result)
      dataset_Tag = xml[dataset_start[index]:dataset_finish[index]+15]
      # create a copy with just the catalogue tags to analyze them separately
      dt_copy = dt_copy.replace(dataset_Tag, '')
      
    g = Graph()
    g.parse(data = dt_copy)

# gets the title of the catalogue
    for sub, pred, obj in g:
      met = str_metric(pred, g)
      if met == "dct:title":
        response.title = obj
        break
    
    # initial values to avoid some properties are missing
    response.issued = 0
    response.modified = 0
    response.keyword = 0
    response.theme = 0
    response.spatial = 0
    response.temporal = 0
    response.contactPoint = 0
    response.publisher = 0
    response.accessRights = 0
    response.accessRightsVocabulary = 0
    response.accessURL = []
    response.accessURL_Perc = 0
    response.downloadURL = 0
    response.downloadURLResponseCode = []
    response.downloadURLResponseCode_Perc = 0
    response.format = 0
    response.dctFormat_dcatMediaType = 0
    response.formatMachineReadable = 0
    response.formatNonProprietary = 0
    response.license = 0
    response.licenseVocabulary = 0
    response.mediaType = 0
    response.rights = 0
    response.byteSize = 0
    response.shacl_validation = 0
    response.score = {}

    countDataset = 0
    countDistr = 0
    tempArrayDownloadUrl = []
    tempArrayAccessUrl = []
    # iterate over the datasets metrics to count positive values
    for dataset in response.datasets:
      countDataset += 1
      if dataset.issuedDataset == True:
        response.issued += 1
      del dataset.issuedDataset
      if dataset.modifiedDataset == True:
        response.modified += 1
      del dataset.modifiedDataset
      if dataset.accessRights == True:
        response.accessRights += 1
      if dataset.accessRightsVocabulary == True:
        response.accessRightsVocabulary += 1
      if dataset.contactPoint == True:
        response.contactPoint += 1
      if dataset.publisher == True:
        response.publisher += 1
      if dataset.keyword == True:
        response.keyword += 1
      if dataset.theme == True:
        response.theme += 1
      if dataset.spatial == True:
        response.spatial += 1
      if dataset.temporal == True:
        response.temporal += 1
      if dataset.shacl_validation == True:
        response.shacl_validation += 1
      for distr in dataset.distributions:
        countDistr += 1
        if distr.issued == True:
          response.issued += 1
        if distr.modified == True:
          response.modified += 1
        if distr.byteSize == True:
          response.byteSize += 1
        if distr.rights == True:
          response.rights += 1
        if distr.license == True:
          response.license += 1
        if distr.licenseVocabulary == True:
          response.licenseVocabulary += 1
        if distr.downloadURL == True:
          response.downloadURL += 1
        tempArrayDownloadUrl.append(distr.downloadURLResponseCode)
        tempArrayAccessUrl.append(distr.accessURL)
        if distr.format == True:
          response.format += 1
        if distr.formatMachineReadable == True:
          response.formatMachineReadable += 1
        if distr.formatNonProprietary == True:
          response.formatNonProprietary += 1
        if distr.mediaType == True:
          response.mediaType += 1
        if distr.dctFormat_dcatMediaType == True:
          response.dctFormat_dcatMediaType += 1

    # distribution level percentages, based on distributions counts
    response.issued = round(response.issued / (countDataset + countDistr) * 100)
    response.modified = round(response.modified / (countDataset + countDistr) * 100)
    response.byteSize = round(response.byteSize / countDistr * 100)
    response.rights = round(response.rights / countDistr * 100)
    response.licenseVocabulary = round(response.licenseVocabulary / response.license * 100)
    response.license = round(response.license / countDistr * 100)
    response.downloadURL = round(response.downloadURL / countDistr * 100)
    list_unique = (list(set(tempArrayDownloadUrl)))
    for el in list_unique:
      if el in range(200, 399):
        response.downloadURLResponseCode_Perc += round(tempArrayDownloadUrl.count(el) / countDistr * 100)
      response.downloadURLResponseCode.append({"code": el, "percentage": round(tempArrayDownloadUrl.count(el) / countDistr * 100)})
    list_unique = (list(set(tempArrayAccessUrl)))
    for el in list_unique:
      if el in range(200, 399):
        response.accessURL_Perc += round(tempArrayAccessUrl.count(el) / countDistr * 100)
      response.accessURL.append({"code": el, "percentage": round(tempArrayAccessUrl.count(el) / countDistr * 100)})
    response.format = round(response.format / countDistr * 100)
    response.formatMachineReadable = round(response.formatMachineReadable / countDistr * 100)
    response.formatNonProprietary = round(response.formatNonProprietary / countDistr * 100)
    response.mediaType = round(response.mediaType / countDistr * 100)
    response.dctFormat_dcatMediaType = round(response.dctFormat_dcatMediaType / (countDistr*2) * 100)

    # dataset level percentages, based on datasets counts
    response.accessRightsVocabulary = round(response.accessRightsVocabulary / response.accessRights * 100)
    response.accessRights = round(response.accessRights / countDataset * 100)
    response.contactPoint = round(response.contactPoint / countDataset * 100)
    response.publisher = round(response.publisher / countDataset * 100)
    response.keyword = round(response.keyword / countDataset * 100)
    response.theme = round(response.theme / countDataset * 100)
    response.spatial = round(response.spatial / countDataset * 100)
    response.temporal = round(response.temporal / countDataset * 100)
    response.shacl_validation = round(response.shacl_validation / countDataset * 100)


    weights = Object()
    # weights
    # full list of weight can be found https://data.europa.eu/mqa/methodology?locale=en
    weights.keyword_Weight = math.ceil(30 / 100 * response.keyword)
    weights.theme_Weight = math.ceil(30 / 100 * response.theme)
    weights.spatial_Weight = math.ceil(20 / 100 * response.spatial)
    weights.temporal_Weight = math.ceil(20 / 100 * response.temporal)
    weights.contactPoint_Weight = math.ceil(20 / 100 * response.contactPoint)
    weights.publisher_Weight = math.ceil(10 / 100 * response.publisher)
    weights.accessRights_Weight = math.ceil(10 / 100 * response.accessRights)
    weights.accessRightsVocabulary_Weight = math.ceil(5 / 100 * response.accessRightsVocabulary)
    weights.accessURL_Weight = math.ceil(50 / 100 * response.accessURL_Perc)
    weights.downloadURL_Weight = math.ceil(20 / 100 * response.downloadURL)
    weights.downloadURLResponseCode_Weight = math.ceil(30 / 100 * response.downloadURLResponseCode_Perc)
    weights.format_Weight = math.ceil(20 / 100 * response.format)
    weights.dctFormat_dcatMediaType_Weight = math.ceil(10 / 100 * response.dctFormat_dcatMediaType)
    weights.formatMachineReadable_Weight = math.ceil(20 / 100 * response.formatMachineReadable)
    weights.formatNonProprietary_Weight = math.ceil(20 / 100 * response.formatNonProprietary)
    weights.license_Weight = math.ceil(20 / 100 * response.license)
    weights.licenseVocabulary_Weight = math.ceil(10 / 100 * response.licenseVocabulary)
    weights.mediaType_Weight = math.ceil(10 / 100 * response.mediaType)
    weights.rights_Weight = math.ceil(5 / 100 * response.rights)
    weights.byteSize_Weight = math.ceil(5 / 100 * response.byteSize)
    weights.issued_Weight = math.ceil(5 / 100 * response.issued)
    weights.modified_Weight = math.ceil(5 / 100 * response.modified)
    weights.shacl_validation_Weight = math.ceil(30 / 100 * response.shacl_validation)

    weights.findability = weights.keyword_Weight + weights.theme_Weight + weights.spatial_Weight + weights.temporal_Weight
    weights.accessibility = weights.accessURL_Weight + weights.downloadURL_Weight + weights.downloadURLResponseCode_Weight
    weights.interoperability = weights.format_Weight + weights.dctFormat_dcatMediaType_Weight + weights.formatMachineReadable_Weight + weights.formatNonProprietary_Weight + weights.mediaType_Weight + weights.shacl_validation_Weight
    weights.reusability = weights.license_Weight + weights.licenseVocabulary_Weight + weights.contactPoint_Weight + weights.publisher_Weight + weights.accessRights_Weight + weights.accessRightsVocabulary_Weight 
    weights.contextuality = weights.rights_Weight + weights.byteSize_Weight + weights.issued_Weight + weights.modified_Weight

    weights.overall = weights.findability + weights.accessibility + weights.interoperability + weights.reusability + weights.contextuality

    response.score = weights.__dict__

  else:
    # if the file is a dataset, it needs to be analyzed on dataset level
    response = dataset_calc(xml, pre)

  class EmployeeEncoder(json.JSONEncoder): 
        def default(self, o):
            return o.__dict__

  # if the file is a catalogue and id is provided, it updates the catalogue history
  # id should not be none because if user did not provide it, it is generated by the system before calling main function
  if id != None and xml.rfind('<dcat:Catalog ') != -1:
    now = datetime.now()
    collection_name.update_one({'_id': ObjectId(id)},  {'$push': {"history": { "created_at": now.strftime("%d/%m/%Y %H:%M:%S"),"catalogue":json.loads(json.dumps(response, indent=4, cls=EmployeeEncoder)) } }}) 
  # if the file is a dataset and id is provided, it updates the dataset history
  elif id != None and xml.rfind('<dcat:Catalog ') == -1:
    now = datetime.now()
    collection_name.update_one({'_id': ObjectId(id)},  {'$push': {"history": { "created_at": now.strftime("%d/%m/%Y %H:%M:%S"),"dataset":json.loads(json.dumps(response, indent=4, cls=EmployeeEncoder)) } }})

# if url is provided, it sends the results of analisys to the url
  if url != None:
    # print("Sending request to", url)
    
    res = requests.post(url, json.dumps(response, indent=4, cls=EmployeeEncoder))
    
    # print("Status Code", res.status_code)
    return res
  else:
    return response


app = FastAPI(title="BeOpen mqa-scoring")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base model
class Options(BaseModel):
    xml: Optional[str] = None
    file_url: Optional[str] = None
    url: Optional[str] = None
    id: Optional[str] = None

# api to start a new analisys and save on db the results for both case catalogue and dataset
# accept only rdf files, as string or by url, or by file in the submit/file api
# can specify the id of the catalogue or dataset if it was already created before
# the analisys can be long, so it is sent to the user a message that the request has been accepted and if new analisys it also returns the id of the new catalogue or dataset
@app.post("/submit")
async def useCaseConfigurator(options: Options, background_tasks: BackgroundTasks):
    try:
        configuration_inputs = options
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail="Inputs not valid")
    try:
      if configuration_inputs.xml == None and configuration_inputs.file_url == None:
        return HTTPException(status_code=400, detail="Inputs not valid")
      elif configuration_inputs.xml != None:
        xml = configuration_inputs.xml
      else:
        url_response = requests.get(configuration_inputs.file_url)
        xml = url_response.text

# sort the datasets and distributions tags to avoid problems with the rdf parser
      dataset_start = [m.start() for m in re.finditer('(?=<dcat:Dataset)', xml)]
      dataset_finish = [m.start() for m in re.finditer('(?=</dcat:Dataset>)', xml)]
      if len(dataset_start) != len(dataset_finish):
        return HTTPException(status_code=400, detail="Could not sort datasets")
      
      distribution_start = [m.start() for m in re.finditer('(?=<dcat:distribution>)', xml)]
      distribution_finish = [m.start() for m in re.finditer('(?=</dcat:distribution>)', xml)]
      if len(distribution_start) != len(distribution_finish):
        return HTTPException(status_code=400, detail="Could not sort distributions")
      
      # on rdf files the xml tag is not always present, so it is necessary to check if it is present and if it is not
      # the rdf files is always present, and need to be added for parsing, even with xml tag if present
      # if xml tag is present, the closing of rdf tag is the second '>' present in the file otherwise it is the first one (closing_index)
      closing_index = 2
      if xml.rfind('<?xml', None, 10) == -1:
        closing_index = 1

      pre = xml[:find_nth(xml,'>',closing_index) ] + '>'

      # check if the xml is valid
      test_string = pre + xml[dataset_start[0]:dataset_finish[0]+15] + '</rdf:RDF>'
      dt_copy = xml

      if xml.rfind('<dcat:Catalog ') != -1:
        # cut off all the tags on catalogue level, and leave just the tags on dataset level to analyze them separately
        for index, item in enumerate(dataset_start):
          dataset_Tag = xml[dataset_start[index]:dataset_finish[index]+15]
          # create a copy with just the catalogue tags to analyze them separately
          dt_copy = dt_copy.replace(dataset_Tag, '')
      else:
        # cut off all the tags on datasets level, and leave just the tags on distribution level to analyze them separately
        for index, item in enumerate(dataset_start):
          distr_tag = xml[distribution_start[index]:distribution_finish[index]+20]
          # cut off the distribution tag from the dataset string to obtain just the dataset properties to analyze them separately
          dt_copy = dt_copy.replace(distr_tag, '')
        dt_copy = dt_copy.replace(dt_copy[dt_copy.rfind('<adms:identifier>'):dt_copy.rfind('</adms:identifier>')+18], '')
      try:
        g = Graph()
        g.parse(data = test_string)
        g = Graph()
        g.parse(data = dt_copy)
      except:
        print(traceback.format_exc())
        return HTTPException(status_code=400, detail="Could not parse xml")
      
      title = ""
      # gets the title of the catalogue
      for sub, pred, obj in g:
        met = str_metric(pred, g)
        if met == "dct:title":
          title = obj
          break

      # Get the database
      try:
        dbname = get_database()
        collection_name = dbname["mqa"]
        now = datetime.now()
        # print(configuration_inputs.id)
        # check if the id is present, if it is not, it creates a new item in the db
        if configuration_inputs.id == None:
          if xml.rfind('<dcat:Catalog ') != -1:
            type = "catalogue"
          else: 
            type = "dataset"
          new_item = {
            "creation_date" : now.strftime("%d/%m/%Y %H:%M:%S"),
            "last_modified" : now.strftime("%d/%m/%Y %H:%M:%S"),
            "type": type,
            "title": title,
            "history": []
          }
          inserted_item = collection_name.insert_one(new_item)
          id = str(inserted_item.inserted_id)
        else:
          id = configuration_inputs.id
          # take the element in db by id and check if types correspond
          type = collection_name.find_one({'_id': ObjectId(id)})["type"]
          if xml.rfind('<dcat:Catalog ') != -1 and type == "dataset":
            return HTTPException(status_code=400, detail="The file is a catalogue, but the id is from a dataset")
          elif xml.rfind('<dcat:Catalog ') == -1 and type == "catalogue":
            return HTTPException(status_code=400, detail="The file is a dataset, but the id is from a catalogue")
          # check if in the db there are already 5 analisys, if yes, it deletes the oldest one
          if collection_name.find_one({'_id': ObjectId(id)})["history"] != None and len(collection_name.find_one({'_id': ObjectId(id)})["history"]) > 4:
            collection_name.update_one({'_id': ObjectId(id)},  {'$pop': {"history": -1}})
          collection_name.update_one({'_id': ObjectId(id)},  {'$set': {"last_modified": now.strftime("%d/%m/%Y %H:%M:%S")}})
      except:
        print(traceback.format_exc())
        id = None
        collection_name = None

      # start the analisys in background
      background_tasks.add_task(main, xml, pre, dataset_start, dataset_finish, configuration_inputs.url, collection_name, id)
      # send the response to the user
      if configuration_inputs.id != None:
        return {"message": "The request has been accepted"}
      else:
        return {"message": "The request has been accepted", "id" : id}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error" + str(e))
    

# api to start a new analisys and save on db the results for both case catalogue and single dataset
# accept only rdf files as file (format-data). Can be sent as string or by url in the /submit api
# can specify the id of the catalogue or dataset if it was already created before
# the analisys can be long, so it is sent to the user a message that the request has been accepted and if new analisys it also returns the id of the new catalogue or dataset
@app.post("/submit/file")
async def useCaseConfigurator(background_tasks: BackgroundTasks, file: UploadFile = File(...), url: Optional[str] = None, id: Optional[str] = None):
  try:
    xml = file.file.read()
    xml = xml.decode("utf-8")
    file.file.close()
    
# sort the datasets and distributions tags to avoid problems with the rdf parser
    try:
      dataset_start = [m.start() for m in re.finditer('(?=<dcat:Dataset)', xml)]
      dataset_finish = [m.start() for m in re.finditer('(?=</dcat:Dataset>)', xml)]
      if len(dataset_start) != len(dataset_finish):
        return HTTPException(status_code=400, detail="Could not sort datasets")
      
      distribution_start = [m.start() for m in re.finditer('(?=<dcat:distribution>)', xml)]
      distribution_finish = [m.start() for m in re.finditer('(?=</dcat:distribution>)', xml)]
      if len(distribution_start) != len(distribution_finish):
        return HTTPException(status_code=400, detail="Could not sort distributions")
      
      # on rdf files the xml tag is not always present, so it is necessary to check if it is present and if it is not
      # the rdf files is always present, and need to be added for parsing, even with xml tag if present
      # if xml tag is present, the closing of rdf tag is the second '>' present in the file otherwise it is the first one (closing_index)
      closing_index = 2
      if xml.rfind('<?xml', None, 10) == -1:
        closing_index = 1

      pre = xml[:find_nth(xml,'>',closing_index) ] + '>'

      # check if the xml is valid
      test_string = pre + xml[dataset_start[0]:dataset_finish[0]+15] + '</rdf:RDF>'
      dt_copy = xml

      # cut off all the tags on catalogue level, and leave just the tags on dataset level to analyze them separately
      for index, item in enumerate(dataset_start):
        dataset_Tag = xml[dataset_start[index]:dataset_finish[index]+15]
        # create a copy with just the catalogue tags to analyze them separately
        dt_copy = dt_copy.replace(dataset_Tag, '')
        
      try:
        g = Graph()
        g.parse(data = test_string)
        g = Graph()
        g.parse(data = dt_copy)
      except:
        print(traceback.format_exc())
        return HTTPException(status_code=400, detail="Could not parse xml")
      
      title = ""
      # gets the title of the catalogue
      for sub, pred, obj in g:
        met = str_metric(pred, g)
        if met == "dct:title":
          title = obj
          break
      
      # Get the database
      try:
        # check if the id is present, if it is not, it creates a new item in the db
        dbname = get_database()
        collection_name = dbname["mqa"]
        now = datetime.now()
        if id == None:
          if xml.rfind('<dcat:Catalog ') != -1:
            type = "catalogue"
          else: 
            type = "dataset"
          new_item = {
            "creation_date" : now.strftime("%d/%m/%Y %H:%M:%S"),
            "last_modified" : now.strftime("%d/%m/%Y %H:%M:%S"),
            "type": type,
            "title": title,
            "history": []
          }
          inserted_item = collection_name.insert_one(new_item)
          new_id = str(inserted_item.inserted_id)
        else:
          new_id = id
          # take the element in db by id and check if types correspond
          type = collection_name.find_one({'_id': ObjectId(new_id)})["type"]
          if xml.rfind('<dcat:Catalog ') != -1 and type == "dataset":
            return HTTPException(status_code=400, detail="The file is a catalogue, but the id is from a dataset")
          elif xml.rfind('<dcat:Catalog ') == -1 and type == "catalogue":
            return HTTPException(status_code=400, detail="The file is a dataset, but the id is from a catalogue")
          
          # check if in the db there are already 5 analisys, if yes, it deletes the oldest one
          if collection_name.find_one({'_id': ObjectId(new_id)})["history"] != None and len(collection_name.find_one({'_id': ObjectId(new_id)})["history"]) > 4:
            collection_name.update_one({'_id': ObjectId(new_id)},  {'$pop': {"history": -1}})
          collection_name.update_one({'_id': ObjectId(new_id)},  {'$set': {"last_modified": now.strftime("%d/%m/%Y %H:%M:%S")}})
      except:
        print(traceback.format_exc())
        new_id = None
        collection_name = None


      # start the analisys in background
      background_tasks.add_task(main, xml, pre, dataset_start, dataset_finish, url, collection_name, new_id)
      # send the response to the user
      if id != None:
        return {"message": "The request has been accepted"}
      else:
        return {"message": "The request has been accepted", "id" : new_id}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error" + str(e))
  except Exception:
      print(traceback.format_exc())
      return {"message": "There was an error uploading the file"}
  
  # api to get the last results of a catalogue or dataset analisys by id
@app.get("/get/analisys/{id}")
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
@app.post("/get/analisys/{id}")
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
  

  
  # api to delete a catalogue or dataset by id
@app.delete("/delete/element/{id}")
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
@app.delete("/delete/analisys/{id}")
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
        else:
          # if index is provided, it deletes the analisys of that date and index
          for i in range(len(res)):
            if res[i]["created_at"][:res[i]["created_at"].rfind(' ')] == date and i == int(index):
              del res[i]
        response = collection_name.update_one({'_id': ObjectId(id)},  {'$set': {"history": res}})
        if response.modified_count == 1:
          return {"message": "Deleted successfully"}
        else:
          return {"message": "There was a problem deleting the item"}
  except Exception as e:
    print(traceback.format_exc())
    raise HTTPException(status_code=500, detail="Internal Server Error" + str(e))
  
#api to get all id's of catalogues and datasets
@app.get("/get/all")
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


# api to get the current version
@app.get("/version")
def get_version():
  return {"version": "1.1.2"}

# if __name__ == "__main__":
#   main()

appPort = os.getenv("PORT", 8000)
if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=appPort)
    # uvicorn.run(app, host='localhost', port=appPort)