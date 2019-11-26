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
import sqlite3

import numpy as np
import pandas as pd

from add_measure import *


def perturb_model(
        osm_file, epw_file, design_file, config_file, measure_file, run=None):
    """"""

    # Provide OpenStudio path and current file path
    with open(config_file, 'r') as f:
        config = json.load(f)
        exe_path = config['OpenStudioPath']
        measure_folder = config['MeasureDirectory']

    # OenStudio Model name
    mdl_name = pathlib.Path(osm_file).stem

    # Workflow root directory
    root_dir = pathlib.Path.cwd()

    # Directory where OpenStudio measures are located
    measure_dir = root_dir.joinpath(measure_folder)

    # Directory for parametric analysis workflow outputs
    osw_dir = root_dir.joinpath('osw')

    # Directory for generated model instances
    mdl_dir = root_dir.joinpath('model')

    # Directory for simulation outputs
    run_dir = root_dir.joinpath('run')

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

    # Create osw template and model params in JSON
    osw_template = {}
    osw_template['file_paths'] = [str(root_dir)]
    osw_template['measure_paths'] = [str(measure_dir)]
    osw_template['seed_file'] = str(pathlib.Path(osm_file))
    osw_template['weather_file'] = str(pathlib.Path(epw_file))

    # Read experimental design of model parameter values
    design_table = pd.read_csv(design_file)

    # Read measure lookup table and generate a list of measures' arguments
    lookup_table_full = pd.read_csv(measure_file, index_col=0)
    lookup_table = lookup_table_full.loc[design_table.columns].reset_index()
    measure_list = []
    for i in range(lookup_table.shape[0]):
        measure_list.append(lookup_table.loc[i, :].to_dict())

    # Create osw file using OpenStudio
    n_run = design_table.shape[0]
    osw_path = []
    run_inst_dirs = []
    for i in range(n_run):
        osw_inst = osw_template.copy()

        # Run directory
        run_inst_dir = run_dir.joinpath('{}_Inst_{}'.format(mdl_name, i+1))
        run_inst_dirs.append(run_inst_dir)
        osw_inst['run_directory'] = str(run_inst_dir)

        # Measures
        osw_inst['steps'] = []
        for j, measure in enumerate(measure_list):
            osw_inst['steps'].extend(
                create_measure(measure, design_table.iloc[i, j])
            )

        # TEMPORARY: Add outside air temperature output
        osw_inst['steps'].append(
            {
                'measure_dir_name': 'AddOutputVariable',
                'arguments': {
                    'variable_name': 'Site Outdoor Air Drybulb Temperature',
                    'reporting_frequency': 'timestep'
                }
            }
        )

        # Generate osw files
        osw_path_inst = osw_dir.joinpath(
            '{}-Inst_{}.osw'.format(mdl_name, i+1)
        )
        with open(osw_path_inst, 'w') as f:
            f.write(json.dumps(osw_inst))
        osw_path.append(osw_path_inst)

    # Call OpenStudio command to generate E+ model and/or run simulation
    if run == 'osm':
        # OpenStudio workflow
        for i in range(n_run):
            command_line = '{} run -w "{}"'.format(
                exe_path, str(osw_path[i])
            )
            os.system(command_line)

            # Copy the in.idf and in.osm to the model folder
            for file_ext in ['idf', 'osm']:
                file_name = '{}-Inst_{}'.format(mdl_name, i+1)
                copy_model_file(
                    run_inst_dirs[i], mdl_dir.joinpath(file_ext),
                    file_name, file_ext
                )

    else if run == 'idf':
        # EnergyPlus workflow
        for i in range(n_run):
            command_line = '{} run -m -w "{}"'.format(
                exe_path, str(osw_path[i])
            )
            os.system(command_line)

            # Copy the in.idf and in.osm to the model folder
            for file_ext in ['idf', 'osm']:
                file_name = '{}-Inst_{}'.format(mdl_name, i+1)
                copy_model_file(
                    run_inst_dirs[i], mdl_dir.joinpath(file_ext),
                    file_name, file_ext
                )
        pass

    else:
        # Post-process only
        pass

    # TEMPORARY: Collect simulation outputs
    rng = pd.date_range('1/1/2017 0:00', '12/31/2017 23:45', freq='15T')
    out_spec = {
        'Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)': (
            'SELECT Value FROM ReportVariableWithTime '
            'WHERE KeyValue="Environment" '
            'AND Name="Site Outdoor Air Drybulb Temperature" '
            'AND ReportingFrequency="Zone Timestep"'
        ),
        'Electricity:Facility [J](TimeStep)': (
            'SELECT Value FROM ReportVariableWithTime '
            'WHERE Name="Electricity:Facility" '
            'AND ReportingFrequency="Zone Timestep"'
        )
    }
    for d in run_dir.iterdir():
        if d.is_dir():
            out_file = d.joinpath('eplusout.sql')
            rlt_file = out_dir.joinpath('{}.csv'.format(d.stem))
            with sqlite3.connect(out_file) as conn:
                df = pd.DataFrame(index=rng)
                for name, query in out_spec.items():
                    df[name] = pd.read_sql_query(query, conn).values
            df.to_csv(rlt_file)


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
    (model, weather, design) = tuple([sys.argv[i] for i in range(1, 4)])
    args = [model, weather, design, 'config.ini', 'measure_lookup.csv', 'osm']
    for i in range(4, 7):
        try:
            args[i-1] = sys.argv[i]
        except IndexError:
            break
    perturb_model(*args)
