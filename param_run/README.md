# Uncertainty and Sensitivity Analysis Workflow for Building Demand Flexibility
Use this workflow to perform uncertainty and sensitivity analysis of building demand flexibility.

## Usage

### Configuration

Use *config.ini* to specify how analysis is performed:
* `OpenStudioPath`: path to the OpenStudio installation.
* `MeasureDirectory`: name of the folder where measures are stored.
* `InputDirectory`: name of the folder where input files, including OS models, weather files, and csv files of parameter sample values, are stored.
* `ModelID`: unique case ID.
* `BaseModel`: name of the baseline OS model.
* `DFModel`: name of the OS model that implements demand flexibility strategy.
* `Weather`: name of the weather file.
* `FloorArea`: building floor area in *sq.ft*, used to calculate demand shed intensity.
* `DesignType`: type of the experimental design used for the analysis, can be:
-- "Param": parametric analysis.
-- "MCS": Monte Carlo simulation with Latin Hypercube sampling.
-- "SA": Sensitivity analysis using Morris method.
* `Design`: name of the file that contains parameter sample values.
* `Size`: sample size, required for Monte Carlo simulation.
* `Problem`: specification of Morris method design, which include:
-- `r`: number of repetitions.
-- `levels`: number of levels each parameter's cumulative density function (CDF) will be divided into.
* `Parameters`: a list of specifications for parameters to be analyzed. For each parameter:
-- `name`: name of the parameter, needs to be included in the *Parameter Name* column of the *measure_lookup.csv* file.
-- `distribution`: type of the probabilistic distribution of the parameter's uncertainty, currently only support "Normal", "Uniform", and "Triangle".
-- `parameters`: probabilistic distribution parameters, see code for how to specify for each distribution
-- `form`: how the specified probabilistic distribution is applied to the parameter value, can be "Addition", "Multiplier", or "Actual".
-- `label`: a more descriptive name of the parameter that can be used as x axis in histograms.
-- `ref`: optional reference for the specified probabilistic distribution


### Perform analysis
For parametric analysis:
1. Manually create a csv file that contains parameter sample values. Make sure parameter names in the header are included in the *Parameter Name* column of the *measure_lookup.csv* file. See *design_wwr.csv* and *design_param.csv* in *inputs* folder for examples.
2. Create the configuration file accordingly, use *config_param.ini* as a template. Make sure all input files are placed correctly, and `Design` is the name of the csv file created in the above step.
3. Run *run_sim.py* and *visualize.py*. For example, in command prompt:
`python run_sim.py config_example.ini`
`python visualize.py config_example.ini`

For Monte Carlo simulation and sensitivity analysis using Morris method:
1. Create the configuration file accordingly, use *config_mcs.ini* and *config_sa.ini* as templates. Make sure all input files are placed correctly.
2. Run *design.py* to generate design matrix and csv file of parameter sample values. For example in command prompt:
`python design.py config_example.ini`
After completion, check that the file(s) are correctly generated. Sensitivity analysis will generate an additional file with a "cdf" suffix. This file is the design matrix of the CDF space and will be used in the analysis later.
3. Run *run_sim.py* and *visualize.py*. For example, in command prompt:
`python run_sim.py config_example.ini`
`python visualize.py config_example.ini`

### Outputs
All simulation and analysis outputs are stored in the *sim* folder created by the process. It includes a set of sub-folders:
* "osw": contains all simulation instance osw files.
* "osm": contains all simulation instance osm files.
* "idf": contains all simulation instance idf files.
* "run": contains all simulation instance raw outputs, including a sub-folder for each instance.
* "output": contains the post-processed demand flexibility related outputs for each simulation instance, as well as a few result summary files:
-- *{ModelID}_Ref.csv*: outputs of the reference case.
-- *{ModelID}_{DesignType}.csv*: outputs of all the instance cases.
-- *{ModelID}_{DesignType}_Output.csv*: outputs of Monte Carlo simulation and sensitivity analysis, where the demand shed intensity is averaged over all hours of the considered period within each instance.
-- *{ModelID}_SA_Morris.csv*: Morris method results.
* "plot": contains all visualization plots.

## Caveats and Todos

* Develop measures for more OpenStudio parameters
*Note: For each new measure developed, make sure fill the *measure_lookup.csv* file accordingly. See existing entries for example.*
