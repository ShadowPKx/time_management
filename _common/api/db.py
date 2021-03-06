import inspect
import os
import random
import sys
import time

currentdir = os.path.dirname(os.path.abspath(
        inspect.getfile(inspect.currentframe())))
sys.path.insert(0, os.path.dirname(os.path.dirname(currentdir)))

from _common.api import _settings
from _common.api import auth
from _common.api import headers
from _common.api import utils
from _common.api._settings import mydb
from _common.api._settings import mydb_connection

#
# Functions for storing data for different tables
# This functions are used in many places of project
# and changes may broke everything
#
tasks_keymap = {
    'order': 'ordr',
    'device_id': 'devid',
    'defered': 'defered_interval',
    'duration': 'duration_time',
    'start': 'start_time',
    'done': 'done_time',
    'utc': 'utc_flag',
    'isUTC': 'utc_flag'

}


# return id or 0 - error, anything < 0 is  also error
def saveTask(data: dict) -> int:
    # do all necessary checks and convert types
    data = utils.replace_keys(data, tasks_keymap)
    required = {'devid', 'title', 'desc', 'type'}
    if not (required.issubset(data.keys())):
        return -1
    # Convert all values only to Integers and Strings.
    # Other primitive types except float - it's a big lying
    int_fields = {'id', 'devid', 'type', 'alarm_type', 'state', 'priority', 'ordr', 'start_time', 'done_time',
                  'duration_time', 'repeat_type', 'repeat_value', 'defered_interval', 'year', 'month', 'day', 'hour',
                  'minute', 'timezone', 'utc_flag', 'serial'}
    for key in data:
        value = data[key]
        if (key in int_fields):
            if value is None:
                data[key] = 0
            else:
                if not (isinstance(value, int)):
                    try:
                        data[key] = int(value)
                    except Exception:
                        return -2
        else:
            if not (isinstance(value, str)):
                if value is None:
                    data[key] = ''
                else:
                    try:
                        data[key] = str(value)
                    except Exception:
                        return -3
    data['title'] = data['title'][:350]
    if data['devid'] < 1:
        return -4

    if data['type'] == 0:  # timer
        required = {'alarm_type', 'start_time', 'repeat_type', 'repeat_value', 'defered_interval', 'year', 'month',
                    'day', 'hour', 'minute', 'timezone', 'utc_flag'}
        if not (required.issubset(data.keys())):
            return -5
    elif data['type'] == 1:  # for the whole day
        required = {'start_time', 'repeat_type', 'repeat_value', 'year', 'month', 'day', 'timezone'}
        if not (required.issubset(data.keys())):
            return -6
    elif data['type'] == 2:  # notes
        required = {'state', 'priority'}
        if not (required.issubset(data.keys())):
            return -7

    elif data['type'] == 3:  # geo based reminders
        required = {'start_time', 'repeat_type', 'repeat_value', 'locations'}
        if not (required.issubset(data.keys())):
            return -8
    else:
        return -9  # not supported task type

    timestamplong = int(time.time() * 1000)
    timestampstr = str(int(timestamplong))
    gid_generator = str(int(timestamplong) - 1592000000000)

    if ('id' not in data) or (data['id'] is None) or (data['id'] < 1):  # new record in tasks
        data['id'] = 0

    if ('globalid' not in data) or (data['globalid'] is None) or len(data['globalid']) < 5:
        data['globalid'] = ''

    if (data['id'] == 0) and len(data['globalid']) == 0:  # 1-1
        data['globalid'] = gid_generator + utils.rand_string(6) +\
                           str(data['type'] + str(data['devid']))
    elif (data['id'] != 0) and len(data['globalid']) == 0:  # 0-1
        data['globalid'] = getGlobalFromId(data['id'])
        if len(data['globalid']) == 0:
            data['globalid'] = gid_generator + utils.rand_string(6) +\
                               str(data['type'] + str(data['devid']))
    elif (data['id'] == 0) and len(data['globalid']) != 0:  # 1-0
        data['id'] = getIdFromGlobal(data['globalid'])
    elif (data['id'] != 0) and len(data['globalid']) != 0:  # 0-0
        pass  # may be check that globalid is correct with id
    else:
        return -100  # not possible

    if (data['id'] == 0) and (('created' not in data) or (data['created'] is None) or (int(data['created']) < 10)):
        data['created'] = timestampstr  # dont change this later never!

    # internal update time field
    data['srv_update_time'] = timestampstr

    # always update time after any changes
    if ('update_time' not in data) or (data['update_time'] is None):
        data['update_time'] = timestampstr

    # always change serial after any updates ;-)
    if ('serial' not in data) or (data['serial'] is None):
        data['serial'] = random.randint(1, 50000)

    tags = data.pop('tags', None)
    temp_global_id = data['globalid']  # store value before unset
    temp_dev_id = data['devid']
    data['update_devid'] = data['devid']
    if (data['id'] > 0):  # dont change this values!
        data.pop('created', None)  # dont change this values!
        data.pop('globalid', None)  # dont change this values!
        data.pop('devid', None)  # dont change this values!

    if ('locations' in data) and not (data['locations'] is None):
        data['locations'] = str(data['locations'])[:2048]
    sql = ''
    if (data['id'] > 0):
        sql = 'update tasks set ' +\
              __build_update(data) + ' where id=' + str(data['id'])
        data['globalid'] = temp_global_id
        data['devid'] = temp_dev_id
        try:
            mydb.execute(sql)
        except Exception as ex:
            utils.log(utils.clearUserLogin(str(ex)), 'error')
            return -11
    else:
        sql = 'insert into tasks ' + __build_insert(data)
        data['globalid'] = temp_global_id
        data['devid'] = temp_dev_id
        try:
            mydb.execute(sql)
        except Exception as ex:
            utils.log(utils.clearUserLogin(str(ex)), 'error')
            return -12
        data['id'] = mydb_connection.insert_id()

    tags_db_ids = []
    tags_db_ids.append('0')
    if not (tags is None):
        tags_arr = str(tags).split(',')
        if len(tags_arr) > 0:
            for tag in tags_arr:
                if (tag is not None) and (len(tag) > 0):
                    tags_db_ids.append(str(setTaskTag(data['id'], tag)))

    sql = 'delete from tasks_tags where taskid=' + str(data['id']) + ' and tagid not in (' + ','.join(tags_db_ids) + ')'
    try:
        mydb.execute(sql)
    except Exception:
        pass
    return data['id']


