import sys
import os
import string
import random
import yaml
import argparse
import threading
from hcloud import Client
from hcloud.images.domain import Image
from hcloud.server_types.domain import ServerType
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading
# https://stackoverflow.com/questions/14088294/multithreaded-web-server-in-python/51559006#51559006

global configVars


class Handler(BaseHTTPRequestHandler):

	def do_GET(self):
		self.send_response(200)
		self.end_headers()
		self.wfile.write(b'Hello world\t' + threading.currentThread().getName().encode() + b'\t' + str(threading.active_count()).encode() + b'\n')


class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
	pass


def handle_error(message, e, quit):
	'''
	Takes Error message and error and prints it with verbose option and system exit option
	'''
	print('\033[91m' + "[-] " + message + '\033[0m')
	if verbose and e != None:
		e.print_exc()
	if quit:
		sys.exit()


def message_positiv(message):
	'''
	Prints positive message (in green)
	'''
	print('\033[92m' +"[+] " + message + '\033[0m')



def message_info(message):
	'''
	Prints info message
	'''
	print("[*] " + message)



def message_warning(message):
	'''
	Prints red message
	'''
	print('\033[93m' + "[-] " + message + '\033[0m')


def read_file(filePath):
	'''
	Read File
	'''
	try:
		f = open(filePath, "r")
		out = f.read()
		f.close()
	except IOError as e:
		handle_error("--filePath file could not be found. exiting...",e,True)

	return out


def write_file(filePath, content):
	'''
	Read File
	'''
	try:
		f = open(filePath, "w+")
		f.write(content)
		f.close()
	except IOError as e:
		handle_error("file could not be created, exiting...",e,True)


def read_file_by_line(filePath):
	'''
	Read File
	'''
	try:
		f = open(filePath, "r")
		out = f.readlines()
		f.close()
	except IOError as e:
		handle_error("--filePath file could not be found. exiting...",e,True)

	return out



def check_if_file_exists(filePath):
	'''
	Check if a file exists
	'''
	if os.path.isfile(filePath):
		return True
	else:
		return False


def load_config(configPath):
	'''
	Load a yaml config file
	'''
	if not check_if_file_exists(configPath):
		handle_error("Config path not correct", None, True)

	with open(configPath, 'r') as stream:
		try:
			global configVars
			configVars = yaml.safe_load(stream) # alternatively load(stream) (if you need to load serialized objects)
		except yaml.YAMLError as exc:
			handle_error("Parsing of yaml file failed", exc, True)



def id_generator(size=100, chars=string.ascii_uppercase + string.digits):
	'''
	Generate a random id
	'''
	return ''.join(random.choice(chars) for _ in range(size))


def start_server():
	# Setup stuff here...
	server.serve_forever()


if __name__ == "__main__":
	try:
		# Setup
		servers = []
		ips = []
		argparser = argparse.ArgumentParser()
		argparser.add_argument("--configPath", type=str, help="Path to yaml config file",nargs="+", required=True)
		argparser.add_argument("--verbose", type=bool, help="Verbose mode", const=True, default=False, nargs="?")
		args = argparser.parse_args()
		verbose = args.verbose

		# Load config
		load_config(args.configPath[0])
		
		# Read and clean input list
		input_list = read_file_by_line(configVars["input_list_path"])

		splits = configVars["input_list_machine_factor"]
		input_list_parts = []
		part_ids = []
		while input_list:
			input_list_part = input_list[:splits]
			part_id = id_generator(size=40)
			part_ids.append(part_id)
			write_file("./parts/"+part_id, ''.join(str(e) for e in input_list_part) )
			input_list_parts.append(input_list_part)
			input_list = input_list[splits:]
		
		# For every part we need to create a machine
		# Upload the part into the machine
		# Wait till machine is completely initialized
		# Run whatever script we want to run (with input_part_list as parameter e.g. nmap)
		# Wait till nmap is done and get the list (maybe with webhooks?) (we are able to call a URL as soon as cloud-init is done!)

		client = Client(token=configVars["hetzner_cloud_api_key"])  # Please paste your API token here between the quotes
		user_data_template = read_file(configVars["cloud_init_path"])
		
		import socket
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		host_ip = s.getsockname()[0]
		s.close()

		for part_id in part_ids:
			user_data_part = user_data_template
			user_data_part = user_data_part.replace("<host_ip>", host_ip) 
			user_data_part = user_data_part.replace("<part_id>", part_id)

			response = client.servers.create(name=part_id, server_type=ServerType("cx11"), image=Image(name="ubuntu-18.04"), user_data=user_data_part, ssh_keys=[client.ssh_keys.get_by_name("tmp")])
			servers.append(response.server) 
		
		for server in servers:
			print(server.public_net.ipv4.ip)
		
	except KeyboardInterrupt:
		handle_error("Keyboard Interrupt detected, exiting...", None, True)
	except KeyError as e:
		handle_error("Error with the yaml config file. Key missing: {}".format(str(e)), e, True)
