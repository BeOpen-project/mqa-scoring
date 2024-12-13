
import os
import csv
import re
import json
import traceback
import requests
from rdflib import Graph

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
    voc.append(str(obj))
  return voc

# check if the response of edp validator contains the property "shacl:conforms" and return the value
def valResult(d):
  if 'shacl:conforms' in d:
    return d['shacl:conforms']
  for k in d:
    if isinstance(d[k], list):
      for i in d[k]:
        if 'shacl:conforms' in i:
          return i['shacl:conforms']

# send the request to the EDP validator and get the response
def edp_validator(file: str):
  check = False
  try:
    r_edp = requests.post(URL_EDP, data=bytes(file, 'utf-8'), headers=HEADERS)
    r_edp.raise_for_status()
  except requests.exceptions.HTTPError as err:
    # print(traceback.format_exc())
    raise SystemExit(err)
  report = json.loads(r_edp.text)
  if valResult(report):
    check = True
  return check

def checkVocabulary(obj, file):
  found = False
  try:
    with open(file, 'rt', encoding="utf8") as f:
      reader = csv.reader(f, delimiter=',')
      for row in reader:
        for field in row:
          if obj in field:
            found = True
            break
        if found == True:
          break
  except:
    return False
    # print(traceback.format_exc())
  return found


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
  
  # distribution object
  response = prepareResponse()

  g = Graph()
  g.parse(data = str)

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
        # print(traceback.format_exc())
        accessURL_List.append(400)

    elif met == "dcat:downloadURL":
      response.downloadURL = True
      try:
        res = requests.get(obj)
        downloadURLResponseCode_List.append(res.status_code)
      except:
        # print(traceback.format_exc())
        downloadURLResponseCode_List.append(400)
    # in catalogue formats the property dct:MediaTypeOrExtent is inside an empty dct:format tag. The empty tag must be skipped and not counted
    elif (met == "dct:format" and obj != '' and obj != None) or met == "dct:MediaTypeOrExtent":
      response.format = True
      response.formatMachineReadable = checkVocabulary(obj, MACH_READ_FILE)
      response.formatNonProprietary = checkVocabulary(obj, NON_PROP_FILE)
      try:
        g2 = Graph()
        g2.parse(obj, format="application/rdf+xml")
        if (obj, None, None) in g2: 
          dctFormat_dcatMediaType_List.append(True)
        else:
          dctFormat_dcatMediaType_List.append(False)
      except:
        # print(traceback.format_exc())
        dctFormat_dcatMediaType_List.append(False)

    elif (met == "dct:license" and obj != "" and obj != None ) or met == "dct:LicenseDocument":
      response.license = True
      response.licenseVocabulary = checkVocabulary(obj, LICENSE_FILE)

    elif met == "dcat:mediaType":
      response.mediaType = True
      try:
        # removes the prefix from the url to check if it is in the vocabulary 
        # takes the last part of the url after the last / to check if it is in the vocabulary 
        mediatype = obj.split('/')[-1]
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
          # print(traceback.format_exc())
          dctFormat_dcatMediaType_List.append(False)
      except:
        # print(traceback.format_exc())
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
      res = edp_validator(dataset_str)
      if res == True:
        response.shacl_validation = True
      else:
        response.shacl_validation = False
    except:
      # print(traceback.format_exc())
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
        response.accessRightsVocabulary = checkVocabulary(obj, ACCESSRIGHTS_FILE)
  
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
