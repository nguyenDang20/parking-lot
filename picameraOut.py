from time import sleep
from picamera import PiCamera
# from check_exist import check_exist
import requests 
import numpy as np
import cv2
from FCMManager import sendNotification, sendPush
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from sendToAdmin import sendToAdmin 
import servo
import checkIn
import json

db = firestore.client()

camera = PiCamera()
camera.resolution = (640, 480)
content_type = 'image/jpeg'
headers = {'content-type': content_type}
licenseNumber='a'
tokens=[]

def saveOut(doc_ref):
	tokens.clear()
	get_id= doc_ref.get({u'id'})
	id= u'{}'.format(get_id.to_dict()['id'])
	users_ref=db.collection(u'Users').document(id)
	#admin=admin=='True'
	get_token=users_ref.get({u'token'})
	token=u'{}'.format(get_token.to_dict()['token'])
	checkin=False #ra
	tokens.append(token)
	sendPush("xac nhan lay xe", "xac nhan lay xe?", tokens)
	res = requests.get('http://detectparking.ddns.net/auth/').text 
	while res == 'None':
		res = requests.get('http://detectparking.ddns.net/auth/').text
		print('wait')
		continue
	dict=res
	res = json.loads(dict)
	license1=str(res[u'command'])
					#	print(type(license1))
	print(license1)
	if license1=='YES':			
		get_name=users_ref.get({u'name'})
		name=u'{}'.format(get_name.to_dict()['name'])
		get_admin=users_ref.get({u'admin'})
		admin=u'{}'.format(get_admin.to_dict()['admin'])
		admin = admin == 'True'
		data={
			u'id':id,
			u'time':firestore.SERVER_TIMESTAMP,
			u'name':name,
			u'admin':admin,
			u'checkin':checkin
		}
		db.collection(u'TimeInOut').add(data)
		print('saved!')
	else:
		print('an trom')

while True:
		output = np.empty((480, 640, 3), dtype=np.uint8)
		camera.capture(output,'rgb')
		output = cv2.cvtColor(output , cv2.COLOR_BGR2RGB)
		_, img_encoded= cv2.imencode('.jpg',output)
		response=requests.post('http://detectparking.ddns.net/predict/',headers=headers ,data=img_encoded.tobytes())
		print(response.text)
		if len(response.text) > 1:
			typeVehicle, license1 = response.text.split('-')
			if not checkIn.TrueResult(typeVehicle,license1):
				print('ko du ky tu')
				continue
			#license1=input()
			print('licenseNumber',licenseNumber)
			if licenseNumber!=license1:
				print('here')
				doc_ref=db.collection(u'LicensePlateNumber').document(license1)
				doc=doc_ref.get()
				if doc.exists:
					if checkIn.ParkingCheck(doc_ref,db): #False
						print('xe trong bai')
						saveOut(doc_ref)
						servo.dongmocong()
					else:
						print('o ngoai roi')
						
				else: 
					sendToAdmin(img_encoded,'Kiểm tra xe ra')
					license1 = requests.get('http://detectparking.ddns.net/selfPredict/').text
					while license1=='None':
						license1 = requests.get('http://detectparking.ddns.net/selfPredict/').text
						continue
					print(license1)
					dict=license1
					res = json.loads(dict)
					license1=str(res[u'command'])
					print(license1)
				
					doc_ref=db.collection(u'LicensePlateNumber').document(license1)
					doc=doc_ref.get()
					if doc.exists:#true
						if checkIn.ParkingCheck(doc_ref,db):
							
							print('xe trong bai')
							saveOut(doc_ref)
							servo.dongmocong()					
						else:
							print('luu roi di ra khoi lan')
					else:
						print('Tai khoan da bi xoa')
			licenseNumber= license1
			print('Trung lap bien so')
		else:
			print('khong co xe')
			continue