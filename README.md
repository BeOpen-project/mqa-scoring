# mqa-scoring

The Metadata Quality Assurance (MQA) methodology is defined by the data.europa.eu consortium with the aim of improving the accessibility of datasets published on EU open data portals. It specifies several indicators that help to improve the quality of the metadata harvested by the data.europa.eu portal.

Mqa-scoring is a tool that calculates the score a metadata obtains according to the MQA indicators. The tool also verifies that the requirements specified by the MQA for each indicator are met.

## Installation

`pip install -r requirements.txt`

## Docker installation

`docker compose up -d`

## Usage

`python mqa-scoring.py -h`

## Usage logging in file

`python mqa-scoring.py -f '.\input\file\path' > output.txt`

FORMAT: 1A
HOST: https://platform.beopen-dep.it/mqa-validator/

# mqa-scoring

Mqa-scoring is a simple API that allows consumers to generate a catalog score by following the documentation that can be read at the following link: https://data.europa.eu/mqa/methodology?locale=en.

## Info Collection [/version]


### Version [GET]

Retrieve version number

+ Response 200 (application/json)

            {
                "version": "1.0.0" (string)
            }

## Submit Catalogue JSON Collection [/submit] 

### Submit Analisys with JSON [POST]

Use this API to generate an analysis of a new catalog or update an existing one by specifying the id. 
When the API is called, it provides an immediate response after validating the correctness in the syntax, 
then if a url is present, it will send it the results as well as save you to a database to make them available via API GET

+ Request (application/json)

            { 
                "xml": "<?xml version='1.0'?><rdf:RDF    xmlns:dct='http://purl.org/dc/terms/'   xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'   xmlns:dcat='http://www.w3.org/ns/dcat#'    xmlns:foaf='http://xmlns.com/foaf/0.1/'> <dcat:Catalog rdf:about=''> ...  </dcat:Catalog></rdf:RDF>", (string)
                "url": "example-callback.url", (string, optional)
                "id": "65844c8d7025f07fb57230a0" (string, optional)
            }

+ Response 200 (application/json)


    + Body

            {
                "message": "The request has been accepted",
                "id": "659bd8c7aeb93c11ca548331"
            }
        
+ Response 201 (application/json)


    + Body

            {
                "message": "The request has been accepted"
            }
        
## Submit Catalogue FILE Collection [/submit/file] 

### Submit Analisys with FILE [POST]

Use this API to generate an analysis of a new catalog or update an existing one by specifying the id. 
When the API is called, it provides an immediate response after validating the correctness in the syntax, 
then if a url is present, it will send it the results as well as save you to a database to make them available via API GET

+ Request (multipart/form-data; boundary=---BOUNDARY)

            -----BOUNDARY
        Content-Disposition: form-data; name="file[file]"; filename="example.rdf"

        /9j/4AAQSkZJRgABAQEAYABgAAD/yc5PTgyPGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8URofHh0a
        HBwgJC4nICIIxwjIyMjIyMjIAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMy
        MjIyMjIyMjIyMjIyMjIyMjIyMjIyMyMjIyMjL/wAARCAABAAEDASIAL/wAARCAABAAEDASIAXCVD
        AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFAEB
        AAAAAAAAAAAAAAAAAAAAAP/EABgAMAwEAAhEDEQwEDEQAAAAAAD/2gAMAwEAAhEDEQA/AL+AD//Z
        -----BOUNDARY

            -----BOUNDARY
        Content-Disposition: form-data; name="url[text]";
        
        example-callback.url

        -----BOUNDARY (optional)
        
            -----BOUNDARY
        Content-Disposition: form-data; name="id[text]";
        
        659bd8c7aeb93c11ca548331

        -----BOUNDARY (optional)
+ Response 200 (application/json)


    + Body

            {
                "message": "The request has been accepted",
                "id": "659bd8c7aeb93c11ca548331"
            }
        
+ Response 201 (application/json)


    + Body

            {
                "message": "The request has been accepted"
            }
            
            
## Retrive scores Collection [/get/catalogue/{id}]

### Get Catalogue results [GET]
This API returns all values from the last analysis generated for the specified catalog id.

