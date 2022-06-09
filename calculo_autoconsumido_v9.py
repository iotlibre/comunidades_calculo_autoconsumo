
#!/usr/bin/env python
import configparser
import paho.mqtt.publish as publish
import json
from datetime import datetime
from datetime import timedelta
from datetime import date
import http.client
import time 
import requests
import logging
from logging.handlers import RotatingFileHandler

# Para obtener mas detalle: level=logging.DEBUG
# Para comprobar el funcionamiento: level=logging.INFO
logging.basicConfig(
        level=logging.DEBUG,
        handlers=[RotatingFileHandler('./logs/log_autoconsumido.log', maxBytes=10000000, backupCount=4)],
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p')

parser = configparser.ConfigParser()

'''
Cambio de una fecha en formato iso a formato Datetime
'ultima': '2022-06-02T14:00:00+02:00'
2022-06-07T11:00:00+02:00
year= int(d['date'].split("/")[0])
type(isoD)
<class 'datetime.datetime'>


'''
def isoformatD(iso):
     dateL= iso.split("+")[0].split("T")
     year = int(dateL[0].split("-")[0])
     month = int(dateL[0].split("-")[1])
     day = int(dateL[0].split("-")[2])
     hour = int(dateL[1].split(":")[0])
     minutes = int(dateL[1].split(":")[0])
     isoD = datetime(year, month, day, hour, minutes, 00, 00000)
     logging.debug("isoD :" + str(isoD))
     return isoD


'''datetime
https://docs.python.org/3/library/datetime.html#module-datetime

formato de la última lectura 
"2022-06-01T20:00:00+02:00"

register del reading_register_ :
{'name': 'jesus', 'key': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'autoconsumed': 1.5562099999999917, 'exported': 1.7128100000000104, 'imported': 7.078883750000001, 'ultima': '2022-06-02T14:00:00+02:00'}

http://direccion_del_servidor.com/input/post?node=jesus&fulljson={"autoconsumedp":1.499,"exportedp":1.551,"importedp":7.079,"time":"2022-06-02T13:00:00"}&xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
'''
def emoncms_tx(position):
    
    emonServer = parser.get('emoncms_server','emon_ip')
    userKey =  reading_register_[position]["key"]
    nodeNameS = reading_register_[position]["name"]
    # emonServer = "direccion_del_servidor.com"
    # userKey = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    
    autoconsumedS = str(round(reading_register_[position]["autoconsumed"],3))
    exportedS = str(round(reading_register_[position]["exported"],3))
    importedS = str(round(reading_register_[position]["imported"],3))

    #Correcciones horarias 
    timeI = reading_register_[position]["ultima"].split("+")[0]
    # emonCms muestra el consumo de una hora en el inicio de la hora (+1)
    zoneI = int(reading_register_[position]["ultima"].split("+")[1].split(":")[0]) + 1
    enerTimeS = (isoformatD(timeI) - timedelta(hours=zoneI)).isoformat()
    

    urlEmon =  "http://"
    urlEmon += emonServer
    urlEmon += "/input/post?node="
    urlEmon += nodeNameS
    urlEmon += "&fulljson={\"autoconsumed\":"
    urlEmon += autoconsumedS
    urlEmon += ",\"exported\":"
    urlEmon += exportedS
    urlEmon += ",\"imported\":"
    urlEmon += importedS
    urlEmon += ",\"time\":\""
    urlEmon += enerTimeS
    urlEmon += "\"}&apikey="
    urlEmon += userKey
    
    logging.debug("++++ " + urlEmon)
    response_text = requests.get(urlEmon)
    logging.debug("+++ " + str(response_text))
    time.sleep(0.4)

''' Procesar la lectura antes de enviarla.
data0n:
["2022-05-30T20:00:00+02:00",1.1659999999999968]
register:
{"name":"jesus","key":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","autoconsumed": 1.1,"exported": 1.1,"imported": 1.1,"ultima": "2022-05-30T20:00:00+02:00"}

'''
def procesar_lectura(data0n,data1n,position):
    
    register = reading_register_[position]    
    imporetedEnergy = register["imported"]
    autoconsumedEnergy = register["autoconsumed"]
    exportedEnergy = register["exported"]
    ultimaI=register["ultima"]
    
    logging.debug(register)
    
    logging.debug(data0n[0])
    logging.debug(data1n[0])
    logging.debug(data0n[1])
    logging.debug(data1n[1])    
    
    lastTimeD = isoformatD(ultimaI)
    currentTimeD = isoformatD(data0n[0])
    
    timeOk = 1
    decodedOk = 1
    
    if(lastTimeD >= currentTimeD):
        timeOk = 0
    if(currentTimeD.replace(tzinfo=None) + timedelta(hours=2) >= datetime.now()):
        timeOk = 0
    if(timeOk == 1):
        try:
            importedHour= data0n[1]-data1n[1]
            if(importedHour >= 0):
                imporetedEnergy = imporetedEnergy +  importedHour
                autoconsumedEnergy = autoconsumedEnergy + data1n[1]
            else:
                exportedEnergy = exportedEnergy + abs(importedHour)
                autoconsumedEnergy = autoconsumedEnergy + data0n[1]            
        except:
            logging.debug("registro incorrecto")
            decodedOk = 0
        
    logging.debug("imporetedEnergy: " + str(imporetedEnergy))
    logging.debug("autoconsumedEnergy: " + str(autoconsumedEnergy))
    logging.debug("exportedEnergy: " + str(exportedEnergy))

    if(timeOk == 1 and decodedOk == 1):
        reading_register_[position]["imported"] = imporetedEnergy
        reading_register_[position]["autoconsumed"] = autoconsumedEnergy
        reading_register_[position]["exported"] = exportedEnergy
        reading_register_[position]["ultima"] = data0n[0] 
        
        emoncms_tx(position)
    
    # logging.debug(register)

''' ver reading_register con formato json
cat registers/reading_register.txt | python -m json.tool
'''
def abrir_reading_register():
    rr_path = "registers/reading_register.txt"
    lectura=open(rr_path, "r", encoding="utf-8")
    data = json.load(lectura)
    lectura.close()
    return data

def save_reading_register(register_):
    rr_path = "registers/reading_register.txt"
    writing =open(rr_path, "w", encoding="utf-8")
    json.dump(register_,writing)
    writing.close()

'''comprobar_consulta
comprobar que los formatos son correctos antes de enviarlos a procesar
data_: datos leidos en json(los 2 feedId)
rr_index: indice del registro de cliente (reading_register_)
comprobar que hay un numero de registros mínimo

register del reading_register_  :
{"name":"jesus","key":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","autoconsumed": 1.1,"exported": 1.1,"imported": 1.1,"ultima": "2022-05-30T20:00:00+02:00"}
<class 'dict'>

'''
def comprobar_consulta(data_, rr_position):  #reading register position, objeto datetime.datetime 
    logging.debug("comprobar_consulta()")
    
    consultaOk = 1;
    try:
        data0 = data_[0]["data"]
        data1 = data_[1]["data"]
    except:
        logging.warning("Error en el formato de los datos recibidos")
        consultaOk = 0
        
    if(consultaOk == 0):
        consultaOk = 0
    elif((type(data0) != type(list())) or (type(data1) != type(list()))):
        consultaOk = 0;
        logging.warning("Error type list")
    elif ((len(data0) < 4) or (len(data1) < 4)):
        consultaOk = 0;
        logging.warning("Error longitud < 4")
    else:
        consultaOk = 1;
        
    if(consultaOk == 1):
        valid_power_data = {}
        for x in data0:
            try:
                index = data0.index(x)
                logging.debug("++++ Procesado de la posicion: "+ str(index))
                logging.debug(x)
                logging.debug(data1[index])
            except:
                logging.warning("Error en el calculo de los datos")
                consultaOk = 0
            if(consultaOk == 1):
                procesar_lectura(x,data1[index],rr_position)
            
def formato_lectura(text):
    try:
        data = json.loads(text)
    except:
        data = []
    return data
'''
datos necesarios para la consulta
---------------------------------
http://direccion_del_servidor.com/feed/data.json?ids=45,40&start=2022-05-30 20:00&end=now&interval=3600&average=0&timeformat=iso8601&skipmissing=0&limitinterval=0&delta=1,1&apikey=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

emonServer = "direccion_del_servidor.com"
feedId="33"
startDateQ="21-05-2022 10:00"
endDateQ="2022/04/09"
userKey = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

https://docs.python.org/3/library/datetime.html#datetime-objects
'''

def consulta_de_consumos(position):
    emonServer = parser.get('emoncms_server','emon_ip')
    # feedId="45,40"                      # consumo: 45. generacion 40    
    feedId = reading_register_[position]["feed"]
    userKey = reading_register_[position]["key"]
    startDateQ=""
    # last datetime (registered datetimeformat)
    lastDatetimeD = isoformatD(x["ultima"])   #tiempo de la última lectura del query anterior
    logging.debug("lastDatetimeD ---> " + str(lastDatetimeD) )
    end_date_d = datetime.now()
    delta= timedelta(days=20)
    
    if(lastDatetimeD.replace(tzinfo=None) + delta <= end_date_d):
        lastDatetimeD = end_date_d - delta # star date datetime(format)
        
    # Se parte de lastDatetimeD
    star_hour_str = str(lastDatetimeD.hour) + ":00" 
    if (lastDatetimeD.hour <= 9):
        star_hour_str = "0" + str(lastDatetimeD.hour) + ":00"
    star_day_str = str(lastDatetimeD.day)
    if (lastDatetimeD.day <= 9):
        star_day_str = "0" + str(lastDatetimeD.day)    
    star_month_str = str(lastDatetimeD.month)
    if (lastDatetimeD.month <= 9):
        star_month_str = "0" + str(lastDatetimeD.month)
    startDateQ = str(lastDatetimeD.year) + "-" + star_month_str + "-" + star_day_str + "T" + star_hour_str

    '''  
    http://direccion_del_servidor.com/feed/data.json?id=33&start=21-05-2022 10:00&end=now&interval=3600&average=0&timeformat=excel&skipmissing=0&limitinterval=0&delta=1&apikey=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    '''
    url = "http://"
    url += emonServer
    url += "/feed/data.json?ids="
    url += feedId
    url += "&start="
    url += startDateQ
    url += "&end=now&interval=3600&average=0&timeformat=iso8601&skipmissing=0&limitinterval=0&delta=1,1&apikey="
    url += userKey
       
    logging.info(url)
    
    # Consulta de los consumos
    payload={}

    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    response_text = response.text
    return response_text

    
#************************
#** LOGICA DE PROCESO ***
#************************
# mqtt y tiempo de ejecucion
parser.read('config_autoconsumido.ini')


'''Cada x en reading_register_
-----------------------------
reading_register es un fichero con los datos de cada usuario que incluye los datos de la última lectura valida
El formato es: Lista de diccionarios
cada elemento del listado:
[{"name":"jesus","key":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx","autoconsumed": 1.1,"exported": 1.1,"imported": 1.1,"ultima": {"year": 2022, "month": 5, "day": 24, "hour": 20, "minute": 0}}]
<class 'dict'>

La consulta a emonCms debe tener el siguiente formato
http://direccion_del_servidor.com/feed/data.json?ids=33,34&start=21-05-2022 10:00&end=now&interval=3600&average=0&timeformat=excel&skipmissing=0&limitinterval=0&delta=1,1&apikey=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

datos necesarios para la consulta
---------------------------------
emonServer = "direccion_del_servidor.com"
feedId="33,34"
startDateQ="21-05-2022 10"
userKey = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
La consulta se hace hasta el momento actual
'''
reading_register_ = abrir_reading_register()

for x in reading_register_:
    rr_index = reading_register_.index(x) #reading_register_ index
    response = consulta_de_consumos(rr_index)
    response_txt = response      #respuesta en texto de la consulta
    lastDatetimeI = x["ultima"] #tiempo de la última lectura del query anterior
    # logging.debug(response_txt)
    # logging.debug(type(response_txt))# <class 'str'>
    data_red = formato_lectura(response_txt) #devuelve la lectura en json
    
    # data_red: datos leidos en json(los 2 feedId)
    # rr_index: indice del registro de cliente (reading_register_)
    # ultima lectura valida del query anterior (datetime.datetime)
    comprobar_consulta(data_red,rr_index)

save_reading_register(reading_register_)


    





