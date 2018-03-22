import matplotlib.pyplot as plt
import seaborn
import params
import json
import numpy
import ws_listener
import logging
import time
import threading
import sqlite3
import argparse
from pathlib import Path
#import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

class DataObj():

    def __init__(self, storage=None):
        # Query the server to get the num of roads
        #endpoint = params.URL
        #resp = requests.get(
        #        endpoint + '/api/macro/sample/info')
        #numLines = resp->numLines
        numLines = params.sample_net['numLines']
        self.lines = {k: [] for k in range(numLines)}
        self.xdata = []
        self.storage = storage
        if self.storage is None:
            return
        afile = Path(self.storage)
        if afile.exists():
            logger.debug('Found existing storage')
            val = input('This storage already exists.\n' +\
                        'Enter 1 to continue (previous data ' +\
                        'will be lost if they are not consistent).\n' +\
                        'Enter other key to exit > ')
            if not val == '1':
                return
        self.__init_storage()

    def __init_storage(self):
        if self.storage is None:
            return
        try:
            conn = sqlite3.connect(self.storage)
        except:
            logger.warning('Error while connecting to the storage.')
            return
        try:
            c = conn.execute('PRAGMA table_info("history")')
        except:
            conn.close()
            c = self.__drop_and_create()
            return
        res = c.fetchall()
        conn.close()
        if not res:
            # table does not exists
            logger.debug('Did not find history table')
            c = self.__create_history_table()
            return
        logger.debug('Found existing history table')
        must_match = {x for x in self.lines.keys()}
        for row in res:
            if row[0] == 0:
                if not row[1] == '_id' or \
                   not row[2] == 'integer':
                    logger.debug('_id does not match')
                    return self.__drop_and_create()
            elif row[0] == 1:
                if not row[1] == 'clock' or \
                   not row[2] == 'timestamp':
                    logger.debug('Datetime does not match')
                    return self.__drop_and_create()
            else:
                if not row[2] == 'real':
                    logger.debug('Roads type do not match')
                    return self.__drop_and_create()
                try:
                    must_match.remove(int(row[1]))
                except:
                    logger.debug('Roads ID do not match')
                    return self.__drop_and_create()
        if len(must_match) > 0:
            logger.debug('Roads ID do not match')
            return self.__drop_and_create()
        logger.debug('Existing history table is OK')
        return True

    def __drop_and_create(self):
        try:
            conn = sqlite3.connect(self.storage)
        except:
            logger.warning('Error while connecting to the storage.')
            return False
        drop_cmd = 'DROP TABLE IF EXISTS history;'
        logger.debug('Dropping existing history table...')
        try:
            c = conn.execute(drop_cmd)
            conn.commit()
        except Exception as e:
            logger.warning('Cannot drop table')
            logger.warning(str(e))
            return False
        conn.close()
        return self.__create_history_table()

    def __create_history_table(self):
        try:
            conn = sqlite3.connect(self.storage)
        except:
            logger.warning('Error while connecting to the storage.')
            return False
        logger.debug('Creating new history table...')
        sql = "CREATE TABLE IF NOT EXISTS history( " +\
              "_id integer primary key autoincrement, " +\
              "clock timestamp unique," +\
              ",".join([" '{}' real "] * len(self.lines)) + ");"
        try:
            c = conn.execute(sql.format(*(x for x in self.lines.keys())))
            conn.commit()
        except Exception as e:
            logger.warning(str(e))
            return False
        conn.close()
        return True

    def __store_sample(self, state, timestamp):
        if self.storage is None:
            return False
        if not len(state) == len(self.lines):
            logger.warning('Trying to store a bad state: Skipped.')
            return False
        try:
            conn = sqlite3.connect(self.storage)
        except Exception as e:
            logger.warning('Error while connecting to the storage.')
            logger.warning(str(e))
            return False
        sql = 'INSERT INTO history VALUES (' +\
              'NULL, "{}",' + ','.join([' {}'] * len(self.lines)) + ');'
        values = [v for k,v in sorted(state.items())]
        try:
            c = conn.execute(sql.format(timestamp, *values))
            conn.commit()
        except Exception as e:
            logger.warning('Cannot save to storage the new data')
            logger.warning(str(e))
            conn.close()
            return False
        conn.close()
        return True

    def notify(self, notifier, message):
        logger.debug('Message is > {}'.format(message))
        try:
            msg = json.loads(message)
            body = msg['state']
            timestamp = msg['timestamp']
        except:
            logger.debug('Message discarded due to the format')
            return
        if not len(body) == len(self.lines):
            logger.warning('Trying to store a bad state: Skipped.')
            return
        for k in self.lines:
            self.lines[k].append(body[str(k)])
        try:
            self.xdata.append(self.xdata[-1] + 1)
        except:
            self.xdata.append(0)
        self.__store_sample(body, timestamp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--storage',
                        action='store',
                        required=False,
                        dest='storage',
                        default=None,
                        help='Path to storage file (sqlite)')
    args = parser.parse_args()
    data_store = DataObj(storage=args.storage)
    arguments = {'ping_timeout': 5,
                 'reply_timeout': 10,
                 'sleep_time': 5}
    client = ws_listener.WSClient(
                    params.URL, **arguments)
    client.register(data_store)
    wst = threading.Thread(
        target=ws_listener.start_ws_client, args=(client,))
    wst.daemon = True
    wst.start()
    plt.ion()
    seaborn.set()
    axes = plt.gca()
    axes.set_xlabel('Time [steps from start]')
    axes.set_ylabel('Veh.')
    lines2D = {}
    for k in data_store.lines:
        lines2D[k] = axes.plot([], [], label=k)[0]
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=4, fancybox=True, shadow=True, frameon=True)
    time.sleep(5)
    while True:
        time.sleep(10)
        try:
            xmax = data_store.xdata[-1] + 5
        except:
            xmax = 5
        ymax = max([x for l in data_store.lines.values() for x in l]) + 5
        axes.set_xlim(0, xmax)
        axes.set_ylim(0, ymax)
        for k in lines2D:
            lines2D[k].set_data(
                data_store.xdata, data_store.lines[k])
        plt.pause(0.01)
