import json
import os
from update_model import *
import csv
import shutil
import copy

# Provide OpenStudio path and current file path
with open("config.ini", 'r') as f:
    OpenStudioPath = json.load(f)['OpenStudioPath']

file_path = os.getcwd()

# Dump model parameters to json file
fieldnames = (
    "BaseModelId", "bldg_type", "bldg_vintage", "climate_zone", "time_step"
)
with open('medium_office.csv', 'r') as f:
    reader = csv.DictReader(f, fieldnames)
    next(reader)
    with open('model_paras.json', 'w') as out:
        out.write(json.dumps([row for row in reader]))

fieldnames = (
    "MeasureId", "base_tstat", "start_hour", "end_hour", "precool_hours",
    "precool_deg", "reset_deg"
)
with open('measure_tstat_paras.csv', 'r') as f:
    reader = csv.DictReader(f, fieldnames)
    next(reader)
    with open('measure_tstat_paras.json', 'w') as out:
        out.write(json.dumps([row for row in reader]))

# Read osw template and model params in JSON
with open("model_template.osw", 'r') as f:
    model_template = json.load(f)

with open('model_paras.json', 'r') as f:
    model_params = json.load(f)

with open('measure_tstat_paras.json', 'r') as f:
    measure_tstat_params = json.load(f)

# Create osw model using OpenStudio and call OpenStudio command
# to generate E+ model file
for item in model_params:
    new_osw = copy.deepcopy(model_template)
    new_osw['steps'].append(create_prototype_measure(item))
    new_osw['steps'].append(create_timestep_measure(item))
    for tstat in measure_tstat_params:
        new_osw['steps'].append(create_precool_measure(tstat))
        new_osw['steps'].append(create_gta_measure(tstat))
        with open(
            'osw_output/{}_{}.osw'.format(
                item['BaseModelId'], tstat['MeasureId']
            ), 'w'
        ) as f:
            f.write(json.dumps(new_osw))

        # Call OpenStudio command to generate E+ model
        osw_output = (
            file_path
            + '/osw_output/{}_{}.osw'.format(
                item['BaseModelId'], tstat['MeasureId']
            )
        )
        commandLine = (
            OpenStudioPath + ' run -m -w ' + '"{}"'.format(osw_output)
        )
        os.system(commandLine)

        # Copy the in.idf to the eplus output folder
        idf_output = file_path + '/osw_output/run/in.idf'
        idf_file = (
            file_path
            + '/osw_output/eplus/{}_{}.idf'.format(
                item['BaseModelId'], tstat['MeasureId']
            )
        )
        if os.path.exists(idf_output):
            shutil.copyfile(idf_output, idf_file)
        else:
            print('''in.idf doesn't exist.''')
        # Copy the in.osm to the eplus output folder
        osm_output = file_path + '/osw_output/run/in.osm'
        osm_file = (
            file_path
            + '/osw_output/eplus/{}_{}.osm'.format(
                item['BaseModelId'], tstat['MeasureId']
            )
        )
        if os.path.exists(osm_output):
            shutil.copyfile(osm_output, osm_file)
        else:
            print('''in.osm doesn't exist.''')
        print('Done.')
