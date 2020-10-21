# Open the class to add new methods
class OpenStudio::Model::Model
  
  # Creates a schedule with one tuesday, one saturday, and one sunday per month
  def create_reporting_schedule_3days_per_month()
    
    reporting_schedule = self.getScheduleRulesetByName("Reporting_schedule_3_days_per_Month")
    
    if reporting_schedule.empty?
    
      twenty_four_hrs = OpenStudio::Time.new(0,24,0,0)
      
      # schedule: One weekday, one in January, one in May, one in August
      # We start with a default profile of always zero (no reporting)
      reporting_schedule = OpenStudio::Model::ScheduleRuleset.new(self)
      reporting_schedule.setName("Reporting_schedule_3_days_per_Month")
      reporting_schedule.defaultDaySchedule.setName("ALWAYS_OFF day")
      reporting_schedule.defaultDaySchedule.addValue(twenty_four_hrs, 0.0)
      
      for i in 1..12
        monthly_priority_sch = OpenStudio::Model::ScheduleRule.new(reporting_schedule)
        monthly_priority_sch.setName("1st week of #{OpenStudio::MonthOfYear.new(1).valueDescription} Rule")
        
        # Start the first of the month and end the 7th
        monthly_priority_sch.setStartDate(self.getYearDescription.makeDate(i, 1))
        monthly_priority_sch.setEndDate(self.getYearDescription.makeDate(i, 7))
        
        # Get a Tuesday, Saturday and Sunday
        monthly_priority_sch.setApplySunday(true)
        monthly_priority_sch.setApplyMonday(false)
        monthly_priority_sch.setApplyTuesday(true)
        monthly_priority_sch.setApplyWednesday(false)
        monthly_priority_sch.setApplyThursday(false)
        monthly_priority_sch.setApplyFriday(false)
        monthly_priority_sch.setApplySaturday(true)
        
        day_schedule = monthly_priority_sch.daySchedule
        day_schedule.setName("#{monthly_priority_sch.name} Day")
        day_schedule.addValue(twenty_four_hrs, 1)
      end
      
      puts "Created a reporting schedule that will report one Tuesday, one Saturday and one Sunday per month"
    
    else
      reporting_schedule = reporting_schedule.get
    end
    
    return reporting_schedule
    
  end
  
  # Create an output variable
  # Name [Str]: optional name for the output variable (not used in E+)
  # key [Str]: Optional key
  # variable_name [Str]: Mandatory variable name to report (check the .rdd)
  # reporting_frequency [Str]: 'Detailed', 'Timestep', 'Hourly', 'Daily', 'Monthly', 'RunPeriod', 'Annual', 'Environment'
  # reporting_schedule OpenStudio ScheduleRuleset, optional. 
  def create_output_variable(name, key, variable_name, reporting_frequency, reporting_schedule)
    
    # Checking inputs
    if variable_name.nil?
      puts "You MUST provide a variable name"
      return false
    end
    if reporting_frequency.nil?
      puts "You MUST provide a reporting_frequency"
      return false
    end
    
    outputVariable = OpenStudio::Model::OutputVariable.new(variable_name, self)
    outputVariable.setReportingFrequency(reporting_frequency)
    
    # Deal with the optionals
    if !name.nil?
      outputVariable.setName(name)
    end
    if !key.nil?
      outputVariable.setKeyValue(key)
    end
    if !reporting_schedule.nil?
      outputVariable.setSchedule(reporting_schedule)
    end
  
  end # end of create_output_variable
  
end