def setTaskTag(tid: int, tag: str):
    tag = utils.removeDoubleSpaces(
            utils.removeQuotes(utils.removeNonUTF(utils.stripTags(tag.replace(',', ''))))).title()[:50]
    tag_id = 0
    sql = 'select id from tags where name="' + tag + '"'
    try:
        mydb.execute(sql)
    except Exception:
        pass
    row = mydb.fetchone()
    str_time = str(int(time.time() * 1000))
    if row is None:
        sql = 'insert into tags (name,created_user,created) values ("' + tag + '",' + str(
                auth.user_id) + ',' + str_time + ')'
        try:
            mydb.execute(sql)
        except Exception:
            pass
        tag_id = mydb_connection.insert_id()
    else:
        tag_id = int(row['id'])
    if (tag_id is None) or (tag_id < 1):
        return 0
    sql = 'insert into tasks_tags set taskid=' + str(tid) + ', tagid=' + str(tag_id) + ', created=' + str_time
    try:
        mydb.execute(sql)
    except Exception:
        pass
    return tag_id


def __setTaskTagId(tid: int, tag_id: int):
    if (tag_id is None) or (tag_id < 1):
        return
    str_time = str(int(time.time() * 1000))
    sql = 'insert into tasks_tags set taskid=' + str(tid) + ', tagid=' + str(tag_id) + ', created=' + str_time
    try:
        mydb.execute(sql)
    except Exception:
        pass
    return tag_id


