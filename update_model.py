'''
functions for creating different measure given the model params
'''
def create_prototype_measure(params):
    output = dict()
    output.update({'measure_dir_name': 'CreateDOEPrototypeBuilding'})
    output['arguments']={}
    output['arguments']['building_type'] = params.get('bldg_type')
    output['arguments']['template'] = params.get('bldg_vintage')
    output['arguments']['climate_zone'] = params.get('climate_zone')
    return output


def create_rvalue_measure(params):
    output = dict()
    output.update({'measure_dir_name': 'IncreaseWallRValue'})
    output['arguments']={}
    output['arguments']['r_value'] = params.get('WallRValue')
    return output

