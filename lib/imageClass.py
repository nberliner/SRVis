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
import numpy as np
import matplotlib
import matplotlib.pyplot as plt


from PyQt4.QtCore import *
from PyQt4.QtGui import *

matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PyQt4'
 
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT

from matplotlib.patches import Rectangle
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable

from visualiseLocalisations import ImageHistogram


class NavigationToolbar(NavigationToolbar2QT):
    # Thanks to: http://stackoverflow.com/a/15549675
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]


class MyMatplotlibWidget(FigureCanvas):
    """ Base class for the matplotlib widgets """
    def __init__(self, parent=None, aspect='auto', title='', width=5, height=5, dpi=120 ):
        
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        
        self.fig.suptitle(title, fontsize=10, fontweight='bold')
        self.axes = self.fig.add_subplot(111)
        self.fig.subplots_adjust(right=0.9, top=0.85, left=0.1, bottom=0.15)
        self.fig.set_facecolor('None')

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(parent)
        
        # Add the navigation control to zoom/pan/etc. the plots
        self.toolbar = NavigationToolbar(self.canvas, self.canvas)




class imageHistogramWidget(MyMatplotlibWidget):
    
    def __init__(self, data, title='Title', parent=None):
        
        super(imageHistogramWidget, self).__init__(parent=parent, aspect='equal')
        self.toolbar = NavigationToolbar(self, self) # Why do I have to add it here again??
        
        assert(np.shape(data)[1] == 2)
        
        # Initialise some variables
        self.data    = data
        self.H       = None
        self.extent  = None
        self.binSize = 1
        
        self.scaleMin = None
        self.scaleMax = None
        
        self.im       = None
        self.colorbar = None
        self.scalebar = None
        self.scalebarUnit = 100.0 # conversion between pixels und nm
        self.dataMinX = np.min(data[:,0])
        self.dataMinY = np.max(data[:,1])
        
        self.get2DHistogram = ImageHistogram()   
        
        # Connect the pan/zoom events to the scale bar update
        self.axes.callbacks.connect('xlim_changed', self.updateScaleBar)
        self.axes.callbacks.connect('ylim_changed', self.updateScaleBar)
    
    def setData(self, data):
        self.data = data
    
    def updateScaleBar(self, args):
#        xmin, ymin, deltax, deltay = self.axes.viewLim.bounds
#        width = 10
#        height = 2
        try:
            self.scalebar.remove()
        except AttributeError: # Handle the case if the scalebar is not yet drawn
            pass
        patch = self._setupScalebar()
#        self.scalebar = self.axes.add_patch( Rectangle((xmin+5, ymin-5), width, height, facecolor="white", edgecolor='none') )
        self.scalebar = self.axes.add_patch( patch )
        self.draw()
        print 'Updating the updateScaleBar', self.axes.viewLim.bounds
        print 'The scalebar', self.scalebar
    
    def _setupScalebar(self):
        # Check the selected ROI, calculate the units and construct the rectangle that should be plotted
        xmin, ymin, deltax, deltay = self.axes.viewLim.bounds
        xmax = xmin + deltax
        ymax = ymin + deltay
        
        # Check which scalebar length should be used
        scalebarLength = self._getScalebarLength(xmax-xmin)
        scalebarWidth  = 0.1 * scalebarLength
        
        print 'scalebarLength', scalebarLength
        print 'scalebarWidth', scalebarWidth
        
        # Fix the scalebar at 2% of the bottom left of the view
        twoPercentX = 0.05 * (xmax - xmin)
        twoPercentY = 0.05 * (ymax - ymin)
        
        if self.dataMinX >= xmin:
            xpos = self.dataMinX + twoPercentX
        else:
            xpos = xmin + twoPercentX
        if self.dataMinY - twoPercentY <= ymin:
            ypos = self.dataMinY + twoPercentY - scalebarWidth
        else:
            ypos = ymin + twoPercentY - scalebarWidth
            
        return Rectangle((xpos, ypos), scalebarLength, scalebarWidth, facecolor="green", edgecolor='black')
    
    def _getScalebarLength(self, extendX):
        # Take 50nm, 100nm, 500nm, 1000nm, 5000nm, 10000nm
        extendX *= self.scalebarUnit # Convert to nm
        
        # scalebar shoul fill 5% to 10% of the image range
        print 'extendX', extendX
        if 0.05 <= 50.0/extendX and 50.0/extendX < 0.1:
            length = 50.0
        elif 0.05 <= 100.0/extendX and 100.0/extendX < 0.1:
            length = 100.0
        elif 0.05 <= 500.0/extendX and 500.0/extendX < 0.1:
            length = 500.0
        elif 0.05 <= 1000.0/extendX and 1000.0/extendX < 0.1:
            length = 1000.0
        elif 0.05 <= 5000.0/extendX and 5000.0/extendX < 0.1:
            length = 5000.0
        else:
            length = 10000.0
        return length / self.scalebarUnit
#        elif 0.05 <= 10000.0/extendX and 10000.0/extendX < 0.01:
#            return 10000
    
    def redraw(self):
