https://github.com/youngpm/gdalmanylinux

use GDAL w/ManyLinux Wheels

1. make a new virtual env for this function
2. clone the repo above into this `ls4-00-project` function folder
3. from the this function folder: `cd gdalmanylinux`
4. `make wheels`. this takes awhile 'but once complete you should have a subdirectory called wheels'
5. `cd ..` back into the function directory
6. `pip install ./gdalmanylinux/wheels/GDAL-2.3.0-cp36-cp36m-manylinux1_x86_64.whl`
