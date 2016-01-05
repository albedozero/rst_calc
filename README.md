Rise/Set Time Calculator
====================
Allows quick calculation of rise/set times for an astronomical object
for use in planning observations.

Using/Installing RST Calculator
====================
RST Calculator can be run using the Python (2.7) interpreter. Required python libraries are:
- wxpython
- pyephem

Simply copy the script to the desired location to install it. The location of the python
interpreter must be in the path environment variable.

Standalone Executables
====================
PyInstaller has been used to compile RSTCalc into standalone executables for some systems. These
can be run without python installed. 
These are found in exec/. PyInstaller can be obtained from https://github.com/pyinstaller/pyinstaller.
To compile for a different system using pyinstaller, clone this repository and pyinstaller on that
machine, and run the command

      pyinstaller fits_hydra.py -F -i <icon_file>

where *icon_file* is the appropriate icon file found in icons/, if desired.



MIT License
