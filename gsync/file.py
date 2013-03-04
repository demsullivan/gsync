from apiclient import errors
from apiclient.http import MediaFileUpload

import mimetypes, os, sys

class GFile(object):
    def __init__(self, service, data):
        self.id = data.get('id', None)
        self.title = data.get('title', '')
        self.parents = data.get('parents', [])
        self.isRoot = False

        self.data = data

        self.service = service
        #self.children = GFileCollection()
        
    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            raise KeyError

    def set_service(self, service):
        self.service = service

    def create(self, filename):
        if not os.path.exists(filename):
            raise ValueError, "%s does not exist!" % filename

        body = {
            'title': self.title,
            'description': self.data.get('description', ''),
            'parents': self.parents
        }

        (mtype, encoding) = mime_type = mimetypes.guess_type(filename)
        if mtype is None:
            mtype = 'application/octet-stream'
        media_body = MediaFileUpload(filename, resumable=True, mimetype=mtype)

        req = self.service.files().insert(body=body, media_body=media_body)
        response = None
        err_count = 0
        while response is None:
            try:
                status, response = req.next_chunk()
            except:
                err_count += 1
                if err_count == 10:
                    sys.stdout.write("\ntoo many errors uploading this file. skipping...")
                    break
                continue
            else:
                if status:
                    sys.stdout.write("\b\b\b\b%s%" % (str(int(status.progress() * 100)).rjust(3)))
                    sys.stdout.flush()
        sys.stdout.write("\b\b\b\b100%\n")
        sys.stdout.flush()
        if response:
            self.id = response['id']
