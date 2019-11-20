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

def create_timestep_measure(params):
    output = dict()
    output.update({'measure_dir_name': 'SetTimestep'})
    output['arguments']={}
    output['arguments']['timestep'] = params.get('time_step')
    return output

def create_rvalue_measure(params):
    output = dict()
    output.update({'measure_dir_name': 'IncreaseWallRValue'})
    output['arguments']={}
    output['arguments']['r_value'] = params.get('WallRValue')
    return output

def create_gta_measure(params):
    output = dict()
    output.update({'measure_dir_name': 'ChangeHeatingAndCoolingSetpoint'})
    output['arguments']={}
    output['arguments']['cooling_adjustment'] = params.get('reset_deg')
    output['arguments']['heating_adjustment'] = 0
    output['arguments']['start_hour'] = params.get('start_hour')
    output['arguments']['end_hour'] = params.get('end_hour')
    return output

def create_precool_measure(params):
    output = dict()
    output.update({'measure_dir_name': 'ChangeHeatingAndCoolingSetpoint'})
    output['arguments']={}
    output['arguments']['cooling_adjustment'] = 0 - int(params.get('precool_deg'))
    output['arguments']['heating_adjustment'] = 0
    output['arguments']['start_hour'] = int(params.get('start_hour'))-int(params.get('precool_hours'))
    output['arguments']['end_hour'] = params.get('start_hour')
    return output