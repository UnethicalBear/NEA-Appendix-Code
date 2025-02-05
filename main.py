import os
import sys
import json
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QCloseEvent, QIcon
from functools import partial

import BOM_DigikeyAPI
import BOM_MouserAPI

# This condition checks if the user is using a high quality monitor. If so, it makes sure the UI library is aware of this.
if hasattr(QtWidgets.QApplication, 'setAttribute'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

import BOMViewerHandler
import ExprEditorHandler                # references to the subwindow files
import TruthTableEditorHandler  
import ExportLanguageHandler

import errorLogging                     # file that allows for easy error handling
import databaseHandler                  # allows for saving of files

class RenameExprDialog(QtWidgets.QDialog):    # Class that manages dialog pop-up for renaming an expression 
    def __init__(self, currentName):
        super().__init__()                          # this invokes PyQt5's internal code
        
        self.setWindowTitle("Rename Expression")    # Set the size and window title 
        self.setMinimumSize(300,100)
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel    # Add the option buttons (Ok and Cancel) 

        self.buttonBox = QDialogButtonBox(QBtn)     # Create the UI element for the options
        self.buttonBox.accepted.connect(self.accept)# link options to reject and accept methods so it is possbile to
        self.buttonBox.rejected.connect(self.reject)# see which one was clicked

        self.layout = QVBoxLayout()                 # create the main UI layout
        self.layout.addWidget(QLabel(f"Enter a new name: (current name is \"{currentName})\"")) # add the indicator for the current name
        newName = QLineEdit()                       # Add a text edit (single line) for the new name
        newName.setObjectName("lineEdit")           # rename it to lineEdit so it can be retrieved later
        self.layout.addWidget(newName)              # add new line edit to UI
        self.layout.addWidget(self.buttonBox)       # add the option buttons
        self.setLayout(self.layout)                 # finalise layout

class MainEditorWindow(QtWidgets.QMainWindow):      # Class that manages the UI functionality for the main winodw
    def __init__(self, args):
        super(MainEditorWindow, self).__init__()    # this invokes PyQt5's internal code
        
        uic.loadUi("UI/UI_MainEditor.ui", self)     # load UI data from the relevant UI file
        self.setFixedSize(self.size())              # this stops the window from being resized
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))

        self.workingExpression = None               # name of the expression being edited
        self.commitNewExpressionName = False        # Whether we need to rename the current expression on close
        
        # References to child windows:
        self.exprWindowReference    = ExprEditorHandler.EVWindow()                             # create the subwindows for each of the available tools
        self.truthTWindowReference  = TruthTableEditorHandler.TTWindow()                     # and then save them into the class so they can be 
        self.exprExporterWindowRef  = ExportLanguageHandler.EXWindow()                       # accessed at a later time
        self.BOMViewerWindowRef     = BOMViewerHandler.BVWindow()
        
        # UI components needed from this window
        self.truthTableBtn  = self.findChild(QPushButton, "truthTableBtn")              
        self.boolExprBtn    = self.findChild(QPushButton, "exprBtn")
        self.exportBtn      = self.findChild(QPushButton, "codeExprtBtn")
        self.BOMBtn         = self.findChild(QPushButton, "BOMBtn")
        
        # the "Close all windows" button in each subwindow
        self.closeAllButtons = [
            self.truthTWindowReference.findChild(QAction,   "actionClose_completely"),
            self.exprWindowReference.findChild(QAction,     "actionCloseAll"),
            self.exprExporterWindowRef.findChild(QAction,   "actionCloseAll"),
            self.BOMViewerWindowRef.findChild(QAction,   "actionCloseAll"),
            self.findChild(QAction, "actionCloseAll")
        ]
        
        # every close all button should cause the app to exit
        for btn in self.closeAllButtons:
            btn.triggered.connect(self.close)
        
        # expression info label in the main editor main window
        self.infoLabel      = self.findChild(QLabel, "infoLbl")
        
        # Menu Actions (e.g. File->Save)
        self.actionOpenBOM      = self.findChild(QAction,"actionOpen_BOM_Editor")
        self.actionOpenExpr     = self.findChild(QAction,"actionOpen_Boolean_Expression_Output") 
        self.actionOpenExport   = self.findChild(QAction,"actionOpen_Code_Exporter")
        self.actionOpenTruthT   = self.findChild(QAction,"actionOpen_Truth_Table_Editor")
        
        # Open window actions to be linked to the relevant functions
        self.actionOpenTruthT   .triggered.connect(self.openTruthTable)
        self.actionOpenExport   .triggered.connect(self.openExportWindow)
        self.actionOpenExpr     .triggered.connect(self.openExprWindow)
        self.actionOpenBOM      .triggered.connect(self.openBOMWindow)
        
        # open the relevant subwindow when the window icon is pressed
        self.truthTableBtn      .clicked.connect(self.openTruthTable)
        self.boolExprBtn        .clicked.connect(self.openExprWindow)
        self.exportBtn          .clicked.connect(self.openExportWindow)
        self.BOMBtn             .clicked.connect(self.openBOMWindow)
        
        # Arrows that display whether a window is disabled, not yet generated or completed
        self.link1          = self.findChild(QLabel, "link1")
        self.link2          = self.findChild(QLabel, "link2")
        self.link3          = self.findChild(QLabel, "link3")
        
        # set default links
        self.activateBOMWindow(False)
        self.activateExportWindow(False)
        self.activateExprViewer(False)
        
        ### CHILD UI REFERENCES ### 
        # This is needed because in some cases we need a reference to a UI element contained within the child windows, e.g. a reference 
        # to the submmit button in the truth table editor. This mainly occurs for when data needs to be sent between windows.
        
        # Truth Table Submit Button (to link to Expr Editor)
        self.truthTWindowReference.generateSOPBtn.clicked.connect(self.truthTableEditorSubmitData)
        self.truthTWindowReference.actGenExpr.triggered.connect(self.truthTableEditorSubmitData)
        
        # Expression Editor Export Button (links to export handler)
        self.exprWindowReference.exportHDLBtn.clicked.connect(self.exprEditorExportHDL)
        self.exprWindowReference.exportProgBtn.clicked.connect(self.exprEditorExportProg)
        self.exprWindowReference.createBOMBtn.clicked.connect(self.exprEditorCreateBOM)
        
        # Expression Exporter 
        self.exprExporterWindowRef.goBtn.clicked.connect(partial(self.markLinkAsCompleted, 2))
        
        # BOM Generator
        self.BOMViewerWindowRef.generatorWindowRef.executeBtn.clicked.connect(partial(self.markLinkAsCompleted, 3))
        
        # Save buttons from each window are managed from the main window
        self.saveBtnMainWindow  = self.findChild(QAction, "actionSave")
        self.saveBtnTTWindow    = self.truthTWindowReference.findChild(QAction, "actionSave")
        self.saveBtnExprWindow  = self.exprWindowReference.findChild(QAction, "actionSave")
        self.saveBtnExprtWindow = self.exprExporterWindowRef.findChild(QAction, "actionSave")
        self.saveBtnBOMWindow   = self.BOMViewerWindowRef.findChild(QAction, "actionSave")
        
        # should saving in a subwindow save eveyrthing or just that subwindow?
        self.saveBtnsAreLinkedRef = self.findChild(QAction, "actionSaveFromSub") 
        
        # partial functions allow each save button to have a different "signature"
        # so that we can tell where it came from        
        self.saveBtnMainWindow. triggered.connect(partial(self.saveProjectFromWindow, 0))
        self.saveBtnTTWindow.   triggered.connect(partial(self.saveProjectFromWindow, 1))
        self.saveBtnExprWindow. triggered.connect(partial(self.saveProjectFromWindow, 2))
        self.saveBtnExprtWindow.triggered.connect(partial(self.saveProjectFromWindow, 3))
        self.saveBtnBOMWindow.  triggered.connect(partial(self.saveProjectFromWindow, 4))
        
        # Option to rename the current window
        self.actionRenameThis   = self.findChild(QAction, "actionRename")
        self.actionRenameThis.triggered.connect(self.renameCurrentExpr)
        
        self.databaseReference = databaseHandler.databaseHandler()
        
        # Load Data from sys.argv 
        
        if len(args) != 4:
            errorLogging.raiseFatalError("Fatal Error (Code 27)", "Fatal Error 27!\nIf you ran main.exe directly this will not work. Use the project manager.")
            return
        
        self.expressionID = int(args[2])
        loadData = args[1].replace("\\\"","\"")
        self.dataLoadedRef:dict = loadData
        try:
            loadedDataDict = dict(json.loads(loadData))
        except json.JSONDecodeError:
            errorLogging.raiseGenericFatalError(6)
            return

        # the expression's data contains categories we don't know about 
        if list(loadedDataDict.keys()).sort() != ["ME","TT","EV","EX","BV"].sort():
            errorLogging.raiseGenericFatalError(7)
    
        # Loading Data Into Main Editor:
        try:
            # current expression's name
            self.workingExpression = loadedDataDict["ME"][0]
            self.infoLabel.setText(f"Working Expression: {loadedDataDict["ME"][0]}")
            if len(args[3]) > 0:
                # this expression is part of projects in args[3]
                projects = args[3].split(",")
                # put these projects in the info label
                self.infoLabel.setText(self.infoLabel.text() + "\nAs part of projects: "+ ", ".join(projects))
            else:
                # not part of any projects
                self.infoLabel.setText(self.infoLabel.text() + " - independent of projects.")
        except IndexError:
            # there was missing data
            errorLogging.raiseGenericFatalError(8)
        except TypeError:
            # there was data, but it wasn't the right type
            errorLogging.raiseGenericFatalError(9)
        except Exception as e:
            # other internal error
            errorLogging.raiseGenericFatalError(10, additionalDbgInfo=e)
            
        # Loading Data into Truth Table Editor 
        try:
            truthTableData = loadedDataDict["TT"]
            
            # number of variables
            self.truthTWindowReference.noVarsSpinBox.setValue(int(truthTableData[0]))
            # setup the saved truth table
            for i, spinBox in enumerate(self.truthTWindowReference.outputSpinBoxes):
                spinBox.setValue(int(truthTableData[1][i]))
            # setup user options
            self.truthTWindowReference.actAutoCloseWin.setChecked(int(truthTableData[2]))
            self.truthTWindowReference.actAutoOpenExpr.setChecked(int(truthTableData[3]))
            # setup links
            self.truthTWindowReference.isDone = int(truthTableData[4])
            
            if int(truthTableData[4]):
                self.markLinkAsCompleted(1)
                
        # TT data was missing, incorrect or corrupted
        except IndexError:
            errorLogging.raiseGenericFatalError(11)
        except TypeError:
            errorLogging.raiseGenericFatalError(12)
        except Exception as e:
            errorLogging.raiseGenericFatalError(13, additionalDbgInfo=e)
    
        # Loading Data into Boolean Expression Viewer
        try:
            exprEditorData = loadedDataDict["EV"]
            if exprEditorData[0]:
                # if we have generated an expression, load its details
                self.exprWindowReference.setExpressionText(exprEditorData[1], exprEditorData[3], exprEditorData[2], exprEditorData[4])
                self.exprWindowReference.actionAutoClose.setChecked(exprEditorData[5])
                self.exprWindowReference.actionAutoOpenBOM.setChecked(exprEditorData[6])
                self.exprWindowReference.actionAutoOpenExport.setChecked(exprEditorData[7])
                
                ## EV's has been generated hasn't been saved (should be EV's instead of TTs)
                ## Identities used string not generated if no identies applied.
                
                self.activateExprViewer()
        # EV data was missing, incorrect or corrupted
        except IndexError:
            errorLogging.raiseGenericFatalError(14)
        except TypeError:
            errorLogging.raiseGenericFatalError(15)
        except Exception as e:
            errorLogging.raiseGenericFatalError(16, additionalDbgInfo=e)
            
        # Loading Data into Code Exporter
        try:
            codeExportData = loadedDataDict["EX"]
            # if we have previously been given an expression to export
            if self.exprWindowReference.outputExpr != None:
                # register expression with exporter window
                self.exprExporterWindowRef.registerExpr(self.exprWindowReference.outputExpr)
            
            # if we've completed this / available / disabled
            
            if not self.exprWindowReference.outputExpr: # no expression generated => disabled
                self.activateExportWindow(False)
            elif codeExportData[0]:                     # expression generated and link finished => completed
                self.markLinkAsCompleted(2)
            else:
                self.activateExportWindow()             # expression generated but not finished => availble
            
            # loading user configureable options 
            if codeExportData[1] != None:
                self.exprExporterWindowRef.actionAutoClose.setChecked(codeExportData[1])
                
            # user has already selected a lanugage type
            if codeExportData[2] in ["Prog","HDL"]:
                self.exprExporterWindowRef.setLanguageMenu(codeExportData[2])
                self.exprExporterWindowRef.setDefaultType()
            else:
                # default to programming lanugage over hDL
                self.exprExporterWindowRef.setLanguageMenu("Prog")
            
            # User has already selected a language
            if codeExportData[3] != None:
                self.exprExporterWindowRef.langComboBox.setCurrentIndex(codeExportData[3])
                self.exprExporterWindowRef.updateExtensionLabel()
            else:
                # default to the first one
                self.exprExporterWindowRef.langComboBox.setCurrentIndex(0)
                self.exprExporterWindowRef.updateExtensionLabel()
            
            if codeExportData[4] != None:
                if os.path.exists(codeExportData[4]):
                    # update default directory
                    self.exprExporterWindowRef.updateDirectoryLabel(codeExportData[4])
                    self.exprExporterWindowRef.setDefaultDirectory()
                else:
                    # default directory doesn't exist
                    errorLogging.raiseError(
                    "Error (Code 25)", "An error (Code 25) occured.\nThe means the default directory for the Expression Exporter does not exist.\nThis error is non fatal."
                    )
                    self.exprExporterWindowRef.updateDirectoryLabel(os.path.expanduser("~"))
                    self.exprExporterWindowRef.setDefaultDirectory()
                    
            else:
                # set home directory as the default directory
                self.exprExporterWindowRef.updateDirectoryLabel(os.path.expanduser("~"))
            
        # EX data was missing, incorrect or corrupted
        except IndexError:
            errorLogging.raiseGenericFatalError(17)
        except TypeError:
            errorLogging.raiseGenericFatalError(18)
        except Exception as e:
            errorLogging.raiseGenericFatalError(19, additionalDbgInfo=e)
    
        # Loading Data into BOM Viewer 
        try:
            BOMLoadData = loadedDataDict["BV"]
            if BOMLoadData[-1]:
                # BOM finished
                self.markLinkAsCompleted(3)
            # send the saved components to the BOM window
            self.BOMViewerWindowRef.loadSaveDataDict(BOMLoadData)
            
            
        # BV window was missing, incorrect or ocrrupted
        except IndexError:
            errorLogging.raiseGenericFatalError(17)
        except TypeError:
            errorLogging.raiseGenericFatalError(18)
        except Exception as e:
            errorLogging.raiseGenericFatalError(19, additionalDbgInfo=e)
            
        # Mark finished sections as complete
        if loadedDataDict["TT"][-1]:
            self.markLinkAsCompleted(1)
        
        if loadedDataDict["EX"][0]:
            self.markLinkAsCompleted(2)
        
        if loadedDataDict["BV"][-1]:
            self.markLinkAsCompleted(3)
            
    def renameCurrentExpr(self):
        # old expression name
        oldName = self.workingExpression
        
        # if the user renames succesfully:
        renameDialog = RenameExprDialog(self.workingExpression)
        if renameDialog.exec():
            
            # validate the new name
            tempText = renameDialog.findChild(QLineEdit, "lineEdit").text()
            if not all((c.isalnum() or c == "_") for c in tempText):
                errorLogging.raiseInfoDlg("Error!", "Expression name may only contain alphanumeric characters or _")
                return
        
            # change the working expression to the new name and update user                   
            self.workingExpression = tempText
            errorLogging.raiseInfoDlg("Rename Expression OK", f"Your expression has been renamed from {oldName} to {self.workingExpression}. This change will come into affect when you close the Expression.")
            
            # update text label
            currentInfoText = self.infoLabel.text()
            splitAt : int = currentInfoText.find(oldName) + len(oldName)
            projectTextToAppend = currentInfoText[splitAt:] 
            self.infoLabel.setText("Working Expression: " + self.workingExpression + projectTextToAppend)
            
            # need to commit on close
            self.commitNewExpressionName = True
            
    def markLinkAsCompleted(self, linkNo : int):
        if linkNo < 1 or linkNo > 3:
            errorLogging.raiseGenericFatalError(47, additionalDbgInfo=f"MOD: {linkNo}")
        
        [print, self.activateExprViewer, self.activateExportWindow, self.activateBOMWindow][linkNo]()
        
        linkLookup = [None, self.link1, self.link2, self.link3]
        linkLookup[linkNo].setStyleSheet("color: rgb(0, 255, 0);")
        
    def activateExprViewer(self,setActive:bool=True):
        self.actionOpenExpr.setEnabled(setActive)
        self.boolExprBtn.setEnabled(setActive)
        if setActive:
            self.link1.setStyleSheet("color: rgb(0, 0, 0);") 
        else:
            self.link1.setStyleSheet("color: rgb(128, 128, 128);")
    
    def activateExportWindow(self,setActive:bool=True):
        self.actionOpenExport.setEnabled(setActive)
        self.exportBtn.setEnabled(setActive)
        if setActive:
            self.link2.setStyleSheet("color: rgb(0, 0, 0);") 
        else:
            self.link2.setStyleSheet("color: rgb(128, 128, 128);")
        
    def activateBOMWindow(self,setActive:bool=True):
        self.actionOpenBOM.setEnabled(setActive)
        self.BOMBtn.setEnabled(setActive)
        if setActive:
            # turn to black colour
            self.link3.setStyleSheet("color: rgb(0, 0, 0);") 
        else:
            # grey (disabled)
            self.link3.setStyleSheet("color: rgb(128, 128, 128);")   
    
    # Open subwindow functions
    def openTruthTable(self):
        self.truthTWindowReference.show()
        self.truthTWindowReference.activateWindow()
    
    def openExprWindow(self):
        self.exprWindowReference.show()
        self.exprWindowReference.activateWindow()
    
    def openExportWindow(self):
        self.exprExporterWindowRef.show()
        self.exprExporterWindowRef.activateWindow()
    
    def openBOMWindow(self):
        #activate window and show
        self.BOMViewerWindowRef.show()
        self.BOMViewerWindowRef.activateWindow()
        
    def exprEditorExportHDL(self):
        self.exprExporterWindowRef.registerExpr(self.exprWindowReference.outputExpr)
        self.exprExporterWindowRef.setLanguageMenu("HDL")
        if self.exprWindowReference.actionAutoOpenExport.isChecked():
            self.openExportWindow()
        if self.exprWindowReference.actionAutoClose.isChecked():
            self.exprWindowReference.hide()
        
        self.activateExportWindow()
        
        if self.findChild(QAction, "actionSave_on_Generate").isChecked():
            self.saveProjectFromWindow(0, True)
        
    def exprEditorExportProg(self):
        self.exprExporterWindowRef.registerExpr(self.exprWindowReference.outputExpr)
        self.exprExporterWindowRef.setLanguageMenu("Prog")
        if self.exprWindowReference.actionAutoOpenExport.isChecked():
            self.openExportWindow()
        if self.exprWindowReference.actionAutoClose.isChecked():
            self.exprWindowReference.hide()
        
        self.activateExportWindow()
        
        if self.findChild(QAction, "actionSave_on_Generate").isChecked():
            self.saveProjectFromWindow(0, True)
    
    def exprEditorCreateBOM(self):
        # called when create BOM pressed
        # first check for internet connection
        hasNet = self.BOMViewerWindowRef.generatorWindowRef.checkForInternet()
        
        self.BOMViewerWindowRef.createBOM.setEnabled(
            hasNet and BOM_MouserAPI.API_KEY != None and BOM_DigikeyAPI.CLIENT_ID !=None and BOM_DigikeyAPI.CLIENT_SECRET != None
        )
            
        # register the boolean expression with the window
        self.BOMViewerWindowRef.registerExpr(self.exprWindowReference.outputExpr)
        # hide/show windows as required
        if self.exprWindowReference.actionAutoClose.isChecked():
            self.exprWindowReference.hide()
        if self.exprWindowReference.actionAutoOpenBOM.isChecked():
            self.openBOMWindow()
            
        self.activateBOMWindow()
        
        # auto save if requried
        if self.findChild(QAction, "actionSave_on_Generate").isChecked():
            self.saveProjectFromWindow(0, True)
    
    def truthTableEditorSubmitData(self):
        # expression viewer can be enabled (this doesnt show the window just prepares it)
        self.activateExprViewer()
        # mark the truth table section as complete
        self.markLinkAsCompleted(1)
        
        if self.findChild(QAction, "actionSave_on_Generate").isChecked():
            self.saveProjectFromWindow(0, True)
        
        # if the auto close is selected, close this window
        if self.truthTWindowReference.actAutoCloseWin.isChecked():
            self.truthTWindowReference.hide()
        # if the auto open next window 
        if self.truthTWindowReference.actAutoOpenExpr.isChecked():
            self.exprWindowReference.show()
        
        # get the Truth Table from the Truth Table Editor Window
        dataToSend = self.truthTWindowReference.submitData()    
        # send this data to the Expression Editor Window
        self.exprWindowReference.sendDataToWindow(dataToSend)   
    
    # Save / close functions
    def saveProjectFromWindow(self, callerID, disableConfirmation=False):
        # print(f"started save, block? {disableConfirmation}, caller: {callerID}")
        try:
            # get a new dictionary copy of the current save data 
            saveDict = dict(json.loads(self.dataLoadedRef)).copy()
        except (json.JSONDecodeError, TypeError):
            # if we can't do this somethign has gone very wrong!
            errorLogging.raiseGenericFatalError(23)

        # save all windows        
        if self.saveBtnsAreLinkedRef.isChecked() or callerID == 0:
            # save all data from all subwindows and main editor
            saveDict = dict(json.loads(self.dataLoadedRef)).copy()
            
            # get all the subwindow's to return their save data and overwrite the current save data
            saveDict["ME"] = [self.workingExpression, saveDict["ME"][1]]
            saveDict["TT"] = self.truthTWindowReference.getSaveData()
            saveDict["EV"] = self.exprWindowReference.getSaveData()
            saveDict["EX"] = self.exprExporterWindowRef.getSaveData()
            saveDict["BV"] = self.BOMViewerWindowRef.getSaveData()
            
        else:
            # only save window that called this function
            match callerID:
                case 1: # Truth Table Editor
                    saveDict["TT"] = self.truthTWindowReference.getSaveData()
                case 2: # Expression Viewer
                    saveDict["EV"] = self.exprWindowReference.getSaveData()
                case 3: # Code Exporter                       
                    saveDict["EX"] = self.exprExporterWindowRef.getSaveData()
                case 4: # BOM Tool   
                    saveDict["BV"] = self.BOMViewerWindowRef.getSaveData()
        try:       
            # try to convert our new savedata to a string for the SQL db    
            outputStr = json.dumps(saveDict)
            # connect to main
            self.databaseReference.connectToDatabase("main.db")
            # save the expression's data
            self.databaseReference.saveExpression(self.expressionID, outputStr)
            # close the connection
            self.databaseReference.closeConnection()
            # tell user all went ok
            if not disableConfirmation:
                errorLogging.raiseInfoDlg("Saved ok!", "Saved Expression.")

            # print(f"finished save, block? {disableConfirmation}, caller: {callerID}")
        # couldn't convert -> invalid save data -> internal error    
        except json.JSONDecodeError:
            errorLogging.raiseGenericFatalError(24)
            
    def closeEvent(self, data : QCloseEvent):
        if not self.commitNewExpressionName and not self.findChild(QAction, "actionAutoSave").isChecked():
            # no need to open SQL database
            self.databaseReference.closeConnection()
            app.exit()
            sys.exit()
        
        if not self.databaseReference.isConnectionOpen():
            # connect to main if not already done so
            self.databaseReference.connectToMain()
        
        # we can't close yet because we need to update the database
        if self.commitNewExpressionName:
            # update the name (sys.argv 2 is the current expression's id)
            self.databaseReference.executeSQLQuery(f"UPDATE Expressions SET expressionName = \"{self.workingExpression}\" WHERE ExpressionID = {sys.argv[2]}")
        
        # check for save on close
        if self.findChild(QAction, "actionAutoSave").isChecked():
            self.saveProjectFromWindow(0, True)
        
        
        self.databaseReference.closeConnection()    
        sys.exit()
    
app = QtWidgets.QApplication(sys.argv)
app.setStyleSheet("""
QMainWindow, QDialog {
    background-color: #2b3c6b;
}
QMenuBar, QScrollArea {
    background-color: #7b92d1;
}
QTableWidget {
    background-color: #7b92d1;
}
QCommandLinkButton{
    color: #b5b5b5;
}
QCommandLinkButton:hover {
    color: white;
}
QLabel, QStatusBar, QCheckBox, QScrollArea {
    color: white;
}

QScrollBar:vertical {
    background: #f0f0f0;
    width: 12px;
    margin: 0px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #0078D7;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #005A9E; 
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none; 
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none; 
}
""")
window = MainEditorWindow(sys.argv)
window.show()
sys.exit(app.exec_())
