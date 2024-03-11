# file_uploader.py MinIO Python SDK example
from datetime import datetime
import os
from minio import Minio
from minio.error import S3Error

def getUserInfo():
    return None

# save the file of the analisys in the minio bucket. Bucket -> id(folder) -> date.json (max:5)
def minio_saveFile(nameFile,jsonFile): # jsonFile is a string with the json
    # Create a client with the MinIO server playground, its access key
    # and secret key.
    client = Minio("play.min.io",
        access_key="Q3AM3UQ867SPQQA43P2F",
        secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    )

    # get current date
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
    
    # The file to upload, change this path if needed
    source_file = "./tmp/" + nameFile + ".json"

    # The destination bucket and filename on the MinIO server
    bucket_name = "asteroid-test"
    destination_file = nameFile + "/" + dt_string + ".json"

    # Make the bucket if it doesn't exist.
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)
        print("Created bucket", bucket_name)
    else:
        print("Bucket", bucket_name, "already exists")

    # check if folders inside nameFile are more then 4, delete the oldest one
    objects = minio_listFiles(nameFile)
    if len(objects) > 4:
        # get the oldest folder using the date in the folder name
        # delete the oldest folder
        client.remove_object(bucket_name, objects[0].object_name)


    # check if the tmp folder exists and create it if not
    if not os.path.exists("./tmp"):
        os.makedirs("./tmp")
    # save tmp file
    with open(source_file, "w") as file:
        file.write(jsonFile)

    with open(source_file, "rb") as file_data:
        # Upload the file, renaming it in the process
        client.put_object(
            bucket_name, destination_file, file_data, length=-1, part_size=10*1024*1024,
        )
        # delete tmp file
        file.close()
        file_data.close()
        os.remove(source_file)

    print(
        source_file, "successfully uploaded as object",
        destination_file, "to bucket", bucket_name,
    )

# get the last file of the analisys
def minio_getFile(nameFile):
    client = Minio("play.min.io",
        access_key="Q3AM3UQ867SPQQA43P2F",
        secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    )
    # sort folders by date in name
    objects = minio_listFiles(nameFile)

    # get last inserted folder
    destination_file = nameFile + "/" + objects[-1].object_name + ".json"
    # The destination bucket on the MinIO server
    bucket_name = "asteroid-test"
    # Download the file
    client.get_object(
        bucket_name, objects[-1].object_name, destination_file,
    )
    print(
        destination_file, "successfully downloaded from bucket", bucket_name
    )
    return destination_file

# list all files in the bucket
def minio_listAllFiles():
    client = Minio("play.min.io",
        access_key="Q3AM3UQ867SPQQA43P2F",
        secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    )
    # The destination bucket and filename on the MinIO server
    bucket_name = "asteroid-test"
    # List the files
    objects = client.list_objects(bucket_name, recursive=True)
    for obj in objects:
        print(obj.bucket_name, obj.object_name)
    return objects

# list all files in a folder
def minio_listFiles(folderName):
    client = Minio("play.min.io",
        access_key="Q3AM3UQ867SPQQA43P2F",
        secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    )
    # The destination bucket and filename on the MinIO server
    bucket_name = "asteroid-test"
    # List the files
    objects = client.list_objects(bucket_name, prefix=folderName, recursive=True)
    objects = list(objects)
    objects.sort(key=lambda x: x.last_modified)
    for obj in objects:
        print(obj.bucket_name, obj.object_name)
    return objects

# delete the file of the analisys at the index
def minio_deleteFile(nameFile,index): # index from 0 to 4
    if index < 0 or index > 4:
        print("index out of range")
        return "index out of range"
    
    client = Minio("play.min.io",
        access_key="Q3AM3UQ867SPQQA43P2F",  
        secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    )
    # The destination bucket and filename on the MinIO server
    bucket_name = "asteroid-test"
    # sort folders by date in name
    objects = minio_listFiles(nameFile)
    # get the file to delete
    destination_file = objects[index].object_name
    # Delete the file
    client.remove_object(bucket_name, destination_file)
    print(
        destination_file, "successfully deleted from bucket", bucket_name,
    )
    return destination_file

# delete the folder with the file of the last analisys
def minio_delete_LastFile(nameFile):
    client = Minio("play.min.io",
        access_key="Q3AM3UQ867SPQQA43P2F",  
        secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    )
    # The destination bucket and filename on the MinIO server
    bucket_name = "asteroid-test"
    # sort folders by date in name
    objects = minio_listFiles(nameFile)
    # get the file to delete
    destination_file = objects[len(objects) - 1].object_name
    # Delete the file
    client.remove_object(bucket_name, destination_file)
    print(
        destination_file, "successfully deleted from bucket", bucket_name,
    )
    return destination_file

# delete folder of all analisys
def minio_deleteFolder(folderName):
    client = Minio("play.min.io",
        access_key="Q3AM3UQ867SPQQA43P2F",
        secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    )
    # The destination bucket and filename on the MinIO server
    bucket_name = "asteroid-test"
    # list objects in the folder
    objects = minio_listFiles(folderName)
    # delete all objects with remove objects
    for obj in objects:
        client.remove_object(bucket_name, obj.object_name)
    print(
        folderName, "successfully deleted from bucket", bucket_name,
    )
    return folderName


# if __name__ == "__main__":
#     try:
        # minio_saveFile("12345689","{'a':'b'}")
        # minio_listFiles("12345689")
        # minio_listAllFiles()
        # getFile("12345689")
        # minio_deleteFile("1234568",0)
        # minio_delete_LastFile("123456")
        # minio_deleteFolder("123456")
    # except S3Error as exc:
    #     print("error occurred.", exc)

