"""
Main workflow to perturb OpenStudio model parameters to analyze DF metrics
variations

"""


import os
import sys
import pathlib
import shutil
import json
import csv

import numpy as np
import pandas as pd

from add_measure import *


def perturb_model(osm_file, design_file, config_file, measure_file):
    """"""
    # Provide OpenStudio path and current file path
    with open(config_file, 'r') as f:
        config = json.load(f)
        exe_path = config['OpenStudioPath']
        measure_folder = config['MeasureDirectory']

    # OenStudio Model name
    model_name = pathlib.Path(osm_file).stem

    # Workflow root directory
    root_dir = pathlib.Path.cwd()

    # Directory where OpenStudio measures are located
    measure_dir = root_dir.joinpath(measure_folder)

    # Directory for parametric analysis workflow outputs
    osw_dir = root_dir.joinpath('osw')
    shutil.rmtree(osw_dir, ignore_errors=True)
    pathlib.Path.mkdir(osw_dir)

    # Directory for model instance outputs
    out_dir = root_dir.joinpath('osm')
    shutil.rmtree(out_dir, ignore_errors=True)
    pathlib.Path.mkdir(out_dir)

    # Create osw template and model params in JSON
    osw_template = {}
    osw_template['file_paths'] = [str(root_dir)]
    osw_template['measure_paths'] = [str(measure_dir)]
    osw_template['seed_file'] = osm_file

    # Read experimental design of model parameter values
    design_table = pd.read_csv(design_file)

    # Read measure lookup table and generate a list of measures' arguments
    lookup_table_full = pd.read_csv(measure_file, index_col=0)
    lookup_table = lookup_table_full.loc[design_table.columns].reset_index()
    measure_list = []
    for i in range(lookup_table.shape[0]):
        measure_list.append(lookup_table.loc[i, :].to_dict())

    # Set RUBYLIB environment variable RUBYLIB

    # Create osw file using OpenStudio and call OpenStudio command
    # to generate E+ model file
    for i in range(design_table.shape[0]):
        osw_inst = osw_template.copy()
        osw_inst['steps'] = []
        for j, measure in enumerate(measure_list):
            osw_inst['steps'].extend(
                create_measure(measure, design_table.iloc[i, j])
            )

        osw_path = osw_dir.joinpath('{}-Inst_{}.osw'.format(model_name, i+1))
        with open(osw_path, 'w') as f:
            f.write(json.dumps(osw_inst))

        # Call OpenStudio command to generate E+ model
        command_line = '{} run -m -w "{}"'.format(exe_path, str(osw_path))
        os.system(command_line)

        # Copy the in.idf to the eplus output folder
        idf_output = osw_dir.joinpath('run', 'in.idf')
        idf_file = out_dir.joinpath('{}-Inst_{}.idf'.format(model_name, i+1))
        if os.path.exists(idf_output):
            shutil.copyfile(idf_output, idf_file)
        else:
            print('''in.idf doesn't exist.''')
        # Copy the in.osm to the eplus output folder
        osm_output = osw_dir.joinpath('run', 'in.osm')
        osm_file = out_dir.joinpath('{}-Inst_{}.osm'.format(model_name, i+1))
        if os.path.exists(osm_output):
            shutil.copyfile(osm_output, osm_file)
        else:
            print('''in.osm doesn't exist.''')


if __name__ == "__main__":
    model = sys.argv[1]
    design = sys.argv[2]
    try:
        config = sys.argv[3]
    except IndexError:
        config = 'config.ini'
    try:
        measure = sys.argv[4]
    except IndexError:
        measure = 'measure_lookup.csv'
    perturb_model(model, design, config, measure)
