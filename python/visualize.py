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
            val = input('This storage already exists.\n' + \
                        'Enter 1 to continue (previous data will be lost if the format is different).\n' + \
                        'Enter other key to exit > ')
            if not val == '1':
                return
        self.__init_storage()

    def __init_storage(self):
        if self.storage is None:
            return
        conn = sqlite3.connect(self.storage)
        try:
            c = conn.execute('PRAGMA table_info("history")')
        except:
            # table does not exists
            conn.close()
            c = self.__create_history_table()
            return
        res = c.fetchall()
        conn.close()
        logger.debug('Found existing history table')
        must_match = {x for x in self.lines.keys()}
        for row in res:
            if row[0] == 0:
                if not row[1] == '_id' or \
                   not row[2] == 'INTEGER':
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

    def __drop_and_create(self):
        conn = sqlite3.connect(self.storage)
        drop_cmd = 'DROP TABLE history;'
        logger.debug('Dropping existing history table...')
        c = conn.execute(drop_cmd)
        conn.commit()
        conn.close()
        return self.__create_history_table()

    def __create_history_table(self):
        conn = sqlite3.connect(self.storage)
        logger.debug('Creating new history table...')
        sql = "CREATE TABLE IF NOT EXISTS history( " +\
              "_id integer primary key autoincrement, " +\
              "clock timestamp," +\
              ",".join([" '{}' real "] * len(self.lines)) + ");"
        c = conn.execute(sql.format(*(x for x in self.lines.keys())))
        conn.commit()
        conn.close()
        return c

    '''
    def __store_sample(self, data):
        if self.storage is None:
            return
        conn = sqlite3.connect(self.storage)
        c = conn.cursor()
        sql = "INSERT INTO hystory VALUES (" +\
              "NULL,
   '''

    def notify(self, notifier, message):
        logger.debug('DataObj notified with message > {}'.format(message))
        try:
            body = json.loads(message)
            body = body['state']
        except:
            return
        for k in self.lines:
            self.lines[k].append(body[str(k)])
        try:
            self.xdata.append(self.xdata[-1] + 1)
        except:
            self.xdata.append(0)


if __name__ == '__main__':
    data_store = DataObj()
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
