# -*- coding: utf-8 -*-

"""
Script to generate design matrix for analysis

"""

import pathlib
import sys
import json

from scipy import stats
import numpy as np
import pandas as pd

import pyDOE2
from SALib.sample import morris


def generate_design(config_file):
    """"""
    with open(config_file, 'r') as f:
        config = json.load(f)

    root_dir = pathlib.Path.cwd().joinpath('sim')
    input_dir = pathlib.Path.cwd().joinpath(config['InputDirectory'])
    output_dir = root_dir.joinpath('output')
    design_type = config['DesignType']
    design_file = config['Design']
    design_path = input_dir.joinpath(design_file)

    if design_type.lower() == 'mcs':
        params = config['Parameters']
        size = config['Size']
        generate_lhs_design(params, size, input_dir, design_file)
    elif design_type.lower() == 'sa':
        params = config['Parameters']
        problem = config['Problem']
        generate_morris_design(params, problem, input_dir, design_file)
    else:
        print("Error: Unknown analysis type")


def generate_lhs_design(params, size, out_dir, filename):
    """"""
    # Design setting
    p = len(params)
    names = [param['name'] for param in params]

    # Generate design matrix on parameter CDF space from [0, 1]
    design = pyDOE2.lhs(p, size, criterion='maximin', iterations=20)

    # Translate design matrix into parameter sample values
    sample = np.empty(design.shape)

    for i, param in enumerate(params):
        if param['form'].lower() == 'actual':
            dist_params = param['parameters']
        else:
            # TODO Support other forms of uncertainty
            dist_params = param['parameters']
        d = dist_generator(dist_params, param['distribution'])
        sample[:, i] = d.ppf(design[:, i])

    # Export design sample
    pd.DataFrame(sample, columns=names).to_csv(
        out_dir.joinpath(filename), index=False
    )


def generate_morris_design(params, setting, out_dir, filename):
    """"""
    # Design setting
    p = len(params)
    names = [param['name'] for param in params]
    problem = {
        'num_vars': p,
        'names': names,
        'bounds': np.tile(np.array([1e-3, 1 - 1e-3]), (p, 1))
    }

    # Generate design matrix on parameter CDF space from [0, 1]
    design = morris.sample(
        problem, N=setting['r'], num_levels=setting['levels']
    )

    # Translate design matrix into parameter sample values
    sample = np.empty(design.shape)
    for i, param in enumerate(params):
        if param['form'].lower() == 'actual':
            dist_params = param['parameters']
        else:
            # TODO Support other forms of uncertainty
            dist_params = param['parameters']
        d = dist_generator(dist_params, param['distribution'])
        sample[:, i] = d.ppf(design[:, i])

    # Export design sample
    pd.DataFrame(sample, columns=names).to_csv(
        out_dir.joinpath(filename), index=False
    )
    pd.DataFrame(design, columns=names).to_csv(
        out_dir.joinpath(filename.replace('.csv', '_cdf.csv')), index=False
    )


def dist_generator(pars, distribution=None):
    """
    Generate SciPy distribution instance.

    Arguments:

    pars: NumPy 1-D array of two elements
        Parameters of the specified distribution of the uncertainty

    """
    if distribution is None:
        distribution = 'Uniform'
        print("Warning: Missing distribution type; set to uniform by default")

    if distribution == 'Uniform':
        dist = stats.uniform(loc=pars[0], scale=np.diff(pars))
    elif distribution == 'Normal':
        dist = stats.norm(loc=pars[0], scale=pars[1])
    elif distribution == 'RandInt':
        dist = stats.randint(low=pars[0], high=pars[1])
    elif distribution == 'Triangle':
        dist = stats.triang(
            c=(pars[2] - pars[0]) / np.diff(pars[:2]),
            loc=pars[0], scale=np.diff(pars[:2]),
        )
    else:
        dist = stats.uniform()

    return dist


if __name__ == "__main__":
    """"""
    config = sys.argv[1]
    generate_design(config)
