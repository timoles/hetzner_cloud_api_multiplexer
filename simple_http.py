#!/usr/bin/env python3
"""
Very simple HTTP server in python for logging requests
Usage::
    ./server.py [<port>]
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import os
import subprocess
from hcloud import Client
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
global verbose
global db_connection


class S(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        f = open("./parts/" + self.path, "rb")
        out = f.read()
        print(out)
        f.close()
        self.wfile.write(out)

    def do_POST(self):
        content_length = 0
        try:
            content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
        except:
            message = "Warning, content-length was wrong. We correct it to zero"  # TODO don't correct like that, handle it properly
            print('\033[93m' + "[-] " + message + '\033[0m')
            content_length = 0
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))

        body = post_data.decode('utf-8')
        position = body.find('hostname=')
        hostname = body[position + len("hostname="):]
        position = hostname.find('&')
        hostname = hostname[:position]
        if db_check_if_id_exists(self.path[1:]):
            if check_if_file_exists("parts/" + hostname):
                print(str(self.headers["Host"]))
                user = "root"
                ip = self.client_address[0]
                scp_path = "/root/results/"
                scp_dest = "./results/"
                p = subprocess.Popen(["scp", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-r", user + "@" + ip + ":" + scp_path, scp_dest])
                sts = os.waitpid(p.pid, 0)
                print("Copy done")
                client = Client(token=configVars["hetzner_cloud_api_key"])  # Please paste your API token here between the quotes
                servers = client.servers.get_all()
                for server in servers:
                    print("Found server: " + server.public_net.ipv4.ip)
                    if server.public_net.ipv4.ip == ip:
                        client.servers.delete(server)
                        break
                print("Done")  # TODO also set active status to zero in DB
        else:
            print("Got message for part_id that does not exist")

        self._set_response()
        self.wfile.write(b"")


def connect_to_db():
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
    db_connection = {"conn": conn, "metadata": metadata}
    return db_connection


def db_check_if_id_exists(test_part_id):
    parts_table = Table("parts_table", db_connection["metadata"], autoload=True)
    print("timo")
    s = select([parts_table]).where(parts_table.c.part_id == test_part_id)
    for row in db_connection["conn"].execute(s):
        return True  # TODO make this call only fetch first result and handle accordingly
    return False

def check_if_file_exists(filePath):
    '''
    Check if a file exists
    '''
    if os.path.isfile(filePath):
        return True
    else:
        return False


def handle_error(message, e, quit):
    '''
    Takes Error message and error and prints it with verbose option and system exit option
    '''
    print('\033[91m' + "[-] " + message + '\033[0m')
    if verbose and e:
        e.print_exc()
    if quit:
        sys.exit()


def load_config(configPath):
    '''
    Load a yaml config file
    '''
    if not check_if_file_exists(configPath):
        handle_error("Config path not correct", None, True)

    with open(configPath, 'r') as stream:
        try:
            global configVars
            configVars = yaml.safe_load(stream)  # alternatively load(stream) (if you need to load serialized objects)
        except yaml.YAMLError as exc:
            handle_error("Parsing of yaml file failed", exc, True)


def run(server_class=HTTPServer, handler_class=S, port=8080):
    global db_connection
    global verbose
    db_connection = connect_to_db()
    verbose = True
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--configPath", type=str, help="Path to yaml config file", required=True)
    argparser.add_argument("--port", type=int, help="Port on which the server opens", required=True, default=80)
    argparser.add_argument("--verbose", type=bool, help="Verbose mode", const=True, default=False, nargs="?")
    args = argparser.parse_args()
    verbose = args.verbose

    load_config(args.configPath)
    
    run(port=int(args.port))
