import os
import base64
import hashlib
import hmac

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime.apiproxy_errors import OverQuotaError, CapabilityDisabledError

# only enable debug on dev server
DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Development')

PASSWORD = 'mysecret'

class PomboEntry(db.Model):
    filename = db.StringProperty()
    filedata = db.BlobProperty()
    creation_date = db.DateTimeProperty(auto_now_add=True)

class PomboEntryHandler(webapp.RequestHandler):
    def get(self):
        key = self.request.query_string
        if key == '':
            self.error(404)
            return
        pe = PomboEntry.get_by_key_name(key)
        if pe is None:
            self.error(404)
            return

        self.response.headers['Content-Type'] = 'application/pgp-encrypted'
        self.response.headers['Content-Disposition'] = 'inline; filename=%s' % pe.filename
        self.response.out.write(pe.filedata)

class PomboAdminHandler(webapp.RequestHandler):
    def get(self):
        entries = PomboEntry.all().order('-creation_date')
        self.response.out.write(template.render('pomboadmin.html',
            {'entries':entries}))

class PomboHandler(webapp.RequestHandler):
    def post(self):
        if self.request.get('myip'):
            self.response.out.write(self.request.remote_addr)
            return
        else:
            token = self.request.get('token')
            filedata = self.request.get('filedata')
            filename = self.request.get('filename')
            if not token or token != hmac.new(PASSWORD, filedata+'***'+filename, hashlib.sha1).hexdigest():
                self.error(401)
                self.response.out.write('Wrong password')
                return
            if not filename.endswith('.gpg'):
                self.error(415)
                self.response.out.write('Not a gpg file')
                return
            # use the token as key_name; should be unique
            pe = PomboEntry(key_name=token, filename=filename, filedata=base64.b64decode(filedata))
            try:
                pe.put()
            except (db.Error, OverQuotaError, CapabilityDisabledError):
                self.response.out.write('Could not write file.')
                self.error(500)
                return

            self.response.out.write('File stored.')

application = webapp.WSGIApplication( [
            ('/pombo/entry', PomboEntryHandler),
            ('/pombo/admin', PomboAdminHandler),
            ('/pombo', PomboHandler)],
            debug=DEBUG)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
