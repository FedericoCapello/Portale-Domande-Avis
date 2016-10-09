# Importa le librerie richieste
import os
import urlparse
import json
import urllib

from protorpc import messages
import logging

from google.appengine.api import users
from google.appengine.api import channel
from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers

import webapp2
import jinja2

# Carica JINJA per la gestione delle pagine HTML
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# Dizionario che collega la tipologia di ente al selfie di default se non specificato
DEFAULT_SELFIE = {
    'Test': 'img/drop.jpg',
    '': 'img/drop.jpg',
    'bicocca': 'img/drop.jpg',
    'Papa Gio': 'img/drop.jpg',
    'Bolognini': 'img/drop.jpg',
    'CA.RI.S.M.A.': 'img/drop.jpg',
    'Mascheroni': 'img/drop.jpg',
    'Leo da Vinci': 'img/drop.jpg',
    'Lussana': 'img/drop.jpg',
    'Salesiani': 'img/drop.jpg',
    'A.I.S.M.': 'img/drop.jpg',
    'A.I.S.M. Mi': 'img/drop.jpg',
    'A.I.S.M. Ge': 'img/drop.jpg',
    'A.I.S.M. Ba': 'img/drop.jpg',
    'A.I.S.M. Pc': 'img/drop.jpg'
}

# Dizionario che collega la tipologia di ente all'immagine di background
BACKGROUND_IMAGES = {
    'Test': 'img/avis.jpg',
    'bicocca': 'img/bicocca.jpg',
    '': 'img/avis.jpg',
    'Papa Gio': 'img/papa_giovanni.jpg',
    'Bolognini': 'img/bolognini.jpg',
    'CA.RI.S.M.A.': 'img/carisma.jpg',
    'Mascheroni': 'img/mascheroni.jpg',
    'Leo da Vinci': 'img/leonardo_da_vinci.jpg',
    'Lussana': 'img/lussana.jpg',
    'Salesiani': 'img/salesiani.jpg',
    'A.I.S.M.': 'img/aisma.jpg',
    'A.I.S.M. Mi': 'img/aisma.jpg',
    'A.I.S.M. Ge': 'img/aisma.jpg',
    'A.I.S.M. Ba': 'img/aisma.jpg',
    'A.I.S.M. Pc': 'img/aisma.jpg'
}

# Dizionario che collega la tipologia di ente alla sua denominazione estesa
ENTE_TO_STR = {
    'bicocca': "Universita' Bicocca",
    '': 'Pubblico',
    'Test': 'Pubblico',
    'Papa Gio': 'Osp. Papa Giovanni XXIII',
    'Bolognini': 'Osp. Bolognini',
    'CA.RI.S.M.A.': 'CA.RI.S.M.A',
    'Mascheroni': 'L. S. Mascheroni',
    'Leo da Vinci': 'Ist. L. Da Vinci',
    'Lussana': 'L. S. Lussana',
    'Salesiani': 'Ist. "Don Bosco" Treviglio',
    'A.I.S.M.': 'A.I.S.M.',
    'A.I.S.M. Mi': 'A.I.S.M. Milano',
    'A.I.S.M. Ge': 'A.I.S.M. Genova',
    'A.I.S.M. Ba': 'A.I.S.M. Bari',
    'A.I.S.M. Pc': 'A.I.S.M. Piacenza'

}

# Dizionario che collega la denominazione estesa di un ente al suo nome contratto
STR_TO_ENTE = {
    "Universita' Bicocca": "bicocca",
    "Pubblico": "",
    "": "",
    'Osp. Papa Giovanni XXIII': 'Papa Gio',
    'Osp. Bolognini': 'Bolognini',
    'CA.RI.S.M.A': 'CA.RI.S.M.A.',
    'L. S. Mascheroni': 'Mascheroni',
    'Ist. L. Da Vinci': 'Leo da Vinci',
    'L. S. Lussana': 'Lussana',
    'Ist. "Don Bosco" Treviglio': 'Salesiani',
    'A.I.S.M.': 'A.I.S.M.',
    'A.I.S.M. Milano': 'A.I.S.M. Mi',
    'A.I.S.M. Genova': 'A.I.S.M. Ge',
    'A.I.S.M. Bari': 'A.I.S.M. Ba',
    'A.I.S.M. Piacenza': 'A.I.S.M. Pc'

}