def __build_update(data: dict) -> str:
    result = ""
    for key in data:
        value = data[key]
        if (key == 'id') or (key == 'globalid') or (key == 'created'):  # ignore this fields
            continue
        if (isinstance(value, str)):
            result = result + '`' + key + '`="' +\
                     mydb_connection.escape_string(value) + '",'
        elif (isinstance(value, int)):
            result = result + '`' + key + '`=' + str(value) + ','
    return result.strip(", ")


def __build_insert(data: dict) -> str:
    prefix = ""
    postfix = ""
    for key in data:
        if key == 'id':  # ignore this fields
            continue
        value = data[key]
        if isinstance(value, str):
            prefix = prefix + '`' + key + '`,'
            postfix = postfix + '"' +\
                      mydb_connection.escape_string(value) + '",'

        elif isinstance(value, int):
            prefix = prefix + '`' + key + '`,'
            postfix = postfix + str(value) + ','
    # return last part of insert statement
    return '(' + prefix.strip(", ") + ') values (' + postfix.strip(", ") + ')'


def getIdFromGlobal(global_id: str) -> int:
    sql = 'select id from tasks where globalid="' + global_id + '"'
    mydb.execute(sql)
    row = mydb.fetchone()
    if not (row is None):
        return int(row['id'])
    return 0


def getGlobalFromId(id: int) -> str:
    sql = 'select globalid from tasks where id="' + str(id) + '"'
    mydb.execute(sql)
    row = mydb.fetchone()
    if not (row is None):
        return str(row['globalid'])
    return ""


__linkedDevices = None
__ownDevices = None
__linkedTasks = None


def getUserLinkedDevices(user_id: int, devid: int = 0, incomming: bool = True, outgoing: bool = True,
                         cache: bool = True) -> dict:
    global __linkedDevices
    if (devid == 0) and incomming and outgoing and cache and (not (__linkedDevices is None)):
        return __linkedDevices.copy()
    result = {
        'in': {
            '0': [], '1': [], '2': [], '3': [], 'link': [],
            'all': {}  # map of all external-ids - senders
        },
        'out': {
            '0': [], '1': [], '2': [], '3': [], 'link': [],
            'all': {}  # map of all external-ids - receivers
        },
        'all': {},  # map of all external-ids, without own ids
        'names': {},  # simply map of all names with login
    }

    addsql = ''
    if devid > 0:
        addsql = ' and d2.id=' + str(devid) + ' '

    result_all = result['all']
    result_names = result['names']
    if incomming:
        # get external devices that send info to user  id - src (ext-dev), dst - user device
        sql = '''select u.login,d2.name as dst_name,s.dst,d.name,d.id,s.sync0,s.sync1,s.sync2,s.sync3
                from devices as d
                inner join sync_devices as s on s.src=d.id and s.`state`>0
                inner join devices as d2 on s.dst=d2.id and d2.`uid`=''' + str(user_id) + addsql + ''' and d2.`state`>0
                inner join users as u on d.uid=u.id
                where d.state>0
                '''

        # utils.debug(sql)
        mydb.execute(sql)
        rows = mydb.fetchall()
        result_in = result['in']
        result_in_all = result_in['all']
        obj = {}
        for row in rows:
            result_names[row['id']] = {  # external
                'device': row['name'],
                'user': row['login']
            }
            result_names[row['dst']] = {
                'device': row['dst_name']
            }
            result_all[row['id']] = row['id']
            result_in_all[row['id']] = row['id']
            obj = {'src': row['id'], 'dst': row['dst'], 'sync0': row['sync0'],
                   'sync1': row['sync1'], 'sync2': row['sync2'], 'sync3': row['sync3']}
            result_in['link'].append(obj)
            if (row['sync0'] == 0):
                result_in['0'].append(obj)
            if (row['sync1'] == 1):
                result_in['1'].append(obj)
            if (row['sync2'] == 2):
                result_in['2'].append(obj)
            if (row['sync3'] == 3):
                result_in['3'].append(obj)

    if outgoing:
        # get external devices that receive info from user  id - desctination (ext-dev), src - user device
        sql = '''select u.login,d2.name as src_name,s.src,d.name,d.id,s.sync0,s.sync1,s.sync2,s.sync3 
            from devices as d
            inner join sync_devices as s on s.dst=d.id and s.`state`>0
            inner join devices as d2 on s.src=d2.id and d2.`uid`=''' + str(user_id) + addsql + ''' and d2.`state`>0
            inner join users as u on d.uid=u.id
            where d.state>0
            '''
        # utils.debug(sql)
        mydb.execute(sql)
        rows = mydb.fetchall()
        result_out = result['out']
        result_out_all = result_out['all']
        for row in rows:
            result_names[row['id']] = {  # external
                'device': row['name'],
                'user': row['login']
            }
            result_names[row['src']] = {
                'device': row['src_name']
            }
            result_all[row['id']] = row['id']
            result_out_all[row['id']] = row['id']
            obj = {'src': row['src'], 'dst': row['id'], 'sync0': row['sync0'],
                   'sync1': row['sync1'], 'sync2': row['sync2'], 'sync3': row['sync3']}
            result_out['link'].append(obj)
            if (row['sync0'] == 0):
                result_out['0'].append(obj)
            if (row['sync1'] == 1):
                result_out['1'].append(obj)
            if (row['sync2'] == 2):
                result_out['2'].append(obj)
            if (row['sync3'] == 3):
                result_out['3'].append(obj)

    if (devid == 0) and incomming and outgoing:
        __linkedDevices = result.copy()
    return result


