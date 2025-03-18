import socket
import os
from dotenv import load_dotenv
load_dotenv(".env")

def label_printer_connection(zpl_string, printer_address, printer_port):
	try:
		# encoded label string
		label =  zpl_string.encode(encoding="ascii",errors="ignore")

		# creating the socket connection and sending the data to the printer
		mysocket = socket.socket(socket.af_inet,socket.sock_stream)
		mysocket.connect((printer_address, printer_port)) #connecting to host
		mysocket.send(label) #using bytes
		mysocket.close () #closing connection

		return f"{zpl_string}\n sent to printer: {printer_address}:{printer_port}"

	except Exception as ex:
		return f"could not send data to printer: {printer_address}:{printer_port} due to:\n {ex}"
