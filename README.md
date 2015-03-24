SRVis
=====

Visualisation tool for super-resolution localisation data

### Installation ###
1. Install Python 2.7 Anaconda (http://docs.continuum.io/anaconda/)
2. Update the Anaconda installation by running
	$ conda update conda
	$ conda update anaconda
3. Make sure the following dependecies are installed
	```
		$ conda install pyqt
		$ conda install -c soft-matter tifffile
	```
4. Copy the SRVis folder to your computer
5. Run SRVis.py
	```
		$ python SRVis.py
	```

### Troubleshooting ###
+ If running on Kubuntu make sure to do the following (see https://github.com/ContinuumIO/anaconda-issues/issues/32 for more information)
	1. Put a file qt.conf in your anaconda installation directory, e.g. /home/user/bin/anaconda/bin/ and add the following
	```
		[Paths]
		Plugins = '.'
	```
	2. Clear the QT_PLUGIN_PATH variable, for example via (note this works only temporarily)
	```
		$ export QT_PLUGIN_PATH=""
	```
+ I have been running it on a Windows machine. So it can work :) 
	