# Dizionario che collega url di un ente al suo nome contratto
URL_TO_ENTE = {
    'bicocca': 'bicocca',
    '': '',
    'hpg23': 'Papa Gio',
    'bolognini': 'Bolognini',
    'carisma': 'CA.RI.S.M.A.',
    'mascheroni': 'Mascheroni',
    'leodavinci': 'Leo da Vinci',
    'lussana': 'Lussana',
    'salesiani': 'Salesiani',
    'aism': 'A.I.S.M.',
    'aismmi': 'A.I.S.M. Mi',
    'aismge': 'A.I.S.M. Ge',
    'aismba': 'A.I.S.M. Ba',
    'aismpc': 'A.I.S.M. Pc'
}

# Dizionario che collega gli orientamenti EXIF alle trasformazioni da applicare
N_TO_T = {
    1: '',
    6: '',
    3: '',
    8: '',
    2: '',
    5: '',
    4: '',
    7: ''
}

N_TO_T_old = {
    1: '',
    6: '-r90',
    3: '-r180',
    8: '-r270',
    2: '-fv',
    5: '-r90-fv',
    4: '-r180-fv',
    7: '-r270-fv'
}

# Ritorna l'URL di base
def get_base_url():
    if os.environ[AUTH_DOMAIN] == "gmail.com":
        app_id = os.environ[APPLICATION_ID]
        return "https://" + app_id + ".appspot.com"
    else:
        return "https://" + os.environ[AUTH_DOMAIN]

# Modello di risposta OK
class OK(messages.Message):
    content = messages.StringField(1)


# Modello di Domanda per il datastore
class Domanda(ndb.Model):
    nome          = ndb.StringProperty()                    # Nome
    ente          = ndb.StringProperty()                    # Ente
    testo_domanda = ndb.StringProperty()                    # Testo della domanda se presente
    email         = ndb.StringProperty()                    # Email 
    selfie_key    = ndb.BlobKeyProperty()                   # Chiave del selfie. Permette di accedere al selfie
    audio_key     = ndb.BlobKeyProperty()                   # Chiave dell'audio. Permette di accedere all'audio
    orientation   = ndb.IntegerProperty(default=1)          # Orientamento dell'immagine
    stato         = ndb.IntegerProperty()                   # Stato della domanda. da 0 a 4
    data          = ndb.DateTimeProperty(auto_now_add=True) # Data di aggiunta della domanda


