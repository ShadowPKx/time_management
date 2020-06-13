import sys
import datetime
import time
import json
import random
import string


from _common.api import auth
from _common.api._settings import mydb_connection, mydb
from _common.api import utils
from _common.api import db


# SQL query MUST be optimized later
def getTotalIdsString(user_id: int, devid: int, chanel0: int, chanel1: int, chanel2: int, chanel3: int) -> str:
    links = getLinkedDevices(devid)
    own = getOwnDevices(user_id, devid, chanel0, chanel1, chanel2, chanel3)
    tasks = getLinkedTasks(devid)
    result = []
    sql = '''
    select group_concat(globalid separator '+') as val from tasks
    where state=20 and
    (
    (id in (''' + ','.join(tasks) + '''))
    or
    (type=0 and devid in (''' + (','.join(links['0'])) + '''))
    or
    (type=1 and devid in (''' + (','.join(links['1'])) + '''))
    or
    (type=2 and devid in (''' + (','.join(links['2'])) + '''))
    or
    (type=3 and devid in (''' + (','.join(links['3'])) + '''))
    or
    (type in (''' + chanel0 + ',' + chanel1 + ',' + chanel2 + ',' + chanel3 + ''')
     and devid in (''' + (','.join(own['all'])) + '''))
    )
    '''
    mydb.execute(sql)
    row = mydb.fetchone()
    if(row is None):
        return ''
    if 'val' not in row:
        return ''
    if row['val'] is None:
        return ''
    return row['val']
    # myown device will get all data that its owned


def getLinkedDevices(devid: int) -> dict:
    result = {'0': [], '1': [], '2': [], '3': [], 'all': []}
    sql = '''select s.src as id, d.name, s.chanel0,s.chanel1,s.chanel2,s.chanel3
    from sync_devices s, devices d
    where s.dst=''' + str(devid) + ''' and s.state>0 and d.id=s.src
    '''
    mydb.execute(sql)
    rows = mydb.fetchall()
    for row in rows:
        result['all'].append(row)
        if(row['chanel0'] == 0):
            result['0'].append(row['id'])
        if(row['chanel1'] == 1):
            result['1'].append(row['id'])
        if(row['chanel2'] == 2):
            result['2'].append(row['id'])
        if(row['chanel3'] == 3):
            result['3'].append(row['id'])
    if len(result['0']) < 1:
        result['0'].append(0)
    if len(result['1']) < 1:
        result['1'].append(0)
    if len(result['2']) < 1:
        result['2'].append(0)
    if len(result['3']) < 1:
        result['3'].append(0)
    if len(result['all']) < 1:
        result['all'].append({'id': 0, 'name': ''})
    return result


def getOwnDevices(user_id: int, devid: int, chanel0: int, chanel1: int, chanel2: int, chanel3: int) -> dict:
    result = {'0': [devid], '1': [devid], '2': [
        devid], '3': [devid], 'all': [devid]}
    sql = '''select d.id,d.name
    from devices d
    where d.uid=''' + str(user_id) + ''' and d.state>0 and d.id!=''' + str(devid) + '''
    '''
    mydb.execute(sql)
    rows = mydb.fetchall()

    # myown device will get all data that its owned
    for row in rows:
        result['all'].append(row)
        if(chanel0 == 0):
            result['0'].append(row['id'])
        if(chanel1 == 1):
            result['1'].append(row['id'])
        if(chanel2 == 2):
            result['2'].append(row['id'])
        if(chanel3 == 3):
            result['3'].append(row['id'])
    if len(result['0']) < 1:
        result['0'].append(0)
    if len(result['1']) < 1:
        result['1'].append(0)
    if len(result['2']) < 1:
        result['2'].append(0)
    if len(result['3']) < 1:
        result['3'].append(0)
    if len(result['all']) < 1:
        result['all'].append(0)
    return result


def getLinkedTasks(devid: int) -> list:
    result = []
    sql = '''select d.id
    from sync_tasks s, tasks t
    where s.dst=''' + str(devid) + ''' and s.tid=t.id and t.state=20'''

    mydb.execute(sql)
    rows = mydb.fetchall()
    # myown device will get all data that its owned

    for row in rows:
        result.append(row['id'])

    if len(result) < 1:
        result.append(0)
    return result