def getDefaultDevice(user_id: int) -> int:
    sql = 'select id from devices where uid=' + str(user_id) + ' order by `default` desc,id limit 1'
    mydb.execute(sql)
    row = mydb.fetchone()
    if row is None:
        return 0
    return int(row['id'])


def getUserOwnDevices(user_id: int, devid: int = 0, myself: bool = False, cache: bool = True) -> dict:
    global __ownDevices
    if (devid == 0) and cache and (not (__ownDevices is None)):
        return __ownDevices.copy()

    result = {'0': [], '1': [], '2': [], '3': [], 'link': [], 'all': [], 'names': {}}

    sql = '''select d.id,d.name,d.sync0,d.sync1,d.sync2,d.sync3, d.`default`
    from devices d
    where d.uid=''' + str(user_id) + ''' and d.state>0
    '''

    if devid > 0:
        if (myself):
            sql = '''select d.id,d.name,d.sync0,d.sync1,d.sync2,d.sync3, d.`default`
            from devices d
            where d.uid=''' + str(user_id) + ''' and id=''' + str(devid) + ''' and d.state>0
            '''
            mydb.execute(sql)
            rows = mydb.fetchall()
            for row in rows:
                result['all'].append(row)
                result['link'].append(row['id'])
                result['names'][row['id']] = row['name']
                result['0'].append(row['id'])
                result['1'].append(row['id'])
                result['2'].append(row['id'])
                result['3'].append(row['id'])

        sql = '''select d.id,d.name,d.`default`,
            CASE WHEN d.sync0<d2.sync0 then d.sync0 else d2.sync0 end as sync0,
            CASE WHEN d.sync1<d2.sync1 then d.sync1 else d2.sync1 end as sync1,
            CASE WHEN d.sync2<d2.sync2 then d.sync2 else d2.sync2 end as sync2,
            CASE WHEN d.sync3<d2.sync3 then d.sync3 else d2.sync3 end as sync3
            from devices d
            inner join devices d2 on d.uid=d2.uid and d2.id=''' + str(devid) + ''' and d2.state>0
            where d.uid=''' + str(user_id) + ''' and d.id!=''' + str(devid) + ''' and d.state>0
            '''

    mydb.execute(sql)
    rows = mydb.fetchall()

    # myown device will get all data that its owned
    for row in rows:
        result['all'].append(row)
        result['link'].append(row['id'])
        result['names'][row['id']] = row['name']
        if (row['sync0'] == 0):
            result['0'].append(row['id'])
        if (row['sync1'] == 1):
            result['1'].append(row['id'])
        if (row['sync2'] == 2):
            result['2'].append(row['id'])
        if (row['sync3'] == 3):
            result['3'].append(row['id'])

    if (devid == 0):
        __ownDevices = result.copy()
    return result


