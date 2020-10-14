import queue
import threading
from loguru import logger
class QueueManager():
    def __init__(self):
        self._q = {}
        self.lock = threading.Lock()
        
    def put(self, key, value):
        if key in self._q:
            pass
        else:
            self._q[key] = queue.Queue(1)
            self._q[key].put(0)

        with self.lock:
            try :
                remove_value = self._q[key].get_nowait()
                logger.debug({
                'event': 'queue is full! and clear',
                'value': remove_value,
                })
            except Exception as e:
                print()
            logger.debug({
                'event': 'put',
                'value': value,
            })
            self._q[key].put_nowait(value)

    def get(self):
        msg = {}
        try:
            with self.lock:
                for k, v in self._q.items():
                    logger.debug(v.queue[0])
                    msg[k] = v.queue[0]
            # for k, v in self._qdict.items():
        except queue.Empty as e:
            print(e)
        return msg