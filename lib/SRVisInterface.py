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
from PyQt4.QtCore import *
from PyQt4.QtGui  import *

import os.path as osp

class messageBox(QMessageBox):
    
    def __init__(self, parent=None):
        
        super(messageBox, self).__init__(parent)
    
    def print_message(self, msg):
        
        self.setText("Test Message")

class openDialog(QDialog):
    
    sendHome = Signal(str)
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        
        self.mainWindow = parent
        self.resize(500, 150)
        self.setWindowTitle('Load new data')
        
        self.home = osp.expanduser("~")
        
        self.outerLayout = QVBoxLayout()
        
        # Image
        self.imageLayout = QHBoxLayout()
        self.form_layout_image = QFormLayout()
        self.ImagePath       = QLineEdit(self)
        self.form_layout_image.addRow('Image:', self.ImagePath)
        self.openButtonImage = QPushButton('Browse', self)
        self.openButtonImage.clicked.connect(self.clickedOpenImage)
        
        self.imageLayout.addLayout(self.form_layout_image)
        self.imageLayout.addWidget(self.openButtonImage)
        
        # Localisations
        self.localizationLayout = QHBoxLayout()
        self.form_layout_loc = QFormLayout()
        self.LocalisationPath       = QLineEdit(self)
        self.form_layout_loc.addRow('Localizations:', self.LocalisationPath)
        self.openButtonLoc = QPushButton('Browse', self)
        self.openButtonLoc.clicked.connect(self.clickedOpenLocalizations)
        
        self.localizationLayout.addLayout(self.form_layout_loc)
        self.localizationLayout.addWidget(self.openButtonLoc)
     
        self.outerLayout.addLayout(self.imageLayout)
        self.outerLayout.addLayout(self.localizationLayout)
       
        # Make the check boxes for the file types
        self.groupBoxLocalisations = QGroupBox("Localisations")

        self.radioLoc1 = QRadioButton("&RapidSTORM")
#        self.radioLoc2 = QRadioButton("&Peakselector")
        self.radioLoc4 = QRadioButton("&XYT")
        self.radioLoc1.setChecked(True)

        self.vboxLoc = QVBoxLayout()
        self.vboxLoc.addWidget(self.radioLoc1)
#        self.vboxLoc.addWidget(self.radioLoc2)
        self.vboxLoc.addWidget(self.radioLoc4)
        self.vboxLoc.addStretch(1)
        
        # Add the field for the pixel size in nm
        self.pixelSizeLayout = QFormLayout()
        self.pixelSize       = QLineEdit(self)
        self.CountsPerPhoton = QLineEdit(self)
        self.pixelSize.setPlaceholderText("100")
        self.CountsPerPhoton.setPlaceholderText("1")
        self.pixelSizeLayout.addRow('Pixel size (in nm):', self.pixelSize)
        self.pixelSizeLayout.addRow('Counts per photon:', self.CountsPerPhoton)
        
        self.vboxLoc.addLayout(self.pixelSizeLayout)
        
        self.groupBoxLocalisations.setLayout(self.vboxLoc)

        self.vboxButtons = QHBoxLayout()
        self.vboxButtons.addWidget(self.groupBoxLocalisations)
        self.vboxButtons.addStretch(1)
        

        self.outerLayout.addLayout(self.vboxButtons)
        
        self.outerLayout.addStretch(1)
        
        # Create and add the label to show the close and open buttons
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addStretch(1)
        self.openButton  = QPushButton('&Open', self)
        self.openButton.clicked.connect(self.clickedOpen)
        self.closeButton = QPushButton('&Cancel', self)
        self.closeButton.clicked.connect(self.reject)
        
        self.buttonLayout.addWidget(self.openButton)
        self.buttonLayout.addWidget(self.closeButton)
        
        self.outerLayout.addLayout(self.buttonLayout)
        
        self.setLayout(self.outerLayout)
        
    
    def showWindow(self):
        self.show()
    
    def clickedOpenImage(self):
        path = QFileDialog.getOpenFileName(self, 'Open file', self.home)
        if path == '': # user pressed cancel
            return
        self.home = osp.dirname(str(path))
        self.ImagePath.setText(path)
        return
    
    def clickedOpenLocalizations(self):
        path = QFileDialog.getOpenFileName(self, 'Open file', self.home)
        if path == '': # user pressed cancel
            return
        self.home = osp.dirname(str(path))
        self.LocalisationPath.setText(path)
        return

    def clickedOpen(self):
        self.mainWindow.statusBusy('Loading data..')
        fileNameImage      = str(self.ImagePath.text())
        fnameLocalisations = str(self.LocalisationPath.text())
        
        # check which input file is selected
        if self.radioLoc1.isChecked():
            fnameLocalisationsType = 'rapidstorm'
