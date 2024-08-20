import socket
import numpy as np
import binascii
import yaml
from time import sleep
import paho.mqtt.client as mqtt

with open("C:/Users/joans/Documents/GitHub/HA-MyScript/custom_components/Smartdomo.yaml", "r") as f:   
    Smartdomo_Config = yaml.safe_load(f)
DebugFlag = Smartdomo_Config["DebugFlag"]
if DebugFlag: print('DebugFlag: '+str(DebugFlag))
Smartdomo_IP = Smartdomo_Config["Smartdomo_IP"]
if DebugFlag: print('Smartdomo_IP: '+Smartdomo_IP)
MQTT_Broker_IP = Smartdomo_Config["MQTT_Broker_IP"]
if DebugFlag: print('MQTT_Broker_IP: '+MQTT_Broker_IP)
MQTT_Username = Smartdomo_Config["MQTT_Username"]
if DebugFlag: print('MQTT_Username: '+MQTT_Username)
MQTT_Password = Smartdomo_Config["MQTT_Password"]
if DebugFlag: print('MQTT_Password: '+MQTT_Password)

#Variable Timer para Lectura de Datos Smartdomo
Timer = 0
  
#Arreglo para almacenar estado puertos virtuales Smartdomo
Vport = np.array([
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,],
[0, 0, 0, 0, 0, 0, 0, 0,]
],np.ubyte)

#Variable para almacenar estado previo de los puertos y detectar cambios de estado
VportStrPrev = ''

# Funcion envio proceso resulado comando scada v que lee con un solo comando 24 puertos virtuales
def SendCommandSCADA_v():
    comando = "scada v\r\n"
    if DebugFlag: print(comando)
    #implementar try except y manejar adecuadamente errores de conexion
    #try:
    TCP_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCP_Socket.connect((Smartdomo_IP,23))
    RxData = TCP_Socket.recv(1024)
    #print(RxData.decode('ascii','ignore'))
    TCP_Socket.send(b"\r\n")
    #print(RxData.decode('ascii','ignore'))
    TCP_Socket.send(comando.encode('ascii'))
    sleep(0.1)
    RxData = TCP_Socket.recv(1024)
    RxDataString = RxData.decode('ascii','ignore')
    if DebugFlag: print(RxDataString)
    TCP_Socket.send(b"exit\r\n")
    #print(RxData.decode('ascii','ignore'))
    TCP_Socket.shutdown(socket.SHUT_RDWR)
    TCP_Socket.close()
    RxIndex = RxDataString.find("#50:") 
    # validar que efectivamente se recibio respuesta antes de seguir con proceso, 
    # implementar contador de re-intentos y matar la conexion al 3ro
    # retornar dicho estado en caso de falla para para actualizar estado del sistema en superloop
    if DebugFlag: print("Index RxDataString comando scada #50: ", RxIndex)
    VPortsString = ''
    if RxIndex > 1:
        for x in range(RxIndex+4, RxIndex+52): 
            VPortsString = VPortsString + RxDataString[x]
        if DebugFlag: print('Trama solo resultado comando scada: ',VPortsString)
        DecodeSCADA_v(VPortsString)
        return True
    else:
        if DebugFlag: print('\033[1;31mFalla de comando scada!!!')
        return False

# Funcion que decodifica el resultado del comando scada v y lo guarda en el array VPort
def DecodeSCADA_v(VString):
    global Vport
    global VportStrPrev

    if VString != VportStrPrev:
        if DebugFlag: print('Prcesando Cambios en Puertos Virtuales')
        VportStrPrev = VString
        for v in range(0,24):
            VportHexStr = VString[v*2]+VString[v*2+1]
            #VportTempInt = bin(int(VportTempStr, 16)).zfill(8)
            VportInt = "{0:08b}".format(int(VportHexStr, 16))
            VportBinStr = str(VportInt)
            #print('Estado Puerto Virtual',i,':'+VportHexStr,VportBinStr)
            for bit in range(0,8):
                #print('Estado Puerto Virtual',i,j,': '+VportBinStr[7-j])
                Vport[v,bit] = VportBinStr[7-bit]
                MQTT_Topic_ESTADO = 'SMARTDOMO/ESTADO/V'+str(v)+'.'+str(bit)
                if Vport[v,bit]:
                    if DebugFlag: print('Update Salida Puerto Virtual',v,bit,'ON')
                    MQTT_client.publish(MQTT_Topic_ESTADO,"1")
                else:
                    if DebugFlag: print('Update Salida Puerto Virtual',v,bit,'OFF')
                    MQTT_client.publish(MQTT_Topic_ESTADO,"0")

        if DebugFlag: print('Estado Actual Puertos Virtuales 0 a 23',Vport)
    else:
        if DebugFlag: print('No hay Cambios en Puertos Virtuales')

