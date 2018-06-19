from sensors.common.constants import *

# Sensor drivers
from sensors.raspi.sensor import mq131
from sensors.raspi.sensor import dht11
from sensors.raspi.sensor import sm50

# Simulated sensors
from sensors.simulator.sensor import mq131 as sim_mq131
from sensors.simulator.sensor import dht11 as sim_dht11
from sensors.simulator.sensor import sm50 as sim_sm50


def get_sensor_instance_simulator(typ, *args, **kwargs):
    if typ == CFG_SENSOR_TYPE_MQ131:
        return sim_mq131.Mq131(typ, *args, **kwargs)
    elif typ == CFG_SENSOR_TYPE_DHT11:
        return sim_dht11.Dht11(typ, *args, **kwargs)
    elif typ == CFG_SENSOR_TYPE_SM50:
        return sim_sm50.Sm50(typ, *args, **kwargs)
    else:
        raise ValueError("Unknown sensor type {0}".format(typ))


def get_sensor_instance(typ, *args, **kwargs):
    if typ == CFG_SENSOR_TYPE_MQ131:
        return mq131.Mq131(typ, *args, **kwargs)
    elif typ == CFG_SENSOR_TYPE_DHT11:
        return dht11.Dht11(typ, *args, **kwargs)
    elif typ == CFG_SENSOR_TYPE_SM50:
        return sm50.Sm50(typ, *args, **kwargs)
    else:
        raise ValueError("Unknown sensor type {0}".format(typ))


def get_transport_instance(typ, **kwargs):
    # Avoid circular imports...
    from sensors.domain.transport import Transport
    from sensors.transport.https import HttpsTransport
    if typ == Transport.TRANSPORT_TYPE_HTTPS:
        return HttpsTransport(typ, **kwargs)
    else:
        raise ValueError("Unknown transport {0}".format(typ))
