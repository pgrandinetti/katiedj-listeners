import matplotlib.pyplot as plt
import seaborn
import params
import json
import numpy
import ws_listener
#import requests

class DataObj():

    def __init__(self):
        # Query the server to get the num of roads
        #endpoint = params.URL
        #resp = requests.get(
        #        endpoint + '/api/macro/sample/info')
        #numLines = resp->numLines
        numLines = params.sample_net['numLines']
        self.lines = {k: [] for k in range(numLines)}
        self.xdata = []

    def notify(self, notifier, message):
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

import time
import random
import threading
from matplotlib.pyplot import cm

def test(plotter):
    while True:
        time.sleep(random.randint(1,3))
        msg = {0: random.random(),
               1: random.random()}
        #print('TEST: Notifying...')
        plotter.notify(None, json.dumps(msg))


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
    lines2D = {}
    color = cm.rainbow(numpy.linspace(0, 1, len(data_store.lines.keys())))
    for k, c in zip(data_store.lines, color):
        lines2D[k] = axes.plot([], [], c)[0]
    time.sleep(5)
    while True:
        time.sleep(10)
        try:
            xmax = data_store.xdata[-1] + 5
        except:
            xmax = 5
        axes.set_xlim(0, xmax)
        axes.set_ylim(0, 20)
        for k in lines2D:
            lines2D[k].set_data(
                data_store.xdata, data_store.lines[k])
        plt.pause(0.01)
