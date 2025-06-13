# paraSLURM

**paraSLURM** is a lightweight command-line tool that simplifies the submission and management of jobs on the [CMCB's](https://www.tu-dresden.de/cmcb) HPC cluster, which uses **SLURM** as its workload manager. It is designed to make high-throughput job handling more user-friendly by providing convenient commands to **push**, **stop**, **clean**, or investigate **crashed** jobs.

---

## 🚀 Features

- Submit multiple jobs via a jobs file
- Customize SLURM resources (nodes, CPUs, memory, time)
- Easily manage job lifecycles (stop, clean up, check failures)
- Wrapper designed specifically for CMCB's SLURM setup

---

## 🧰 Usage

```bash
usage: para_slurm.py [-h] [-f JOBS_FILE] [-n NODES] [-c CPU] [-t TIME] [-m MEMORY] {stop,clean,crashed,push}jobs_name
```

### Mandatory arguments

| Argument                    | Description          |
| --------------------------- | -------------------- |
| `{stop,clean,crashed,push}` | The task to perform: |
| `jobs_name`                 | A name/identifier for a set of jobs |


- push: Submit jobs  
- stop: Cancel running jobs  
- clean: Remove temporary job files  
- crashed: List jobs that failed or crashed  

jobs_name - A name used to identify this batch of jobs

### Optional arguments

| Argument                           | Description                                       |
| ---------------------------------- | ------------------------------------------------- |
| `-h`, `--help`                     | Show help message and exit                        |
| `-f JOBS_FILE`, `--file JOBS_FILE` | Path to a text file with one job command per line |
| `-n NODES`, `--nodes NODES`        | Number of compute nodes requested                 |
| `-c CPU`, `--cpu CPU`              | Number of CPUs requested per job                  |
| `-t TIME`, `--time TIME`           | Time (in minutes) requested per job               |
| `-m MEMORY`, `--memory MEMORY`     | Memory requested per CPU (in GB)                  |

### Examples

#### Submit a batch of jobs listed in jobs.txt with specific resource requirements
```
python para_slurm.py push my_analysis_batch -f jobs.txt -n 1 -c 4 -t 120 -m 8
```

#### Stop all running jobs from the batch
```
python para_slurm.py stop my_analysis_batch
```

#### Clean up job files
```
python para_slurm.py clean my_analysis_batch
```

#### List crashed jobs from the batch
```
python para_slurm.py crashed my_analysis_batch
```

### Requirements
- python 3.x
- Access to a SLURM-based HPC cluster
- SLURM installed and configured in your environment

### Author
Developed by Virag Sharma
Contact: virag.compbiologist@gmail.com

### Contributions
Feel free to open issues or submit pull requests if you'd like to contribute or suggest improvements.


