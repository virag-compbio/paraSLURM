import sys, os
import shutil
import time
import getpass
from pathlib import Path
from argparse import ArgumentParser
from utils import run_subprocess, check_job_failed
from typing import List, Dict
import warnings

class Job(object):
    ''' define the base class for a Job object '''

    ## get some class-level attributes
    pwd = os.getcwd()

    def __init__(self, job_name, task_name) -> None:
        self.__job_name = job_name
        self.__task_name = task_name

        self.__base_dir = Path(Job.pwd) / ".para" / self.__job_name
        self.__dir_stderr = self.__base_dir / "stderr"
        self.__dir_stdout = self.__base_dir / "stdout"

    @staticmethod
    def extract_job_line(job_file) -> str:
        ''' return the last line of the script file which basically contains the job '''

        with open(job_file, 'r') as FI:
            lines_list = FI.readlines()
        return [line for line in lines_list if not line.startswith('#')][0].rstrip('\n').replace(' || echo "Job crashed"','')
            
    def __action_clean(self) -> None:
        ''' clean an existing jobs name directory  '''

        if not self.__base_dir.is_dir():
            warnings.warn(f'The para jobs directory {self.__base_dir} does not exist. Nothing to be cleaned!')
        else:
            shutil.rmtree(self.__base_dir)

    def __action_crashed(self) -> List[str]:
        ''' get the list of crashed jobs '''

        jobs_crashed_list = [
            Job.extract_job_line(self.__base_dir / job_file)
            for job_file in os.listdir(self.__dir_stdout)
            if check_job_failed(self.__dir_stdout / job_file, self.__dir_stderr / job_file) == 1
        ]
        for job in jobs_crashed_list:
            print(job)

    def __action_stop(self) -> None:
        ''' call scancel on the jobs list and cancels all runnning jobs '''

        job_ids_file = self.__base_dir / "jobs_ids.txt"
        with open(job_ids_file, 'r') as FI:
            for job in FI:
                job = job.rstrip("\n")
                run_subprocess(f'scancel {job}')
        
    def main(self) -> None:
        
        if self.__task_name == "clean":
            self.__action_clean()
        elif self.__task_name == "crashed":
            self.__action_crashed()
        elif self.__task_name == "stop":
            self.__action_stop()

class JobSubmit(object):
    ''' the class that deals with a job submission '''

    ## get some class-level attributes at the very beginning
    pwd = os.getcwd()
    username = getpass.getuser()

    def __init__(self, jobs_name: str, jobs_list: Path, params_dict: Dict[str, int]) -> None:
        self.__jobs_name = jobs_name
        self.__jobs_list = jobs_list
        self.__params_dict = params_dict

        self.__base_dir = Path(JobSubmit.pwd) / ".para" / self.__jobs_name
        self.__stdout_dir = self.__base_dir / "stdout"
        self.__stderr_dir = self.__base_dir / "stderr"

    def __create_job_file(self, stdout_file: str, stderr_file: str, job_script: str, job_line: str) -> None:
        ''' create the sbatch file that basically submits the job '''

        with open(job_script, "w") as FO:
            FO.write("#!/bin/bash\n")
            FO.write("#SBATCH --mail-type=BEGIN,END\n")
            FO.write(f"#SBATCH -e {stdout_file}\n")
            FO.write(f"#SBATCH -o {stderr_file}\n")

            ## now deal with optional parameters:
            if "nodes" in self.__params_dict:
                FO.write(f"#SBATCH --nodes={self.__params_dict['nodes']}\n")
            if "cpu" in self.__params_dict:
                FO.write(f"#SBATCH --cpus-per-task={self.__params_dict['cpu']}\n")
            if "time" in self.__params_dict:
                FO.write(f"#SBATCH --time={self.__params_dict['time']}\n")
            if 'memory' in self.__params_dict:
                FO.write(f"#SBATCH --mem={self.__params_dict['memory']}G\n")
            FO.write(f'{job_line} || echo "Job crashed"\n')

    def __get_jobs_ids_dict(self):

        jobs_ids_dict: dict[int, int] = dict()
        ## create a dict where the key is the job identifier while the value is the particular job i.e. the line from the jobs file.

        with open(self.__base_dir / "jobs_ids.txt", "w") as FO, open(self.__jobs_list, 'r') as FI:
            for ct, job_line in enumerate(FI):
                job_line = job_line.strip('\n')
                job_script =  self.__base_dir / f'o.{ct}'   
                stdout_file = self.__stdout_dir / f'o.{ct}'
                stderr_file = self.__stderr_dir / f'o.{ct}'

                self.__create_job_file(stdout_file, stderr_file, job_script, job_line)

                ## submit the job
                job_id_string = run_subprocess(f'sbatch {job_script}', True) 
                ## returns something like "Submitted batch job 985797"
                
                job_identifier = int(job_id_string.split(' ')[-1])
                jobs_ids_dict[job_identifier] = ct ## i.e. the last field
                FO.write(f'{job_identifier}\n')

        return jobs_ids_dict
    
    @staticmethod
    def parse_job_status_string(job_status_string):
        ''' parse the output of squeue and return the job's status '''

        status_string_list = job_status_string.split('\n')
        if len(status_string_list) == 2:
            status_relevant_fields_list = status_string_list[1].split()
            return status_relevant_fields_list[4]
        return ''

    def __check_jobs_status(self, jobs_ids_dict):

        all_jobs_list = list(jobs_ids_dict.keys())
        all_jobs_finished = False
        time_total = 0

        while all_jobs_finished != True:
            failed, finished, running, pending = 0, 0, 0, 0

            for j in all_jobs_list:
                job_status = JobSubmit.parse_job_status_string(run_subprocess(f'squeue -u {JobSubmit.username} -j {j}', True))

                if job_status == '':
                    ct = jobs_ids_dict[j]
                    stdout_file = self.__stdout_dir / f'o.{ct}'
                    stderr_file = self.__stdout_dir / f'o.{ct}'
                    failed_job = check_job_failed(stdout_file, stderr_file)

                    if failed_job == 1:
                        failed += 1
                    else:
                        finished += 1
                elif job_status == 'R':
                    running += 1
                elif job_status == 'PD':
                    pending += 1

            print("##############################\n\n")
            print(f'Waited for {time_total} seconds so far')
            print(f'Number of running jobs {running}')
            print(f'Number of failed jobs {failed}')
            print(f'Number of finished jobs {finished}')
            print(f'Number of pending jobs {pending}')
            print("##############################\n\n")

            time.sleep(60)
            time_total += 60

            if failed + finished == len(all_jobs_list):
                all_jobs_finished = True

    def __create_dirs(self):
        ''' sanity check plus creates the base directory and then the directories for stdout and stderr '''

        try:
            self.__base_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            print(f'The para jobs directory {self.__base_dir} already exists. Delete this directory and resubmit the jobs. Aborting')
            sys.exit(1)
        
        for dir in [self.__base_dir, self.__stdout_dir, self.__stderr_dir]:
            dir.mkdir(parents = True, exist_ok = True)

    def main(self):
        self.__create_dirs()
        jobs_ids_dict = self.__get_jobs_ids_dict()
        self.__check_jobs_status(jobs_ids_dict)

