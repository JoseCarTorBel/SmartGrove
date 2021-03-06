import socket
import subprocess
import logging
from datetime import datetime
import I2C_LCD_driver
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from GoogleDrive import GoogleDrive


# LCD lib
lcd=I2C_LCD_driver.lcd()


# GoogleDrive lib
goodr = GoogleDrive()

# Logging conf
logging.basicConfig( level=logging.DEBUG, filename='/home/pi/SmartGrove/Raspberry/Cliente.log')

# Bluetooth conf
serverMACAddress = 'F0:08:D1:C8:DB:FE'
port = 1
size=1024

# Objeto que guarda la trama recibida por el esp32
class Trama:
	hora=""
	temperatura=-1
	humedad=-1
	def __init__(self,hor,tem,hum):
		self.hora=hor
		self.temperatura=tem
		self.humedad=hum
	def getTrama(self):
		return [self.hora,self.temperatura,self.humedad]




logging.info("=========================================================================")
while(1):
	recibido=[]
	tramas=0
	try:
		s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

		logging.info("----------------------------------------------------")
		lcd.lcd_display_strings(str(datetime.now()), "ESPERANDO AL CLIENTE")
		logging.info(str(datetime.now())+" Raspberry> Intento conectarme al ESP32")

		s.connect((serverMACAddress,port))
		while 1:
			data = s.recv(size)
			if data:
				strData = data.decode("UTF-8")
				if('#' in strData):
					recibido.append(Trama(str(datetime.now()),int(strData.split("#")[0]),int(strData.split("#")[1])))
					tramas+=1

					logging.info(str(datetime.now())+" Raspberry> Recibido: "+strData)
					lcd.lcd_display_strings(str(datetime.now()), str(strData))
					s.send("ACK\n".encode("utf-8"))
					grupo=20
					if(tramas%grupo==0): # Esto lo hacemos para no saturar a peticiones la API ya que si no bloquea la conexion
						aux=grupo
						enviar=[]
						while(aux>0):
							enviar.append(recibido[tramas-aux].getTrama())
							aux-=1
						goodr.insertRows(enviar)
						logging.info(str(datetime.now())+" Raspberry> Subo datos al servidor")

		s.close() #fin while

	except KeyboardInterrupt: # Capturamos el CTRL+C para cerrar manualmente la conexion
		logging.info(str(datetime.now())+" Raspberry> Cierro conexion (CTRL-C)")
		lcd.lcd_display_strings(str(datetime.now()), "Cliente parado)")
		s.close()
		exit()
	except ConnectionResetError:  # Capturamos el reset de conexion
		logging.info(str(datetime.now())+" Raspberry> Cierro conexion")
		lcd.lcd_display_strings(str(datetime.now()), "Cierro conexion")
	except ConnectionRefusedError:# Capturamos el refused para que siga el bucle
		s.close()
		logging.info(str(datetime.now())+" Raspberry> Fallo")
		lcd.lcd_display_strings(str(datetime.now()), "Fallo")
		time.sleep(5)
	except TimeoutError:# Es posible que de timeoout conection
		s.close()
		logging.info(str(datetime.now())+" Raspberry> Fallo")
		lcd.lcd_display_strings(str(datetime.now()), "Fallo")
		time.sleep(5) 
	except: # Cualquier otra expecion abortara la ejecucion del programa
		lcd.lcd_display_strings(str(datetime.now()), "ERROR-> LOG")
		raise


