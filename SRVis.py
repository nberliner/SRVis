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

__version__ = 'SRVis version 0.1'

import sys
sys.path.insert(1,'lib')
 
# Import the core and GUI elements of Qt
from PyQt4.QtCore import *
from PyQt4.QtGui  import *

import os.path as osp
import matplotlib
import numpy as np

matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PyQt4'

# Import program specific classes and functions
from dataHandler    import dataHandler
from imageClass     import overlayWidget, dataWidget, imageHistogramWidget
from SRVisInterface import openDialog, PyMultiPageWidget, messageBox


class SRVis(QMainWindow):
 
    def __init__(self):
        """
        SRVis is a program to visualise super-resolution microscopy data.
        Its main purpose is to verify the correct localisation of single
        molecule fitting routines. For this purpose localisations can be
        overlayed with the original TIFF image to visually verify their
        accuracy.
        
        Currently rapidstorm data as well as xyt data is supported.
        """
        
        # Initialize the object as a QWidget and
        # set its title and minimum width
        QMainWindow.__init__(self)
        self.setWindowTitle('SRVis')
        self.setMinimumWidth(400)
        
        # Some intital data initialisation
        self.data          = None
        self.home          = osp.expanduser("~")
        
        self.binSize       = 1
        self.scaleMin      = None
        self.scaleMax      = None
        self.blurHistogram = False
        self.dataTypes     = list()
        self.filterValues  = dict()
        
        self.localisationPrecision = 20.0 # assume an initial value of 20nm
        
        self.initialised   = False
        
        # Create the main layout
        #
        # ________________________
        # |       |               |
        # | left  |  plot layout  |
        # | pane  |               |
        # |       |_______________|
        # |       | button layout |
        # ------------------------
        #
        #
        # Create the QVBoxLayout that lays out the main part and the buttons
        self.outerLayout = QHBoxLayout()

        # Mabe not super nice.. Create a main widget and set it as layout        
        self.mainWindow = QWidget(self)
        self.mainWindow.setLayout(self.outerLayout)
        
        # Create the layout of the main part and add it to the outer layout
        self.layout       = QHBoxLayout()
        self.leftPane     = QVBoxLayout()        
        
        # Add the left-right splitter         
        self.layoutWindow   = QWidget()
        self.leftPaneWindow = QWidget()
        self.leftPaneWindow.setMaximumWidth(300) # restrict it to not grow too wide
        
        self.layoutWindow.setLayout(self.layout)
        self.leftPaneWindow.setLayout(self.leftPane)
        self.splitterLeftRight = QSplitter(Qt.Horizontal)
        self.splitterLeftRight.addWidget(self.leftPaneWindow)
        self.splitterLeftRight.addWidget(self.layoutWindow)

        self.outerLayout.addWidget(self.splitterLeftRight)
        

        # Create the left pane holding input fields
        self.form_layout  = QFormLayout()
        self.form_layout2 = QFormLayout()
        

        self.frame        = QSpinBox(self)
        self.markerSize   = QLineEdit(self)
        self.HistBinSize  = QLineEdit(self)
        self.QTscaleMin   = QLineEdit(self)
        self.QTscaleMax   = QLineEdit(self)
        self.QTHistBlur   = QCheckBox(self)
        
        self.frame.setSingleStep(1)
        self.frame.setValue(0)
        self.frame.setRange(0, 100)
        
        self.markerSize.setPlaceholderText("40")
        self.HistBinSize.setPlaceholderText("1")
        self.QTscaleMin.setPlaceholderText("Auto")
        self.QTscaleMax.setPlaceholderText("Auto")
        
        self.frame.valueChanged.connect(self.frameValueChange)
        self.markerSize.returnPressed.connect(self.changeMarkerSize)
        self.HistBinSize.returnPressed.connect(self.changeBinSize)
        self.QTscaleMin.returnPressed.connect(self.changeQTscaleMin)
        self.QTscaleMax.returnPressed.connect(self.changeQTscaleMax)
        self.QTHistBlur.stateChanged.connect(self.changeQTBlur)
        
        # Add them to the form layout with a label
        self.form_layout.addRow('Frame:', self.frame)
        self.form_layout.addRow('Marker size:', self.markerSize)
        self.form_layout.addRow('Bin size (in px):', self.HistBinSize)
        self.form_layout.addRow('2D histogram scale max.:', self.QTscaleMax)
        self.form_layout.addRow('2D histogram scale min.:', self.QTscaleMin)
        self.form_layout.addRow('Apply gaussian blur:', self.QTHistBlur)
        
        self.reloadImageButton  = QPushButton('&Update Image Histogram', self)
        self.reloadImageButton.clicked.connect(self.updateImageHistogramData)

        # Add the controls for the PSF limiting
        self.pltSelector   = QComboBox()

        self.filterMin     = QLineEdit(self)
        self.filterMax     = QLineEdit(self)
        self.filterMin.returnPressed.connect(self.filterData)
        self.filterMax.returnPressed.connect(self.filterData)
        
        self.filterMin.setPlaceholderText("min")
        self.filterMax.setPlaceholderText("max")

        self.localisationCountTotal  = QLabel('', self)
        self.localisationCount       = QLabel('', self)
        self.filterMedian            = QLabel('', self)
        self.filterMean              = QLabel('', self)
        self.filterStd               = QLabel('', self)

        self.form_layout2.addRow('Nr. of initial localisations:', self.localisationCountTotal)
        self.form_layout2.addRow('Nr. of selected localisations:', self.localisationCount)
        self.form_layout2.addRow('Filter lower bound:', self.filterMin)
        self.form_layout2.addRow('Filter upper bound:', self.filterMax)
        self.form_layout2.addRow('Filtered data median:', self.filterMedian)
        self.form_layout2.addRow('Filtered data mean:', self.filterMean)
        self.form_layout2.addRow('Filtered data std:', self.filterStd)
        
        
        self.leftPane.addLayout(self.form_layout)
        self.leftPane.addWidget(self.reloadImageButton)
        self.leftPane.addWidget(self.pltSelector)
        self.leftPane.addLayout(self.form_layout2)
        self.leftPane.addStretch(1)
        
        self.layout.addLayout(self.leftPane)

        # create the pot window and the open and close button line
        self.rightPane        = QVBoxLayout()
        self.mainFrame        = QVBoxLayout()
        self.buttonLayout     = QHBoxLayout()
        self.buttonLayout.addStretch(1)
        
        self.mainFrameWindow    =  QWidget()
        self.buttonLayoutWindow = QWidget()

        self.rightPane.addLayout(self.mainFrame)
        self.rightPane.addLayout(self.buttonLayout)
        self.layout.addLayout(self.rightPane)
        
        
        # Create and add the label to show the close and open buttons
        self.openButton  = QPushButton('&Open', self)
        self.openButtonCall = openDialog(self)
        self.openButton.clicked.connect(self.openButtonCall.showWindow)
        self.reloadButton  = QPushButton('&Reload', self)
        self.reloadButton.clicked.connect(self.reloadData)
        self.saveButton  = QPushButton('&Save', self)
        self.saveButton.clicked.connect(self.saveLocalisation)
        self.closeButton = QPushButton('&Close', self)
        self.closeButton.clicked.connect(QCoreApplication.instance().quit)
        
        self.buttonLayout.addWidget(self.openButton)
        self.buttonLayout.addWidget(self.reloadButton)
        self.buttonLayout.addWidget(self.saveButton)
        self.buttonLayout.addWidget(self.closeButton)

        # add the plot with overlay to the window
        self.imageLayout = QHBoxLayout()
        self.imageLayout.sizeHint()

        self.imageOverlay = PyMultiPageWidget(parent=self)
        self.imageLayout.addWidget(self.imageOverlay)

        self.mainFrame.addLayout(self.imageLayout)

        self.plotFrame = overlayWidget(self.data)
        
        self.imageOverlay.addPage(self.plotFrame.canvas, '')
        
        self.openButtonCall.sendHome.connect(self.setHome)

        # Add the frame slider
        self.frameSlider = QSlider(self)
        self.frameSlider.setOrientation(Qt.Horizontal)
        self.frameSlider.setMinimum(0)
        self.frameSlider.setMaximum(100)
        self.frameSlider.valueChanged.connect(self.frameValueChange)
        self.mainFrame.addWidget(self.frameSlider)
        
        # Add a statusbar message
        self.statusBar()
        
        # Set the outerLayout as the window's main layout
        self.setCentralWidget(self.mainWindow)

    def statusReady(self, msg=None):
        if msg == None:
            self.statusBar().showMessage('Status: Ready')
        else:
            self.statusBar().showMessage('Status: ' + msg + ' Done')
    
    def statusBusy(self, msg='Status: Busy..'):
        self.statusBar().showMessage('Status: ' + msg)
        
    def updateHistogramm(self):
        self.statusBusy('Updating histograms..')
        self.plotFrame.redraw()
        self.plotHistogram.redraw()
        self.statusReady('Updating histograms..')
        return
            

    def pltChange(self, plot):
        self.updateHistogramm()
        return
      
    def frameValueChange(self, frame):
        assert( isinstance(frame, int) )
        
        self.frameSlider.setValue( frame )
        self.plotFrame.redraw(frame)
        self.frame.setValue(frame)
        
    def changeMarkerSize(self):
        try:
            size = int(self.markerSize.text())
        except ValueError: # nothing entered
            return
        self.plotFrame.markerSize = size
        self.plotFrame.redraw()
        return
    
    
    def changeImageHistogram(self, scaleMin, scaleMax, binSize):
        self.statusBusy('Updating image histogram..')
        self.QTHistogram.plot(scaleMin, scaleMax, binSize)
        self.QTHistogram.redraw()
        self.statusReady('Updating image histogram..')
    
    def changeBinSize(self):
        try:
            self.binSize = float(self.HistBinSize.text())
        except ValueError: # nothing entered
            return
        self.statusBusy('Updating bin size..')
        self.changeImageHistogram(self.scaleMin, self.scaleMax, self.binSize)
        self.statusReady('Updating bin size..')
            
    def changeQTscaleMin(self):
        if str(self.QTscaleMin.text()).lower() == 'auto':
            self.scaleMin = None
        else:
            try:
                self.scaleMin = float(self.QTscaleMin.text())
            except ValueError: # nothing entered
                return
        self.statusBusy('Rescaling image histogram..')
        self.changeImageHistogram(self.scaleMin, self.scaleMax, self.binSize)
        self.statusReady('Rescaling image histogram..')
    
    def changeQTscaleMax(self):
        if str(self.QTscaleMax.text()).lower() == 'auto':
            self.scaleMax = None
        else:
            try:
                self.scaleMax = float(self.QTscaleMax.text())
            except ValueError: # nothing entered
                return
        self.statusBusy('Rescaling image histogram..')
        self.changeImageHistogram(self.scaleMin, self.scaleMax, self.binSize)
        self.statusReady('Rescaling image histogram..')
    
    def changeQTBlur(self):
        self.blurHistogram = self.QTHistBlur.isChecked()
        if self.initialised: # only try to plot once initialized
            self.statusBusy('Blurring image histogram..')
            # Set sigma to be around 20nm
            sigma = self.localisationPrecision / (self.pxSize * self.binSize)
            self.QTHistogram.setGaussianBlur(self.blurHistogram, sigma)
            # Update the histogram
            self.changeImageHistogram(self.scaleMin, self.scaleMax, self.binSize)
            self.statusReady('Blurring image histogram..')
    
    
    def updateImageHistogramData(self):
        self.statusBusy('Updateting image data..')
        d = np.asarray(self.data.data.localisations()[['x','y']])
        self.QTHistogram.setData(d)
        self.changeImageHistogram(self.scaleMin, self.scaleMax, self.binSize)
        self.statusReady('Updateting image data..')

    @pyqtSlot(str, str)
    def setHome(self, home):
        self.home = home
        return


    def reloadData(self):
        pass
