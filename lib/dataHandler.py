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
    def __init__(self, fnameImage, fnameLocalisations, fnameLocalisationsType, pixelSize, CpPh, eps=50):

        if fnameImage == None or fnameImage == '':
            self.image = None
        else:
            print 'Reading the image'
            self.image         = Tiff.TiffFile(fnameImage)
        
        print 'Reading the localisations'
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
        if self.image == None:
            return 0
        else:
            return len(self.image)
        
    def getLocalisations(self, frame):
        """ Return X and Y localisation data that can be directly
        used in a matplotlib scatter plot """
        data = self.data.localisations()
        xy   = np.asarray(data[ data['frame'] == frame ][['x','y']])
        return xy[:,0], xy[:,1]
    
    def filterData(self, filterValues):
        self.data.filterAll(filterValues, relative=False)
    
    def saveLocalisations(self, fname, pxSize):
        self.data.writeToFile(fname, pixelSize=pxSize)





