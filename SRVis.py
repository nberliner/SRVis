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
from SRVisInterface import openDialog, PyMultiPageWidget


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
        
        # Initialise some values
        self._initValues()
        
        self.histogramLayout = None
        
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
        self.QTBlurSigma  = QLineEdit(self)
        self.scalebar     = QLineEdit(self)
        
        self.frame.setSingleStep(1)
        self.frame.setValue(0)
        self.frame.setRange(0, 100)
        
        self.markerSize.setPlaceholderText("40")
        self.HistBinSize.setPlaceholderText("1")
        self.QTscaleMin.setPlaceholderText("Auto")
        self.QTscaleMax.setPlaceholderText("Auto")
        self.QTBlurSigma.setPlaceholderText("20")
        self.scalebar.setPlaceholderText("None")
        
        self.frame.valueChanged.connect(self.frameValueChange)
        self.markerSize.returnPressed.connect(self.changeMarkerSize)
        self.HistBinSize.returnPressed.connect(self.changeBinSize)
        self.QTscaleMin.returnPressed.connect(self.changeQTscaleMin)
        self.QTscaleMax.returnPressed.connect(self.changeQTscaleMax)
        self.QTHistBlur.stateChanged.connect(self.changeQTBlur)
        self.QTBlurSigma.returnPressed.connect(self.changedSigma)
        self.scalebar.returnPressed.connect(self.setScalebar)
        
        # Add them to the form layout with a label
        self.form_layout.addRow('Frame:', self.frame)
        self.form_layout.addRow('Marker size:', self.markerSize)
        self.form_layout.addRow('Bin size (in px):', self.HistBinSize)
        self.form_layout.addRow('2D histogram scale max.:', self.QTscaleMax)
        self.form_layout.addRow('2D histogram scale min.:', self.QTscaleMin)
        self.form_layout.addRow('Apply gaussian blur:', self.QTHistBlur)
        self.form_layout.addRow('Gaussian blur sigma (in nm):', self.QTBlurSigma)
        self.form_layout.addRow('Add scalebar (in nm):', self.scalebar)
        
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
    
    def _initValues(self):
        self.binSize       = 1
        self.scaleMin      = None
        self.scaleMax      = None
        self.blurHistogram = False
        self.sigma         = 1.0
        self.dataTypes     = list()
        self.filterValues  = dict()

    def statusReady(self, msg=None):
        if msg is None:
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
        
        # Set both input field to the new value
        self.frameSlider.setValue( frame )
        self.frame.setValue(frame)
        
        # Update the image
        try:
            self.plotFrame.redraw(frame)
        except AttributeError: # this happens if there is no raw image specified by the user
            pass
        except ValueError: # this happens because the self.loc is not set to None.. but doing
                           # creates another problem. (see imageClass.py)
            pass
        
        
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
        self.updateSigma()
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
            # Set the gaussian blur
            self.QTHistogram.setGaussianBlur(self.blurHistogram, self.sigma)
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
        if self.data is not None:
            self.statusBusy('Reloading localisation data..')
            self.data.reloadData('localisations') # Update the localisation data
            
            # Update the localisation count
            self.localisationCountTotal.setText( str(len(self.data.data.localisations())) )
            
            # Update the histograms
            self.updateHistograms()
            self.plotFrame.redraw()
            
            # Update the image histogram
            self.updateImageHistogramData()
            
            self.statusReady(None)
        return

    def filterData(self):
        if self.histogramLayout.getCurrentIndex() == 0 and self.fileNameImage is not None: # the QT plot or nr loc per frame
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
        try:
            self.plotFrame.redraw()
        except: # errors can happen if there is no raw image specified, the image is not yet initialised etc.
            pass
        self.statusReady('Filtering data..')
    
    def getHistogramIndex(self):
        idx  = self.histogramLayout.getCurrentIndex()
        idxs = range(self.histogramLayout.count()) # the first one is the QT histogram
        if self.fileNameImage is not None:
            idx -= 1 # Minus one for the image histogram
            idxs = range(1,self.histogramLayout.count()) 
        
        return idx, idxs
    
    def getCurrentHistogram(self):
        idx, _ = self.getHistogramIndex()
        dataType = self.dataTypes[idx]
        histogram = self.histogramLayout.getPage()
        return dataType, histogram
        
    def updateHistograms(self):
        self.statusBusy('Updating histograms..')
        self.localisationCount.setText( str(len(self.data.data.localisations(dataFilter=True))) )
        _, idxs = self.getHistogramIndex() # get the correct indexes

        # Update the histograms
        for idx in idxs:
            dataType = self.dataTypes[idx-idxs[0]] # start at zero
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

    def updateSigma(self):
        self.sigma = self.localisationPrecision / (self.pxSize * self.binSize)
        self.QTBlurSigma.setText( "%.2f" %self.localisationPrecision ) # update the user interface
    
    def changedSigma(self):
        self.sigma = float(self.QTBlurSigma.text()) / (self.pxSize * self.binSize)
    
    def setScalebar(self):
        try:
            scalebarLength = self.scalebar.text()
            if str(scalebarLength) == "": # user reset to None
                scalebarLength = None
            else:
                scalebarLength = float(scalebarLength)
        except:
            print 'Scalebar input not understood'
            self.scalebar.setText("")
            scalebarLength = None
        
        if self.initialised: # if not the image doesn't exist yet
            self.QTHistogram.setScalebarLength(scalebarLength)
            self.QTHistogram.updateScaleBar(None)
    
    def clearAll(self):
        # Clear everything to create a fresh view
        # Clear the input fields
        self.HistBinSize.clear()
        self.QTscaleMin.clear()
        self.QTscaleMax.clear()
        self.QTHistBlur.setCheckState(Qt.Unchecked)
        self.QTBlurSigma.clear()
        self.scalebar.clear()
        
        # Clear the TIFF image and remove the image histogram
        try:
            self.plotFrame.reset()
            if self.imageOverlay.count() == 2: # only remove image histogram widget
                self.imageOverlay.removePage(1)
                self.imageOverlay.setCurrentIndex(0)
        except:
            raise
        # Remove the histogram plots
        self.initialised = self.initaliseShowData()
        self.pltSelector.clear()
        
        # Reset the filter values
        self.filterValues = dict()
        
        # Clear the input fields
        self.filterMin.clear()
        self.filterMax.clear()
        
        # Reset the frame number
        self.frame.setValue(0)
        self.frameSlider.setValue(0)
        
        # Reset some initial values
        self._initValues()


    def initaliseShowData(self):
        if self.histogramLayout is not None:
            self.imageLayout.removeWidget(self.histogramLayout)
            self.histogramLayout.setParent(None)
        
        self.histogramLayout = PyMultiPageWidget(self.pltSelector)
        self.histogramLayout.currentIndexChanged.connect(self.changedHistogram)
        self.imageLayout.addWidget(self.histogramLayout)
        return True

    def showData(self, fileNameImage, fnameLocalisations, fnameLocalisationsType, pxSize, CpPh):

        # Clear the previous data
        self.clearAll()
        
        ## use for testing
