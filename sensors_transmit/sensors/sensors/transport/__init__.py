import io
import math
import json

from sensors.domain.observation import Observation
from sensors.domain.multiobservation import MultiObservation


class AuthenticationException(Exception):
    def __init__(self, message):
        self.message = message


class TransmissionException(Exception):
    def __init__(self, message):
        self.message = message


def observations_list_to_dict(observations):
    d = {}
    for o in observations:
        if isinstance(o, Observation):
            obs_for_datastream = d.get(o.datastreamId, [])
            obs_for_datastream.append(o)
            d[o.datastreamId] = obs_for_datastream
        elif isinstance(o, MultiObservation):
            obs_for_multidatastream = d.get(o.multidatastreamId, [])
            obs_for_multidatastream.append(o)
            d[o.multidatastreamId] = obs_for_multidatastream
        else:
            raise TypeError("Observation of type {0} is unknown".format(o.__class__.__name__))
    return d


JSON_DATASTREAM = ('{{"Datastream":{{"@iot.id":"{datastreamId}"}},'
                   '"components":["phenomenonTime","result","FeatureOfInterest/id","parameters"],'
                   '"dataArray@iot.count":{count},'
                   '"dataArray":[{dataArray}]'
                   '}}')

JSON_DATASTREAM_NO_FOI = ('{{"Datastream":{{"@iot.id":"{datastreamId}"}},'
                          '"components":["phenomenonTime","result","parameters"],'
                          '"dataArray@iot.count":{count},'
                          '"dataArray":[{dataArray}]'
                          '}}')

JSON_MULTIDATASTREAM = ('{{"MultiDatastream":{{"@iot.id":"{multidatastreamId}"}},'
                   '"components":["phenomenonTime","result","FeatureOfInterest/id","parameters"],'
                   '"dataArray@iot.count":{count},'
                   '"dataArray":[{dataArray}]'
                   '}}')

JSON_MULTIDATASTREAM_NO_FOI = ('{{"MultiDatastream":{{"@iot.id":"{multidatastreamId}"}},'
                          '"components":["phenomenonTime","result","parameters"],'
                          '"dataArray@iot.count":{count},'
                          '"dataArray":[{dataArray}]'
                          '}}')


def observations_to_json(observations_dict, allow_nan=False):
    json_str_io = io.StringIO()

    datastreams = observations_dict.keys()
    num_datastreams = len(datastreams)

    if num_datastreams > 0:
        json_str_io.write('[')
        for (i, datastream_id) in enumerate(datastreams, start=1):
            obs_for_ds = observations_dict[datastream_id]
            count = len(obs_for_ds)
            if count > 0:
                # First, generate observation dataArray
                data_array = io.StringIO()
                # Write first element to dataArray
                o = obs_for_ds[0]
                # Check to see if this is a MultiObservation, if so we are
                # dealing with a MultiDatastream
                is_multidatastream = isinstance(o, MultiObservation)
                result = o.result
                if not allow_nan:
                    result = _filter_nan(result, is_multidatastream)
                e = None
                foi_present = False
                if o.featureOfInterestId is not None:
                    foi_present = True
                    e = [o.phenomenonTime, result, o.featureOfInterestId, o.parameters]
                else:
                    foi_present = False
                    e = [o.phenomenonTime, result, o.parameters]
                data_array.write(json.dumps(e))
                # Write remaining elements to dataArray
                for o in obs_for_ds[1:]:
                    result = o.result
                    if not allow_nan:
                        result = _filter_nan(result, is_multidatastream)
                    if foi_present:
                        e = [o.phenomenonTime, result, o.featureOfInterestId, o.parameters]
                    else:
                        e = [o.phenomenonTime, result, o.parameters]
                    data_array.write(',')
                    data_array.write(json.dumps(e))
                # Second, generate Datastream JSON (with all dataArray elements)
                d = None
                if foi_present:
                    if is_multidatastream:
                        d = JSON_MULTIDATASTREAM.format(multidatastreamId=datastream_id,
                                                        count=count,
                                                        dataArray=data_array.getvalue())
                    else:
                        # This is a regular Datastream
                        d = JSON_DATASTREAM.format(datastreamId=datastream_id,
                                                   count=count,
                                                   dataArray=data_array.getvalue())
                else:
                    if is_multidatastream:
                        d = JSON_MULTIDATASTREAM_NO_FOI.format(multidatastreamId=datastream_id,
                                                               count=count,
                                                               dataArray=data_array.getvalue())
                    else:
                        # This is a regular Datastream
                        d = JSON_DATASTREAM_NO_FOI.format(datastreamId=datastream_id,
                                                          count=count,
                                                          dataArray=data_array.getvalue())
                data_array.close()
                # Third, write Datastream JSON
                json_str_io.write(d)
                if i < num_datastreams:
                    # There is one or more remaining Datastream(s)
                    json_str_io.write(',')
        json_str_io.write(']')
    json_str = json_str_io.getvalue()
    json_str_io.close()

    return json_str


def _filter_nan(result, is_multidatastream, replacement=None):
    if is_multidatastream:
        new_result = []
        for (i, r) in enumerate(result):
            if type(result[i]) is float and math.isnan(result[i]):
                new_result.append(replacement)
            else:
                new_result.append(r)
        return new_result
    else:
        if type(result) is float and math.isnan(result):
            return replacement
        else:
            return result