+ Response 200 (application/json)

            {
                "created_at": "21/12/2023 14:33:16",
                "catalogue": {
                    "datasets": [
                        {
                            "distributions": [
                                {
                                    "title": "Distribution title",
                                    "accessURL": 200,
                                    "downloadURL": false,
                                    "downloadURLResponseCode": 400,
                                    "format": true,
                                    "dctFormat_dcatMediaType": false,
                                    "formatMachineReadable": false,
                                    "formatNonProprietary": false,
                                    "license": true,
                                    "licenseVocabulary": false,
                                    "mediaType": false,
                                    "issued": false,
                                    "modified": false,
                                    "rights": false,
                                    "byteSize": false
                                }, ...
                            ],
                            "title": "Dataset title",
                            "issued": 0,
                            "modified": true,
                            "keyword": false,
                            "theme": false,
                            "spatial": false,
                            "temporal": false,
                            "contactPoint": true,
                            "publisher": false,
                            "accessRights": false,
                            "accessRightsVocabulary": false,
                            "accessURL": [
                                    {
                                        "code": 200,
                                        "percentage": 100
                                    }
                                ],
                            "downloadURL": 0,
                            "downloadURLResponseCode": [
                                    {
                                        "code": 400,
                                        "percentage": 100
                                    }
                                ],
                            "format": 100,
                            "dctFormat_dcatMediaType": 0,
                            "formatMachineReadable": 0,
                            "formatNonProprietary": 0,
                            "license": 100,
                            "licenseVocabulary": 0,
                            "mediaType": 0,
                            "rights": 0,
                            "byteSize": 0,
                            "shacl_validation": true
                        }, ...
                    ],
                    "title": "Catalogue title",
                    "issued": 8,
                    "modified": 12,
                    "keyword": 57,
                    "theme": 43,
                    "spatial": 14,
                    "temporal": 0,
                    "contactPoint": 71,
                    "publisher": 71,
                    "accessRights": 43,
                    "accessRightsVocabulary": 100,
                    "accessURL": [
                        {
                            "code": 200,
                            "percentage": 96
                        },
                        {
                            "code": 404,
                            "percentage": 4
                        }
                    ],
                    "accessURL_Perc": 96,
                    "downloadURL": 2,
                    "downloadURLResponseCode": [
                        {
                            "code": 400,
                            "percentage": 98
                        },
                        {
                            "code": 200,
                            "percentage": 2
                        }
                    ],
                    "downloadURLResponseCode_Perc": 2,
                    "format": 100,
                    "dctFormat_dcatMediaType": 3,
                    "formatMachineReadable": 0,
                    "formatNonProprietary": 0,
                    "license": 96,
                    "licenseVocabulary": 0,
                    "mediaType": 4,
                    "rights": 0,
                    "byteSize": 4,
                    "shacl_validation": 100,
                    "score": {
                        "keyword_Weight": 18,
                        "theme_Weight": 13,
                        "spatial_Weight": 3,
                        "temporal_Weight": 0,
                        "contactPoint_Weight": 15,
                        "publisher_Weight": 8,
                        "accessRights_Weight": 5,
                        "accessRightsVocabulary_Weight": 5,
                        "accessURL_Weight": 48,
                        "downloadURL_Weight": 1,
                        "downloadURLResponseCode_Weight": 1,
                        "format_Weight": 20,
                        "dctFormat_dcatMediaType_Weight": 1,
                        "formatMachineReadable_Weight": 0,
                        "formatNonProprietary_Weight": 0,
                        "license_Weight": 20,
                        "licenseVocabulary_Weight": 0,
                        "mediaType_Weight": 1,
                        "rights_Weight": 0,
                        "byteSize_Weight": 1,
                        "issued_Weight": 1,
                        "modified_Weight": 1,
                        "shacl_validation_Weight": 30,
                        "findability": 34,
                        "accessibility": 50,
                        "interoperability": 52,
                        "reusability": 53,
                        "contextuality": 3,
                        "overall": 192
                    }
                }
            }

### Get Catalogue results filtered [POST]
This API return the values of the last analisys generated, filtered by parameters use entered in the request.