# Gestisce il caricamento di una domanda da parte di un utente
class InserisciDomandaHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        
            upload_audio, upload_selfie, nuova_domanda = None, None, None
            ente = STR_TO_ENTE[self.request.get('ente')]
            ori = 1

            logging.debug(self.request.get('testo'))

            testo_da_salvare = urllib.unquote(self.request.get('testo').encode('ascii')).decode('utf-8')
            nome_da_salvare = urllib.unquote(self.request.get('nome').encode('ascii')).decode('utf-8')
            # Inizializza i dati da inviare al moderatore per un aggiornamento istantaneo
            channel_data = {
                'nome': nome_da_salvare,
                'ente': ente,
                'email': self.request.get('email'),
                'stato': 2,
                'background_url': BACKGROUND_IMAGES['Test']
            }

            is_selfie, is_audio, is_text = False, False, False

            # Indici di dove si trovino l'audio e il selfie
            selfie_i = 0
            audio_i = 1

            # Se il testo inviato non e' vuoto allora c'e' il testo
            if len(testo_da_salvare) != 0:
                is_text = True


            # Se i file di upload sono 2 verifica dove sia l'audio e dove sia il selfie. Inoltre, controlla che i file siano giusti
            if len(self.get_uploads()) == 2:
                if 'audio' in self.get_file_infos()[1].content_type:
                    is_audio = True

                if 'image' in self.get_file_infos()[0].content_type:
                    is_selfie = True

                if 'audio' in self.get_file_infos()[0].content_type:
                    is_audio = True
                    audio_i = 0

                if 'image' in self.get_file_infos()[1].content_type:
                    is_selfie = True
                    selfie_i = 1

            # Se il file di upload e' 1 vedi se e' l'audio o il selfie
            elif len(self.get_uploads()) == 1:
                if 'audio' in self.get_file_infos()[0].content_type:
                    is_audio = True

                if 'image' in self.get_file_infos()[0].content_type:
                    is_selfie = True
            else:
                pass

            # Logga le informazioni

            if is_selfie:
                img = images.Image(blob_key=self.get_uploads()[selfie_i].key())
                img.rotate(0)
                img.execute_transforms(parse_source_metadata=True)
                metadata = img.get_original_metadata()
                try:
                    ori = int(metadata["Orientation"])
                except KeyError:
                    ori = 1


            # Se c'e' una domanda testuale
            if is_text:
                # Se, inoltre, ci sono 
                if is_audio and is_selfie:

                    # Trova l'audio e il selfie
                    upload_audio  = self.get_uploads()[audio_i]
                    upload_selfie = self.get_uploads()[selfie_i]

                    # Prepara una nuova domanda da inserire nel Datastore
                    nuova_domanda = Domanda(
                        nome          = nome_da_salvare,
                        email         = self.request.get('email'),
                        audio_key     = upload_audio.key(),
                        selfie_key    = upload_selfie.key(),
                        testo_domanda = testo_da_salvare,
                        orientation   = ori,
                        ente          = ente,
                        stato         = 2
                    )

                    # Aggiungi campi ai dati da inviare immediatamente al moderatore
                    channel_data['audio_key'] = str(upload_audio.key())
                    channel_data['testo_domanda'] = testo_da_salvare
                    channel_data['selfie_url'] = images.get_serving_url(upload_selfie.key(), crop=True, size=500) + N_TO_T[ori]

                # Se invece c'e' solo l'audio e non il selfie
                elif is_audio:

                    # Trova l'audio
                    upload_audio  = self.get_uploads()[0]

                    # Prepara una nuova domanda da inserire nel Datastore
                    nuova_domanda = Domanda(
                        nome          = nome_da_salvare,
                        email         = self.request.get('email'),
                        audio_key     = upload_audio.key(),
                        testo_domanda = testo_da_salvare,
                        ente          = ente,
                        stato         = 2
                    )

                    # Aggiungi campi ai dati da inviare immediatamente al moderatore
                    channel_data['audio_key'] = str(upload_audio.key())
                    channel_data['testo_domanda'] = testo_da_salvare
                    channel_data['selfie_url'] = DEFAULT_SELFIE["Test"]

                # Se invece c'e' solo un selfie
                elif is_selfie:

                    # Trova il selfie
                    upload_selfie = self.get_uploads()[0]

                    # Prepara una nuova domanda da inserire nel Datastore
                    nuova_domanda = Domanda(
                        nome          = nome_da_salvare,
                        email         = self.request.get('email'),
                        selfie_key    = upload_selfie.key(),
                        orientation   = ori,
                        testo_domanda = testo_da_salvare,
                        ente          = ente,
                        stato         = 2
                    )

                    # Aggiungi campi ai dati da inviare immediatamente al moderatore
                    channel_data['testo_domanda'] = testo_da_salvare
                    channel_data['selfie_url'] = images.get_serving_url(upload_selfie.key(), crop=True, size=500) + N_TO_T[ori]

                # Se, infine, c'e' solo il testo
                else:

                    # Prepara una nuova domanda da inserire nel Datastore
                    nuova_domanda = Domanda(
                        nome          = nome_da_salvare,
                        email         = self.request.get('email'),
                        testo_domanda = testo_da_salvare,
                        ente          = ente,
                        stato         = 2
                    )

                    # Aggiungi campi ai dati da inviare immediatamente al moderatore
                    channel_data['testo_domanda'] = testo_da_salvare
                    channel_data['selfie_url'] = DEFAULT_SELFIE["Test"]

            # Se non c'e' il testo
            else:

                # Se pero' ci sono sia audio che selfie
                if is_audio and is_selfie:

                    # Trova audio e selfie
                    upload_audio  = self.get_uploads()[audio_i]
                    upload_selfie = self.get_uploads()[selfie_i]

                    # Prepara nuova domanda da inserire nel Datastore
                    nuova_domanda = Domanda(
                        nome          = nome_da_salvare,
                        email         = self.request.get('email'),
                        audio_key     = upload_audio.key(),
                        selfie_key    = upload_selfie.key(),
                        orientation   = ori,
                        ente          = ente,
                        stato         = 2
                    )

                    # Aggiungi campi ai dati da inviare immediatamente al moderatore
                    channel_data['audio_key'] = str(upload_audio.key())
                    channel_data['selfie_url'] = images.get_serving_url(upload_selfie.key(), crop=True, size=500) + N_TO_T[ori]

                # Se c'e' solo l'audio
                elif is_audio:

                    # Trova l'audio
                    upload_audio  = self.get_uploads()[0]

                    # Prepara nuova domanda da inserire nel Datastore
                    nuova_domanda = Domanda(
                        nome          = nome_da_salvare,
                        email         = self.request.get('email'),
                        audio_key     = upload_audio.key(),
                        ente          = ente,
                        stato         = 2
                    )

                    # Aggiungi campi ai dati da inviare immediatamente al moderatore
                    channel_data['audio_key'] = str(upload_audio.key())
                    channel_data['selfie_url'] = DEFAULT_SELFIE[ente]

                # Se c'e' solo un selfie c'e' stato un errore
                elif is_selfie:
                    pass

                # Se proprio non c'e' nulla c'e' stato un errore
                else:
                    pass
                    
            # Aggiungi la domanda al Datastore
            key = nuova_domanda.put()
            
            # Aggiungi la chiave della domanda ai dati da inviare al moderatore
            channel_data['websafeKey'] = str(nuova_domanda.key.urlsafe())

            # Invia i dati al moderatore!
            channel.send_message("41", json.dumps(channel_data))


