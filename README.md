# SciUnit Parallel Execution Guide

This guide provides instructions for installing and using SciUnit with GNU Parallel for efficient parallel execution of tasks.

## 1. Installing SciUnit

To install SciUnit, please refer to the official repository:

[**SciUnit GitHub Repository**](https://github.com/depaul-dice/sciunit)

## 2. Installing GNU Parallel

Follow these steps to install GNU Parallel:

### Step-by-Step Installation

1. **Download the latest version:**
   curl -s https://ftp.gnu.org/gnu/parallel/parallel-latest.tar.bz2 --output parallel-latest.tar.bz2

2. **Extract the downloaded file:**
   tar xjf parallel-latest.tar.bz2

3. **Change to the extracted directory:**
   cd parallel-<tab>  # Use tab completion to select the correct directory

4. **Configure the installation prefix:**
   ./configure --prefix=$HOME/parallel-install

5. **Build and install:**
   make install

6. **Update your PATH:**
   export PATH=$HOME/parallel-install/bin:$PATH

### 3. Verify Installation

Ensure that GNU Parallel is installed and working correctly by running:
parallel -j 8 wc -l ::: /etc/*.conf
This command should return the line counts of all .conf files in the /etc directory.

## 4. Running SciUnit Commands

### Serial Execution

For instructions on executing SciUnit commands serially, visit:

- [**SciUnit Documentation**](https://github.com/depaul-dice/sciunit)
- [**SciUnit Run**](https://sciunit.run/)

### Parallel Execution

You can utilize GNU Parallel to run SciUnit commands in parallel:

#### A. Parallel Execution of Commands

To execute multiple commands in parallel, such as:
python3 test.py 1
python3 test.py 2
python3 test.py 3
Use the following command:
parallel sciunit parallel_exec python3 test.py ::: 1 2 3

#### B. Parallel Repetition of Outputs

If the output of the previous parallel execution produces results e1, e2, and e3, you can repeat these commands in parallel with:
parallel sciunit repeat ::: e1 e2 e3

---

### C. Using slurm
To run jobs on a cluster using Slurm, you can create a Slurm job script that might look like the following. To execute the job, simply use the command sbatch command.slurm.

```
#!/bin/bash

#SBATCH --job-name=audit
#SBATCH --output=slurm-audit.out
#SBATCH --error=slurm-audit.out
#SBATCH --time=02:00:00
#SBATCH --ntasks-per-node=1

parallel -j4 sciunit parallel_exec python3 test.py ::: 1 2 3
```
