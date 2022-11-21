import time
import numpy as np
from multiprocessing import shared_memory

R3E_SHARED_MEMORY_NAME = "$R3E"
DATA_INTERVAL = 0.5
TRY_CONNECT_INTERVAL = 5


def connect_r3e(try_connect_interval=TRY_CONNECT_INTERVAL):
    r3e_shm = None
    while r3e_shm is None:
        try:
            r3e_shm = shared_memory.SharedMemory(name=R3E_SHARED_MEMORY_NAME)
        except FileNotFoundError:
            print('Connect files, wait to connect.')
            time.sleep(try_connect_interval)
        else:
            print('Connected to r3e.')

    return r3e_shm


def get_r3e_data(r3e_shm):
    if r3e_shm is None:
        return

    # c = np.ndarray((100,), dtype=np.int32, buffer=r3e_shm.buf)
    c = np.ndarray((100,), buffer=r3e_shm.buf)

    np.savetxt('r3e_dump.txt', c)

    while True:
        print(c)
        time.sleep(DATA_INTERVAL)
