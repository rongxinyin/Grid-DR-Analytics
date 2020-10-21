# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/


# require csv
require 'csv'
#load helper file
require "#{File.dirname(__FILE__)}/resources/os_report.rb"


# start the measure
class OutputVariablesFromCsv < OpenStudio::Ruleset::ModelUserScript

  # human readable name
  def name
    return "Output variables from csv"
  end

  # human readable description
  def description
    return "Loads a csv file from a path (see the resource folder), and adds the report variables.
There's a helper function to create a reporting schedule that will report one tuesday, one saturday, and one sunday per month. Helpful to report at detailed timestep without overloading the SQL file"
  end

  # human readable description of modeling approach
  def modeler_description
    return """See \\test\\output_variables.csv for an example of setup.
In the CSV file, only the fields key, variable_name and reporting_frequency are mandatory.
The field 'reporting_schedule':
- if blank, always 1,
- if reporting_schedule_3_days_per_month a schedule reporting a tuesday, a saturday and a sunday will be created and applied.
- you can also supply a schedule from your model. If the schedule doesn't exist, a warning is issued and the variable isn't requested.

In the 'key' field you add several keys separated by commas, and it will create separate variables for each.

In Windows Explorer You use Shift + Right click on your file then 'copy as path' and there is no need to strip the leading and trailing quote marks, I'm handling it in the procedure"""
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Ruleset::OSArgumentVector.new

    # Path argument
    file_path = OpenStudio::Ruleset::OSArgument.makeStringArgument("file_path", true)
    file_path.setDisplayName("Enter the path to the file")
    file_path.setDescription("Example: 'C:\\Projects\\output_variables.csv'")
    args << file_path

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
    file_path = runner.getStringArgumentValue("file_path", user_arguments)

    # check the file path for reasonableness
    if file_path.empty?
      runner.registerError("Empty path was entered.")
      return false
    end

    # Strip out the potential leading and trailing quotes
    file_path.gsub!('"','')

    if !File.exist? file_path
      runner.registerError("The file at path #{file_path} doesn't exist.")
    else
      raw_data =  CSV.table(file_path)
      # Transform to array of hashes
      variables = raw_data.map { |row| row.to_hash }

      # If at least one variable has asked for a reporting schedule
      if variables.any? {|h| (h[:reporting_schedule] != nil) && (h[:reporting_schedule].downcase == 'reporting_schedule_3_days_per_month')}
        model.create_reporting_schedule_3days_per_month()
      end

      numberVariables = 0
      requestedVariables = 0
      variables.each do |var|

        if var[:key]
          keys = var[:key].split(",").each {|v| v.strip}
        else
          keys = [nil]
        end

        keys.each do |key|

          requestedVariables += 1

          if var[:reporting_schedule].nil?
            model.create_output_variable(var[:metric], key, var[:variable_name], var[:reporting_frequency], nil)
            numberVariables += 1
            #puts "#{key}, #{var[:variable_name]} - YES"
          else
            reporting_schedule = model.getScheduleByName(var[:reporting_schedule])
            if reporting_schedule.empty?
              runner.registerWarning("For (key, variable_name) = (#{key.nil? ? "*": key}, #{var[:variable_name]}), you supplied a reporting schedule named '#{var[:reporting_schedule]}' which cannot be located. Variable will NOT be requested")
              puts "#{key.nil? ? "*": key}, #{var[:variable_name]} - NOT request due to bad schedule"
            else
              reporting_schedule = reporting_schedule.get
              model.create_output_variable(var[:metric], key, var[:variable_name], var[:reporting_frequency], reporting_schedule)
              numberVariables += 1
              #puts "#{key}, #{var[:variable_name]} - YES"
            end
          end
        end

      end
    end

    # report final condition of model
    runner.registerFinalCondition("Added #{numberVariables} new variables out of #{requestedVariables} requested")

    return true

  end
  
end

# register the measure to be used by the application
OutputVariablesFromCsv.new.registerWithApplication
