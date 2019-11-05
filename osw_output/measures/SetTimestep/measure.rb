# insert your copyright here

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# start the measure
class SetTimeStep < OpenStudio::Measure::ModelMeasure
  # human readable name
  def name
    # Measure name should be the title case of the class name.
    return 'SetTimeStep'
  end

  # human readable description
  def description
    return 'set simulation timestep'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'modify simulation timestep'
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new

    # make an argument for setting timestep

    timestep = OpenStudio::Measure::OSArgument.makeIntegerArgument('timestep', true)

    timestep.setDisplayName('New timestep')
    timestep.setDescription('Number of timesteps per hour .')
    timestep.setDefaultValue(4)
    args << timestep

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
    timestep = runner.getIntegerArgumentValue('timestep', user_arguments)

    model_time_step = model.getTimestep
    old_timestep = model_time_step.numberOfTimestepsPerHour
    runner.registerWarning("The model started with timestep of #{old_timestep}.")
    model_time_step.setNumberOfTimestepsPerHour(timestep)
    new_timestep = model_time_step.numberOfTimestepsPerHour
    runner.registerWarning("The model finished with timestep of #{new_timestep}.")
    
    return true
  end
end

# register the measure to be used by the application
SetTimeStep.new.registerWithApplication