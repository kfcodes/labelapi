import socket
import os
from dotenv import load_dotenv
load_dotenv(".env")

def print_zpl_label(label_string, printer_address, printer_port):
	try:
		# encoded label string
		label =  label_string.encode(encoding="ascii",errors="ignore")

		# creating the socket connection and sending the data to the printer
		mysocket = socket.socket(socket.af_inet,socket.sock_stream)
		mysocket.connect((printer_address, printer_port)) #connecting to host
		mysocket.send(label) #using bytes
		mysocket.close () #closing connection

		return f"printed the pallet label on printer: {printer_address}, {printer_port}"

	except Exception as ex:
		return str(f"could not print label on {printer_address}, port: {printer_port}due to the following: \n {ex}")