#        self.draw()
        self.toolbar.dynamic_update() # This seems to slightly faster than self.draw()

    def setGaussianBlur(self, blur, sigma):
        self.get2DHistogram.setGaussianBlur(blur, sigma)
    
    def calculate2DHistogram(self, scaleMin, scaleMax, binSize=1):
        self.H, self.extent, self.sm, scaleMin, scaleMax = self.get2DHistogram(self.data, scaleMin, scaleMax, binSize)
        return scaleMin, scaleMax
    
    def plot(self, scaleMin=None, scaleMax=None, binSize=1, blur=True):
        if self.H == None or self.binSize != binSize or self.scaleMin != scaleMin or self.scaleMax != scaleMax:
            self.binSize = binSize
            self.scaleMin, self.scaleMax = self.calculate2DHistogram(scaleMin, scaleMax, binSize=binSize)


        if self.colorbar != None:
            # Thanks to: http://stackoverflow.com/a/5265614
            self.fig.delaxes(self.fig.axes[1])
            self.fig.subplots_adjust(right=0.90)

        # In order to keep the pan/zoom after updating the image is kept
        # and only the data is updated after the first image has been plotted.
        if self.im == None:
            self.im = self.axes.imshow(self.H, extent=self.extent, interpolation='nearest', origin='upper', cmap='gist_heat')
        else:
            self.im.set_data(self.H)
        norm = matplotlib.colors.Normalize(vmin=self.scaleMin, vmax=self.scaleMax)
        self.im.set_norm(norm)

        # Add a colorbar to the image
        divider = make_axes_locatable(self.axes)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        self.colorbar = self.fig.colorbar(self.sm, cax=cax)
        
        

class overlayWidget(MyMatplotlibWidget):
    """ matplot widget used to overlay the localisations (or tracks) with
    the original image stack.
    """

    def __init__(self, data=None, parent=None):
        super(overlayWidget, self).__init__(parent=parent, aspect='equal', width=6, height=6)
        
        self.data = data

        # Set some axes properties
        self.axes.invert_yaxis() # the origin of the images is in the top left corner
        if self.data != None:
            self.initialise()
        
        # Initialse some variables
        self.im      = None
        self.loc     = None
        
        self.markerSize   = 40
        self.lw           = 1
        self.currentFrame = 0
    
    def updateView(self):
        self.canvas.draw()
        
    def initialise(self):
        self.drawFirstImage()
        self.plotFirstLocalisations()
        
        # Update the ax boundaries
        imgSize = np.shape(self.data.getImage(0))
        axLimit = np.max(imgSize) - 1 # in case it is non square
        self.axes.set_xlim([0, axLimit])
        self.axes.set_ylim([axLimit, 0]) # keep the inverted y-axis

        self.updateView()
        return

    def drawFirstImage(self):
        imageData = self.data.getImage(0)
        self.im  = self.axes.imshow(imageData, interpolation='none', origin='upper', cmap = plt.cm.Greys_r)
        return
    
    def updateImage(self, frame):
        self.currentFrame = frame # update frame
        imageData = self.data.getImage(frame)
        self.im.set_data( imageData )
        return
    
    def plotFirstLocalisations(self):
        X, Y = self.data.getLocalisations(0)
        self.loc = self.axes.scatter(x=X, y=Y, facecolors='none', edgecolors='blue', s=self.markerSize, zorder=200)
        return
        
    def updateLocalisations(self, frame):
        X, Y = self.data.getLocalisations(frame)
        self.loc.remove()
        self.loc = self.axes.scatter(x=X, y=Y, facecolors='none', edgecolors='blue', s=self.markerSize, zorder=200)
        return
    
    def redraw(self, frame=None):
        if frame == None:
            frame = self.currentFrame
        assert( isinstance(frame, int) )
        self.updateImage(frame)
        self.updateLocalisations(frame)
        self.updateView()
        return




class dataWidget(MyMatplotlibWidget):
    
    def __init__(self, data, dataUnfiltered=None, title='Title', parent=None, normalise=1.0):
        
        super(dataWidget, self).__init__(parent=parent, title=title)
        
        self.toolbar = NavigationToolbar(self, self)

        self.data           = data
        if dataUnfiltered == None:
            self.dataUnfiltered = data
        else:
            self.dataUnfiltered = dataUnfiltered
            
        self.dataType = None
        self.bins = None

        self.normalise = np.zeros(np.shape(data)) # see hist entry in http://matplotlib.org/api/axes_api.html
        self.normalise[:,] = 1.0/normalise

    def redraw(self):
        self.draw()

    def setData(self, dataUnfiltered, data):
        self.data = np.asarray(data)
        self.dataUnfiltered = np.asarray(dataUnfiltered)
        
        dataMin = np.min(self.dataUnfiltered)
        dataMax = np.max(self.dataUnfiltered)
        binwidth = ( dataMax - dataMin ) / 50.0
        
        # Set the histogram bins
        self.bins = np.arange(dataMin, dataMax + binwidth, binwidth)
        
        # Set the axes limits
        self.axes.set_xlim([dataMin,dataMax])
    
    def plotHistogram(self):
        self.axes.clear()
        if self.bins == None:
            self.bins = 50
        
        # Plot the data
        self.axes.hist(self.dataUnfiltered, bins=self.bins, normed=False, weights=self.normalise, histtype='bar', facecolor='grey', edgecolor='None',  alpha=0.8, rwidth=0.8)
        self.axes.hist(self.data, bins=self.bins, normed=False, weights=self.normalise, histtype='bar', facecolor='blue', rwidth=0.8, zorder=10)
        
        self.redraw()
        return




























