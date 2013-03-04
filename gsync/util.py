from apiclient import errors
from file import GFile
import sys

def get_file_list(service, key='id', params={}):
    err_count = 0
    page_token = None
    file_cache = {}
    while True:
        try:
            if page_token:
                params['pageToken'] = page_token
            files = service.files().list(**params).execute()

            for item in files['items']:
                if not file_cache.has_key(item[key]):
                    itemObj = GFile(service, item)
                    file_cache[item[key]] = itemObj

            page_token = files.get('nextPageToken')
            if not page_token:
                break
        except errors.HttpError, error:
            #self.output('An error occurred: %s' % error)
            err_count += 1
            if err_count == 10:
                sys.stderr.write('Encountered 10 errors in a row!')
                sys.stderr.flush()
                break
    return file_cache
