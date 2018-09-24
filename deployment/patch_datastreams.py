import argparse

from LearnSTAClient import LearnSTAClient

parser = argparse.ArgumentParser(description='Add QAQC and AQI datastreams')
parser.add_argument('ds_out')
parser.add_argument('sta_host')
parser.add_argument('sta_authid')
parser.add_argument('sta_authkey')
args = parser.parse_args()

c = LearnSTAClient("https://{0}/SensorThingsService/v1.0".format(args.sta_host),
                   "https://{0}/SensorThingsService/auth/login".format(args.sta_host),
                   args.sta_authid, args.sta_authkey)

c.patchdatastreams(args.ds_out)
