import re
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
import sys

import dllWrapper
import errorLogging

class EVWindow(QtWidgets.QMainWindow):
    def __init__(self):
        
        # setup UI
        super(EVWindow, self).__init__()
        uic.loadUi("UI/UI_ExprEditor.ui", self)
        self.setFixedSize(self.size())              # this stops the window from being resized.
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))
        
        # need a clipbaord handler for ctrl+c
        self.clipboardHandler = QApplication.clipboard()
    
        # child UI components we need references to
        self.actionCopy     = self.findChild(QAction, "actionCopy")
        self.actionCopyDbg  = self.findChild(QAction, "actionCopyDbg")
        self.actionCopyAll  = self.findChild(QAction, "actionCopyAll")
        self.outputLabel    = self.findChild(QLabel, "outputLbl")
        
        # continue to next section buttons
        self.exportHDLBtn   = self.findChild(QCommandLinkButton, "exportHDLBtn")
        self.exportProgBtn  = self.findChild(QCommandLinkButton, "exportPLBtn")
        self.createBOMBtn   = self.findChild(QCommandLinkButton, "genBOMBtn")
        
        # more UI actions we need references for
        self.actionCopy.triggered.connect(self.copyExprToClipboard)
        self.actionCopyDbg.triggered.connect(self.copyDebugToClipboard)
        self.actionCopyAll.triggered.connect(self.copyAllToClipboard)
        
        self.actionAutoOpenExport   = self.findChild(QAction, "actionAutoOpenExport")
        self.actionAutoOpenBOM      = self.findChild(QAction, "actionAutoOpenBOM")
        self.actionAutoClose        = self.findChild(QAction, "actionAutoClose")  
        
        # Setup the scrollbar so we can see big pieces of text
        sA = self.findChild(QScrollArea, "scrollArea")
        sA.takeWidget()
        sA.setWidget(self.outputLabel)
        sA.setWidgetResizable(True)  # Allows resizing with the window
        sA.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        sA.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # use rich text for labels
        self.outputLabel.setTextFormat(Qt.TextFormat.RichText)
        
        self.saveData = []
        self.isGenerated = False
        self.outputExpr = ""

        # setup our dll
        dllWrapper.dllInit()
    
    def copyAllToClipboard(self):
        self.clipboardHandler.setText(f"Expr: {self.outputExpr} Debug: {self._copyDebugToClipboard()}")
    
    # copy the output expression to clipboard
    def copyExprToClipboard(self):
        self.clipboardHandler.setText(self.outputExpr)

    # copy the debug text to clipboard
    def _copyDebugToClipboard(self):
        # get the debug text (which has html tags for formatting data)
        debugText = self.outputLabel.text()[self.outputLabel.text().find("Debug"):]
        
        # This regex is anything between <> tags which is the formatting html used to make the string look good
        htmlStuff = re.findall("</?[a-z \"=\\-:;]*/?>", debugText)
        
        # for every html tag we found
        for htmlItem in htmlStuff:
            # remove it from the text
            debugText = debugText.replace(htmlItem, "")
        
        # remove the debug prefix as it looks ugly
        return debugText.removeprefix("Debug")
        
    def copyDebugToClipboard(self):
        self.clipboardHandler.setText(self._copyDebugToClipboard())
    
    # register whether this section has been generated
    def registerGenerated(self, isGenerated):
        self.isGenerated = isGenerated

    # This is the function that recieves the truth table and processes it
    def sendDataToWindow(self, data):
        # convert the truth table to sum of products form
        SOP = dllWrapper.sumOfProducts(data[0], data[1])
        
        if SOP == "0" or SOP == "1":   # Constant output, no need to simplify
            self.setExpressionText(exprOut=SOP, SOP_RAW=SOP, passes=0, identites="Predefined constant result")
            errorLogging.raiseInfoDlg("Boolean Expression Warning!", f"The Truth Table you entered had a constant output of {SOP}. This is likely not intended, you may wish to check your data before proceeding.")
        else:
            # we can potentially simplify this expression
            BOOL = dllWrapper.simplifyBooleanExpr(SOP)
            # this is the simplified expression
            self.outputExpr = BOOL[0]
            # set the output text label in the GUI 
            self.setExpressionText(exprOut=BOOL[0], SOP_RAW=SOP, passes=BOOL[2], identites=BOOL[1])

    def setExpressionText(self, exprOut, SOP_RAW, passes, identites):
        # get the expression's data
        self.outputExpr = exprOut
        # update save data
        self.saveData = [True, exprOut, passes, SOP_RAW, identites]
        
        self.outputLabel.setText(
            # this looks messy but Qt looks better if we put in HTML format with the required ata
            f"<p><span style=\" font-weight:600;\">\
                Expression Generated: {exprOut}</span></p><p><span style=\" font-style:italic; text-decoration: underline;\">\
                Debug</span><span style=\" text-decoration: underline;\"><br/></span><span style=\" font-style:italic;\">\
                Raw SOP: {SOP_RAW} </span><br/><span style=\" font-style:italic;\">Passes: {passes}</span><br/><span style=\"\
                font-style:italic;\">Identities Used: {identites}</span></p>"
            )
    
    def getSaveData(self) -> str:
        # return all the data in the system needed to save
        return (self.saveData + [self.actionAutoClose.isChecked(), self.actionAutoOpenBOM.isChecked(), self.actionAutoOpenExport.isChecked()])
        
if __name__ == '__main__':
    _exprEditorApp = QtWidgets.QApplication(sys.argv)
    _exprEditorWindow = EVWindow()
    _exprEditorWindow.show()
    sys.exit(_exprEditorApp.exec_())