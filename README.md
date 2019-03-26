# Mandat
Un script Python >=3.7 pour délivrer un service mandataire TCP asynchrone (contexte SSL ou non). 

---

Lance un serveur en écoute sur le port 8443 vers l'extérieur, et rebascule le contenu binaire récupéré des clients vers un service tiers (ici le port 8000 ; la récupération se fait dans les sens). 

Pour les tests, vous pouvez utiliser dans une autre console, le serveur "automatique" de Python de distribution d'un dossier : 
$ python3.7 -m http.server 

... qui écoute sur le port 8000.
