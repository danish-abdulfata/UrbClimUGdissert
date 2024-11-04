### Model and Coding Notes

```
micromamba env installtion failure: 
warning  libmamba You are using 'pip' as an additional package manager.
    Be aware that packages installed with 'pip' are managed independently from 'conda-forge' channel.

Installing pip packages: supy==2024.7.12.dev0
'"C:\Users\Danish\micromamba\condabin\micromamba"' is not recognized as an internal or external command,
operable program or batch file.
critical libmamba pip failed to install packages
```

testing `python -m pip install supy` - works!

USE mklink for Windows
`mklink /d C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\data "C:\Users\Danish\OneDrive - University College London\dissertation_data\lcz-supy-global-data"`

Git Subtree commandline
`git subtree add --prefix C:\Users\Danish\Documents\GitHub\UrbClimUGdissert\supy-lcz-global\ https://github.com/UrbanClimateRisk-UCL/supy-lcz-global main --squash`

Git Overleaf Update
`git submodule update --remote --merge`

AFTER RUNNING PUSH LCOAL REPO TO MAIN.