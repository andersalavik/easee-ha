#!/usr/bin/env python

import asyncio
import websockets
import requests
import json
import paho.mqtt.publish as publish
import configparser
config = configparser.ConfigParser()


config.read('config.ini')


headers = {
    'Authorization': 'Bearer ' + config['DEFAULT']['haKey'],
    'Content-Type': 'application/json',
}


l1 = json.loads(requests.get('http://'+ config['DEFAULT']['haAddress'] +':'+ config['DEFAULT']['haPort'] +'/api/states/sensor.l1', headers=headers).text)
l2 = json.loads(requests.get('http://'+ config['DEFAULT']['haAddress'] +':'+ config['DEFAULT']['haPort'] +'/api/states/sensor.l2', headers=headers).text)
l3 = json.loads(requests.get('http://'+ config['DEFAULT']['haAddress'] +':'+ config['DEFAULT']['haPort'] +'/api/states/sensor.l3', headers=headers).text)

#print(l1["state"]) 
#print(l2["state"]) 
#print(l3["state"]) 
requests.get('http://'+ config['DEFAULT']['easeeAddress'] +'/challenge?code='+ config['DEFAULT']['easeePin'] +'', timeout=5)
l = [float(l1["state"]),float(l2["state"]),float(l3["state"])]

#print(l)

#print(int(max(l)))


async def status(uri):
	async with websockets.connect(uri,close_timeout=5) as websocket:

		await websocket.send('{"cmd":"GET_TELEMETRY"}')
		greeting2 = await websocket.recv()
		return greeting2


async def config_stat(uri):
    async with websockets.connect(uri,close_timeout=5) as websocket:


        await websocket.send('{"cmd":"GET_USER_CONFIG"}')
        greeting = await websocket.recv()
        return greeting


conf = asyncio.get_event_loop().run_until_complete(
    config_stat('ws://'+ config['DEFAULT']['easeeAddress'] +':9000'))

conf = json.loads(conf)

stats = asyncio.get_event_loop().run_until_complete(
    status('ws://'+ config['DEFAULT']['easeeAddress'] +':9000'))

stats = json.loads(stats)

#print(conf)
#print(stats)

maxcharge = (23  - (int(max(l)) - stats["settings"]["MAX_CURRENT_DRAW"]))


#print(maxcharge)


publish.single("easee/MAX_CURRENT_DRAW/", stats["settings"]["MAX_CURRENT_DRAW"], hostname=config['DEFAULT']['haAddress'], auth = {"username" : config['DEFAULT']['mqttUser'], "password":config['DEFAULT']['mqttPass']})
publish.single("easee/L1_MEASURED_VOLTAGE/", stats["settings"]["L1_MEASURED_VOLTAGE"], hostname=config['DEFAULT']['haAddress'], auth = {"username" : config['DEFAULT']['mqttUser'], "password":config['DEFAULT']['mqttPass']})
publish.single("easee/L2_MEASURED_VOLTAGE/", stats["settings"]["L2_MEASURED_VOLTAGE"], hostname=config['DEFAULT']['haAddress'], auth = {"username" : config['DEFAULT']['mqttUser'], "password":config['DEFAULT']['mqttPass']})
publish.single("easee/L3_MEASURED_VOLTAGE/", stats["settings"]["L3_MEASURED_VOLTAGE"], hostname=config['DEFAULT']['haAddress'], auth = {"username" : config['DEFAULT']['mqttUser'], "password":config['DEFAULT']['mqttPass']})

#maxcharge = 5

json2 = '{"cmd":"SET_USER_CONFIG","settings":{"INSTALLATION_MAX_CHARGE":'+ str(maxcharge) + "}}"
#print(json)

async def send(uri,data):
    async with websockets.connect(uri,close_timeout=5) as websocket:


        await websocket.send(data)
        greeting = await websocket.recv()
        #print(greeting)

if stats["settings"]["MAX_CURRENT_DRAW"] > 0:
    asyncio.get_event_loop().run_until_complete(
        send('ws://'+ config['DEFAULT']['easeeAddress'] +':9000',json2))
    #print('ok')
    publish.single("easee/INSTALLATION_MAX_CHARGE/", maxcharge, hostname=config['DEFAULT']['haAddress'], auth = {"username" : config['DEFAULT']['mqttUser'], "password":config['DEFAULT']['mqttPass']})
elif conf["settings"]["INSTALLATION_MAX_CHARGE"] != 7:
    #print('change to 5A')
    asyncio.get_event_loop().run_until_complete(
        send('ws://'+ config['DEFAULT']['easeeAddress'] +':9000','{"cmd":"SET_USER_CONFIG","settings":{"INSTALLATION_MAX_CHARGE":7}}'))
    publish.single("easee/INSTALLATION_MAX_CHARGE/", 7, hostname=config['DEFAULT']['haAddress'] , auth = {"username" : config['DEFAULT']['mqttUser'], "password":config['DEFAULT']['mqttPass']})


#asyncio.get_event_loop().run_until_complete(
#    config_stat('ws://'+ config['DEFAULT']['easeeAddress'] +':9000'))
