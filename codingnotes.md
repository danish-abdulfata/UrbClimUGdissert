### Model and Coding Notes

USE mklink for Windows
`mklink /d C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\data "C:\Users\Danish\OneDrive - University College London\dissertation_data\lcz-supy-global-data"`
not in use since 10.08.2025

### Git
Git Subtree commandline
`git subtree add --prefix C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\ https://github.com/UrbanClimateRisk-UCL/supy-lcz-global main --squash`

*Pull in new subtree commits*

If you want to pull in any new commits to the subtree from the remote, issue the same command as above, replacing add for pull:

`git subtree pull --prefix overleaf-dissertation [https://github.com/newfivefour/vimrc.git](https://github.com/danish-abdulfata/ug-dissertation) master --squash`

*Updating / Pushing to the subtree remote repository*

If you make a change to anything in subtreeDirectory the commit will be stored in the host repository and its logs. That is the biggest change from submodules.
If you now want to update the subtree remote repository with that commit, you must run the same command, excluding --squash and replacing pull for push.

`git subtree push --prefix overleaf-dissertation https://github.com/danish-abdulfata/ug-dissertation master`

Subtree [cheatcode](https://gist.github.com/SKempin/b7857a6ff6bddb05717cc17a44091202)

https://www.overleaf.com/learn/how-to/GitHub_Synchronization

### Miscellaneous

cd /mnt/c/Users/Danish/Documents/GitHub/UrbClimUGdissert/supy-lcz-global
micromamba activate supy_lcz

python -m runner.runner KL-KualaLumpurTest5 --run-type grid --grid-size 1000 --grid-boxes 40 --metforc-src era5land --urbdesc-src lcz_updated --sitelist sitelist_custom --download-era5 -

python -m test_scripts.run_split_models

free -h --si (for WSL ram)

python -m runner.runner KL-KualaLumpur-2016_1month_s1 --run-type grid --grid-size 1000 --grid-boxes 5 --metforc-src era5land --urbdesc-src lcz_updated --sitelist KL-KualaLumpur-2016_splitlist --download-era5 --do-spinup

```
import supy as sp
import pandas as pd
import numpy as np

sp.show_version()
```

https://liveuclac.sharepoint.com/sites/Geography/ComputerSupport/
SSH Linux Geograhy Lab NW110A
ssh zcfaada@ad@durban.geog.ucl.ac.uk
