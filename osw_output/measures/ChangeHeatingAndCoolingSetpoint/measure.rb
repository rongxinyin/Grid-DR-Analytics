# insert your copyright here

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# start the measure
class ChangeHeatingAndCoolingSetpoint < OpenStudio::Measure::ModelMeasure
  # human readable name
  def name
    # Measure name should be the title case of the class name.
    return 'ChangeHeatingAndCoolingSetpoint'
  end

  # human readable description
  def description
    return 'shift or/and adjust heaing and cooling setpoint'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'shift or/and adjust heaing and cooling setpoint'
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new

    # make an argument for adjustment to cooling setpoint
    cooling_adjustment = OpenStudio::Measure::OSArgument.makeDoubleArgument('cooling_adjustment', true)
    cooling_adjustment.setDisplayName('Degrees Fahrenheit to Adjust Cooling Setpoint By')
    cooling_adjustment.setDefaultValue(1.0)
    args << cooling_adjustment

    # make an argument for adjustment to heating setpoint
    heating_adjustment = OpenStudio::Measure::OSArgument.makeDoubleArgument('heating_adjustment', true)
    heating_adjustment.setDisplayName('Degrees Fahrenheit to Adjust heating Setpoint By')
    heating_adjustment.setDefaultValue(-1.0)
    args << heating_adjustment

    # make arguments for DR start time
    start_hour = OpenStudio::Measure::OSArgument.makeIntegerArgument('start_hour', true)
    start_hour.setDisplayName('start_hour')
    start_hour.setDefaultValue(15)
    args << start_hour

    start_minute = OpenStudio::Measure::OSArgument.makeIntegerArgument('start_minute', true)
    start_minute.setDisplayName('start_minute')
    start_minute.setDefaultValue(0)
    args << start_minute

    # make arguments for DR end time
    end_hour = OpenStudio::Measure::OSArgument.makeIntegerArgument('end_hour', true)
    end_hour.setDisplayName('end_hour')
    end_hour.setDefaultValue(18)
    args << end_hour

    end_minute = OpenStudio::Measure::OSArgument.makeIntegerArgument('end_minute', true)
    end_minute.setDisplayName('end_minute')
    end_minute.setDefaultValue(0)
    args << end_minute

    # make an argument for adjustment to heating setpoint
    alter_design_days = OpenStudio::Measure::OSArgument.makeBoolArgument('alter_design_days', true)
    alter_design_days.setDisplayName('Alter Design Day Thermostats')
    alter_design_days.setDefaultValue(false)
    args << alter_design_days

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
    cooling_adjustment = runner.getDoubleArgumentValue('cooling_adjustment', user_arguments)
    heating_adjustment = runner.getDoubleArgumentValue('heating_adjustment', user_arguments)
    start_hour = runner.getIntegerArgumentValue('start_hour', user_arguments)
    end_hour = runner.getIntegerArgumentValue('end_hour', user_arguments)
    start_minute = runner.getIntegerArgumentValue('start_minute', user_arguments)
    end_minute = runner.getIntegerArgumentValue('end_minute', user_arguments)
    alter_design_days = runner.getBoolArgumentValue('alter_design_days', user_arguments)

    # check the correctness of temperature adjustment input

    if cooling_adjustment < 0
      runner.registerWarning('Lowering the cooling setpoint will increase energy use.')
    elsif cooling_adjustment.abs > 500
      runner.registerError("#{cooling_adjustment} is a larger than typical setpoint adjustment")
      return false
    elsif cooling_adjustment.abs > 50
      runner.registerWarning("#{cooling_adjustment} is a larger than typical setpoint adjustment")
    end
    if heating_adjustment > 0
      runner.registerWarning('Raising the heating setpoint will increase energy use.')
    elsif heating_adjustment.abs > 500
      runner.registerError("#{heating_adjustment} is a larger than typical setpoint adjustment")
      return false
    elsif heating_adjustment.abs > 50
      runner.registerWarning("#{heating_adjustment} is a larger than typical setpoint adjustment")
    end

    #check hour time input

    if start_hour >= 24
      runner.registerError('start hour cannot be larger than 24!')
      return false
    elsif start_hour < 0
      runner.registerError('start hour cannot be smaller than 0!')
      return false
    end
    if end_hour >= 24
      runner.registerError('end hour cannot be larger than 24!')
      return false
    elsif end_hour < 0
      runner.registerError('end hour cannot be smaller than 0!')
      return false
    elsif end_hour < start_hour
      runner.registerError('end hour cannot be smaller than start hour!')
      return false
    end

     #check hour time input

    if start_minute >= 60
      runner.registerError('start minute cannot be larger than 60!')
      return false
    elsif start_minute < 0
      runner.registerError('start minute cannot be smaller than 0!')
      return false
    end
    if end_minute >= 60
      runner.registerError('end minute cannot be larger than 60!')
      return false
    elsif end_minute < 0
      runner.registerError('end minute cannot be smaller than 0!')
      return false
    elsif end_minute < start_minute
      runner.registerError('end minute cannot be smaller than start minute!')
      return false
    end

    # setup OpenStudio units that we will need
    temperature_ip_unit = OpenStudio.createUnit('F').get
    temperature_si_unit = OpenStudio.createUnit('C').get

    # define starting units
    cooling_adjustment_ip = OpenStudio::Quantity.new(cooling_adjustment, temperature_ip_unit)
    heating_adjustment_ip = OpenStudio::Quantity.new(heating_adjustment, temperature_ip_unit)

    # push schedules to hash to avoid making unnecessary duplicates
    clg_set_schs = {}
    htg_set_schs = {}

    # get thermostats and setpoint schedules
    thermostats = model.getThermostatSetpointDualSetpoints
    thermostats.each do |thermostat|
      # setup new cooling setpoint schedule
      clg_set_sch = thermostat.coolingSetpointTemperatureSchedule
      if !clg_set_sch.empty?
        # clone of not alredy in hash
        if clg_set_schs.key?(clg_set_sch.get.name.to_s)
          new_clg_set_sch = clg_set_schs[clg_set_sch.get.name.to_s]
        else
          new_clg_set_sch = clg_set_sch.get.clone(model)
          new_clg_set_sch = new_clg_set_sch.to_Schedule.get
          new_clg_set_sch_name = new_clg_set_sch.setName("#{new_clg_set_sch.name} adjusted by #{cooling_adjustment_ip}")

          # add to the hash
          clg_set_schs[clg_set_sch.get.name.to_s] = new_clg_set_sch
        end
        # hook up clone to thermostat
        thermostat.setCoolingSetpointTemperatureSchedule(new_clg_set_sch)
      else
        runner.registerWarning("Thermostat '#{thermostat.name}' doesn't have a cooling setpoint schedule")
      end

      # setup new heating setpoint schedule
      htg_set_sch = thermostat.heatingSetpointTemperatureSchedule
      if !htg_set_sch.empty?
        # clone of not already in hash
        if htg_set_schs.key?(htg_set_sch.get.name.to_s)
          new_htg_set_sch = htg_set_schs[htg_set_sch.get.name.to_s]
        else
          new_htg_set_sch = htg_set_sch.get.clone(model)
          new_htg_set_sch = new_htg_set_sch.to_Schedule.get
          new_htg_set_sch_name = new_htg_set_sch.setName("#{new_htg_set_sch.name} adjusted by #{heating_adjustment_ip}")

          # add to the hash
          htg_set_schs[htg_set_sch.get.name.to_s] = new_htg_set_sch
        end
        # hook up clone to thermostat
        thermostat.setHeatingSetpointTemperatureSchedule(new_htg_set_sch)
      else
        runner.registerWarning("Thermostat '#{thermostat.name}' doesn't have a heating setpoint schedule.")
      end
    end

    # setting up variables to use for initial and final condition
    clg_sch_set_values = [] # may need to flatten this
    htg_sch_set_values = [] # may need to flatten this
    final_clg_sch_set_values = []
    final_htg_sch_set_values = []

    # consider issuing a warning if the model has un-conditioned thermal zones (no ideal air loads or hvac)
    zones = model.getThermalZones
    zones.each do |zone|
      # if you have a thermostat but don't have ideal air loads or zone equipment then issue a warning
      if !zone.thermostatSetpointDualSetpoint.empty? && !zone.useIdealAirLoads && (zone.equipment.size <= 0)
        runner.registerWarning("Thermal zone '#{zone.name}' has a thermostat but does not appear to be conditioned.")
      end
    end

    # shift_time1 = OpenStudio::Time.new(starthour)
    # shift_time2 = OpenStudio::Time.new(endhour)
    # shift_time3 = OpenStudio::Time.new(24, 0, 0)
        # time_0 = OpenStudio::Time.new(0, 0, 0, 0)
    # time_24 =  OpenStudio::Time.new(0, 24, 0, 0)
    time_start = OpenStudio::Time.new(0, start_hour, start_minute, 0)
    time_end = OpenStudio::Time.new(0, end_hour, end_minute, 0)

    clg_set_schs.each do |k, v| # old name and new object for schedule
      if !v.to_ScheduleRuleset.empty?

        # array to store profiles in
        profiles = []
        schedule = v.to_ScheduleRuleset.get

        # push default profiles to array
        default_rule = schedule.defaultDaySchedule
        profiles << default_rule

        # push profiles to array
        rules = schedule.scheduleRules
        rules.each do |rule|
          day_sch = rule.daySchedule
          profiles << day_sch
        end

        # add design days to array
        if alter_design_days == true
          summer_design = schedule.summerDesignDaySchedule
          winter_design = schedule.winterDesignDaySchedule
          profiles << summer_design
          # profiles << winter_design
        end

        # time objects to use in meausre


        profiles.each do |sch_day|
          day_time_vector = sch_day.times
          day_value_vector = sch_day.values
          clg_sch_set_values << day_value_vector
          sch_day.clearValues
          flag = 0
          for i in 0..(day_time_vector.size - 1)
            v_si = OpenStudio::Quantity.new(day_value_vector[i], temperature_si_unit)
            v_ip = OpenStudio.convert(v_si, temperature_ip_unit).get
            target_v_ip = v_ip + cooling_adjustment_ip
            target_temp_si = OpenStudio.convert(target_v_ip, temperature_si_unit).get
            if day_time_vector[i] > time_start && day_time_vector[i] < time_end && flag == 0
              sch_day.addValue(time_start, day_value_vector[i])
              sch_day.addValue(day_time_vector[i],target_temp_si.value)
              sch_day.addValue(time_end,target_temp_si.value)
              flag = 1
            elsif day_time_vector[i] > time_start && day_time_vector[i] < time_end && flag == 1
              sch_day.addValue(day_time_vector[i],target_temp_si.value)
            elsif day_time_vector[i] <= time_start &&  flag == 0
              sch_day.addValue(time_start, day_value_vector[i])
              sch_day.addValue(day_time_vector[i],day_value_vector[i])
              sch_day.addValue(time_end,target_temp_si.value)
              flag = 1
            elsif day_time_vector[i] >= time_end &&  flag == 0
              sch_day.addValue(time_start, day_value_vector[i])
              sch_day.addValue(day_time_vector[i],day_value_vector[i])
              sch_day.addValue(time_end,target_temp_si.value)
              flag = 1
            else
              sch_day.addValue(day_time_vector[i],day_value_vector[i])
            end
          end
          final_clg_sch_set_values << sch_day.values
        end
      else
        runner.registerWarning("Schedule '#{k}' isn't a ScheduleRuleset object and won't be altered by this measure.")
        v.remove # remove un-used clone
      end
    end
        # make heating schedule adjustments and rename. Put in check to skip and warn if schedule not ruleset
    htg_set_schs.each do |k, v| # old name and new object for schedule
      if !v.to_ScheduleRuleset.empty?

        # array to store profiles in
        profiles = []
        schedule = v.to_ScheduleRuleset.get

        # push default profiles to array
        default_rule = schedule.defaultDaySchedule
        profiles << default_rule

        # push profiles to array
        rules = schedule.scheduleRules
        rules.each do |rule|
          day_sch = rule.daySchedule
          profiles << day_sch
        end

        # add design days to array
        if alter_design_days == true
          summer_design = schedule.summerDesignDaySchedule
          winter_design = schedule.winterDesignDaySchedule
          # profiles << summer_design
          profiles << winter_design
        end

        profiles.each do |sch_day|
          day_time_vector = sch_day.times
          day_value_vector = sch_day.values
          clg_sch_set_values << day_value_vector
          sch_day.clearValues
          flag = 0
          for i in 0..(day_time_vector.size - 1)
            v_si = OpenStudio::Quantity.new(day_value_vector[i], temperature_si_unit)
            v_ip = OpenStudio.convert(v_si, temperature_ip_unit).get
            target_v_ip = v_ip + heating_adjustment_ip
            target_temp_si = OpenStudio.convert(target_v_ip, temperature_si_unit).get
            if day_time_vector[i] > time_start && day_time_vector[i] < time_end && flag == 0
              sch_day.addValue(time_start, day_value_vector[i])
              sch_day.addValue(day_time_vector[i],target_temp_si.value)
              sch_day.addValue(time_end,target_temp_si.value)
              flag = 1
            elsif day_time_vector[i] > time_start && day_time_vector[i] < time_end && flag == 1
              sch_day.addValue(day_time_vector[i],target_temp_si.value)
            elsif day_time_vector[i] <= time_start &&  flag == 0
              sch_day.addValue(time_start, day_value_vector[i])
              sch_day.addValue(day_time_vector[i],day_value_vector[i])
              sch_day.addValue(time_end,target_temp_si.value)
              flag = 1
            elsif day_time_vector[i] >= time_end &&  flag == 0
              sch_day.addValue(time_start, day_value_vector[i])
              sch_day.addValue(day_time_vector[i],day_value_vector[i])
              sch_day.addValue(time_end,target_temp_si.value)
              flag = 1
            else
              sch_day.addValue(day_time_vector[i],day_value_vector[i])
            end
          end
          final_htg_sch_set_values << sch_day.values
        end
      else
        runner.registerWarning("Schedule '#{k}' isn't a ScheduleRuleset object and won't be altered by this measure.")
        v.remove # remove un-used clone
      end
    end

    # reporting final condition of model

    runner.registerFinalCondition("Final cooling setpoints used in the model range  Final heating setpoints used in the model range.")

    return true
  end
end      


# register the measure to be used by the application
ChangeHeatingAndCoolingSetpoint.new.registerWithApplication