def SendCommandPORT_v(Vport, bit, acction):
    comando = "port w v " + Vport + " " + bit +" " + acction + "\r\n"
    #implementar try except y manejar adecuadamente errores de conexion
    #try:
    TCP_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCP_Socket.connect((Smartdomo_IP,23))
    RxData = TCP_Socket.recv(1024)
    #print(RxData.decode('ascii','ignore'))
    TCP_Socket.send(b"\r\n")
    #print(RxData.decode('ascii','ignore'))
    TCP_Socket.send(comando.encode('ascii'))
    RxData = TCP_Socket.recv(1024)
    if DebugFlag: print('Enviando comando port w v'+RxData.decode('ascii','ignore'))
    TCP_Socket.send(b"exit\r\n")
    #print(RxData.decode('ascii','ignore'))
    TCP_Socket.shutdown(socket.SHUT_RDWR)
    TCP_Socket.close()
    #except print("Error al enviar comando"):
    #    pass

def on_message(client, userdata, message):
    if DebugFlag: print("message received: " ,str(message.payload.decode("utf-8")))
    if DebugFlag: print("message topic = ",message.topic)
	
    for v in range(0,24):
        for bit in range(0,8):
            MQTT_Topic_CONTROL = 'SMARTDOMO/CONTROL/V'+str(v)+'.'+str(bit)
            MQTT_Topic_ESTADO = 'SMARTDOMO/ESTADO/V'+str(v)+'.'+str(bit)

            if message.topic == MQTT_Topic_CONTROL:
                if message.payload.decode("utf-8") == '0':
                    if DebugFlag: print('Salida Puerto Virtual',v,bit,'OFF')
                    client.publish(MQTT_Topic_ESTADO,"0")
                    SendCommandPORT_v(str(v),str(bit),'c')
                if message.payload.decode("utf-8") == '1':
                    if DebugFlag: print('Salida Puerto Virtual',v,bit,'ON')
                    client.publish(MQTT_Topic_ESTADO,"1")
                    SendCommandPORT_v(str(v),str(bit),'s')

def check_mqtt_connection_status(client, userdata, flags, rc):
    if rc != 0:
        print("Connection to MQTT broker failed with result code", rc)
        raise Exception("Error: Connection to MQTT broker failed")
    print("Connected to MQTT broker successfully")

def retry_mqtt_connection(client, broker_ip, username, password, n_attempts=5, wait_time=2):
    for i in range(n_attempts):
        try:
            client.username_pw_set(username, password)
            client.connect(broker_ip)
            sleep(0.1)
            for v in range(0,24):
                for bit in range(0,8):
                    MQTT_Topic_CONTROL = 'SMARTDOMO/CONTROL/V'+str(v)+'.'+str(bit)
                    client.subscribe(MQTT_Topic_CONTROL)
            client.loop_start()
            client.publish("SMARTDOMO/ESTADO/SERVICIO","OnLine")
            client.on_connect = check_mqtt_connection_status
            break
        except Exception as e:
            if i == n_attempts - 1:
                raise Exception("Error: MQTT connection failed after multiple attempts")
            print("Error: ", e)
            print("Retrying in {} seconds".format(wait_time))
            sleep(wait_time)


MQTT_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1) #create new instance
retry_mqtt_connection(MQTT_client, MQTT_Broker_IP, MQTT_Username, MQTT_Password)

while True:
    MQTT_client.on_message = on_message
    sleep(0.1)
    Timer = Timer + 1
    if Timer > 30 :
        if DebugFlag: print('Enviando Comando scada v ...')
        SendCommandSCADA_v()
        #aumentar verificacion de resultado del comando scada y en funcion a eso actualiar el estado del sistema
        MQTT_client.publish("SMARTDOMO/ESTADO/SERVICIO","Ok")
        Timer = 0