#        elif self.radioLoc2.isChecked():
#            fnameLocalisationsType = 'peakselector'
        elif self.radioLoc4.isChecked():
            fnameLocalisationsType = 'xyt'
        else:
            print 'No localisation type is checked. Something went wrong..exiting'
            sys.exit() # this is very ugly! Should be changed

        if self.pixelSize.text() == '':
            pxSize = 100 # set the default pixel size
        else:
            pxSize = int(self.pixelSize.text())
        
        if self.CountsPerPhoton.text() == '':
            CpPh = 1
        else:
            CpPh = int(self.CountsPerPhoton.text())

        self.close() # check if this works..
        self.mainWindow.showData(fileNameImage, fnameLocalisations, fnameLocalisationsType, pxSize, CpPh)

        self.sendHome.emit(self.home)
        self.mainWindow.statusReady()




## example taken from here:
## http://ftp.ics.uci.edu/pub/centos0/ics-custom-build/BUILD/PyQt-x11-gpl-4.7.2/examples/designer/plugins/widgets/multipagewidget.py
class PyMultiPageWidget(QWidget):

    currentIndexChanged = pyqtSignal(int)
    pageTitleChanged    = pyqtSignal(str)

    def __init__(self, comboBox=None, parent=None):
        super(PyMultiPageWidget, self).__init__(parent)

#        self.comboBox = QtGui.QComboBox()
#        # MAGIC
#        # It is important that the combo box has an object name beginning
#        # with '__qt__passive_', otherwise, it is inactive in the form editor
#        # of the designer and you can't change the current page via the
#        # combo box.
#        # MAGIC
#        self.comboBox.setObjectName('__qt__passive_comboBox')    

        self.comboBox = comboBox    
        self.stackWidget = QStackedWidget()
        if self.comboBox != None:
            self.comboBox.activated.connect(self.setCurrentIndex)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.stackWidget)
        self.setLayout(self.layout)
        
        self.setSizePolicy ( QSizePolicy.Expanding, QSizePolicy.Expanding)

#    def sizeHint(self):
#        return QSize(150, 150)

    def count(self):
        return self.stackWidget.count()

    def widget(self, index):
        return self.stackWidget.widget(index)

    @pyqtSlot(QWidget)
    def addPage(self, page, title):
        self.insertPage(self.count(), page, title)

    @pyqtSlot(int, QWidget)
    def insertPage(self, index, page, title):
        page.setParent(self.stackWidget)
        self.stackWidget.insertWidget(index, page)
        title = QCoreApplication.translate('PyMultiPageWidget',title)
        page.setWindowTitle(title)
        if self.comboBox != None:
            self.comboBox.insertItem(index, title)

    @pyqtSlot(int)
    def removePage(self, index):
        widget = self.stackWidget.widget(index)
        self.stackWidget.removeWidget(widget)
        if self.comboBox != None:
            self.comboBox.removeItem(index)

    def getPageTitle(self):
        return self.stackWidget.currentWidget().windowTitle()
    
    def getPage(self):
        return self.stackWidget.currentWidget()
    
    @pyqtSlot(str)
    def setPageTitle(self, newTitle):
        self.comboBox.setItemText(self.getCurrentIndex(), newTitle)
        self.stackWidget.currentWidget().setWindowTitle(newTitle)
        self.pageTitleChanged.emit(newTitle)

    def getCurrentIndex(self):
        return self.stackWidget.currentIndex()

    @pyqtSlot(int)
    def setCurrentIndex(self, index):
        if index != self.getCurrentIndex():
            self.stackWidget.setCurrentIndex(index)
            if self.comboBox != None:
                self.comboBox.setCurrentIndex(index)
            self.currentIndexChanged.emit(index)

    pageTitle = pyqtProperty(str, fget=getPageTitle, fset=setPageTitle, stored=False)
    currentIndex = pyqtProperty(int, fget=getCurrentIndex, fset=setCurrentIndex)