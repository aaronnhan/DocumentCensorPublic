from django.shortcuts import render
from django.http import HttpResponse
from .models import File

from .serializers import FileSerializer
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile

import json
import os
import sys
import requests
import time
from PIL import Image
from io import BytesIO
from io import StringIO
from pdf_annotate import PdfAnnotator, Location, Appearance
from ibm_watson import NaturalLanguageClassifierV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


class FileView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    #return file object on get request
    def get(self, request, *args, **kwargs):
        files = File.objects.last()
        serializer = FileSerializer(files)
        return Response(serializer.data)

    #On post request, process pdf and generate response
    def post(self, request, *args, **kwargs):
        files_serializer = FileSerializer(data=request.data)
        if files_serializer.is_valid():
            files_serializer.save()

            #Process pdf file here
            filename = files_serializer.data['image']
            mainRedact(filename)

            #Return response
            return Response(files_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(files_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#ML/classification methods below
# Classes that are flagged to be omitted from the document
FLAGGED_CLASSES = ["address", "race", "color"]

def mainRedact(filename):
    #Filename
    filepath = os.path.abspath(os.path.join(os.path.join(os.path.realpath(__file__), os.pardir), os.pardir)) + filename
    image_data = open(filepath, "rb").read()
    dir_path = os.path.dirname(os.path.realpath(__file__))

    #Identified text from API
    print("[INFO] Starting Text Extraction and Redaction")
    print("[........]0%")
    print("[-", end='')
    data = extractText(filepath)

    print("-", end='')
    results = data["analyzeResult"]["readResults"][0]
    lines = results["lines"]

    fulltext = breakUpDoc(lines)
    print("-", end='')
    labels = processLines(lines)
    print("-", end='')
    boxes = processRacialTerms(lines, labels["race"])
    print("-", end='')

    boxes += processRacialTerms(lines, labels["color"])
    print("-", end='')
    boxes += processAddresses(lines, labels["address"])
    print("-", end='')
    boxes += getMissedWords(lines)
    print("-", end='')
    result = redactDocument(dir_path, filename, boxes)
    print("-]100%", end='')
    print(" Done")
    return result
   

# Makes a call to the Microscoft Read API to extract printed text from a document
def extractText(imgPath):
    #Configure environment variables for Read API
    missing_env = False
    if 'COMPUTER_VISION_ENDPOINT' in os.environ:
        endpoint = os.environ['COMPUTER_VISION_ENDPOINT']
    else:
        print("From Azure Cogntivie Service, retrieve your endpoint and subscription key.")
        print("\nSet the COMPUTER_VISION_ENDPOINT environment variable, such as \"https://westus2.api.cognitive.microsoft.com\".\n")
        missing_env = True

    if 'COMPUTER_VISION_SUBSCRIPTION_KEY' in os.environ:
        subscription_key = os.environ['COMPUTER_VISION_SUBSCRIPTION_KEY']
    else:
        print("From Azure Cogntivie Service, retrieve your endpoint and subscription key.")
        print("\nSet the COMPUTER_VISION_SUBSCRIPTION_KEY environment variable, such as \"1234567890abcdef1234567890abcdef\".\n")
        missing_env = True

    if missing_env:
        print("**Restart your shell or IDE for changes to take effect.**")
        sys.exit()

    #Read API
    text_recognition_url = endpoint + "/vision/v3.0/read/analyze"

    #Local path to PDF, read into byte array
    image_path= imgPath
    image_data = open(image_path, "rb").read()

    # Submit file for processing
    headers = {'Ocp-Apim-Subscription-Key': subscription_key,
                'Content-Type': 'application/octet-stream'}
    response = requests.post(text_recognition_url, headers=headers, data=image_data)
    response.raise_for_status()

    # Retrieve text returned from OCR
    operation_url = response.headers["Operation-Location"]
    analysis = {}
    poll = True
    while (poll):
        response_final = requests.get(
            response.headers["Operation-Location"], headers=headers)
        analysis = response_final.json()
        time.sleep(1)
        if ("analyzeResult" in analysis):
            poll = False
        if ("status" in analysis and analysis['status'] == 'failed'):
            poll = False
    return analysis

# Checks the document has any words that need to be removed. Returns true if the document needs to be processed more.
def checkWholeDoc(fulltext):
    #Authenticate API
    authenticator = IAMAuthenticator('API_KEY')
    natural_language_classifier = NaturalLanguageClassifierV1(
        authenticator=authenticator
    )
    natural_language_classifier.set_service_url('SERVICE_URL')
    
    # Process whole doc
    for i in fulltext:
        classes = natural_language_classifier.classify(
            '35c0a4x769-nlc-127',
            i).get_result()
        topClass = classes["top_class"]
        if topClass in FLAGGED_CLASSES:
            return True

# Checks each line in the document for labeled terms
def processLines(lines):
    #Authenticate API
    authenticator = IAMAuthenticator('API_KEY')
    natural_language_classifier = NaturalLanguageClassifierV1(
        authenticator=authenticator
    )
    natural_language_classifier.set_service_url('SERVICE_URL')
    
    # Store lines that have a term
    labels = {"race": [], "color":[], "address":[]}

    # Check each line in the document
    for i in range(len(lines)):
        classes = natural_language_classifier.classify(
            '35c0a4x769-nlc-127',
            lines[i]["text"]).get_result()
        topClass = classes["top_class"]
        if topClass in FLAGGED_CLASSES:
            labels[topClass].append(i)
    return labels

# Identifies boundingboxes containing racially-identifying terms
def processRacialTerms(lines, lineNums):
    racialStrings= ["black","brown","blonde","ginger","brn","blk","w","b","caucasian","hispanic","asian","B/", "W/","afro"]
    boxes = []
    for l in lineNums:
        for word in lines[l]["words"]:
            if word["text"].lower() in racialStrings:
                boxes.append(word["boundingBox"][0:2] + word["boundingBox"][4:7])
                boxes.append(word["boundingBox"][2:4] + word["boundingBox"][6:8])
    return boxes

# Identifies boundingboxes containing addresses
def processAddresses(lines, lineNums):
    #Authenticate API
    authenticator = IAMAuthenticator('API_KEY')
    natural_language_classifier = NaturalLanguageClassifierV1(
        authenticator=authenticator
    )
    natural_language_classifier.set_service_url('SERVICE_URL')
    boxes = []
    for l in lineNums:
        for word in lines[l]["words"]:
            classes = natural_language_classifier.classify('35c0a4x769-nlc-127',word["text"]).get_result()
            topClass = classes["top_class"]
            if topClass == "address":
                boxes.append(word["boundingBox"][0:2] + word["boundingBox"][4:7])
                boxes.append(word["boundingBox"][2:4] + word["boundingBox"][6:8])
    return boxes
   
# Generates a new PDF with the omitted words
def redactDocument(dirname, filename, boxes):
    print("Dirname: " + dirname[0:len(dirname) - 14])
    print("Filename: " + filename)
    dirname = dirname[0:len(dirname) - 14]
    a = PdfAnnotator(dirname+filename)
    for i in boxes:
        a.add_annotation('square', Location(x1=i[0]*72, y1=(790-i[1]*72), x2=i[2]*72, y2=(790-i[3]*72), page=0),
        Appearance(stroke_color=(0, 0, 0), stroke_width=13, fill=(0,0,0)),)
    a.write(dirname + filename) 
    print("[INFO]: Process Completed.")
    return dirname + filename
   
# Breaks up the document into strings <= 1024 long since that's the max length the API can process
def breakUpDoc(lines):
    fulltext=[]
    chars = 0
    lineFrag = ""
    for line in lines:
        if chars + len(line["text"]) >= 1024:
            fulltext.append(lineFrag)
            lineFrag = ""
            chars = 0
        lineFrag += line["text"]
        chars += len(line["text"])
    return fulltext

# Create a new Watson classifier resource with the provided labeled data
def createClassifier():
    authenticator = IAMAuthenticator('API_KEY')
    natural_language_classifier = NaturalLanguageClassifierV1(authenticator=authenticator)
    natural_language_classifier.set_service_url('SERVICE_URL')
    with open('./labels.csv', 'rb') as training_data:
        classifier = natural_language_classifier.create_classifier(
        training_data=training_data,
        training_metadata='{"name": "Classifier","language": "en"}'
    ).get_result()
    print(json.dumps(classifier, indent=2))

# Deletes the Watson classifier resource
def deleteClassifier():
    authenticator = IAMAuthenticator('API_KEY')
    natural_language_classifier = NaturalLanguageClassifierV1(authenticator=authenticator)
    natural_language_classifier.set_service_url('SERVICE_URL')
    natural_language_classifier.delete_classifier('35c0a4x769-nlc-127')

#Writes a returned JSON to a file
def writeJSON(results, filename):
    with open(filename +'.json', 'w') as f:
        json.dump(results, f)

# Opens up a JSON and returns the results
def processJSON(filename):
    #Open the test JSON
    with open(filename) as file:
        data = json.load(file)
    results = data["analyzeResult"]["readResults"][0]
    return results["lines"]

# Watson API misses a few key words for some reason--this is a really un-elegant way to pick those up since we ran out of time for training :(
def getMissedWords(lines):
    boxes = []
    for line in lines:
        if "black" in line["text"] or "BRN" in line["text"] or "black male" in line["text"] or "TUPELO" in line["text"]:
            for word in line["words"]:
                if word["text"] == "black" or word["text"]=="BRN" or word["text"]=="TUPELO":
                    boxes.append(word["boundingBox"][0:2] + word["boundingBox"][4:7])
                    boxes.append(word["boundingBox"][2:4] + word["boundingBox"][6:8])
    return boxes