#        baseDirectory = './example/'
#        fileNameImage = baseDirectory + 'SRVis_imageData.tif'
#        fnameLocalisations = baseDirectory + 'SRVis_imageData.txt'
        
        
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
        self.updateSigma()
        
        # Get the data and plot the image histogram       
        d = np.asarray(self.data.data.localisations()[['x','y']])
        self.QTHistogram   = imageHistogramWidget(d, title='2D Histogram', parent=self)
        self.QTHistogram.setGaussianBlur(self.blurHistogram, self.sigma) # Update in case the checkbox has been toggled
        self.QTHistogram.plot()
        
        if self.fileNameImage is None: # no TIFF image available, show the histogram instead
            self.imageOverlay.addPage(self.QTHistogram, '')
            self.imageOverlay.setCurrentIndex(1)
        else:
#            if not self.initialised:
#                self.initialised = self.initaliseShowData()
            self.plotFrame.data = self.data
            self.plotFrame.initialise()
            self.histogramLayout.addPage(self.QTHistogram, '2D Histogram Visualisation')
        
        
#        ## Add the 1D histograms to the data        
#        # Add the number of localisations per frame
#        if not self.initialised:
#            self.initialised = self.initaliseShowData()

        # Add the optional histograms
        locData = self.data.data.localisations()
        for dataType in locData.columns:
            if dataType in ['x','y']:
                continue
            self.dataTypes.append(dataType)
            # Add the filter information
            self.filterValues[dataType] = (-np.inf, np.inf)
            # Set the title
            if dataType == 'frame':
                title = '\n\nAvg. nr. of loc. per frame'
            else:
                title = '\n\n' + dataType
            ## Add the histogram to the pltSelector instance
            # The nr. of loc. per frame data should be normalised acording to the bin size
            if dataType == 'frame':
                normalise = np.max(locData[dataType]) / 50.0 # Currently the number of bins is fixed to 50.
                                                             # This neeeds to be changed if the number of bins is changed
            else:
                normalise = 1.0 # Don't normalise

            currentPlotHistogram = dataWidget(locData[dataType] , title=title, parent=self.pltSelector, normalise=normalise )
            currentPlotHistogram.plotHistogram()
            
            self.histogramLayout.addPage(currentPlotHistogram, title.strip())

        self.resize(1500,700)
        self.initialised = True # We're done and set up
        return

    def saveLocalisation(self):
        # Ast the user where to save the data
        path = QFileDialog.getSaveFileName(self, 'Save localisations to', self.home)
        
        self.statusBusy('Saving data to:' + str(path) + ' ..') # update the status bar
        if not path[-4:] == '.dat' and not path[-4:] == '.txt': # check the file extension
            path = str(path) + '.dat'

        self.data.saveLocalisations(str(path), self.pxSize)
        self.statusReady('Saving data')
 
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







