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

class S(BaseHTTPRequestHandler):
    
    def check_if_file_exists(self, filePath):
        '''
        Check if a file exists
        '''
        if os.path.isfile(filePath):
            return True
        else:
            return False


    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))

        body = post_data.decode('utf-8')
        position = body.find('hostname=')
        hostname = body[position + len("hostname="):]
        position = hostname.find('&')
        hostname = hostname[:position]
        if self.check_if_file_exists("parts/" + hostname):
            print(str(self.headers["Host"]))
            user = "root"
            ip = self.client_address[0]
            scp_path = "/root/results/"
            scp_dest = "./results/"
            p = subprocess.Popen(["scp", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-r", user + "@" + ip + ":" + scp_path, scp_dest])
            sts = os.waitpid(p.pid, 0)
            print("Copy done")
            client = Client(token=<YOUR_HETZNER_API_TOKEN)  # Please paste your API token here between the quotes
            servers = client.servers.get_all()
            for server in servers:
                print("Found server: " + server.public_net.ipv4.ip)
                if server.public_net.ipv4.ip == ip:
                    client.servers.delete(server)
                    break            
            print("Done")

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=S, port=8080):
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
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
