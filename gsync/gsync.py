#!/usr/bin/python

import httplib2
import pprint
import os
import sys

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from apiclient import errors
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from directory import GDirectory, GDirectoryCollection
from file import GFile


# Copy your credentials from the APIs Console
CLIENT_ID = '1010375181559.apps.googleusercontent.com'
CLIENT_SECRET = 'XiZZX-Nr4BWp2HxIsi77rqkj'

# Check https://developers.google.com/drive/scopes for all available scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

# Redirect URI for installed apps
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

GSYNC_AUTH_FILE = os.path.join(os.environ['HOME'], '.gsync', 'oauth2.json')
DEBUG = True

class GSync(object):
    def __init__(self, client_id, client_secret, oauth_scope, redirect_uri):
        self.flow = OAuth2WebServerFlow(client_id, client_secret, oauth_scope, redirect_uri)

        if not os.path.exists(GSYNC_AUTH_FILE):
            storage = Storage(GSYNC_AUTH_FILE)
            authorize_url = self.flow.step1_get_authorize_url()

            print 'Go to the following link in your browser: ' + authorize_url
            code = raw_input('Enter verification code: ').strip()

            credentials = self.flow.step2_exchange(code)
            storage.put(credentials)
        else:
            storage = Storage(GSYNC_AUTH_FILE)
            credentials = storage.get()

        self.http = credentials.authorize(httplib2.Http())
        self.service = build('drive', 'v2', http=self.http)
        self.dir_cache = GDirectoryCollection()

    def _cache_remote_dirs(self):
        err_count = 0
        page_token = None
        while True:
            try:
                param = dict(q="mimeType='application/vnd.google-apps.folder'")
                if page_token:
                    param['pageToken'] = page_token
                files = self.service.files().list(**param).execute()

                for item in files['items']:
                    if not self.dir_cache.has_key(item['id']):
                        itemObj = GDirectory(self.service, item)
                        self.dir_cache[item['id']] = itemObj

                page_token = files.get('nextPageToken')
                if not page_token:
                    break
            except errors.HttpError, error:
                self.output('An error occurred: %s' % error)
                err_count += 1
                if err_count == 10:
                    self.output("Encountered 10 errors in a row! exiting...")
                    break

        for id, item in self.dir_cache.items():
            for parent in item.parents:
                if parent['isRoot']:
                    if not self.dir_cache.has_key(parent['id']):
                        self.dir_cache[parent['id']] = GDirectory(self.service, parent)
                        self.dir_cache[parent['id']].isRoot = True
                    else:
                        self.dir_cache[parent['id']].isRoot = True
                    self.root_dir = self.dir_cache[parent['id']]

                if self.dir_cache.has_key(parent['id']):
                    self.dir_cache[parent['id']].children.append(item)

    def sync(self, upload_only=False):
        if len(self.dir_cache) == 0:
            self._cache_remote_dirs()

        # sync remote->local directories first
        if not upload_only:
            self.output("syncing remote directories...")
            pass

        # sync local->remote directories
        self.output("syncing local directories...")
        fs_lookup = {'.': self.root_dir}
        for root, dirs, files in os.walk('.'):
            if fs_lookup.has_key(root):
                root_obj = fs_lookup[root]

            for d in dirs:
                child = root_obj.children.get_by_title(d)
                if child is None:
                    self.output("%s doesn't exist on remote, creating..." % os.path.join(root, d))
                    child = GDirectory(self.service, dict(title=d, parents=[dict(id=root_obj.id)]))
                    child.create()
                fs_lookup[os.path.join(root, d)] = child

        if not upload_only:
            self.output("syncing remote files...")

        self.output("syncing local files...")
        for root, dirs, files in os.walk('.'):
            # TODO: build in some kind of ignore feature
            if '.wd_tv' in root:
                continue
            if fs_lookup.has_key(root):
                root_obj = fs_lookup[root]

            root_obj.get_files()
            for f in files:
                if '.wd_tv' in f:
                    continue
                if not root_obj._files.has_key(f):
                    self.output("%s doesn't exist on remote, uploading...  0%%" % os.path.join(root, f), nonewline=True)
                    f_obj = GFile(self.service, dict(title=f, parents=[dict(id=root_obj.id)]))
                    f_obj.create(os.path.join(root, f))

                
    def output(self, msg, nonewline=False):
        if DEBUG:
            if nonewline:
                sys.stdout.write(msg)
            else:
                sys.stdout.write("%s\n" % msg)
        sys.stdout.flush()

    def upload(self, directory=True, recurse=True):
        pass


def run_test():
    gs = GSync(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)
    gs.sync()
    newdir = GDirectory(gs.service, dict(title="Test Dir", parents=[dict(id=gs.root_dir.id)]))
    print newdir.create()

# def walk_test():
#     for root, dirs, files in os.walk('.'):
#         if root == '.':
#             rootObj = 

def sync_test():
    gs = GSync(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)
    gs.sync(upload_only=True)

def child_test():
    root = GDirectory(None, dict(id=1, title='Root'))
    root_child = GDirectory(None, dict(id=2, title='First Child'))
    root_child2 = GDirectory(None, dict(id=3, title='Second Child'))
    root_child_child = GDirectory(None, dict(id=4, title='First Grandchild'))
    root_child_child2 = GDirectory(None, dict(id=5, title='Second Grandchild'))

    root.children.append(root_child)
    root.children.append(root_child2)

    root_child.children.append(root_child_child)
    root_child.children.append(root_child_child2)

    print "len(root.children)", len(root.children)
    print "root.children", root.children
    print "root's children: ", [x.title for id, x in root.children.items()]
    print "len(root_child.children)", len(root_child.children)
    print "root_child.children", root_child.children
    print "root_child's children: ", [x.title for id, x in root_child.children.items()]

if __name__ == '__main__':
    # walk_test()
    sync_test()
    # child_test()

# Insert a file
# media_body = MediaFileUpload(FILENAME, mimetype='text/plain', resumable=False)
# body = {
#   'title': 'My document',
#   'description': 'A test document',
#   'mimeType': 'text/plain',
#   'parents': ['Pictures']
# }

#file = drive_service.files().insert(body=body, media_body=media_body).execute()
# ret = drive_service.files().list().execute()
# pprint.pprint(ret)
