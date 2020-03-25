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
import multiprocessing as mp

import numpy as np
import pandas as pd

from add_measure import *


def main(config_file, run=None):
    """"""
    with open(config_file, 'r') as f:
        config = json.load(f)

    root_dir = pathlib.Path.cwd()
    input_dir = root_dir.joinpath(config['InputDirectory'])
    model_base = input_dir.joinpath(config['BaseModel'])
    model_df = input_dir.joinpath(config['DFModel'])
    weather = input_dir.joinpath(config['Weather'])
    design = input_dir.joinpath(config['Design'])

    perturb_model(model_base, weather, design, config, run)
    perturb_model(model_df, weather, design, config, run)


def perturb_model(
        osm_file, epw_file, design_file, config,
        run=None, measure_table=None, processes=None):
    """"""
    run = 'osm' if run is None else run
    measure_table = (
        'measure_lookup.csv' if measure_table is None else measure_table
    )
    processes = 4 if processes is None else processes

    # OpenStudio exe path
    exe_path = config['OpenStudioPath']

    # Directory where OpenStudio measures are located
    measure_dir = pathlib.Path.cwd().joinpath(config['MeasureDirectory'])

    # OenStudio Model name
    mdl_name = osm_file.stem

    # Workflow root directory
    sim_dir = pathlib.Path.cwd().joinpath('sim')

    # Directory for parametric analysis workflow outputs
    osw_dir = sim_dir.joinpath('osw')

    # Directory for generated osm instances
    osm_dir = sim_dir.joinpath('osm')

    # Directory for generated idf instances
    idf_dir = sim_dir.joinpath('idf')

    # Directory for simulation outputs
    run_dir = sim_dir.joinpath('run')

    # Directory for simulation outputs
    out_dir = sim_dir.joinpath('output')

    # Directory for analysis results
    rlt_dir = sim_dir.joinpath('result')

    # Directory for visualization plots
    plot_dir = sim_dir.joinpath('plot')

    # Create directories
    for dir_inst in [
            sim_dir, osw_dir, osm_dir, idf_dir, run_dir,
            out_dir, rlt_dir, plot_dir]:
        try:
            pathlib.Path.mkdir(dir_inst)
        except FileExistsError:
            continue

    # Create osw template and model params in JSON
    osw_template = {}
    osw_template['file_paths'] = [str(sim_dir)]
    osw_template['measure_paths'] = [str(measure_dir)]
    osw_template['seed_file'] = str(osm_file)
    osw_template['weather_file'] = str(epw_file)

    # Read experimental design of model parameter values
    design_table = pd.read_csv(design_file)

    # Read measure lookup table and generate a list of measures' arguments
    lookup_table_full = pd.read_csv(measure_table, index_col=0)
    lookup_table = lookup_table_full.loc[design_table.columns].reset_index()
    measure_list = []
    for i in range(lookup_table.shape[0]):
        measure_list.append(lookup_table.loc[i, :].to_dict())

    # Create osw file using OpenStudio
    n_run = design_table.shape[0]
    osw_path = []
    run_inst_dirs = []

    # Reference case
    run_inst_dir = run_dir.joinpath(mdl_name)
    run_inst_dirs.append(run_inst_dir)
    osw_inst = osw_template.copy()
    osw_inst['run_directory'] = str(run_inst_dir)
    osw_inst['steps'] = [
        {
            'measure_dir_name': 'AddOutputVariable',
            'arguments': {
                'variable_name': 'Site Outdoor Air Drybulb Temperature',
                'reporting_frequency': 'timestep'
            }
        }
    ]
    osw_path_inst = osw_dir.joinpath('{}.osw'.format(mdl_name))
    with open(osw_path_inst, 'w') as f:
        f.write(json.dumps(osw_inst))
    osw_path.append(osw_path_inst)

    # Parametric runs
    for i in range(n_run):
        # Run directory
        run_inst_dir = run_dir.joinpath('{}_Inst_{}'.format(mdl_name, i+1))
        run_inst_dirs.append(run_inst_dir)

        # OS workflow
        osw_inst = osw_template.copy()
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
        arg = '{} run -w'.format(exe_path)
    elif run == 'idf':
        # EnergyPlus workflow
        arg = '{} run -m -w'.format(exe_path)
    else:
        arg = '{} run -w'.format(exe_path)

    os.system('{} "{}"'.format(arg, str(osw_path[0])))
    copy_model_file(run_inst_dirs[0], osm_dir, mdl_name, 'osm')
    copy_model_file(run_inst_dirs[0], idf_dir, mdl_name, 'idf')

    # Group simulation
    try:
        with mp.Pool(processes=processes) as pool:
            pool.starmap(run_sim, [(arg, str(p)) for p in osw_path[1:]])
    except NameError:
        for i in range(n_run):
            os.system(
                '{} "{}"'.format(arg, str(osw_path[i+1]))
            )

    for i in range(1, n_run+1):
        # os.system('{} run {}-w "{}"'.format(exe_path, arg, str(osw_path[i])))

        # Copy the in.idf and in.osm to the model folder
        file_name = '{}-Inst_{}'.format(mdl_name, i)
        copy_model_file(run_inst_dirs[i], osm_dir, file_name, 'osm')
        copy_model_file(run_inst_dirs[i], idf_dir, file_name, 'idf')

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


def run_sim(arg, osw_path):
    """"""
    os.system('{} "{}"'.format(arg, osw_path))


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
    config = sys.argv[1]
    try:
        run = sys.argv[2]
    except IndexError:
        run = 'osm'
    main(config, run)
