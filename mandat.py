import ssl 
import asyncio 

# Julien Garderon, mars 2019 
# https://github.com/JGarderon/Mandat 
# Fonctionnel à partir de Python 3.7 (mots-clé async/await) 

PORT_entrant = 8443  
PORT_sortant = 8000 

class Paire: 

	def __init__(self, client_r, client_w): 
		self.client_r = client_r 
		self.client_w = client_w 
		self.service_r = None 
		self.service_w = None 

	async def desservir(self): 
		global PORT_sortant 
		self.service_r, self.service_w = await asyncio.open_connection( 
			'127.0.0.1', 
			PORT_sortant 
		) 

	async def suivre(self, est_client): 
		if est_client: 
			lecteur = self.client_r 
			ecrivain = self.service_w 
		else: 
			lecteur = self.service_r 
			ecrivain = self.client_w 
		while True: 
			portion = await lecteur.read( 128 ) 
			if portion == b"": 
				break 
			ecrivain.write( 
				portion 
			) 
			await ecrivain.drain() 

	async def stopper(self): 
		self.client_w.close() 
		self.service_w.close() 

async def accepter(client_r, client_w): 
	try: 
		obj_conn = Paire( client_r, client_w ) 
		await obj_conn.desservir() 
		obj_conn.tache_client = asyncio.create_task( 
			obj_conn.suivre( True ) 
		) 
		obj_conn.tache_service = asyncio.create_task( 
			obj_conn.suivre( False ) 
		) 
		await obj_conn.tache_client 
		await obj_conn.tache_service 
		await obj_conn.stopper() 
	except ConnectionRefusedError as err: 
		print("err 1", err) 
		# si besoin de clôture le serveur de mandat ici ? 
		writer.close() 

async def lancer(ssl_contexte = None): 
	global PORT_entrant 
	if ssl_contexte is True: 
		ssl_contexte = ssl.SSLContext( 
			ssl.PROTOCOL_TLS_SERVER 
		) 
		ssl_contexte.load_cert_chain( 
			'./server.pem' # à modifier évidemment... 
		) 
		ssl_contexte.check_hostname = False 
	serveur = await asyncio.start_server(
		accepter, 
		'', 
		PORT_entrant, 
		ssl = ssl_contexte 
	) 
	async with serveur:
		await serveur.serve_forever()

asyncio.run( lancer( True ) ) # n'hésitez pas à signaler tout dysfonctionnement ! 

