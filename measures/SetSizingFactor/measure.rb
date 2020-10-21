# insert your copyright here

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# start the measure
class SetSizingFactor < OpenStudio::Measure::ModelMeasure
  def name
    return "SetSizingFactor"
  end

  # human readable description
  def description
    return "set sizing factor"
  end

  # human readable description of modeling approach
  def modeler_description
    return "set a global heating sizing factor and a global cooling sizing factor for calculating zone design heating and cooling loads"
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new

    # make an argument for setting heating sizing factor

    heating_sizing_factor = OpenStudio::Measure::OSArgument.makeDoubleArgument('heating sizing factor', true)

    heating_sizing_factor.setDisplayName('Heating sizing factor')
    heating_sizing_factor.setDescription('A global sizing factor for calculating zone design heating load .')
    heating_sizing_factor.setDefaultValue(1.2)
    args << heating_sizing_factor

    # make an argument for setting cooling sizing factor

    cooling_sizing_factor = OpenStudio::Measure::OSArgument.makeDoubleArgument('cooling sizing factor', true)

    cooling_sizing_factor.setDisplayName('Cooling sizing factor')
    cooling_sizing_factor.setDescription('A global sizing factor for calculating zone design cooling load .')
    cooling_sizing_factor.setDefaultValue(1.2)
    args << cooling_sizing_factor
    return args
  end

  # define what happens when the measure is run
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    # assign the user inputs to variables
    heating_sizing_factor = runner.getDoubleArgumentValue('heating sizing factor', user_arguments)
    cooling_sizing_factor = runner.getDoubleArgumentValue('cooling sizing factor', user_arguments)

    #get the sizing parameters of the model if it exists, otherwise creates and returns a new one
    sizing_factors = model.getSizingParameters

    #set the sizing factors 
    sizing_factors.setHeatingSizingFactor(heating_sizing_factor)
    sizing_factors.setCoolingSizingFactor(cooling_sizing_factor)

    #report the final condition
    # final_heating_sizing_factor = sizing_factors.heatingSizingFactor
    final_heating_sizing_factor = model.getSizingParameters.heatingSizingFactor
    runner.registerWarning("The model finished with heating sizing factor  of #{final_heating_sizing_factor}.")
    final_cooling_sizing_factor = sizing_factors.coolingSizingFactor
    runner.registerWarning("The model finished with cooling sizing factor  of #{final_cooling_sizing_factor}.")
    
    return true
  end
end

# register the measure to be used by the application
SetSizingFactor.new.registerWithApplication