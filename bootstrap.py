import os, sys
from importlib import import_module

from storm import create_database, Store


sys.path.insert(0, os.path.dirname(__file__))
settings = import_module(os.environ.get('AW_SETTINGS', 'settings'))
local_db = Store(create_database(settings.LOCAL_DB))
remote_db = Store(create_database(settings.REMOTE_DB))
