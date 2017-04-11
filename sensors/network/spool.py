import os
import sqlite3



def spool_data(q):
    while True:
        try:
            obs = q.get()
        except:
            pass
        finally:
            pass