#    def reloadData(self):
#        if self.dataInitialised:
##            print 'reloading data'
#            self.data = dataHandler(self.fileNameImage, self.fnameLocalisations, \
#                                    self.fnameLocalisationsType, self.pxSize, \
#                                    self.fnameTracks, self.fnameTracksType)
#            self.plotFrame.data = data
#            self.plotFrame.redraw()
#            
#            self.PSFwidthData, self.PSFratioData = data.getPSFdata()
#            self.localisationCountTotal.setText(str(len(self.PSFwidthData)))
#            self.updatePSFstats(self.PSFwidthData)
#            
#            self.updateHistogramm()
#
#        return

    def filterData(self):
        if self.histogramLayout.getCurrentIndex() == 0 and self.fileNameImage == None: #the QT plot is shown
            return # do nothing
        
        self.statusBusy('Filtering data..')
        # get the min reading
        if str(self.filterMin.text()).lower() == 'min':
            currentMin = -1.0 * np.inf
        else:
            try:
                currentMin = float(self.filterMin.text())
            except ValueError: # nothing entered
                currentMin = -1.0*np.inf
        # get the max reading
        if str(self.filterMax.text()).lower() == 'max':
            currentMax = +1.0 * np.inf
        else:
            try:
                currentMax = float(self.filterMax.text())
            except ValueError: # nothing entered
                currentMax = +1.0*np.inf
        
        # get which dataType should be filtered
        dataType, histogram = self.getCurrentHistogram()

        self.filterValues[dataType] = (currentMin, currentMax)
        self.data.filterData(self.filterValues)
        self.updateHistograms()
        self.plotFrame.redraw()
        self.statusReady('Filtering data..')
    
    def getCurrentHistogram(self):
        idx = self.histogramLayout.getCurrentIndex()
        if self.fileNameImage != None:
            idx -= 1
        dataType = self.dataTypes[idx] #the first one is the  QT histogram
        histogram = self.histogramLayout.getPage()
        return dataType, histogram
        
    def updateHistograms(self):
        self.statusBusy('Updating histograms..')
        self.localisationCount.setText( str(len(self.data.data.localisations(dataFilter=True))) )
        # update all the histograms
        for idx in range(1,self.histogramLayout.count()): # the first one is the QT histogram
            dataType = self.dataTypes[idx-1]
            dataUnfiltered = self.data.data.localisations(dataFilter=False)[dataType]
            dataFiltered   = self.data.data.localisations(dataFilter=True )[dataType]
            
            histogram = self.histogramLayout.widget(idx)
            histogram.setData(dataUnfiltered, dataFiltered)
            histogram.plotHistogram()
            histogram.redraw()
        self.statusReady('Updating histograms..')
        return
    
    def changedHistogram(self, idx):
        dataType, histogram = self.getCurrentHistogram()
        dataFiltered   = self.data.data.localisations(dataFilter=True )[dataType]
        
        self.filterMedian.setText( "%.2f" %np.median(dataFiltered) )
        self.filterMean.setText( "%.2f" %np.mean(dataFiltered) )
        self.filterStd.setText( "%.2f" %np.std(dataFiltered) )
        
        minValue, maxValue = self.filterValues[dataType]

        if minValue == -np.inf:
            self.filterMin.setText("")
        else:
            self.filterMin.setText( str(minValue) )
        if maxValue == np.inf:
            self.filterMax.setText("")
        else:
            self.filterMax.setText( str(maxValue) )


    def showData(self, fileNameImage, fnameLocalisations, fnameLocalisationsType, pxSize, CpPh):
        
        def initalise():
            self.histogramLayout = PyMultiPageWidget(self.pltSelector)
            self.histogramLayout.currentIndexChanged.connect(self.changedHistogram)
            self.imageLayout.addWidget(self.histogramLayout)
            return True
        
        ## use for testing
        baseDirectory = './example/'
        fileNameImage = baseDirectory + 'SRVis_imageData.tif'
        fnameLocalisations = baseDirectory + 'SRVis_imageData.txt'
        
        
        self.fileNameImage          = fileNameImage
        self.fnameLocalisations     = fnameLocalisations
        self.fnameLocalisationsType = fnameLocalisationsType
        self.pxSize                 = pxSize
        
        if self.fileNameImage == '':
            self.fileNameImage = None

        self.data = dataHandler(fileNameImage, fnameLocalisations, fnameLocalisationsType, pxSize, CpPh)
        
        self.frame.setRange(0, self.data.maxImageFrame()-1)
        self.frameSlider.setMaximum(self.data.maxImageFrame()-1)
        
        self.localisationCountTotal.setText( str(len(self.data.data.localisations())) )

        ## Generate the image histogram
        # Find the optimal blurring based on the localisation precision (from rapidstorm)
        if 'Uncertainty x' in self.data.data.localisations().columns:
            mean = self.data.data.localisations()['Uncertainty x'].mean()
            std  = self.data.data.localisations()['Uncertainty x'].std()
            self.localisationPrecision = mean + 2.0*std
        sigma = self.localisationPrecision / (self.pxSize * self.binSize)
        # Get the data and plot the image histogram       
        d = np.asarray(self.data.data.localisations()[['x','y']])
        self.QTHistogram   = imageHistogramWidget(d, title='2D Histogram', parent=self)
        self.QTHistogram.setGaussianBlur(self.blurHistogram, sigma) # Update in case the checkbox has been toggled
        self.QTHistogram.plot()
        
        if self.fileNameImage == None: # no TIFF image available, show the histogram instead
            self.imageOverlay.addPage(self.QTHistogram, '')
            self.imageOverlay.setCurrentIndex(1)
        else:
            if not self.initialised:
                self.initialised = initalise()
            self.plotFrame.data = self.data
            self.plotFrame.initialise()
            self.histogramLayout.addPage(self.QTHistogram, '2D Histogram Visualisation')
        
        
        # add the 1D histograms to the data        
        locData = self.data.data.localisations()
        for dataType in locData.columns:
            if dataType in ['x','y','frame']:
                continue
            if not self.initialised:
                self.initialised = initalise()
            self.dataTypes.append(dataType)
            title = '\n\n' + dataType + ' Histogram'
            currentPlotHistogram = dataWidget( locData[dataType], title=title, parent=self.pltSelector )
            currentPlotHistogram.plotHistogram()
            self.filterValues[dataType] = (-np.inf, np.inf)
            self.histogramLayout.addPage(currentPlotHistogram, dataType)

        self.resize(1500,700)
        self.initialised = True # We're done and set up
        return

    def saveLocalisation(self):
        path = QFileDialog.getSaveFileName(self, 'Save localisations to', self.home)
        print 'Saving data to:', str(path)
        self.data.saveLocalisations(str(path), self.pxSize)
 
    def run(self):
        # Show the form
        self.show()
        # Run the qt application
        qt_app.exec_()




if __name__ == '__main__':
    
    qt_app = QApplication(sys.argv)
    
    # Create an instance of the application window and run it
    app = SRVis()
#    app.run()
    app.show()
    sys.exit(qt_app.exec_())







