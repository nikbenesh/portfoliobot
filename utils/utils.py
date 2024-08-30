import json
import os


def _set(a):
	if a is None:
		return set()
	return set(a)

def arr_to_1d(arr):
	return [el for sub_arr in arr for el in arr]

def load_json(filename):
	with open(filename, 'r') as file:
		data = json.load(file)
	return data


def save_json(data, filename, append=False):
	if append:
		existing_data = load_json(filename)
		data = arr_to_1d([data, existing_data])
		
	with open(filename, 'w') as file:
		json.dump(data, file)


def file_exists(filename):
	return os.path.isfile(filename) and os.path.getsize(filename) > 0


def patch_http_connection_pool(**constructor_kwargs):
    """
    This allows to override the default parameters of the 
    HTTPConnectionPool constructor.
    For example, to increase the poolsize to fix problems 
    with "HttpConnectionPool is full, discarding connection"
    call this function with maxsize=16 (or whatever size 
    you want to give to the connection pool)
    """
    from urllib3 import connectionpool, poolmanager

    class MyHTTPConnectionPool(connectionpool.HTTPConnectionPool):
        def __init__(self, *args,**kwargs):
            kwargs.update(constructor_kwargs)
            super(MyHTTPConnectionPool, self).__init__(*args,**kwargs)
    poolmanager.pool_classes_by_scheme['http'] = MyHTTPConnectionPool

  