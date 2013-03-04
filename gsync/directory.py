from apiclient import errors
from util import get_file_list

class GDirectoryCollection(object):
    def __init__(self, dir_list={}):
        self._dir_list = {}

    def append(self, item):
        self._dir_list.update({item['id']: item})

    def items(self):
        for id, item in self._dir_list.items():
            yield id, item

    def get_by_title(self, title):
        for id, item in self._dir_list.items():
            if item['title'] == title:
                return item
        return None

    def __getitem__(self, key):
        return self.get_by_id(key)

    def __setitem__(self, key, value):
        self._dir_list[key] = value

    def __len__(self):
        return len(self._dir_list)

    def has_key(self, key):
        return self._dir_list.has_key(key)

    def get_by_id(self, id):
        if self._dir_list.has_key(id):
            return self._dir_list[id]
        else:
            return None

class GDirectory(object):
    def __init__(self, service, data):
        self.id = data.get('id', None)
        self.title = data.get('title', 'No title')
        self.parents = data.get('parents', [])
        self.isRoot = False

        self.data = data

        self.service = service
        self.children = GDirectoryCollection()
        self._files = {}

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            raise KeyError

    def get_files(self):
        if len(self._files) == 0:
            self._files = get_file_list(self.service, key='title', params=dict(q="'%s' in parents" % self.id))
        return self._files
            
    def get(self, key, default):
        return self.data.get(key, default)

    def set_service(self, service):
        self.service = service

    def create(self):
        body = {
            'title': self.title,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if self.parents:
            body['parents'] = self.parents

        try:
            f = self.service.files().insert(body=body).execute()
        except errors.HttpError, error:
            print 'An error occurred: %s' % error
        else:
            self.id = f['id']
            self.data = f
            return f
        
        
