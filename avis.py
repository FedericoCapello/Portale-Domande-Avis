import webapp2
import handlers

# Collega gli indirizzi URL alle parti di codice corrispondenti nel file handlers.py
app = webapp2.WSGIApplication([
    ('/', handlers.MainHandler),
    ('/inserisci_domanda', handlers.InserisciDomandaHandler),
    ('/get_upload_url', handlers.GetUploadUrlHandler),
    ('/audio/([^/]+)?', handlers.AudioHandler),
    ('/ente/([^/]+)?', handlers.EnteHandler),
    ('/moderazione', handlers.ModerazioneHandler),
    ('/update', handlers.UpdateStatoHandler),
    ('/mostra', handlers.MostraHandler)
], debug=True)