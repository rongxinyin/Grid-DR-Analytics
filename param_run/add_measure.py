"""
functions for creating different measure given the model params

"""


import copy


def create_measure(params, value):
    output = {}
    output.update({'measure_dir_name': params['Measure Directory']})
    output['arguments'] = {}
    output['arguments'][params['Measure Argument']] = value

    # TODO: Need customization for each parameter measure
    if params['index'].lower() == 'wwr':
        outputs = []
        facades = ['North', 'East', 'South', 'West']
        for facade in facades:
            output_inst = copy.deepcopy(output)
            output_inst['arguments']['facade'] = facade
            outputs.append(output_inst)
        out = outputs
    else:
        out = [output]
    return out