class Parser(object):
    ''' the parser class that handles the input parameters business '''

    def __init__(self) -> None:
        self.__parser = ArgumentParser(description = "paraSLURM - a tool that enables the submission of jobs to CMCB\'s HPC cluster that uses SLURM as the job scheudler")
        self.initialiseParser()
        self.parse()
        self.__params = dict()

    def initialiseParser(self) -> None:
        self.__parser.add_argument('task_name', help = 'The task, has to be one of the following: stop|clean|crashed|push',
                                   type = str, choices = ["stop", "clean", "crashed", "push"])
        self.__parser.add_argument('jobs_name', type = str, help = 'The name of the jobslist that has to undergo one of the actions')
        self.__parser.add_argument('-f', '--file', dest = "jobs_file", type = str, help = 'A list of jobs containted in a file where every line is a job')
        self.__parser.add_argument('-n', '--nodes', dest = "nodes", type = int, help = 'The number of requested nodes')
        self.__parser.add_argument('-c', '--cpu', dest = "cpu", type = int, help = 'The number of requested cpus')
        self.__parser.add_argument('-t', '--time', dest = "time", type = int, help = 'The number of minutes requested for each job')
        self.__parser.add_argument('-m', '--memory', dest = "memory", type = int, help = 'The amount of RAM requested per CPU (in GB)')

    def parse(self) -> None:
        self.__parser.options = self.__parser.parse_args()

    def main(self) -> None:
        if len(sys.argv) <= 1:
            self.__parser.print_help()
            sys.exit()
        
        self.__task_name = self.__parser.options.task_name
        self.__jobs_name = self.__parser.options.jobs_name
  
        if self.__task_name == "push":
        
            self.__jobs_file  = Path(self.__parser.options.jobs_file)
            if not self.__jobs_file.exists():
                print(f"Error: The jobs file '{self.__jobs_file}' does not exist. Aborting")
                sys.exit(1)

            if self.__parser.options.nodes:
                self.__params["nodes"] = self.__parser.options.nodes
            if self.__parser.options.cpu:
                self.__params["cpu"] =  self.__parser.options.cpu
            if self.__parser.options.time:
                self.__params["time"] =  self.__parser.options.time
            if self.__parser.options.memory:
                self.__params["memory"] =  self.__parser.options.memory

    ## getter functions for the attributes
    @property
    def task_name(self):
        return self.__task_name

    @property
    def jobs_name(self):
        return self.__jobs_name
    
    @property
    def params(self):
        return self.__params

    @property
    def jobs_file(self):
        return self.__jobs_file

##########

if __name__ == '__main__':

    pa_object = Parser()
    pa_object.main()
  
    if pa_object.task_name == "push":
        job_submit = JobSubmit(pa_object.jobs_name, pa_object.jobs_file, pa_object.params)
        job_submit.main()
    else:
        job_non_submit = Job(pa_object.jobs_name, pa_object.task_name)
        job_non_submit.main()
