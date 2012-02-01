import time
import threading
import os
import traceback

class Scheduler:
    def __init__(self, command, interval, runnow, name):
        self.lastrun = time.time()
        self.command = command
        self.name = name
        self.interval = interval
        self.thread = threading.Thread(None, self.runcommand, self.name)
        if runnow:
            try:
                self.command.run()
            except:
                print traceback.format_exc()
                os._exit(1)
            
    def runcommand(self):
        while True:
            currentime = time.time()
            if currentime - self.lastrun > self.interval:
                try:
                    if self.command.run():
                        self.lastrun = currentime
                except:
                    print traceback.format_exc()
                    os._exit(1)
            time.sleep(1)