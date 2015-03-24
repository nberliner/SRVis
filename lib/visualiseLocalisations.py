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
from matplotlib import pyplot as plt
from pandas import DataFrame

from mpl_toolkits.axes_grid1 import make_axes_locatable


class Color:
    def __init__(self, scaleMin=None, scaleMax=None):
        self.Nglobal = dict()
        self.cmap = plt.get_cmap('gist_heat')

        self.scaleMin = scaleMin
        self.scaleMax = scaleMax
        
        if scaleMin == scaleMax and scaleMin != None:
            print 'Warning: trying to set zero scaling range!'
            self.scaleMin = scaleMin
            self.scaleMax = scaleMin * 1.1

    def __call__(self, N):
        
        if self.scaleMin == None and self.scaleMax != None:
            c = float(N) / self.scaleMax
        elif self.scaleMin != None and self.scaleMax == None:
            c = float(N)  - self.scaleMin
        elif self.scaleMin == None and self.scaleMax == None:
            c = float(N)
        else:
            c = (float(N) - self.scaleMin) / ( self.scaleMax - self.scaleMin )
  
        return self.cmap(c)
    
    def getColorbar(self):
        return plt.cm.ScalarMappable(cmap=plt.get_cmap('gist_heat'), norm=plt.Normalize(vmin=self.scaleMin, vmax=self.scaleMax))
    



class QuadTree(object):
    """Simple Quad-tree class"""
    def __init__(self, data, eps=10, unitLength=10.0):
        
        if isinstance( data, DataFrame ):
            data = np.array(data[['x','y']])

        assert( np.shape(data)[1] == 2 ) # Data should be two-dimensional
        
        self.data = data
        self.mins = np.array((np.min(data[:,0]), np.min(data[:,1])))
        self.maxs = np.array((np.max(data[:,0]), np.max(data[:,1])))
        
        self.eps      = eps
        self.unitArea = np.power(unitLength,2)
        self.color    = None
        
        self.patches        = [(data, [self.mins, self.maxs]), ]
        self.patchCriterion = [False, ]
        
        self._run()
    
    def _checkPatch(self, patch):
        data, (mins, maxs) = patch
        area = (maxs[0] - mins[0]) * (maxs[1] - mins[1])
        if len(data) < self.eps or area < self.unitArea: # i.e. that would correcpond to a 10 by 10 nm spot
            return [True, ], [(data, (mins, maxs)) ]
        
        xmid, ymid = 0.5 * (mins + maxs)
        xmin, ymin = mins
        xmax, ymax = maxs
        
        # Set the new boundaries of the divided patch
        q1 = (np.asarray([xmin, ymin]), np.asarray([xmid, ymid]))
        q2 = (np.asarray([xmin, ymid]), np.asarray([xmid, ymax]))
        q3 = (np.asarray([xmid, ymin]), np.asarray([xmax, ymid]))
        q4 = (np.asarray([xmid, ymid]), np.asarray([xmax, ymax]))

        # Divide the patch into quadrants
        data_q1 = data[(data[:,0] <  xmid) & (data[:,1] <  ymid)]
        data_q2 = data[(data[:,0] <  xmid) & (data[:,1] >= ymid)]
        data_q3 = data[(data[:,0] >= xmid) & (data[:,1] <  ymid)]
        data_q4 = data[(data[:,0] >= xmid) & (data[:,1] >= ymid)]
        
        return [False, False, False, False], [(data_q1, q1), (data_q2, q2), (data_q3, q3), (data_q4, q4)]
    
    
    def _run(self):

        i = 0
        while not np.all(self.patchCriterion):
            if i == 1000000:
                print 'Maximun iterations step reached'
                break
            i += 1
            patch = self.patches.pop(0) # take the first element
            if self.patchCriterion.pop(0) == False:# remove the flag
                newCriterion, newPatches = self._checkPatch(patch)
            else:
                newCriterion, newPatches = [True, ], [patch, ]
            
            self.patchCriterion.extend(newCriterion)
            self.patches.extend(newPatches)
        
        return

    def setColorBar(self, scaleMin=None, scaleMax=None):
        # scale is (number of localisations) / (area of the patch)
        scaleAuto = list()
        for patch, (mins, maxs) in self.patches:
            size = maxs - mins
            area = (maxs[0] - mins[0]) * (maxs[1] - mins[1])
            N    = float(len(patch)) / area
            scaleAuto.append(N)
            
        scaleMinAuto = np.percentile(scaleAuto, 5)
        scaleMaxAuto = np.percentile(scaleAuto, 95)
        
        if scaleMin == None:
            scaleMin = float(scaleMinAuto)
        else:
            scaleMin = float(scaleMin)
            
        if scaleMax == None:
            scaleMax = float(scaleMaxAuto)
        else:
            scaleMax = float(scaleMax)
            if scaleMax <= scaleMin:
                scaleMax = scaleMin * 1.1 # set it 10% above
        
        self.color = Color(scaleMin, scaleMax)
    
    def plot(self, scaleMin=None, scaleMax=None, fname=None, show=True):
        if scaleMin == None and scaleMax == None and self.color == None:
            self.setColorBar()
        else:
            self.setColorBar(scaleMin, scaleMax)
        
        fig = plt.figure(figsize=(7,7))
        ax  = fig.add_subplot(111, axisbg='black')
        ax.set_aspect('equal')
        ax.set_xlim(self.mins[0], self.maxs[0])
        ax.set_ylim(self.mins[1], self.maxs[1])
    
        sm = self.color.getColorbar()
        # Fake up the array of the scalar mappable. Urgh...
        sm._A = []
        ## see here: http://stackoverflow.com/a/18195921
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(sm, cax=cax)
        
        rectangles = list()
        for patch, (mins, maxs) in self.patches:
            size = maxs - mins
            area = (maxs[0] - mins[0]) * (maxs[1] - mins[1])
            N    = float(len(patch)) / area
            rect = plt.Rectangle(mins, *size, zorder=2,
                                 ec='none', fc=self.color(N))
            rectangles.append(rect)
            ax.add_patch(rect)
        
        if fname != None:
            fig.savefig(fname, bbox_inches='tight')
        if show:
            plt.show()
        
        return fig, ax, rectangles, sm
    