def getUserLinkedTasks(user_id: int, devid: int = 0, cache: bool = True) -> list:
    global __linkedTasks
    if (devid == 0) and cache and (not (__linkedTasks is None)):
        return __linkedTasks.copy()
    result = []
    addsql = ''
    if devid > 0:
        addsql = ' and d.id=' + str(devid) + ' '
    sql = '''select t.id
        from tasks as t
        inner join sync_tasks as s on t.id=s.tid
        inner join devices as d on d.id=s.dst and d.uid=''' + str(user_id) + addsql + ''' and d.state>0
    '''
    mydb.execute(sql)
    rows = mydb.fetchall()

    # myown device will get all data that its owned
    for row in rows:
        result.append(row['id'])
    if (devid == 0):
        __linkedTasks = result.copy()
    return result


__sql_permission_cache = {}


def __arrLinkOwnUnite(links: list, owns: list) -> list:
    b1 = len(links) < 1
    b2 = len(owns) < 1
    if b1 and b2:
        return []
    elif b1 and not b2:
        return (str(x) for x in owns)
    elif not (b1) and (b2):
        return (str(x['src']) for x in links)
    else:
        return list(set().union((str(x['src']) for x in links), (str(x) for x in owns)))


def buildSqlPermissionfilter(user_id: int, devid: int, cache: bool = True) -> str:
    if (cache) and (devid in __sql_permission_cache) and (not (__sql_permission_cache[devid] is None)):
        return __sql_permission_cache[devid]
    links = getUserLinkedDevices(user_id=user_id, devid=devid, incomming=True, outgoing=False, cache=False)
    own = getUserOwnDevices(user_id=user_id, myself=False, devid=devid, cache=cache)
    tasks = getUserLinkedTasks(user_id=user_id, devid=devid, cache=cache)
    tasks_links = ','.join(str(x) for x in tasks)
    dev_0 = ','.join(__arrLinkOwnUnite(links['in']['0'], own['0']))
    dev_1 = ','.join(__arrLinkOwnUnite(links['in']['1'], own['1']))
    dev_2 = ','.join(__arrLinkOwnUnite(links['in']['2'], own['2']))
    dev_3 = ','.join(__arrLinkOwnUnite(links['in']['3'], own['3']))

    sql_filter = ''
    arr = []
    if (devid > 0):
        arr.append(' (t.devid=' + str(devid) + ') ')
    if len(tasks_links) > 0:
        arr.append(' (t.id in (' + tasks_links + ')) ')
    if len(dev_0) > 0:
        arr.append(' (t.type=0 and t.devid in (' + dev_0 + ')) ')
    if len(dev_1) > 0:
        arr.append(' (t.type=1 and t.devid in (' + dev_1 + ')) ')
    if len(dev_2) > 0:
        arr.append(' (t.type=2 and t.devid in (' + dev_2 + ')) ')
    if len(dev_3) > 0:
        arr.append(' (t.type=3 and t.devid in (' + dev_3 + ')) ')

    # for sql request syntax
    if len(arr) < 1:
        arr.append(' (t.devid=0) ')
    sql_filter = '(' + ' or '.join(arr) + ')'
    if cache:
        __sql_permission_cache[devid] = sql_filter
    return sql_filter


def sql_request(sql: str):
    try:
        mydb.execute(sql)
    except Exception as ex:
        utils.log(utils.clearUserLogin(str(ex)), 'error')
        headers.errorResponse('SQL error')


def sql_request_ignore_error(sql: str):
    try:
        mydb.execute(sql)
    except Exception as ex:
        pass


