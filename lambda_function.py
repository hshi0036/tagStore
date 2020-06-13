import json
import base64
import boto3
from PIL import Image
import io
import numpy as np 
import sys, os
import cv2
from io import BytesIO
import uuid


conf = 0.5 #The minimum probability of filtering weak detection：
# Any output with confidence less than this value is eliminated
nms = 0.4 



s3 = boto3.client('s3')
BUCKET_NAME = 'bucket-s3a2'
# data = s3.get_object(Bucket=BUCKET_NAME, Key='yolov3-tiny.weights')
s3.download_file(BUCKET_NAME, 'yolov3-tiny.weights', '/tmp/yolov3-tiny.weights')
s3.download_file(BUCKET_NAME, 'yolov3-tiny.cfg', '/tmp/yolov3-tiny.cfg')
s3.download_file(BUCKET_NAME, 'coco.names', '/tmp/coco.names')
meta = "/tmp/coco.names"
cfg = "/tmp/yolov3-tiny.cfg"
weights = '/tmp/yolov3-tiny.weights'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('tagStoreDB')


def object_detect(image_path, url):
    net = cv2.dnn.readNetFromDarknet(cfg, weights)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    #Load the image, convert it to blob format, and feed it into the network input layer
    img = cv2.imdecode(np.frombuffer(image_path, np.uint8), cv2.IMREAD_COLOR)
    #Net requires input in blob format, which is converted using the function blobFromImage
    blobImg = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blobImg)#The setInput function is called to feed the image into the input layer
    #Get network output layer information (names of all output layers), set and propagate forward
    outInfo = net.getUnconnectedOutLayersNames()
    layerOutputs = net.forward(outInfo)#It is a two-dimensional structure to obtain the information of each output layer and each detection box.
    img_height, img_width, _ = img.shape
    #Get the picture size
    # filter layerOutputs
    #Elements of dimension 1 of layerOutputs: [center_x, center_y, width, height, objectness, n-class score data]
    # filtered results into:
    boxes = [] #All bounding boxes (layer results put together)
    confidences = []#confidences
    classIDs = []#all classification ids
    #filter out boxes with low confidence
    for out in layerOutputs: #Each output layer
        for detection in out: #Each frame
            #Get the confidence
            scores = detection[5:] #The confidence of each category
            classID = np.argmax(scores)#The id with the highest confidence is the classification id
            confidence = scores[classID]#Get the confidence
            #Screening based on confidence
            #Put the bounding box into the picture size
            if confidence > conf:
                center_x = int(detection[0] * img_width)
                center_y = int(detection[1] * img_height)
                width = int(detection[2] * img_width)
                height = int(detection[3] * img_height)
                left = int(center_x - width / 2)
                top = int(center_y - height / 2)
                classIDs.append(classID)
                confidences.append(float(confidence))
                boxes.append([left, top, width, height])
    #Non-maxima suppression (NMS) was applied to further screen out
    indices = cv2.dnn.NMSBoxes(boxes,confidences,conf,nms)#In boxes, the index of reserved box is saved into idxs

    #get the labels list
    with open(meta, 'rt') as f:
        labels = f.read().rstrip('\n').split('\n')
    #Application of test results
    results = []
    for ind in indices:
        res_box = {}
        res_box["label"] = classIDs[ind[0]]
        res_box["accuracy"] = confidences[ind[0]]
        results.append(res_box)

    for result in results:
        lable = result["label"]
        accuracy = result["accuracy"]
        result["label"] = labels[lable]
        result["accuracy"] = round(accuracy * 100, 2)

    return {"objects": results, "url": url}
    
def saveToDB(res, context):
    items = []
    url = res["url"]
    for obj in res['objects']:
        items.append(obj['label'])
    table.put_item(
        Item={
            "id": context.aws_request_id,
            "objects": items,
            "url": url
        }
    )    
    
    

def lambda_handler(event, context):
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']
    url = "https://fit5225-a2.s3.amazonaws.com/images/" + key
    
    s3.download_file(BUCKET_NAME, key, '/tmp/input.jpg')
    # url = "https://fit5225-a2.s3.amazonaws.com/" + "image1.png"
    # with open("/tmp/input.jpg", "wb") as f:
    #     f.write(base64.b64decode(event['body']))
    
    with open('/tmp/input.jpg', "rb") as image:
        f = image.read()
        
    res = object_detect(f, url)
    saveToDB(res, context)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'successful lambda function call'}), 
        'headers': {'Access-Control-Allow-Origin': '*'}}
