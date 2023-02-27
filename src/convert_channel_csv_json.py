import json
import csv

# Init data variable.
data = {'channels': {}}

# Open and read csv.
with open(r'..\telemetry_channels.csv') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    for r_id, row in enumerate(spamreader):
        if r_id == 0:
            header = row
            continue

        for v_id, val in enumerate(row):
            if v_id == 0:
                channel_name = val
                data['channels'][channel_name] = {}
            else:
                data['channels'][channel_name][header[v_id]] = val

with open(r'..\channels.json', 'w') as json_file:
    json.dump(data, json_file, indent=True)


