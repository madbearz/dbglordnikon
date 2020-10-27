# -*- coding: utf-8 -*-
from time import time, sleep
import logger

log = logger.getLogger(__name__)

class Communicator(object):
    instance = None
    def __init__(self):
        if Communicator.instance is not None:
            raise Exception("Too many communicators handlers.")

        Communicator.instance = self
        self.queue = []

    def sendRaw(self, data):
        self.queue.append(data)

    def sendTo(self, to, data):
        return self.queue.append(to)

    def get(self):
        try:
            return self.queue.pop(0)
        except IndexError:
            return None

def getHandler():
    if Communicator.instance is not None:
        return Communicator.instance
    else:
        return Communicator()

