Solar wind source regions code
==============================

[![DOI](https://zenodo.org/badge/368483171.svg)](https://zenodo.org/badge/latestdoi/368483171)

This repository contains the code needed to reproduce the results in
"Active region contributions to the solar wind over multiple solar cycles".

Running
-------
All code is tested in the conda environment specified in the ``environment.yml`` file.
To make use of this you will need an installation of [conda](https://conda.io/).
When this is done the environment can be set up to run the code using the following
shell commands:

```bash
conda env create -f environment.yml --name ars
source activate ars
```

Code structure
--------------
The code is split into three folders:

1. ``1-fetch-data`` contains code to fetch magnetograms from four different magnetogram
   sources. The output of this step is archived at ZENODO LINK HERE.
2. ``2-process-data`` contains code to calculate PFSS solutions and trace regularly spaced
   grids of open field lines through each solution, to measure the connectivity and
   magnetic field strengths of each open field region. The output of this step is also
   archived at ZENODO LINK HERE.
3. ``3-analysis`` contains a set of Jupyter notebooks to reproduce the figures in the paper
   (using the output of step 2).

Each folder has its own README file containing instructions on how to run the code.

Re-mixing the code
------------------
All code is released under the 3-clause BSD license - see the ``LICENSE`` file for more info.
If you make use of any of it in a published work, I would be grateful if you cited
Stansby et al. 2021 Solar Physics, which this code was written for.