def duplicateTask(tid: int, devid: int) -> bool:
    if devid < 1:
        return False
    sql_request('select * from tasks where id=' + str(tid))
    row = mydb.fetchone()
    if row is None:
        return False
    gid = row['globalid']
    if '&' in gid:
        g_arr = gid.split('&', 2)
        gid = g_arr[0]
    gid = gid + '&' + str(devid)
    row['globalid'] = gid
    row['id'] = 0
    row.pop('id', None)
    row['devid'] = devid
    newtid = saveTask(row)
    sql_request('select tagid from tasks_tags where taskid=' + str(tid))
    rows = mydb.fetchall()
    for row in rows:
        __setTaskTagId(newtid, row['tagid'])
    return False


def getTotalUsersCount() -> int:
    sql = 'select count(*) as users_count from users'
    sql_request_ignore_error(sql)
    row = mydb.fetchone()
    count = 0
    if (row is not None) and ('users_count' in row) and (row['users_count'] is not None):
        try:
            count = int(row['users_count'])
        except Exception:
            count = 0
    return count


# >0 - exact id
# ==0 - new task
# <0 must be removed
def checkOneTaskRestoreAccessPermission(global_id: str, uid: int) -> int:
    sql = 'select t.id,d.uid from tasks as t'\
          ' left join devices as d on d.id=t.devid and d.uid=' + str(uid) +\
          ' where t.globalid="' + global_id + '"'
    sql_request(sql)
    row = mydb.fetchone()
    if (row is None):
        return 0

    if 'uid' not in row:
        return -1
    if row['uid'] is None:
        return -1
    if int(row['uid']) != uid:
        return -1

    if 'id' not in row:
        return 0
    if row['id'] is None:
        return 0
    return int(row['id'])


def clearDatabaseGarbage():
    date_limit = str(int((time.time() - (_settings.keep_user_data_month * 31 * 24 * 60 * 60)) * 1000))
    sql = 'select group_concat(u.id separator ",") as ids  from users as u '\
          ' left join ('\
          '     select uid,max(lastconnect) as lastconnect, max(created) as created '\
          '     from devices group by uid'\
          '     ) as d on d.uid=u.id '\
          ' where '\
          ' ('\
          '     ('\
          '     d.lastconnect<' + date_limit +\
          '     and d.created<' + date_limit +\
          '     )'\
          ' or d.uid is NULL'\
          ' ) '\
          ' and u.lastlogin<' + date_limit +\
          ' and u.created<' + date_limit +\
          ' limit 350'
    sql_request_ignore_error(sql)
    row = mydb.fetchone()
    if (row is not None) and ('ids' in row) and (row['ids'] is not None) and (len(row['ids']) > 0):
        ids = row['ids']
        sql = 'delete from users where id in (' + ids + ')'
        sql_request_ignore_error(sql)
        sql = 'delete from devices where uid in (' + ids + ')'
        sql_request_ignore_error(sql)

    sql = 'delete devices '\
          ' from devices '\
          ' left join users on users.id=devices.uid '\
          ' where users.id is Null'
    sql_request_ignore_error(sql)

    sql = 'delete sync_devices '\
          ' from sync_devices '\
          ' left join devices on devices.id=sync_devices.src '\
          ' where devices.id is Null'
    sql_request_ignore_error(sql)

    sql = 'delete sync_devices '\
          ' from sync_devices '\
          ' left join devices on devices.id=sync_devices.dst '\
          ' where devices.id is Null'
    sql_request_ignore_error(sql)

    sql = 'delete sync_tasks '\
          ' from sync_tasks '\
          ' left join devices on devices.id=sync_tasks.dst '\
          ' where devices.id is Null'
    sql_request_ignore_error(sql)

    sql = 'delete tasks '\
          ' from tasks '\
          ' left join devices on devices.id=tasks.devid '\
          ' where devices.id is Null'
    sql_request_ignore_error(sql)

    sql = 'delete tasks_tags '\
          ' from tasks_tags '\
          ' left join tasks on tasks.id=tasks_tags.taskid '\
          ' where tasks.id is Null'
    sql_request_ignore_error(sql)

    sql = 'delete tags '\
          ' from tags '\
          ' left join (select tagid from tasks_tags group by tagid) as tagger on tags.id=tagger.tagid '\
          ' where tagger.tagid is Null'
    sql_request_ignore_error(sql)
