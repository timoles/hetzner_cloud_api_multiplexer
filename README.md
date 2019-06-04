# Project

This Project takes a list with domain names and slices it. It then deploys droplets which download their respective slice. 
After that commands are executed with cloud-init (e.g. nmap scan). After the cloud-init finishes it calls back to simple_http.py. 
After the call back simple_http.py downloads the results and deletes the droplet.

## Setup 

Clone and install hcloud from Hetzner (TODO link)

Insert your Hetzner API token in simple_http.py (Line 55)

Deploy everything on an internet reachable system!

## Infrastructure

### create_server.py

Takes a domain list as input. Slizes the domain list and creates a droplet for each slize. (Careful: Default droplet limit of 10 on Hetzner!)

Insert the name of your SSH key you connected to your Hetzner cloud workspace (The one which also has the API key.)
### simple_http.py

After the cloud-init is done with all provides arguments it phones home to the server it was started from. 
Simple_http recieves this POST request and copys the results from the deployed system.
After that it deletes the droplet.

### delete_all_servers

Just for testing/cleanup purpose. Deletes all droplets in the workspace which the API token is connected to.

(In order to work you need to insert your API token there)