"""
Main workflow to perturb OpenStudio model parameters and analyze DF metrics
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


def perturb_model(osm_file, design_file, config_file, measure_file, run=None):
    """"""
    run = 'osm' if run is None else 'idf'

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

    # Create osw file using OpenStudio
    n_run = design_table.shape[0]
    for i in range(n):
        osw_inst = osw_template.copy()
        osw_inst['steps'] = []
        for j, measure in enumerate(measure_list):
            osw_inst['steps'].extend(
                create_measure(measure, design_table.iloc[i, j])
            )

        osw_path = osw_dir.joinpath('{}-Inst_{}.osw'.format(model_name, i+1))
        with open(osw_path, 'w') as f:
            f.write(json.dumps(osw_inst))

    # Call OpenStudio command to generate E+ model and/or run simulation
    if run == 'osm':
        # OpenStudio workflow
        for i in range(n_run):
            command_line = '{} run -w "{}"'.format(exe_path, str(osw_path))
            os.system(command_line)
    else:
        # EnergyPlus workflow
        for i in range(n_run):
            command_line = '{} run -m -w "{}"'.format(exe_path, str(osw_path))
            os.system(command_line)

            # Copy the in.idf and in.osm to the eplus output folder
            for model in ['idf', 'osm']:
                copy_model_file(osw_dir, out_dir, model_name, i+1, model)


def copy_model_file(src_dir, dst_dir, name, idx, file_type=None):
    """Copy energy model file."""
    file_type = 'osm' if file_type is None else 'idf'

    src_file = src_dir.joinpath('run', 'in.{}'.format(file_type))
    dst_file = dst_dir.joinpath('{}-Inst_{}.{}'.format(name, idx, file_type))
    try:
        shutil.copyfile(src_file, dst_file)
    except FileNotFoundError:
        print('''in.{} doesn't exist.'''.format(file_type))


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
