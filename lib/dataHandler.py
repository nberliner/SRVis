#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
SRVis  Copyright (C) 2015  Niklas Berliner
"""
import sys

import numpy as np
import tifffile as Tiff
from localisationClass import rapidstormLocalisations, XYTLocalisations

#from visualiseLocalisations import QuadTree

class dataHandler():
    """
    Interface between the data and the SRVis application
    
    The super-resolution data is stored in a pandas DataFrame and the TIFF image
    is read using tifffile.py (see http://www.lfd.uci.edu/~gohlke/code/tifffile.py.html)
    """
    def __init__(self, fnameImage, fnameLocalisations, fnameLocalisationsType, pixelSize, CpPh, eps=50):

        if fnameImage == None or fnameImage == '':
            self.image = None
        else:
            print 'Reading the image'
            self.image         = Tiff.TiffFile(fnameImage)
        
        print 'Reading the localisations'
        # Here other localisation data types can be added if desired
        if fnameLocalisationsType == 'rapidstorm':
            self.data = rapidstormLocalisations()
            self.data.readFile(fnameLocalisations, photonConversion=CpPh, pixelSize=pixelSize)
        elif fnameLocalisationsType == 'xyt':
            self.data = XYTLocalisations()
            self.data.readFile(fnameLocalisations, pixelSize=pixelSize)
        else:
            print 'No localisation type is checked. Something went wrong..exiting'
            sys.exit() # Very ugly! Should be changed to a popup!

    def getImage(self, frame):
        """ Returns the frame as np.array """
        return self.image[frame].asarray()
        
    def maxImageFrame(self):
        """ Returns the number of frames """
        if self.image == None:
            return 0
        else:
            return len(self.image)
        
    def getLocalisations(self, frame):
        """ Return X and Y localisation data as numpy arrays that can be 
        directly used in a matplotlib scatter plot """
        data = self.data.localisations()
        xy   = np.asarray(data[ data['frame'] == frame ][['x','y']])
        return xy[:,0], xy[:,1]
    
    def filterData(self, filterValues):
        """ Filter the localisation data based on the filter conditions in
        filterValues.
        
        filterValues must be a dict with dataType that should be filtered as
        keys and the min and max values as values, i.e. e.g.
            filterValues = dict()
            filterValues['SNR'] = (20, None)
        """
        self.data.filterAll(filterValues, relative=False)
    
    def saveLocalisations(self, fname, pxSize):
        """ Save the (filtered) localisations to disk """
        self.data.writeToFile(fname, pixelSize=pxSize)





