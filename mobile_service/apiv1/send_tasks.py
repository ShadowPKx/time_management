#!/usr/local/bin/python3

import os
import sys
import inspect
import json
import time
currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
sys.path.insert(0, os.path.dirname(os.path.dirname(currentdir)))
from _common.api._settings import mydb, mydb_connection
from _common.api import auth
from _common.api import headers
from _common.api import utils
from _common.api import db
from mobile_service.apiv1 import mobile

headers.jsonAPI()
if not(auth.isMobile):  # check that this request from mobile application
    headers.errorResponse('Wrong type')

devid = auth.user_some_state
if(auth._POST is None):  # only POST accepted
    headers.errorResponse('Wrong information')
json = auth._POST
if 'data' not in json:
    headers.errorResponse('Nothing was sent')
data = json['data']
mobile_crc32 = json['sync_info']['crc32']
mobile_time = json['sync_info']['time']
if len(data) > 0:
    for task in data:
        db.saveTask(task)

# After updating we check CRC32 values,
# if they are different - need to check
obj = mobile.getTotalIdsString(
    auth.user_id, auth.user_some_state, auth.user_sync0, auth.user_sync1, auth.user_sync2, auth.user_sync3)
obj['crc32'] = utils.crc32(obj['val'])
