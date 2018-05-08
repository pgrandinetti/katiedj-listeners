import params

import sqlite3
import logging
import json
from pathlib import Path


logger = logging.getLogger(__name__)


class DataObj:

    def __init__(self, storage=None):
        numLines = params.sample_net['numLines']
        self.lines = {k: [] for k in range(numLines)}
        self.xdata = []
        self.storage = storage
        if self.storage is None:
            return
        afile = Path(self.storage)
        if afile.exists():
            logger.debug('Found existing storage')
            val = input('This storage already exists.\n'
                        'Enter 1 to continue (previous data '
                        'will be lost if they are not consistent).\n'
                        'Enter other key to exit > ')
            if not val == '1':
                return
        self.__init_storage()

    def __init_storage(self):
        if self.storage is None:
            return
        conn = self.create_connection()
        if conn is None:
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
        must_match = set(self.lines.keys())
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
        conn = self.create_connection()
        if conn is None:
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
        finally:
            conn.close()
        return self.__create_history_table()

    def __create_history_table(self):
        conn = self.create_connection()
        if conn is None:
            return False
        logger.debug('Creating new history table...')
        sql = "CREATE TABLE IF NOT EXISTS history( " +\
              "_id integer primary key autoincrement, " +\
              "clock timestamp unique," +\
              ",".join([" '{}' real "] * len(self.lines)) + ");"
        try:
            c = conn.execute(
                sql.format(*(list(self.lines.keys())))
            )
            conn.commit()
        except Exception as e:
            logger.warning(str(e))
            return False
        finally:
            conn.close()
        return True

    def __store_sample(self, state, timestamp):
        if self.storage is None:
            return False
        if not len(state) == len(self.lines):
            logger.warning('Trying to store a bad state: Skipped.')
            return False
        conn = self.create_connection()
        if conn is None:
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
            return False
        finally:
            conn.close()
        return True

    def create_connection(self):
        try:
            conn = sqlite3.connect(self.storage)
            return conn
        except Exception as e:
            logger.warning('Error while connecting to the storage.')
            logger.warning(str(e))
            return None

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
