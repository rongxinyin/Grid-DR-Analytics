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

    if design_type.lower() == 'mcs':
        params = config['Parameters']
        size = config['Size']
        design_path = input_dir.joinpath(design_file)
        generate_lhs_design(params, size, design_path)
    elif design_type.lower() == 'sa':
        params = config['Parameters']
    else:
        print("Error: Unknown analysis type")


def generate_lhs_design(params, size, out_path):
    """"""
    p = len(params)
    names = [param['name'] for param in params]
    design = pyDOE2.lhs(p, size, criterion='maximin', iterations=20)
    sample = np.empty(design.shape)
    for i, param in enumerate(params):
        d = dist_generator(param['parameters'], param['distribution'])
        sample[:, i] = d.ppf(design[:, i])

    pd.DataFrame(sample, columns=names).to_csv(out_path, index=False)


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

    switcher = {
        'Uniform': stats.uniform(loc=pars[0], scale=np.diff(pars)),
        'Normal': stats.norm(loc=pars[0], scale=pars[1]),
        'RandInt': stats.randint(low=pars[0], high=pars[1]),
    }
    return switcher.get(distribution, stats.norm())


if __name__ == "__main__":
    """"""
    config = sys.argv[1]
    generate_design(config)
