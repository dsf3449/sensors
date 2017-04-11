from sensors.common.logging import get_logger

logger = get_logger()

def spool_data(q):
    while True:
        try:
            logger.debug("Spooler getting from queue...")
            obs = q.get()
            logger.debug("Spooler received: {0}".format(str(obs)))
        except KeyboardInterrupt:
            break
        except:
            pass
        finally:
            pass



