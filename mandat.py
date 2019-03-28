import ssl 
import asyncio 
import sys 
import configparser 
import os 

# Julien Garderon, mars 2019 
# https://github.com/JGarderon/Mandat 
# Fonctionnel à partir de Python 3.7 (mots-clé async/await) 

Mandat_type = {
	"port_entrant": int, 
	"port_sortant" : int, 
	"client_tls" : bool 
} 

Mandats_liaisons = {} 
Mandats = [] 

def log(*a, **b): 
	print( *a, **b )  

class Paire: 

	def __init__(self, client_r, client_w): 
		self.client_r = client_r 
		self.client_w = client_w 
		self.service_r = None 
		self.service_w = None 

	async def desservir(self, port_sortant): 
		self.service_r, self.service_w = await asyncio.open_connection( 
			'127.0.0.1', 
			port_sortant 
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
		port_entrant = obj_conn.client_w.get_extra_info('socket').getsockname()[1] 
		await obj_conn.desservir( Mandats_liaisons[port_entrant] )  
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
		log( ">> err 1", err ) 
		# si besoin de clôture le serveur de mandat ici ? 
		writer.close() 

async def lancer_individuellement(mandat): 
	if mandat["client_tls"] is True: 
		ssl_contexte = ssl.SSLContext( 
			ssl.PROTOCOL_TLS_SERVER 
		) 
		ssl_contexte.load_cert_chain( 
			'./server.pem' 
		) 
		ssl_contexte.check_hostname = False 
	else: 
		ssl_contexte = None 
	log( 
		">> lancement d'un mandat (port %s)" 
		% mandat["port_entrant"] 
	) 
	return await asyncio.start_server(
		accepter, 
		'', 
		mandat["port_entrant"], 
		ssl = ssl_contexte 
	) 

async def resoudre(): 
	global Mandats 
	while True: 
		for mandat in Mandats: 
			await mandat["serveur"].start_serving() 

async def lancer(): 
	global Mandats 
	for cle, mandat in enumerate( Mandats ): 
		serveur = await lancer_individuellement( mandat ) 
		Mandats[cle]["serveur"] = serveur 
		Mandats_liaisons[mandat["port_entrant"]] = mandat["port_sortant"] 
	await resoudre() 

def preparer(): 
	global Mandats 
	try: 
		if len(sys.argv)<2: 
			raise Exception( 
				"vous devez indiquer un fichier "
				+"de configuration"
			) 
		configuration_chemin = sys.argv[1] 
		if not os.path.isfile( configuration_chemin ): 
			raise Exception( 
				"le fichier de configuration indiqué "
				+"n'est pas accessible" 
			) 
		log( 
			">> compréhension du fichier de configuration "
			+"'%s'" % configuration_chemin 
		)
		configurateur = configparser.ConfigParser() 
		configurateur.read( configuration_chemin ) 
		_cherche = Mandat_type.keys() 
		for mandat_nom in configurateur: 
			if mandat_nom == "DEFAULT": 
				continue 
			set_mandat = set( configurateur.options(mandat_nom) ) 
			Mandats.append( 
				{item:Mandat_type[item]( configurateur.get( mandat_nom, item ) ) for item in _cherche if item in set_mandat} 
			) 
		asyncio.run( lancer() ) 
	except Exception as err: 
		log( "err 2", err ) 
		pass 

if __name__=="__main__": 
	preparer() 

