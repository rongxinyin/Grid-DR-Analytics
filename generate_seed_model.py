import json
import os
from update_model import *
import csv
import pathlib
import shutil
import copy

# Provide OpenStudio path and current file path
# with open("config.ini", 'r') as f:
#     OpenStudioPath = json.load(f)['OpenStudioPath']

file_path = os.getcwd()

# Dump model parameters to json file
# fieldnames = ("BaseModelId", "bldg_type", "bldg_vintage", "climate_zone", "time_step")
# with open('medium_office.csv', 'r') as f:
#     reader = csv.DictReader(f, fieldnames)
#     next(reader)
#     with open('model_paras.json', 'w') as out:
#         out.write(json.dumps([row for row in reader]))

# fieldnames = ("MeasureId", "base_tstat", "start_hour", "end_hour", "precool_hours", "precool_deg", "reset_deg")
# with open('measure_tstat_paras.csv', 'r') as f:
#     reader = csv.DictReader(f, fieldnames)
#     next(reader)
#     with open('measure_tstat_paras.json', 'w') as out:
#         out.write(json.dumps([row for row in reader]))

# fieldnames = ("output", "variable_name", "reporting_frequency")
# with open('output_variable_meter.csv', 'r') as f:
#     reader = csv.DictReader(f, fieldnames)
#     next(reader)
#     with open('output_variable_meter.json', 'w') as out:
#         out.write(json.dumps([row for row in reader]))

# Read osw template and model params in JSON
# with open("model_template.osw", 'r') as f:
#     model_template = json.load(f)

# with open(file_path+'/model_input/bldg_type.json', 'r') as f:
#     bldg_type = json.load(f)
#
# with open(file_path+'/model_input/bldg_vintage.json', 'r') as f:
#     bldg_vintage = json.load(f)
#
# with open(file_path+'/model_input/climate.json', 'r') as f:
#     climate = json.load(f)

# # print(bldg_type)
# def generate_seed_model(seed_model_params, weather_file):
#     # create an id for seed osw model
#     seed_osw_id = '{}-{}-{}'.format(seed_model_params.get('bldg_type'),
#                                    seed_model_params.get('bldg_vintage').split('-')[-1],
#                                    seed_model_params.get('climate_zone').split('-')[-1])
#     seed_osw = {"modelId": seed_osw_id, "model_params": {'seed_file': '', "weather_file": weather_file, "steps": []}}
#     seed_osw['model_params']['steps'].append(create_prototype_measure(seed_model_params))
#     # with open(file_path+'/osw_output/{}.osw'.format(new_osw_id), 'w') as output:
#     #     output.write(json.dumps(new_osw))
#     return seed_osw

# # read measure input as json
# gta_measure_list = []
# with open(file_path + '/measure_input/measure_tstat_paras.csv', 'r') as f:
#     reader = csv.DictReader(f)
#     for row in reader:
#         gta_measure_list.append(json.dumps(row))
#
# output_variable_list = []
# with open(file_path + '/measure_input/output_variable_meter.csv', 'r') as f:
#     reader = csv.DictReader(f)
#     for row in reader:
#         output_variable_list.append(json.dumps(row))
#
# # create osw file of each measure
# for item in gta_measure_list:
#     item = json.loads(item)
#     new_osw = copy.deepcopy(seed_osw)
#     new_osw.update({"modelId": '{}-{}'.format(new_osw.get('modelId'), item.get('measureId'))})
#     new_osw['model_params']['steps'].append(create_timestep_measure(ts='4'))
#     new_osw['model_params']['steps'].append(create_precool_measure(item))
#     new_osw['model_params']['steps'].append(create_gta_measure(item))
#     with open(file_path + '/osw_out/{}.osw'.format(new_osw['modelId']), 'w') as f:
#         f.write(json.dumps(new_osw))
#
#     commandLine = OpenStudioPath + ' run -w ' + osw_output
# Call OpenStudio command to generate E+ model

# osw_output = file_path + '/osw_output/{}.osw'.format(item['BaseModelId'], tstat['MeasureId'])
# commandLine = OpenStudioPath + ' run -w ' + osw_output
# os.system(commandLine)

# with open('measure_tstat_paras.json', 'r') as f:
#     measure_tstat_params = json.load(f)

# with open('output_variable_meter.json', 'r') as f:
#     output_variable_meter = json.load(f)

# Create osw model using OpenStudio and call OpenStudio command to generate E+ model file
# for item in bldg_type:
#     # new_osw = copy.deepcopy(model_template)
#     new_osw = {'seed_file':null,"weather_file": null,"steps": []}
#     new_osw['steps'].append(create_prototype_measure(item))
#     new_osw['steps'].append(create_timestep_measure(item))
#     for tstat in measure_tstat_params:
#         new_osw['steps'].append(create_precool_measure(tstat))
#         new_osw['steps'].append(create_gta_measure(tstat))
#         for report_output in output_variable_meter:
#             if report_output['output']=='variable':
#                 new_osw['steps'].append(create_output_variable_measure(report_output))
#             else:
#                 new_osw['steps'].append(create_output_meter_measure(report_output))
#             with open('osw_output/{}_{}.osw'.format(item['BaseModelId'],tstat['MeasureId']), 'w') as f:
#                 f.write(json.dumps(new_osw))
#
#             # Call OpenStudio command to generate E+ model
#             osw_output = file_path + '/osw_output/{}_{}.osw'.format(item['BaseModelId'], tstat['MeasureId'])
#             commandLine = OpenStudioPath + ' run -w ' + osw_output
#             os.system(commandLine)
#
#             # Copy the in.idf to the eplus output folder
#             idf_output = file_path+'/osw_output/run/in.idf'
#             idf_file = file_path+'/osw_output/eplus/{}_{}.idf'.format(item['BaseModelId'],tstat['MeasureId'])
#             if os.path.exists(idf_output):
#                 shutil.copyfile(idf_output, idf_file)
#             else:
#                 print('''in.idf doesn't exist.''')
#             # Copy the in.osm to the eplus output folder
#             osm_output = file_path + '/osw_output/run/in.osm'
#             osm_file = file_path + '/osw_output/eplus/{}_{}.osm'.format(item['BaseModelId'],tstat['MeasureId'])
#             if os.path.exists(osm_output):
#                 shutil.copyfile(osm_output, osm_file)
#             else:
#                 print('''in.osm doesn't exist.''')
#             print('Done.')