class ImageHistogram(object):
    """ Simple class to plot super-resolution localisation data in a 2D histogram. """
    def __init__(self):
        
        self.color = None
    
    def __call__(self, data, scaleMin=None, scaleMax=None, binSize=1):
        
        X = data[:,0]
        Y = data[:,1]
        binsX = np.ceil(((np.max(X)) - np.min(X)) / float(binSize))
        binsY = np.ceil(((np.max(Y)) - np.min(Y)) / float(binSize))
        
        H, xedges, yedges = np.histogram2d(X, Y, bins=(binsX,binsY))
        extent = [yedges[0], yedges[-1], xedges[-1], xedges[0]]
        
        if scaleMin == None and scaleMax == None:
            color, scaleMin, scaleMax = self._setColorBar(H)
        else:
            color, scaleMin, scaleMax = self._setColorBar(H, scaleMin, scaleMax)
            
        sm = color.getColorbar()
        # fake up the array of the scalar mappable. Urgh...
        sm._A = []
        ## see here: http://stackoverflow.com/a/18195921
#        divider = make_axes_locatable(ax)
#        cax = divider.append_axes("right", size="5%", pad=0.05)
        return H, extent, sm, scaleMin, scaleMax
        
    
    def _setColorBar(self, H, scaleMin=None, scaleMax=None):
        scaleMinAuto = np.percentile(H[::-1], 5)
        scaleMaxAuto = np.percentile(H[::-1], 98)

        if scaleMin == None:
            scaleMin = float(scaleMinAuto)
        else:
            scaleMin = float(scaleMin)
            
        if scaleMax == None:
            scaleMax = float(scaleMaxAuto)
        else:
            scaleMax = float(scaleMax)
            if scaleMax <= scaleMin:
                scaleMax = scaleMin * 1.1 # set it 10% above
        
        color = Color(scaleMin, scaleMax)
        return color, scaleMin, scaleMax

