+ Request (application/json)

            {
                "parameters": "title, mediaType_Weight, datasets, datasets.distributions.accessURL"
            }


+ Response 200 (application/json)

            {
                "created_at": "21/12/2023 14:33:16",
                "catalogue": {
                    "datasets": [
                        {
                            "distributions": [
                                {
                                    "title": "Distribution title",
                                    "accessURL": 200,
                                    "downloadURL": false,
                                    "downloadURLResponseCode": 400,
                                    "format": true,
                                    "dctFormat_dcatMediaType": false,
                                    "formatMachineReadable": false,
                                    "formatNonProprietary": false,
                                    "license": true,
                                    "licenseVocabulary": false,
                                    "mediaType": false,
                                    "issued": false,
                                    "modified": false,
                                    "rights": false,
                                    "byteSize": false
                                }, ...
                            ],
                            "title": "Dataset title",
                            "issued": 0,
                            "modified": true,
                            "keyword": false,
                            "theme": false,
                            "spatial": false,
                            "temporal": false,
                            "contactPoint": true,
                            "publisher": false,
                            "accessRights": false,
                            "accessRightsVocabulary": false,
                            "accessURL": [
                                    {
                                        "code": 200,
                                        "percentage": 100
                                    }
                                ],
                            "downloadURL": 0,
                            "downloadURLResponseCode": [
                                    {
                                        "code": 400,
                                        "percentage": 100
                                    }
                                ],
                            "format": 100,
                            "dctFormat_dcatMediaType": 0,
                            "formatMachineReadable": 0,
                            "formatNonProprietary": 0,
                            "license": 100,
                            "licenseVocabulary": 0,
                            "mediaType": 0,
                            "rights": 0,
                            "byteSize": 0,
                            "shacl_validation": true
                        }, ...
                    ],
                    "title": "Catalogue title",
                    "issued": 8,
                    "modified": 12,
                    "keyword": 57,
                    "theme": 43,
                    "spatial": 14,
                    "temporal": 0,
                    "contactPoint": 71,
                    "publisher": 71,
                    "accessRights": 43,
                    "accessRightsVocabulary": 100,
                    "accessURL": [
                        {
                            "code": 200,
                            "percentage": 96
                        },
                        {
                            "code": 404,
                            "percentage": 4
                        }
                    ],
                    "accessURL_Perc": 96,
                    "downloadURL": 2,
                    "downloadURLResponseCode": [
                        {
                            "code": 400,
                            "percentage": 98
                        },
                        {
                            "code": 200,
                            "percentage": 2
                        }
                    ],
                    "downloadURLResponseCode_Perc": 2,
                    "format": 100,
                    "dctFormat_dcatMediaType": 3,
                    "formatMachineReadable": 0,
                    "formatNonProprietary": 0,
                    "license": 96,
                    "licenseVocabulary": 0,
                    "mediaType": 4,
                    "rights": 0,
                    "byteSize": 4,
                    "shacl_validation": 100,
                    "score": {
                        "keyword_Weight": 18,
                        "theme_Weight": 13,
                        "spatial_Weight": 3,
                        "temporal_Weight": 0,
                        "contactPoint_Weight": 15,
                        "publisher_Weight": 8,
                        "accessRights_Weight": 5,
                        "accessRightsVocabulary_Weight": 5,
                        "accessURL_Weight": 48,
                        "downloadURL_Weight": 1,
                        "downloadURLResponseCode_Weight": 1,
                        "format_Weight": 20,
                        "dctFormat_dcatMediaType_Weight": 1,
                        "formatMachineReadable_Weight": 0,
                        "formatNonProprietary_Weight": 0,
                        "license_Weight": 20,
                        "licenseVocabulary_Weight": 0,
                        "mediaType_Weight": 1,
                        "rights_Weight": 0,
                        "byteSize_Weight": 1,
                        "issued_Weight": 1,
                        "modified_Weight": 1,
                        "shacl_validation_Weight": 30,
                        "findability": 34,
                        "accessibility": 50,
                        "interoperability": 52,
                        "reusability": 53,
                        "contextuality": 3,
                        "overall": 192
                    }
                }
            }