def generate_seed_model(epw_file, config_file, model_params_file):
    """"""

    # Provide OpenStudio path and current file path
    with open(config_file, 'r') as f:
        config = json.load(f)
        exe_path = config['OpenStudioPath']
        measure_folder = config['MeasureDirectory']

    # Workflow root directory
    root_dir = pathlib.Path.cwd()
    print(root_dir)

    # Directory where OpenStudio measures are located
    measure_dir = root_dir.joinpath(measure_folder)

    # Directory for parametric analysis workflow outputs
    osw_dir = root_dir.joinpath('osw')

    # Directory for generated model instances
    mdl_dir = root_dir.joinpath('model')

    # Directory for simulation outputs
    run_dir = root_dir.joinpath('run')

    # Directory for analysis outputs
    in_dir = root_dir.joinpath('inputs')

    # Directory for analysis outputs
    out_dir = root_dir.joinpath('output')

    # Directory for visualization plots
    plot_dir = root_dir.joinpath('plot')

    # Create directories
    for dir_inst in [osw_dir, mdl_dir, run_dir, out_dir, plot_dir]:
        try:
            pathlib.Path.mkdir(dir_inst)
        except FileExistsError:
            continue
    for mdl in ['idf', 'osm']:
        try:
            pathlib.Path.mkdir(mdl_dir.joinpath(mdl))
        except FileExistsError:
            continue

    # create a seed model with weather input
    seed_osw_path = []
    run_inst_dirs = []

    # seed_osw = dict()
    # seed_osw['file_paths'] = [str(root_dir)]
    # seed_osw['measure_paths'] = [str(measure_dir)]
    # seed_osw["seed_file"] = ''
    # seed_osw["weather_file"] = epw_file
    # seed_osw["steps"] = []
    # seed_osw_id = ''

    # Read building model param into the seed osw model
    with open(in_dir.joinpath(model_params_file), 'r') as f:
        model_list = json.load(f)

    for model_params in model_list:
        # create a seed osw template
        seed_osw = dict()
        seed_osw['file_paths'] = [str(root_dir)]
        seed_osw['measure_paths'] = [str(measure_dir)]
        seed_osw["seed_file"] = ''
        seed_osw["weather_file"] = epw_file
        seed_osw["steps"] = []
        seed_osw_id = ''
        # run the model list
        for measure in model_params:
            # print(measure['measure_dir_name'])
            if measure['measure_dir_name'] == 'CreateDOEPrototypeBuilding':
                seed_osw_id = '{}-{}-{}'.format(measure['arguments']['building_type'],
                                                  measure['arguments']['template'].split(' ')[-1],
                                                  measure['arguments']['climate_zone'].split('-')[-1])
                print(seed_osw_id)
            seed_osw['steps'].append(measure)

        # Run directory
        run_inst_dir = run_dir.joinpath('{}'.format(seed_osw_id))
        run_inst_dirs.append(run_inst_dir)
        seed_osw['run_directory'] = str(run_inst_dir)

        seed_osw_path_inst = osw_dir.joinpath('{}.osw'.format(seed_osw_id))
        with open(seed_osw_path_inst, 'w') as f:
            f.write(json.dumps(seed_osw))
        seed_osw_path.append(seed_osw_path_inst)

    print(seed_osw_path)

    # Call OpenStudio command to generate E+ model and/or run simulation

    # OpenStudio workflow
    for i in range(len(seed_osw_path)):
        command_line = '{} run -w "{}"'.format(exe_path, str(seed_osw_path[i]))
        os.system(command_line)

        # copy the in.idf and in.osm to the model folder
        for file_ext in ['idf', 'osm']:
            file_name = '{}'.format(seed_osw_id)
            copy_model_file(
                run_inst_dirs[i], mdl_dir.joinpath(file_ext),
                file_name, file_ext
            )

def copy_model_file(src_dir, dst_dir, file_name, file_ext=None):
    """Copy energy model file."""
    file_ext = 'osm' if file_ext is None else file_ext

    src_file = src_dir.joinpath('in.{}'.format(file_ext))
    dst_file = dst_dir.joinpath('{}.{}'.format(file_name, file_ext))
    try:
        shutil.copyfile(src_file, dst_file)
    except FileNotFoundError:
        print('''in.{} doesn't exist.'''.format(file_ext))

if __name__ == "__main__":
    config_file = file_path + '/config.ini'
    epw_file = str(pathlib.Path('weather/USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw'))
    test = 'std_bldg_param_mediumoffice.json'
    generate_seed_model(epw_file, config_file, test)