# Gestisce l'URL /get_upload_url e restituisce un URL per caricare i file della domanda
class GetUploadUrlHandler(webapp2.RequestHandler):
    def get(self):

        # La risposta sara' in formato JSON, lo dice qui
        self.response.headers['Content-Type'] = 'application/json' 

        # Prepara la risposta con l'url per caricare  
        obj = {
            'url': blobstore.create_upload_url('/upload_photo'),
        } 

        # Invia la risposta
        self.response.out.write(json.dumps(obj))


# Gestisce l'URL /audio/<audio_key>
class AudioHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, audio_key):

        # Prende la chiave dell'audio inserita e verifica se esiste. Se non esiste solleva un errore 404
        if not blobstore.get(audio_key):
            self.error(404)

        # Se invece c'e' restituisce l'audio
        else:
            self.send_blob(audio_key)


# Gestisce l'URL /ente/<ente> per inserire domande da parte di un ente specifico
class EnteHandler(webapp2.RequestHandler):
    def get(self, ente):

        # Prepara l'url per caricare i file
        inserisci_url = blobstore.create_upload_url('/inserisci_domanda')

        # Richiama il file di template index.html
        template = JINJA_ENVIRONMENT.get_template('templates/index.html')

        # Restituisce la pagina HTML personalizzata con il nome esteso dell'ente e l'url per caricare i file
        if ente is not None:
            self.response.write(template.render({'form_url': inserisci_url, 'ente': ENTE_TO_STR[URL_TO_ENTE[ente]]}))
        else:
            self.redirect("/")


# Gestisce l'URL / per inserire domande da parte di un pubblico generico
class MainHandler(webapp2.RequestHandler):
    def get(self):
        # Prepara l'url per caricare i file
        inserisci_url = blobstore.create_upload_url('/inserisci_domanda')

        # Richiama il file di template index.html
        template = JINJA_ENVIRONMENT.get_template('templates/index.html')

        # Restituisce la pagina HTML generica con l'url per caricare i file
        self.response.write(template.render({'form_url': inserisci_url}))


# Gestisce l'URL /moderazione
class ModerazioneHandler(webapp2.RequestHandler):

    # Funzione che restituisce tutte le domande da far vedere al moderatore
    def getDomande(self):

        # Chiede le domande al Datastore e le ordina per stato decrescente 4 --> 0 e dalla piu' recente alla meno recente
        domande = Domanda.query().order(-Domanda.stato, -Domanda.data)

        # Aggiunge qualche attributo alle domande
        for domanda in domande:

            # Aggiunge alcuni attributi alle domande: la chiave univoca per ciascuna e l'url dell'immagine di background
            setattr(domanda, "websafeKey", domanda.key.urlsafe())
            setattr(domanda, "background_url", BACKGROUND_IMAGES[domanda.ente])

            # Se la domanda ha un selfie aggiunge l'url del selfie
            if domanda.selfie_key:

                # images.get_serving_url(domanda.selfie_key, crop=True, size=500) taglia l'immagine a quadretto
                setattr(domanda, "selfie_url", images.get_serving_url(domanda.selfie_key, crop=True, size=500) + N_TO_T[domanda.orientation])

            # Se la domanda non ha un selfie aggiunge l'immagine predefinita
            else:
                setattr(domanda, "selfie_url", DEFAULT_SELFIE[domanda.ente])

        return domande

    # Prepara il canale di aggiornamento 41 valido per 7 ore filate e restituisce la pagina di moderazione
    def get(self):
        token = channel.create_channel("41", 420)

        template = JINJA_ENVIRONMENT.get_template('templates/moderazione.html')

        o = urlparse.urlparse(self.request.url)
        self.response.write(template.render({'domande': self.getDomande(), 'token': token, 'base': urlparse.urlunparse((o.scheme, o.netloc, '', '', '', ''))}))


