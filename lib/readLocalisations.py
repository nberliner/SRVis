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

import xml.etree.ElementTree as ET
import numpy as np
from pandas import DataFrame

class indexGenerator():
    """
    Generates an increasing index for each localisation based on the frame
    number. Assumes the frames to be ordered. For use with pandas multiindex
    DataFrames
    """
    def __init__(self):
        self.currentFrame  = 0
        self.previousFrame = 0
        self.idx           = -1

    def __call__(self, frame):
        if frame == self.currentFrame:
            self.idx += 1
            return self.idx
        else:
            # Update the frames
            self.previousFrame = self.currentFrame
            self.currentFrame  = frame
            self.idx = 0
            return self.idx


def readRapidStormLocalisations(fname, photonConversion=1.0, pixelSize=1.0):
    """ Read rapidStorm localisations from text file.
    
        photonConversion should be set to convert the photon counts correctly
       
        with,
            x    = x position
            sx   = error of x position
            y    = y position
            sy   = error of y position
            amp  = amplitude
    
    """
    assert( isinstance(pixelSize, float) or isinstance(pixelSize, int) ) # int for backwards compatibility
    
    photonConversion = float(photonConversion)
    
    idx       = indexGenerator()
    pixelSize = float(pixelSize)
    
    xPosition            = None
    xPositionUncertainty = None
    yPosition            = None
    yPositionUncertainty = None
    amplitude            = None
    imageNumber          = None
    PSFpositionX         = None
    PSFpositionY         = None
    fitResidues          = None
    
    with open(fname, 'r') as f:
        # Check the file structure. Rapidstorm creates variable output columns
        # but stores the column type information in an xml like header file.
        header = f.readline()
        # Use the ElementTree xml parser to read the header
        root = ET.fromstring(header[2:])
        for index, child in enumerate(root):
            if child.attrib['identifier']   == 'Position-0-0':
                xPosition = index
            elif child.attrib['identifier'] == 'Position-0-0-uncertainty':
                xPositionUncertainty = index
            elif child.attrib['identifier'] == 'Position-1-0':
                yPosition = index
            elif child.attrib['identifier'] == 'Position-1-0-uncertainty':
                yPositionUncertainty = index
            elif child.attrib['identifier'] == 'Amplitude-0-0':
                amplitude  = index
            elif child.attrib['identifier'] == 'ImageNumber-0-0':
                imageNumber = index
            elif child.attrib['identifier'] == 'PSFWidth-0-0':
                PSFpositionX = index
            elif child.attrib['identifier'] == 'PSFWidth-1-0':
                PSFpositionY = index
            elif child.attrib['identifier'] == 'FitResidues-0-0':
                fitResidues = index
            elif child.attrib['identifier'] == 'LocalBackground-0-0':
                localBackground = index
            
        # Make sure all necessary fields have been identified
        assert( xPosition            != None )
        assert( yPosition            != None )
        assert( amplitude            != None )
        assert( imageNumber          != None )
        
    ## Read the full file
    allData  = np.loadtxt(fname, skiprows=1) # this is the whole data
    rowCount = np.shape(allData)[0]
    
    # Calculate the SNR
    SNR      = np.zeros((rowCount,1))
    SNR[:,0] = allData[:,amplitude] / allData[:,localBackground]
    allData  = np.concatenate((allData,SNR),axis=1)
    SNRindex = np.shape(allData)[1] - 1
    
    # Add a NaN column (used if a rapidstorm input column is missing)
    zeros   = np.zeros((rowCount,1))
    zeros.fill(np.NaN)
    allData = np.concatenate((allData,zeros),axis=1)

    # Convert the amplitude to photon count
    allData[:,amplitude] /= photonConversion
    
    # Convert the x and y coordinates to pixels
    allData[:,[xPosition,yPosition]] /= pixelSize

    
    # Check which data is there and what needs to be added
    if xPositionUncertainty == None:
        xPositionUncertainty = -1 # select the last column of all zeros
        yPositionUncertainty = -1
    if PSFpositionX == None:
            PSFpositionX = -1
            PSFpositionY = -1
    if fitResidues == None:
        fitResidues = -1
        
    dataIndexes = [xPosition, yPosition, xPositionUncertainty, yPositionUncertainty, \
                   amplitude, imageNumber, fitResidues, SNRindex]
    
    # Assemble the index structure for the DataFrame
    # A two level index is used, i.e.
    # frame_0   0
    #           1
    #           2
    #           ...
    # frame_1   0
    #           1
    #           etc.
    level1 = [ 'frame_' + str(int(frame)) for frame in allData[:,imageNumber] ]
    level2 = [ idx(frame) for frame in allData[:,imageNumber] ]
    index  = [ level1, level2 ]
    
    # These are column names of the DataFrame by which the data can
    # be accessed later.
    columns = ['x','y','Uncertainty x','Uncertainty y','Photon Count', 'frame', \
               'FitResidue', 'SNR']
    
    # Create the DataFrame
    data = DataFrame(allData[:,dataIndexes], columns=columns, index=index)

    return data




def readXYTLocalisations(fname, pixelSize=1.0):
    """
    Read a generic xyt file. The columns must be:
    
            x   y   frame
    
    The first line is skipped as header information.
    """
    # Read the data
    allData  = np.loadtxt(fname, skiprows=1)
    
    # Assemble the index structure for the DataFrame
    # See readRapidStormLocalisations comments for a brief explanation.
    idx         = indexGenerator()
    imageNumber = 2
    level1 = [ 'frame_' + str(int(frame)) for frame in allData[:,imageNumber] ]
    level2 = [ idx(frame) for frame in allData[:,imageNumber] ]
    index  = [ level1, level2 ]
    
    # Put the data together
    data = DataFrame(allData, columns=['x','y','frame'], index=index)
    
    # Convert x and y data to pixels
    data[['x','y']] = data[['x','y']] / float(pixelSize)
    
    return data













