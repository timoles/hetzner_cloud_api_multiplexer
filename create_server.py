"""Summary

Attributes:
    verbose (bool): Description
"""
import sys
import os
import string
import random
import yaml
import argparse
from hcloud import Client
from hcloud.images.domain import Image
from hcloud.server_types.domain import ServerType

from datetime import datetime, timedelta
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref

from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import select

global configVars
verbose = False


class TestError(Exception):
	pass


def handle_error(message, e, quit):
	'''
	Takes Error message and error and prints it with verbose option and system exit option
	
	Args:
	    message (TYPE): Description
	    e (TYPE): Description
	    quit (TYPE): Description
	'''
	print('\033[91m' + "[-] " + message + '\033[0m')
	if verbose and e != None:
		e.print_exc()
	if quit:
		sys.exit()


def message_positiv(message):
	'''
	Prints positive message (in green)
	
	Args:
	    message (TYPE): Description
	'''
	print('\033[92m' +"[+] " + message + '\033[0m')


def message_info(message):
	'''
	Prints info message
	
	Args:
	    message (TYPE): Description
	'''
	print("[*] " + message)


def message_warning(message):
	'''
	Prints red message
	
	Args:
	    message (TYPE): Description
	'''
	print('\033[93m' + "[-] " + message + '\033[0m')


def read_file(filePath):
	'''
	Read File
	
	Args:
	    filePath (TYPE): Description
	
	Returns:
	    TYPE: Description
	'''
	try:
		f = open(filePath, "r")
		out = f.read()
		f.close()
	except IOError as e:
		handle_error("filePath '{}' could not be found. exiting...".format(filePath), e, True)

	return out


def write_file(filePath, content):
	'''
	Read File
	
	Args:
	    filePath (TYPE): Description
	    content (TYPE): Description
	'''
	try:
		f = open(filePath, "w+")
		f.write(content)
		f.close()
	except IOError as e:
		handle_error("file could not be created, exiting...", e, True)


def read_file_by_line(filePath):
	'''
	Read File
	
	Args:
	    filePath (TYPE): Description
	
	Returns:
	    TYPE: Description
	'''
	try:
		f = open(filePath, "r")
		out = f.readlines()
		f.close()
	except IOError as e:
		handle_error("filePath '{}' could not be found. exiting...".format(filePath), e, True)

	return out


def check_if_file_exists(filePath):
	'''
	Check if a file exists
	
	Args:
	    filePath (TYPE): Description
	
	Returns:
	    TYPE: Description
	'''
	if os.path.isfile(filePath):
		return True
	else:
		return False


def load_config(configPath):
	'''
	Load a yaml config file
	
	Args:
	    configPath (TYPE): Description
	'''
	if not check_if_file_exists(configPath):
		handle_error("Config path not correct", None, True)

	with open(configPath, 'r') as stream:
		try:
			global configVars
			configVars = yaml.safe_load(stream)  # alternatively load(stream) (if you need to load serialized objects)
		except yaml.YAMLError as exc:
			handle_error("Parsing of yaml file failed", exc, True)


def id_generator(size=100, chars=string.ascii_uppercase + string.digits):
	'''
	Generate a random id
	
	Args:
	    size (int, optional): Description
	    chars (TYPE, optional): Description
	
	Returns:
	    TYPE: Description
	'''
	return ''.join(random.choice(chars) for _ in range(size))


def connect_to_db():
	"""Summary
	
	Returns:
	    TYPE: Description
	"""
	db_path = "./test.db"  # TODO config path
	engine = create_engine('sqlite:///{}'.format(db_path), echo=False)
	metadata = MetaData(bind=engine)

	Table('parts_table', metadata,
			Column('id', Integer, primary_key=True, autoincrement=True),
			Column('part_id', String),
			Column('server_ip', Integer),
			Column('callback_ip', Integer),
			Column('in_progress', Integer),
			Column('time_stamp', DateTime),
			Column('project_name', String),)
	# Create table
	metadata.create_all()

	# create a database connection
	conn = engine.connect()
	db_ctx = {"conn": conn, "metadata": metadata}
	return db_ctx


def print_active_parts_runtime(conn):
	"""
	Print the runtime of all running parts servers in hours

	Args:
	    conn (TYPE): Connection to the database
	"""
	message_info("Runtime of active parts:")
	message_info("Part | Runtime (h) | Part IP")
	s = select([parts_table]).where(parts_table.c.in_progress == 1)
	for row in conn.execute(s):
		# print(type(row["time_stamp"]))
		# delta = timedelta(1, row["time_stamp"])
		delta = datetime.now() - row["time_stamp"]
		message_info("{} | {} | {}".format(row["part_id"], round(delta.seconds / 60 / 60, 2), row["server_ip"]))
	else:
		message_info("No active parts")


if __name__ == "__main__":
	try:
		raise TestError()
		db_ctx = connect_to_db()
		parts_table = Table("parts_table", db_ctx["metadata"], autoload=True)
		ins_parts = parts_table.insert()

		# Setup
		servers = []
		ips = []
		argparser = argparse.ArgumentParser()
		argparser.add_argument("--configPath", type=str, help="Path to yaml config file", required=True)
		argparser.add_argument("--verbose", type=bool, help="Verbose mode", const=True, default=False, nargs="?")
		argparser.add_argument("--projectName", type=str, help="Path to yaml config file", required=True)
		args = argparser.parse_args()
		verbose = args.verbose

		# Load config
		load_config(args.configPath)
		project_name = args.projectName

		# Read and clean input list
		input_list = read_file_by_line(configVars["input_list_path"])

		print_active_parts_runtime(db_ctx["conn"])

		splits = configVars["input_list_machine_factor"]
		input_list_parts = []
		part_ids = []
		while input_list:
			input_list_part = input_list[:splits]
			part_id = id_generator(size=40)
			part_ids.append(part_id)
			write_file("./parts/" + part_id, ''.join(str(e) for e in input_list_part))
			input_list_parts.append(input_list_part)
			input_list = input_list[splits:]
		MAX_PARTS = 9
		if len(input_list_parts) > MAX_PARTS:
			handle_error("To many parts. Max parts {}, Current parts: {}".format(MAX_PARTS, len(input_list_parts)), None, True)
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

			response = client.servers.create(name=part_id, server_type=ServerType("cx11"), image=Image(name="ubuntu-18.04"),
												user_data=user_data_part, ssh_keys=[client.ssh_keys.get_by_name("tmp")])
			servers.append(response.server)
			exec_parts = ins_parts.values(part_id=part_id, server_ip=response.server.public_net.ipv4.ip, in_progress=1, time_stamp=datetime.now(), project_name=project_name, callback_ip=host_ip)
			try:
				db_ctx["conn"].execute(exec_parts)
			except Exception as e:
				print(e)

		for server in servers:
			print(server.public_net.ipv4.ip)

	except KeyboardInterrupt:
		handle_error("Keyboard Interrupt detected, exiting...", None, True)
	except KeyError as e:
		handle_error("Error with the yaml config file. Key missing: {}".format(str(e)), e, True)
	except TestError as e:
		handle_error("hi", e, True)