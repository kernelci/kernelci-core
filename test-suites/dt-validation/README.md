# notes

make dt_binding_check; make dtbs_check

# *format.py*

## Description of the function of this file:

This script first separates the files that passed from those that failed or had warnings. It then prints the files as a test name along with their statuses (pass/fail). It also creates a JSON object containing the test names mapped to their statuses. 

## The below lines are important to read before running this script
This script will look at a file that has the output of dt_binding_check (preferably all of the output. meaning stdout *AND* stderr) 

To have both stdout and stderr be printed into one file, you must run the following command: `dt_binding_check &> \<filename>`

The file that will be read will be the second argument of the command that runs format.py. eg: `python format.py <filename>`


