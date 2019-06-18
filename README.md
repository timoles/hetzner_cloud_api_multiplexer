# Project

Warning: This Repository is a PoC, under ideal circumstances everything (should) works, but this approach is more or less abandoned due to the fact that I know plan to do everything via the tools provided by aws.

This Project takes a list with domain names and slices it. It then deploys droplets which download their respective slice. 
After that commands are executed with cloud-init (e.g. nmap scan). After the cloud-init finishes it calls back to simple_http.py. 
After the call back simple_http.py downloads the results and deletes the droplet.

## Setup 

Clone and install hcloud from Hetzner (TODO link)

Insert your Hetzner API token in simple_http.py (Line 55)

Deploy everything on an internet reachable system!

## Usage

* Only usable on an www reachable host (Port 80)

* Install the python hcloud from Hetzner

* Fill out the config.yaml

* With the cloud-init you are able to execute commands during the droplet creation (e.g. install dependencies and then run a nmap scan). When the cloud-init commands are all completed the cloud-init makes a POST request with some Metadata to the URL given in the config. After this request the Tools knows that the commands are completed and results are saved in the result folder (TODO exact location). The server is then trying to download the files with scp and afterwards destroys the droplet.

## Infrastructure

### create_server.py

Takes a domain list as input. Slizes the domain list and creates a droplet for each slize. (Careful: Default droplet limit of 10 on Hetzner!)


Insert the name of your SSH key you connected to your Hetzner cloud workspace (The one which also has the API key.)
### simple_http.py

After the cloud-init is done with all provides arguments it phones home to the server it was started from. 
Simple_http recieves this POST request and copys the results from the deployed system.
After that it deletes the droplet.

### delete_all_servers.py

Just for testing/cleanup purpose. Deletes all droplets in the workspace which the API token is connected to.

(In order to work you need to insert your API token there)

## Features TODO

* Better state handling

* Inform about old instances

* Better handling of max machines (put in config aswell)

* Shared class for the sql stuff

* check for sqli

* check out kubernetes

* Error handling if something doesn't work (e.g. phone_home is not working, or scp has problems, ...)