# Gestisce l'URL /update per aggiornare gli stati delle domande
class UpdateStatoHandler(webapp2.RequestHandler):
    def get(self):

        # Trova la chiave di accesso della domanda da aggiornare
        websafeKey = self.request.get("websafeKey")

        # Trova la domanda corrispondente alla chiave
        domanda = ndb.Key(urlsafe=websafeKey).get()

        # Se la domanda non esiste solleva un errore
        if not domanda:
            raise ConflictException('Domanda inesistente')

        # Se il nuovo stato e' 4, ovvero "da pubblicare", prepara i dati da inviare alla pagina /mostra
        if int(self.request.get("stato")) == 4:

            # Inizializza i dati da inviare
            channel_data = {
                'nome': domanda.nome,
                'ente': ENTE_TO_STR[domanda.ente],
                'selfie_url': images.get_serving_url(domanda.selfie_key, crop=True, size=500) + N_TO_T [domanda.orientation] if domanda.selfie_key else DEFAULT_SELFIE[domanda.ente],
                'testo_domanda': domanda.testo_domanda,
                'background_url': BACKGROUND_IMAGES[domanda.ente],
                'websafeKey': str(domanda.key.urlsafe())
            }

            # Se la domanda ha un audio lo aggiunge ai dati
            if domanda.audio_key:
                channel_data['audio_key'] = str(domanda.audio_key)

            # Invia la domanda alla pagina /mostra
            channel.send_message("14", json.dumps(channel_data))        

        # Aggiorna lo stato della domanda nel Datastore
        domanda.stato = int(self.request.get("stato"))
        domanda.put()


# Gestisce l'URL /mostra
class MostraHandler(webapp2.RequestHandler):
    def get(self):

        # Prepara il canale di aggiornamento della pagina mostra
        token = channel.create_channel("14", 420)

        # Prepara la pagina mostra.html
        template = JINJA_ENVIRONMENT.get_template('templates/mostra.html')

        o = urlparse.urlparse(self.request.url)

        # Ottiene le domande con stato = "da mostrare" = 4
        domande = Domanda.query(Domanda.stato == 4).fetch(1)

        # Se sono 0, allora non c'e' ancora nulla. La pagina mostra avra' una copertina temporanea
        if len(domande) == 0:
            self.response.write(template.render({'token': token, 'domanda': None, 'base': urlparse.urlunparse((o.scheme, o.netloc, '', '', '', ''))}))
        
        # Altrimenti considera la prima (e unica) domanda da mostrare
        else:

            # Se ha un selfie lo aggiunge
            if domande[0].selfie_key:
                setattr(domande[0], "selfie_url", images.get_serving_url(domande[0].selfie_key, crop=True, size=500) + N_TO_T [domande[0].orientation])
            
            # Altrimenti aggiunge l'immagine di default per l'ente
            else:
                setattr(domande[0], "selfie_url", DEFAULT_SELFIE[domande[0].ente])

            # Aggiunge l'immagine di background e il nome esteso dell'ente da mostrare
            setattr(domande[0], "background_url", BACKGROUND_IMAGES[domande[0].ente])
            setattr(domande[0], "ente", ENTE_TO_STR[domande[0].ente])

            # Restituisce la pagina con tutte le informazioni
            self.response.write(template.render({'token': token, 'domanda': domande[0], 'base': urlparse.urlunparse((o.scheme, o.netloc, '', '', '', ''))}))


class LetsEncryptHandler(webapp2.RequestHandler):
    def get(self, challenge):
        self.response.headers['Content-Type'] = 'text/plain'
        responses = {
                    '_bQozz1nTsrWU-4Qtf8Yqxzl4HtsaY4lTkVLCXrsywg': '_bQozz1nTsrWU-4Qtf8Yqxzl4HtsaY4lTkVLCXrsywg.cetpn24oOcP9l77ao_7kFwNxRPp4iURfkkE5A5DOYOU',
                    '[challenge 2]': '[response 2]'
                }
        self.response.write(responses.get(challenge, ''))