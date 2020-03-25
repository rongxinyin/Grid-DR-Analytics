require 'openstudio'
require 'openstudio/ruleset/ShowRunnerOutput'

require "#{File.dirname(__FILE__)}/../measure.rb"

require 'test/unit'

class ChangeVAVBoxMinimumAirflowFraction_Test < Test::Unit::TestCase

  def test_ChangeVAVBoxMinimumAirflowFraction_single_air_loop_BadInputs

    # create an instance of the measure
    measure = ChangeVAVBoxMinimumAirflowFraction.new

    # create an instance of a runner
    runner = OpenStudio::Ruleset::OSRunner.new

    # make an empty model
    model = OpenStudio::Model::Model.new

    # get arguments and test that they are what we are expecting
    arguments = measure.arguments(model)
    assert_equal(2, arguments.size)
    count = -1
    assert_equal("object", arguments[count += 1].name)
    assert_equal("minimum_airflow_fraction", arguments[count += 1].name)

    # load the test model
    translator = OpenStudio::OSVersion::VersionTranslator.new
    path = OpenStudio::Path.new(File.dirname(__FILE__) + "/0320_ModelWithHVAC_01.osm")
    model = translator.loadModel(path)
    assert((not model.empty?))
    model = model.get

    # set argument values to good values and run the measure on model with spaces
    arguments = measure.arguments(model)
    argument_map = OpenStudio::Ruleset::OSArgumentMap.new

    count = -1

    object = arguments[count += 1].clone
    assert(object.setValue("Packaged Rooftop VAV with Reheat"))
    argument_map["object"] = object

    minimum_airflow_fraction = arguments[count += 1].clone
    assert(minimum_airflow_fraction.setValue(3))
    argument_map["minimum_airflow_fraction"] = minimum_airflow_fraction

    measure.run(model, runner, argument_map)
    result = runner.result
    puts "test_ChangeVAVBoxMinimumAirflowFraction_single_air_loop_BadInputs"
    #show_output(result)
    assert(result.value.valueName == "Fail")
  end

  def test_ChangeVAVBoxMinimumAirflowFraction_single_plant_loop_GoodInputs

    # create an instance of the measure
    measure = ChangeVAVBoxMinimumAirflowFraction.new

    # create an instance of a runner
    runner = OpenStudio::Ruleset::OSRunner.new

    # make an empty model
    model = OpenStudio::Model::Model.new

    # get arguments and test that they are what we are expecting
    arguments = measure.arguments(model)
    assert_equal(2, arguments.size)
    count = -1
    assert_equal("object", arguments[count += 1].name)
    assert_equal("minimum_airflow_fraction", arguments[count += 1].name)

    # load the test model
    translator = OpenStudio::OSVersion::VersionTranslator.new
    path = OpenStudio::Path.new(File.dirname(__FILE__) + "/0320_ModelWithHVAC_01.osm")
    model = translator.loadModel(path)
    assert((not model.empty?))
    model = model.get

    # set argument values to good values and run the measure on model with spaces
    arguments = measure.arguments(model)
    argument_map = OpenStudio::Ruleset::OSArgumentMap.new

    count = -1

    object = arguments[count += 1].clone
    assert(object.setValue("Packaged Rooftop VAV with Reheat"))
    argument_map["object"] = object

    minimum_airflow_fraction = arguments[count += 1].clone
    assert(minimum_airflow_fraction.setValue(0.4))
    argument_map["minimum_airflow_fraction"] = minimum_airflow_fraction

    measure.run(model, runner, argument_map)
    result = runner.result
    #show_output(result)
    puts "test_ChangeVAVBoxMinimumAirflowFraction_single_plant_loop_GoodInputs"
    assert(result.value.valueName == "Success")
  end

  def test_ChangeVAVBoxMinimumAirflowFraction_all_loops_GoodInputs

    # create an instance of the measure
    measure = ChangeVAVBoxMinimumAirflowFraction.new

    # create an instance of a runner
    runner = OpenStudio::Ruleset::OSRunner.new

    # make an empty model
    model = OpenStudio::Model::Model.new

    # get arguments and test that they are what we are expecting
    arguments = measure.arguments(model)
    assert_equal(2, arguments.size)
    count = -1
    assert_equal("object", arguments[count += 1].name)
    assert_equal("minimum_airflow_fraction", arguments[count += 1].name)

    # load the test model
    translator = OpenStudio::OSVersion::VersionTranslator.new
    path = OpenStudio::Path.new(File.dirname(__FILE__) + "/0320_ModelWithHVAC_01.osm")
    model = translator.loadModel(path)
    assert((not model.empty?))
    model = model.get

    # set argument values to good values and run the measure on model with spaces
    arguments = measure.arguments(model)
    argument_map = OpenStudio::Ruleset::OSArgumentMap.new

    count = -1

    object = arguments[count += 1].clone
    assert(object.setValue("*All Air Loops*"))
    argument_map["object"] = object

    minimum_airflow_fraction = arguments[count += 1].clone
    assert(minimum_airflow_fraction.setValue(0.4))
    argument_map["minimum_airflow_fraction"] = minimum_airflow_fraction

    measure.run(model, runner, argument_map)
    result = runner.result
    #show_output(result)
    puts "test_ChangeVAVBoxMinimumAirflowFraction_all_loops_GoodInputs"
    assert(result.value.valueName == "Success")
  end

end