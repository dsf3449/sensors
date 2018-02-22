import io


class AuthenticationException(Exception):
    def __init__(self, message):
        self.message = message


class TransmissionException(Exception):
    def __init__(self, message):
        self.message = message


def observations_list_to_dict(observations):
    d = {}
    for o in observations:
        obs_for_datastream = d.get(o.datastreamId, [])
        obs_for_datastream.append(o)
        d[o.datastreamId] = obs_for_datastream
    return d


# JSON template for a single SensorThings Datastream within a dataArray POST request
JSON_DATASTREAM = ('{{"Datastream":{{"@iot.id":"{datastreamId}"}},'
                   '"components":["phenomenonTime","result","FeatureOfInterest/id","parameters"],'
                   '"dataArray@iot.count":{count},'
                   '"dataArray":[{dataArray}]'
                   '}}')

JSON_DATA_ARRAY_ELEM = ('['
                        '"{phenomenonTime}",'
                        '{result},'
                        '"{featureOfInterestId}",'
                        '{{{parameters}}}'
                        ']')


def observations_to_json(observations_dict):
    json = io.StringIO()

    datastreams = observations_dict.keys()
    num_datastreams = len(datastreams)

    if num_datastreams > 0:
        json.write('[')
        for (i, datastream_id) in enumerate(datastreams, start=1):
            obs_for_ds = observations_dict[datastream_id]
            count = len(obs_for_ds)
            if count > 0:
                # First, generate observation dataArray
                data_array = io.StringIO()
                # Write first element to dataArray
                o = obs_for_ds[0]
                e = JSON_DATA_ARRAY_ELEM.format(phenomenonTime=o.phenomenonTime,
                                                result=o.result,
                                                featureOfInterestId=o.featureOfInterestId,
                                                parameters=o.get_parameters_as_str())
                data_array.write(e)
                # Write remaining elements to dataArray
                for o in obs_for_ds[1:]:
                    e = JSON_DATA_ARRAY_ELEM.format(phenomenonTime=o.phenomenonTime,
                                                    result=o.result,
                                                    featureOfInterestId=o.featureOfInterestId,
                                                    parameters=o.get_parameters_as_str())
                    data_array.write(',')
                    data_array.write(e)
                # Second, generate Datastream JSON (with all dataArray elements)
                d = JSON_DATASTREAM.format(datastreamId=datastream_id,
                                           count=count,
                                           dataArray=data_array.getvalue())
                data_array.close()
                # Third, write Datastream JSON
                json.write(d)
                if i < num_datastreams:
                    # There is one or more remaining Datastream(s)
                    json.write(',')
        json.write(']')
    json_str = json.getvalue()
    json.close()

    return json_str
