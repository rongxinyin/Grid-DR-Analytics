#start the measure
class ChangeVAVBoxMinimumAirflowFraction < OpenStudio::Ruleset::ModelUserScript

  #define the name that a user will see, this method may be deprecated as
  #the display name in PAT comes from the name field in measure.xml
  def name
    return "Change VAV Box Minimum Airflow Fraction"
  end

  #define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Ruleset::OSArgumentVector.new

    #populate choice argument for constructions that are applied to surfaces in the model
    loop_handles = OpenStudio::StringVector.new
    loop_display_names = OpenStudio::StringVector.new

    #putting air loops and names into hash
    loop_args = model.getAirLoopHVACs
    loop_args_hash = {}
    loop_args.each do |loop_arg|
      loop_args_hash[loop_arg.name.to_s] = loop_arg
    end

    #looping through sorted hash of air loops
    loop_args_hash.sort.map do |key,value|
      show_loop = false
      components = value.demandComponents
      components.each do |component|
        if not component.to_AirTerminalSingleDuctVAVReheat.empty?
          show_loop = true
        end
      end

      #if loop as object of correct type then add to hash.
      if show_loop == true
        loop_handles << value.handle.to_s
        loop_display_names << key
      end
    end

    #add building to string vector with air loops
    building = model.getBuilding
    loop_handles << building.handle.to_s
    loop_display_names << "*All Air Loops*"

    #make an argument for air loops
    object = OpenStudio::Ruleset::OSArgument::makeChoiceArgument("object", loop_handles, loop_display_names,true)
    object.setDisplayName("Choose an Air Loop to Alter.")
    object.setDefaultValue("*All Air Loops*") #if no loop is chosen this will run on all air loops
    args << object

    #make an argument for minimum airflow fraction
    minimum_airflow_fraction = OpenStudio::Ruleset::OSArgument::makeDoubleArgument("minimum_airflow_fraction",true)
    minimum_airflow_fraction.setDisplayName("Constant Minimum Airflow Fraction")
    minimum_airflow_fraction.setDefaultValue(0.3)
    args << minimum_airflow_fraction

    return args
  end #end the arguments method

  #define what happens when the measure is cop
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)

    #use the built-in error checking
    if not runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    #assign the user inputs to variables
    object = runner.getOptionalWorkspaceObjectChoiceValue("object",user_arguments,model) #model is passed in because of argument type
    minimum_airflow_fraction = runner.getDoubleArgumentValue("minimum_airflow_fraction",user_arguments)

    #check the loop for reasonableness
    apply_to_all_loops = false
    loop = nil
    if object.empty?
      handle = runner.getStringArgumentValue("loop",user_arguments)
      if handle.empty?
        runner.registerError("No loop was chosen.")
      else
        runner.registerError("The selected loop with handle '#{handle}' was not found in the model. It may have been removed by another measure.")
      end
      return false
    else
      if not object.get.to_Loop.empty?
        loop = object.get.to_Loop.get
      elsif not object.get.to_Building.empty?
        apply_to_all_loops = true
      else
        runner.registerError("Script Error - argument not showing up as loop.")
        return false
      end
    end  #end of if loop.empty?

    #check the minimum_airflow_fraction for reasonableness
    if minimum_airflow_fraction < 0
      runner.registerError("Please enter a value greater than 0 for Constant Minimum Airflow Fraction")
      return false
    elsif minimum_airflow_fraction > 1
      runner.registerError("Please enter a value less than 1 for Constant Minimum Airflow Fraction")
      return false
    elsif minimum_airflow_fraction < 0.1
      runner.registerWarning("Constant Minimum Airflow Fraction #{minimum_airflow_fraction} is very low.  10% is a typical minimum for rangeability of VAV terminal boxes.")
    elsif minimum_airflow_fraction > 0.5
      runner.registerWarning("Constant Minimum Airflow Fraction #{minimum_airflow_fraction} is very high.  30% is a typical minimum fraction for VAV terminal boxes, but can be higher.  Higher values can represent dampers stuck open.")
    else
      runner.registerInfo("Constant Minimum Airflow Fraction #{minimum_airflow_fraction} is reasonable.")
    end
	
    #get loops for measure
    if apply_to_all_loops
      loops = model.getAirLoopHVACs
    else
      loops = []
      loops << loop
    end

    #loop through air loops
    loops.each do |loop|
      loop = loop.to_AirLoopHVAC.get
      thermal_zones = loop.thermalZones	  
      #find thermal zones on loop
      thermal_zones.each do |thermal_zone|
        #get the VAV boxes for the thermal zone
        vav_boxes = thermal_zone.equipment
        vav_boxes.each do |vav_box|
          airterminal = vav_box.to_AirTerminalSingleDuctVAVReheat
          #alter equipment of the correct type
          if not airterminal.empty?
            airterminal = airterminal.get
            #change the zoneMinimumAirFlowMethod
            airterminal.setZoneMinimumAirFlowMethod("Constant")
            airterminal.setConstantMinimumAirFlowFraction(minimum_airflow_fraction)
          end #if not airterminal.empty?
        end #end vav_boxes.each do
      end #end thermal_zones.each do
	  end #end loops.each do
    
  return true

  end
end

#this allows the measure to be used by the application
ChangeVAVBoxMinimumAirflowFraction.new.registerWithApplication