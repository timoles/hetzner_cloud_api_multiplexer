from hcloud import Client

client = Client(token=<YOUR_HETZNER_API_TOKEN>)  # Please paste your API token here between the quotes
servers = client.servers.get_all()
for server in servers:
	print(server.id)
	
	#print(server.__dict__)
	#print(dir(server.get_actions))
	print(server.public_net)
	print(server.public_net.ipv4.ip)
	test = client.servers.delete(server)
