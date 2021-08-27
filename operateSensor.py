import RPi.GPIO as GPIO

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

import logging

import time

import json

import board

import argparse

import busio

import threading

 

# shadow JSON Schema

#

# {

#     "state: {

#               "desired": {

#                          "dist": <distance>

#                }

#      }

#}

 

deviceShadowHandler = None

 

def getDeviceStatus():

    while True:

        print("Getting device status...\n")

        deviceShadowHandler.shadowGet(customShadowCallback_get, 50)

        time.sleep(60)    

 

def customShadowCallback_get(payload, responseStatus, token):

    if responseStatus == "timeout":

        print("Get request with token " + token + " time out!")

    if responseStatus == "accepted":

        print("========== Printing Device Current Status =========")

        print(payload)

        payloadDict = json.loads(payload)

        #{"state":{"desired":{"light":0},"reported":{"light":100}

        try:

            desired = payloadDict["state"]["desired"]["dist"]

            desiredTime = payloadDict["metadata"]["desired"]["dist"]["timestamp"]

        except Exception:

            print("Failed to get desired state and timestamp.")

        else:

            print("Desired status: " + str(desired) + " @ " + time.ctime(int(desiredTime)))

 

        try:

            reported = payloadDict["state"]["reported"]["dist"]

            #"metadata":{"desired":{"light":{"timestamp":1533893848}},"reported":{"light":{"timestamp":1533893853}}}

            reportedTime = payloadDict["metadata"]["reported"]["dist"]["timestamp"]

        except Exception:

            print("Failed to get reported time or timestamp")

        else:

            print("Reported status: " + str(reported) + " @ " + time.ctime(int(reportedTime)))

        

        print("=======================================\n\n")

    if responseStatus == "rejected":

        print("Get request with token " + token + " rejected!")

 

def customShadowCallback_upate(payload, responseStatus, token):

    # payload is a JSON string which will be parsed by jason lib

    if responseStatus == "timeout":

        print("Update request with " + token + " time out!")

    if responseStatus == "accepted":

        playloadDict = json.loads(payload)

        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

        print("Update request with token: " + token + " accepted!")

        print("dist: " + str(playloadDict["state"]["desired"]["dist"]))

        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    if responseStatus == "rejected":

        print("Update request " + token + " rejected!")

 

 

def customShadowCallback_delete(payload, responseStatus, token):

    if responseStatus == "timeout":

        print("Delete request " + token + " time out!")

    if responseStatus == "accepted":

        print("Delete request with token " + token + " accepted!")

    if responseStatus == "rejected":

        print("Delete request with token " + token + " rejected!")

 

# Cofigure logging

#logger = logging.getLogger("AWSIoTPythonSDK.core")

#logger.setLevel(logging.ERROR)

#streamHandler = logging.StreamHandler()

#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#streamHandler.setFormatter(formatter)

#logger.addHandler(streamHandler)

 

###########################

def distance():

    #set Trigger to HIGH

    GPIO.output(GPIO_TRIGGER,True)

    

    #set Trigger after 0.01ms to Low

    time.sleep(0.00001)

    GPIO.output(GPIO_TRIGGER,False)

    

    StartTime = time.time()

    StopTime = time.time()

    

    #save StartTime

    while GPIO.input(GPIO_ECHO) == 0:

        StartTime = time.time()

    

    #save time of arrival

    while GPIO.input(GPIO_ECHO) == 1:

        StopTime = time.time()

    

    #time difference between start and arrival

    TimeElapsed = StopTime - StartTime

    #multiply with the sonic speed (34300 cm/s)

    #and divide by 2

    distance = (TimeElapsed*34300)/2

    

    return distance

###########################

 

print("Starting...")

 

###########################

#GPIO Mode (BOARD / BCM)

GPIO.setmode(GPIO.BCM)

 

#set GPIO Pins

GPIO_TRIGGER = 18

GPIO_ECHO = 24

 

Buzzer = 23 #set speaker output

 

#set GPIO direction(IN / OUT)

GPIO.setup(GPIO_TRIGGER,GPIO.OUT)

GPIO.setup(GPIO_ECHO,GPIO.IN)

###########################

 

# AWS IoT Core endpoint. Need change some values to yours.

awsiotHost = "a2qsaevf1938ev-ats.iot.us-east-2.amazonaws.com"

awsiotPort = 8883;

rootCAPath = "/home/pi/Hwan/rootCA"

privateKeyPath = "/home/pi/Hwan/rasp-private.pem.key"

certificatePath = "/home/pi/Hwan/rasp-device.pem.crt"

myAWSIoTMQTTShadowClient = None;

myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient("Hwan")

myAWSIoTMQTTShadowClient.configureEndpoint(awsiotHost, awsiotPort)

myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

 

myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)

myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(60) # 10sec

myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(50) #5sec

 

 

#########################

 

while True:

    dist = distance()

    if(dist <= 10.0):

        GPIO.setup(Buzzer, GPIO.OUT)

        time.sleep(0.5)

        

        GPIO.cleanup()

                

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(GPIO_TRIGGER,GPIO.OUT)

        GPIO.setup(GPIO_ECHO,GPIO.IN)

        

        #connect to AWS IoT

        myAWSIoTMQTTShadowClient.connect()

 

        #create a devcie Shadow with persistent subscription

        thingName = "Hwan"

        deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)

 

        #Delete shadow JSON doc

        deviceShadowHandler.shadowDelete(customShadowCallback_delete, 50)

 

        #start a thread to get device status every 5 seconds

        statusLoopThread = threading.Thread(target=getDeviceStatus)

        statusLoopThread.start()

 

        #update shadow in a loop

 

        loopCount = 0

 

        desiredState = str(dist)

        print("#######################")

        print("Someone is Get closer... \"" + desiredState + "\" centimeters away...\n")

        jsonPayload = '{"state":{"desired":{"dist":"' + desiredState + '"}}}'

        print("payload is: " + jsonPayload + "\n")

        deviceShadowHandler.shadowUpdate(jsonPayload, customShadowCallback_upate, 60)

        loopCount += 1

        print("#######################")

        time.sleep(5) #stop for 5sec

            

    else:

        print("Measured Distance = %.1fcm"%dist)

        time.sleep(1)