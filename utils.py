from sys import exit
from pathlib import Path
import subprocess
from typing import Union

import subprocess
from typing import Union

def run_subprocess(command: Union[str, list[str]], return_output: bool = False) -> Union[None, str]:
    ''' execute a shell command and optionally return its output '''
    if isinstance(command, str):
        command = command.split()

    result = subprocess.run(command, capture_output = True, text = True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {command}\n{result.stderr.strip()}")

    return result.stdout.strip() if return_output else None

 
def fetch_last_line(input_file: Path) -> Union[str, None]:
    try:
        with open(input_file, 'r') as FI:
            lines_list = FI.readlines()
            return lines_list[-1].rstrip('\n') if lines_list else ''
    except (FileNotFoundError, PermissionError, OSError) as e:
        print(f'Cannot read the last line from {input_file}. The error message is {e}')
        exit(2)

def check_job_failed(stdout_file: Path, stderr_file: Path) -> int:
    ''' check if a job failed '''

    last_line_so: str = fetch_last_line(stdout_file)
    last_line_se: str = fetch_last_line(stderr_file)

    failure_keywords = {'Job crashed', 'CANCELLED'}
    # check if any of the failure keyword exists in the last line
    if any(keyword in last_line_so or keyword in last_line_se for keyword in failure_keywords):
        return 1
    return 0

def parse_job_status_string(job_status_string):
    ''' parse the output of squeue and return the job's status '''

    status_string_list = job_status_string.split('\n')
    if len(status_string_list) == 2:
        status_relevant_fields_list = status_string_list[1].split()
        return status_relevant_fields_list[4]
    return ''
