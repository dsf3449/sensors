import multiprocessing as mp

import sensors.network.spool as spool

def main():
    try:
        # Start process to send data to
        mp.set_start_method('spawn')
        q = mp.Queue()
        p = mp.Process(target=spool.spool_data, args=(q,))
        p.start()

        
    except:
        pass
    finally:
        p.join()