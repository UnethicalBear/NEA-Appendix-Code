from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets    import *
from PyQt5.QtNetwork    import QLocalServer, QLocalSocket
from PyQt5.QtCore       import Qt, QEventLoop, QSharedMemory
from PyQt5.QtGui        import *

import hashlib      # needed to verify system integrity
import subprocess   # needed to run the main editor from the project manager
import sys          # OS and SYS give system information that is useful e.g. arguments passed and allows other programs to be called from here (e.g. opening an expression)
import os           # ...other programs to be called from here (e.g. opening an expression)
import datetime     # Allows for the lastUpdated field to be employed as this allows us to get the current time
import json         # Allows for JSON to be read, needed to send data to the Main Editor and to import/export files as well as write to the SQL db
import databaseHandler          # Allows for SQL to be written to the main database
import errorLogging             # Allows for easy error logging if the user or system causes an error
from functools import partial   # Additional function tool that helps with PyQT5 UI systems

# System Information

DEV = False                     # Is the system running in development mode or build mode? 
VERSION = "0.1"                 # System version number
WARNING_IMPORT_VERSIONS = []    # Versions of the system where bugs are known to be found, so we can warn the user importing may not work.

UI_FOLDER_HASH =  "02909D17CDE4D545008D9AD9536FADE5E919DC46959B335FF8463E7059BB67D5"
SOP_DLL_HASH   =  "0676E1B7DB47F492A3E1B91635AACFFDE336E282A4E6D5C1F3D053F0C4A332F5"

# End

def reactivateMainWindow(window:QMainWindow):
    # if hidden, show. this is kinda an obvious one
    if window.isHidden():
        window.show()
    else:
        # this is a weird QT operation but bascially forces the window to reassert itself
        # I have no idea why this line is needed but it refuses to work without it
        window.setWindowState(window.windowState() & ~ Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        window.activateWindow()

    # make sure we reopen the database to stop SQL from breaking everything
    window.databaseRef.connectToMain() # ensure the SQL database is reopened properly

class DeleteWarningDialog(QDialog): # This class is a pop-up dialog that warns the user they are about to delete an item forever
    def __init__(self, msg=None):
        super().__init__()
        
        self.setWindowTitle("DELETE WARNING!")  # setup window with size and title
        self.setMinimumSize(300,100)
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel    # add option buttons 

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)        # assign the option buttons to internal fucntions 
        self.buttonBox.rejected.connect(self.reject)        # this means we get a code of 1 for OK and 0 for cancel

        self.layout = QVBoxLayout()
        if msg != None:
            self.layout.addWidget(QLabel(msg))
        else:    
            self.layout.addWidget(QLabel("Are you sure you want to delete this? This is a permenant change that cannot be recovered."))
        self.layout.addWidget(self.buttonBox)               # add a label that warns the user of the actions
        self.setLayout(self.layout)                         # add this label to the layout

class MainProjectEditorWindow(QtWidgets.QMainWindow):
    def __init__(self, databaseRef : databaseHandler.databaseHandler):
        super(MainProjectEditorWindow, self).__init__()
        
        # by default we show Projects not Expressions
        self.isProjectMode = True
        
        # load the relevant UI file into the window
        uic.loadUi("UI/UI_MainProjectEditor.ui", self)
        self.setFixedSize(self.size())              # this stops the window from being resized.
        # set the window icon
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))
        
        self.databaseRef = databaseRef
        self.newProjectWindowRef = NewProjectEditorWindow(databaseRef)
        self.newExprWindowRef = NewExprEditorWindow(databaseRef)
                
        self.projBtn                = self.findChild(QPushButton, "projBtn")
        self.exprBtn                = self.findChild(QPushButton, "exprBtn")
        self.mainTable              = self.findChild(QTableWidget, "outputFrame")
        self.createBtn              = self.findChild(QPushButton, "createBtn")
        self.openPrevBtn            = self.findChild(QPushButton, "openPrevBtn")
        
        self.actionNewExpr          = self.findChild(QAction, "actionNewExpr")
        self.actionNewProj          = self.findChild(QAction, "actionNewProj")
        self.actionOpenPrevProj     = self.findChild(QAction, "actionOpenPrevProj")
        self.actionOpenPrevExpr     = self.findChild(QAction, "actionOpenPrevExpr")
        
        self.actionImport           = self.findChild(QAction, "actionImport")
        self.actionExport           = self.findChild(QAction, "actionExport")
        self.actionDelete           = self.findChild(QAction, "actionDelete")
        
        self.findChild(QAction, "actionQuit_Application").triggered.connect(app.quit)
        
        self.actionNewExpr.triggered.connect(partial(self.createNew, override=2))
        self.actionNewProj.triggered.connect(partial(self.createNew, override=1))
        
        self.actionOpenPrevExpr.triggered.connect(self.openPrevious)
        self.openPrevBtn.clicked.connect(self.openPrevious)
        
        self.actionImport.triggered.connect(self.importJSONFile)
        self.actionExport.triggered.connect(self.exportJSONFile)
        self.actionDelete.triggered.connect(self.deleteCurrentItem)
        
        self.findChild(QAction, "actionClose").triggered.connect(self.close)
        self.findChild(QAction, "actionResetDB").triggered.connect(self.deleteDB)
        
        self.projBtn.clicked.connect(self.projMenuSelected)
        self.exprBtn.clicked.connect(self.exprMenuSelected)
        self.createBtn.clicked.connect(self.createNew)
        
        self.mainTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        self.projMenuSelected() # init with projects by defualt
        
    def projMenuSelected(self):
        # Called when the user switches to project mode
        self.isProjectMode = True
        # get all project data from the Projects Table in the SQL database
        projectsData = self.databaseRef.readSQLQuery("SELECT * FROM Projects")
        
        # project button can't be clicked because we're in project mode and vice-versa
        self.projBtn.setEnabled(False)
        self.exprBtn.setEnabled(True)
        
        # stops duplicate items from appearing by ensuring the table is empty to begin with
        self.mainTable.clear()
        
        # We need 5 columns: ID, name, lastUpdated, Expressions used and the last is for the button to edit the project
        self.mainTable.setColumnCount(5)
        self.mainTable.setHorizontalHeaderItem(0, QTableWidgetItem("ID"))
        self.mainTable.setHorizontalHeaderItem(1, QTableWidgetItem("Name"))
        self.mainTable.setHorizontalHeaderItem(2, QTableWidgetItem("Last Updated"))
        self.mainTable.setHorizontalHeaderItem(3, QTableWidgetItem("Expressions Used"))
        self.mainTable.setHorizontalHeaderItem(4, QTableWidgetItem(" "))
        
        # we have 1 row for each project
        self.mainTable.setRowCount(len(projectsData))
        
        # iterate over the projects we fetched from the database 
        for count, project in enumerate(projectsData):
            # This SQL query gets the information of each expression linked to the Project that we are currently working on
            expressionsUsed = self.databaseRef.readSQLQuery(
                f"SELECT Expressions.* FROM Expressions INNER JOIN ProjHandler ON Expressions.expressionID = ProjHandler.expressionID WHERE ProjHandler.projectID = {project[0]}"
            )
            
            _project = list(project)                            # convert from tuple to list so it can be modified  
            referencedExpr = ""                        
            for link in expressionsUsed:                
                referencedExpr += f"{link[0]}: {link[1]}, "     # add the expression ID and name if the expression is linked to this project
            referencedExpr = referencedExpr[:-2]                # remove trailing ', '
            _project.append(referencedExpr)                     # add to data to fill into table
            
            for i in range(len(_project)):                      # fill the row of the table with the data gathered
                data = QTableWidgetItem(str(_project[i]))       # Create a new item in the table with the current data
                self.mainTable.setItem(count, i, data)          # set this item into the table widget
                
            # The last column is a button to edit the project selected. We need to create a new button, link it to the edit function
            # and then add it to the table in the right-most column
            editProjectButton = QPushButton()
            editProjectButton.setText("Edit")
            editProjectButton.clicked.connect(self.editProject)
            self.mainTable.setCellWidget(count, 4, editProjectButton)
        
    def editProject(self):
        # (re)create the project editor window 
        self.newProjectWindowRef.__init__(self.databaseRef)
        editingID = self.mainTable.item(self.mainTable.currentRow(), 0).text() # get the project ID to be edited
        # we know this ID because when the user clicks edit it changes the current row, so the first column of that row 
        # is the ID we need to edit. We never work out which button was pressed, instead getting the button's location
        # in the grid.
        
        # show the window and activate it
        self.newProjectWindowRef.show()
        self.newProjectWindowRef.activateWindow()
        
        # change the ID of the current editing project to the one we just retrieved
        self.newProjectWindowRef.updateIDLabel(int(editingID))
        # editing a project, not creating it
        self.newProjectWindowRef.setMode(2)
        
    def exprMenuSelected(self):
        # projectMode is now false
        self.isProjectMode = False
        # SQL to retrive the expressions from the database
        expressionData = self.databaseRef.readSQLQuery("SELECT * FROM Expressions")
        
        # we can't click the expressions btn because we're in expressions mode and vice versa
        self.projBtn.setEnabled(True)
        self.exprBtn.setEnabled(False)
        
        
        self.mainTable.clear()
        
        # reformat the table to show Expressions
        self.mainTable.setColumnCount(5)
        self.mainTable.setHorizontalHeaderItem(0, QTableWidgetItem("ID"))
        self.mainTable.setHorizontalHeaderItem(1, QTableWidgetItem("Name"))
        self.mainTable.setHorizontalHeaderItem(2, QTableWidgetItem("Last Updated"))
        self.mainTable.setHorizontalHeaderItem(3, QTableWidgetItem("Part of Projects"))
        self.mainTable.setHorizontalHeaderItem(4, QTableWidgetItem(""))
        
        # 1 row for every expression
        self.mainTable.setRowCount(len(expressionData))
        
        # do this for every expression in the database
        for count, expression in enumerate(expressionData):
            # SQL to select all expressions where there is a link defined between the current project and the expression
            projectsUsed = self.databaseRef.readSQLQuery(
                f"SELECT Projects.* FROM Projects INNER JOIN ProjHandler ON Projects.ProjectID = ProjHandler.projectID WHERE ProjHandler.expressionID = {expression[0]}"
            )
            
            _expression = [expression[0], expression[1], expression[3]]  # convert from tuple to list so it can be modified  
            
            referencedProj = ""                                 # Projects this expression is in
            for link in projectsUsed:                
                referencedProj += f"{link[0]}: {link[1]}, "     # add the expression ID and name if the expression is linked to this project
            referencedProj = referencedProj[:-2]                # remove trailing , and space
            _expression.append(referencedProj)                  # add to data to fill into table
            
            for i in range(len(_expression)):                   # fill the row of the table with the data gathered
                data = QTableWidgetItem(str(_expression[i]))    # convert to str to display the item
                self.mainTable.setItem(count, i, data)         
            
            # add a button to open the expression on the far right
            openBtn = QPushButton()
            openBtn.setText("Open")
            openBtn.clicked.connect(self.openExpression)
            self.mainTable.setCellWidget(count, 4, openBtn)

    def openExpression(self):
        projectID = self.mainTable.item(self.mainTable.currentRow(), 0).text()
        self.openExpressionByID(projectID)
    
    def openExpressionByID(self, exprID):
        # if we're not connected to the database
        if not self.databaseRef.isConnectionOpen():
            # now would be a pretty good time to do so
            self.databaseRef.connectToMain()
        
        # all the projects used by this Expression
        _projectsUsed = self.databaseRef.readSQLQuery(
            f"SELECT Projects.projectName FROM Projects INNER JOIN ProjHandler ON Projects.projectID = ProjHandler.projectID WHERE ProjHandler.expressionID = {exprID}"
        )
        projectsUsed = [proj[0] for proj in _projectsUsed] # get rid of stupid Sqlite formatting and just make this a normal python list
        projectsUsed = str(projectsUsed) 
        projectsUsed = projectsUsed.replace("'","") # remove quotes from SQL query
        projectsUsed = projectsUsed[1:-1] # remove brackets from SQL query
        
        # now get the expression's data
        data = self.databaseRef.readSQLQuery(f"SELECT ExpressionData FROM Expressions WHERE expressionID = {exprID}")[0][0]
        data = data.replace("\\\"", "\"") # replace \" with " to stop triple quotes causing an error
        data = data.replace("\"", "\\\"") # replace " with \" so that the double quotes don't cause an error
        if DEV: # If working on the source code, open using python
            subprocess.Popen(f"python main.py \"{data}\" {exprID} \"{projectsUsed}\"", shell=True)
            # we aren't the active window, release control of db
            self.databaseRef.closeConnection()
            # hide this window
            self.hide()
        else:   # Otherwise, call the executable (active build mode)
            if os.path.exists("main.exe"):
                self.databaseRef.closeConnection()
                self.hide()

                path = os.getcwd() + "\\main.exe"
                subprocess.call(f"{path} \"{data}\" \"{exprID}\" \"{projectsUsed}\"")
            else:
                # lol the executable's gone walkies
                errorLogging.raiseGenericFatalError(26)
          
    def openPrevious(self):
        if not self.databaseRef.isConnectionOpen():
            self.databaseRef.connectToMain()
        # This SQL query gets the expressions data sorted by when they were last updated. The most recent expression is the first.
        data = self.databaseRef.readSQLQuery("SELECT ExpressionID, lastUpdated FROM Expressions ORDER BY lastUpdated DESC")
        if len(data) == 0:
            # no projects exist so cannot open the most recent one
            return
        self.openExpressionByID(data[0][0])

    def importJSONFile(self):
        try:
            # Create new options for opening file
            importFileDlg = QFileDialog.Options()
            importFileDlg |= QFileDialog.DontUseNativeDialog
            
            # set default directory to search in
            downloadsFolder = os.path.expanduser("~") + "\\Downloads"
            
            # Get the user to select a file
            fileName = QFileDialog.getOpenFileName(self,"Choose a file to import...", downloadsFolder,"JSON Files (*.json);;All Files (*)", options=importFileDlg)[0]
           
            # what we are importing
            importDict = {}
            # as above but a string version
            importStr = ""
           
            if fileName: # this means the user selected a file and didn't cancel the operation
                with open(fileName, "r") as f:      # open selected file
                    importStr = json.load(f)        # load json as string
                    importDict = dict(importStr)    # convert json string to dict for better handling
                
                # if the version this was exported from isn't the same as this one errors could be caused
                if (importDict["importInfo"]["systemVersion"] != VERSION):
                    errorLogging.raiseError("Error! (Code 33)", "The version of the imported file is not the version of this system. The import's quality cannot be guarenteed.")
                
                # importing an expression
                if importDict["importInfo"]["importType"] == "Expression":
                    # get the expression's name
                    importedName = importDict["data"]["exprName"]
                    # get the expresison's data and format it for the sql db
                    importedData = json.dumps(importDict["data"]["exprData"])
                    importedData = importedData.replace("\"","\\\"")  
                    # insert into the database and refresh expressions
                    self.databaseRef.executeSQLQuery(f"INSERT INTO Expressions (expressionName, expressionData, lastUpdated) VALUES ('{importedName}','{importedData}', '{databaseHandler.generateTimeStamp()}')")         
                    if not self.isProjectMode:
                        self.exprMenuSelected()
                
                elif importDict["importInfo"]["importType"] == "Project":
                    projectName = importDict["data"]["projectName"]
                    
                    # all queries that need to be made to add the projects & expressions
                    sqlToExecute = []
                    # project iD this project will have
                    importedProjectID = -1
                    
                    nextProjID = self.databaseRef.readSQLQuery("SELECT seq FROM sqlite_sequence WHERE name = 'Projects'")
                    if nextProjID == []:
                        importedProjectID = 0
                    else:
                        importedProjectID = nextProjID[0][0] + 1
                        
                    sqlToExecute.append(
                        f"INSERT INTO Projects (projectName, lastUpdated) VALUES (\"{projectName}\",\"{databaseHandler.generateTimeStamp()}\")"
                    )

                    for expression in importDict["data"]["projectExpressions"]:
                        # get the expression's data
                        importedExprData = expression["exprData"]
                        # convert to string so it can be put in a db
                        importedExprData = json.dumps(importedExprData)
                        # stop special characters messing things up                        
                        importedExprData = importedExprData.replace("\"", "\\\"")
                        
                        # create new expression
                        sqlToExecute.append(f"""INSERT INTO Expressions (expressionName, expressionData, lastUpdated)
                        VALUES (\"{expression["exprName"]}\", \'{importedExprData}\', \"{databaseHandler.generateTimeStamp()}\")""")
                        
                    # Get the next available ExpressionID as this is where we will begin importing    
                    nextID = self.databaseRef.readSQLQuery("SELECT seq FROM sqlite_sequence WHERE name = 'Expressions'")
                    start = 0
                    if nextID == []:
                        start = 0
                    else:
                        start = nextID[0][0] + 1
                        
                    # create a list of all the expressionID's we will import
                    importedExpressionIDs = [start + i for i in range(len(importDict["data"]["projectExpressions"]))]
                    
                    # for each one of them add a link to the imported project
                    for exprID in importedExpressionIDs:
                        sqlToExecute.append(
                            f"INSERT INTO ProjHandler (ProjectID, ExpressionID) VALUES ({importedProjectID}, {exprID})"
                        )
                        
                    # run these queries on the SQL database
                    self.databaseRef.executeMultipleQueries(sqlToExecute)                   
                    
                    if self.isProjectMode:
                        self.projMenuSelected()
            
            errorLogging.raiseInfoDlg("Imported JSON File", f"Imported JSON file \"{fileName}\" from your downloads folder.")
        except json.JSONDecodeError:
            # could not decode the JSON file -> invalid character / syntax etc.
            errorLogging.raiseError("Error!", "An Error (Code 29) occured.\n This means that the file you imported was not JSON. If this is unexpected, contact the developers.")
        except KeyError:
            # key doesn't exist -> file not of correct standard
            errorLogging.raiseError("Error!", "An Error (Code 30) occured.\n This means that the file you imported was not of the correct syntax. If this is unexpected, contact the developers.")
        except IndexError:
            # list not fully complete -> file not of correct standard
            errorLogging.raiseError("Error!", "An Error (Code 31) occured.\n This means that the file you imported was not of the correct syntax. If this is unexpected, contact the developers.")
        except:
            # code didn't run sucessfully -> internal error!
            errorLogging.raiseGenericFatalError(32)
    
    def exportJSONFile(self):
        if self.isProjectMode: # exporting a project
            # get the project id
            exportProjID = self.mainTable.item(self.mainTable.currentRow(), 0).text()
            # get the project name
            projName = self.mainTable.item(self.mainTable.currentRow(), 1).text()
            
            # header that provides some info so when imported we know where the file
            # came from and what to do with it            
            exportDictionary = {
                "importInfo":{
                    "importType":"Project",
                    "systemVersion":VERSION
                },
                "data":{
                    "projectName":projName,
                    "projectExpressions":[]
                }
            }
            
            # get all the expressions in this project
            linkedExpr = self.databaseRef.readSQLQuery(
                f"SELECT Expressions.* FROM Expressions INNER JOIN ProjHandler ON Expressions.expressionID = ProjHandler.expressionID WHERE ProjHandler.projectID = {exportProjID}"
            )
            for link in linkedExpr:
                # for each one, add the relevant fields to the project export
                exportDictionary["data"]["projectExpressions"].append(
                    {
                        "exprName":link[1],
                        "exprData":json.loads(link[2])
                    }
                )
            
            # write to a file in the downloads folder
            fileName = f"PROJ_ID_{exportProjID}.json"
            path = os.path.expanduser("~") + "\\Downloads\\" + fileName
            with open(f"{path}", "w") as f:
                # convert our dictionary to json
                json.dump(exportDictionary, f, indent=4)
            
        else:
            # exporting json file to downloads
            
            # get the expression's id, name and data
            exportID = self.mainTable.item(self.mainTable.currentRow(), 0).text()
            exprName = self.mainTable.item(self.mainTable.currentRow(), 1).text()
            exprData = self.databaseRef.readSQLQuery(f"SELECT expressionData FROM Expressions WHERE expressionID = {exportID}")[0][0]
            
            # turn this data into a dictionary so we can work with it
            exprData = dict(json.loads(exprData))
            
            # header that provides some info so when imported we know where the file
            # came from and what to do with it  
            exportDictionary = {
                "importInfo":{
                    "importType":"Expression",
                    "systemVersion":VERSION
                },
                "data":{
                    "exprName":exprName,
                    "exprData":exprData
                }
            }
            
            # write to a file in the downloads folder
            fileName = f"EXPR_ID_{exportID}.json"
            path = os.path.expanduser("~") + "\\Downloads\\" + fileName
            with open(f"{path}", "w") as f:
                # convert our dictionary to json for writing
                json.dump(exportDictionary, f, indent=4)
        
        errorLogging.raiseInfoDlg("Exported JSON File", f"Exported JSON file \"{fileName}\" to your downloads folder.")
        
    def createNew(self, override=None):
        # override code allows us to force a mode, needed to stop bugs happening
        if override == 1:
            self.projMenuSelected()
        elif override == 2:
            self.exprMenuSelected()
            
        # if we are in project mode, we are creating a new project
        if self.isProjectMode:
            # this loop bascially waits to refresh the database only once the user has
            # finished creating the project, stops the whole thing crashing every 10 seconds 
            waitForFinishedLoop = QEventLoop()
            # show the creation window
            self.newProjectWindowRef.__init__(self.databaseRef)
            self.newProjectWindowRef.show()
            self.newProjectWindowRef.activateWindow()
            # creating mode
            self.newProjectWindowRef.setMode(1)
            self.newProjectWindowRef.updateIDLabel()
            # when the user finishes with the creation window, then update the system
            self.newProjectWindowRef.destroyed.connect(waitForFinishedLoop.quit)
            waitForFinishedLoop.exec()
            self.projMenuSelected() # refresh table in case new project made
        
        else:
            # stop executing code here until the user is done with the other window
            waitForFinishedLoop = QEventLoop()
            # refresh the creation window before opening and activating it
            self.newExprWindowRef.update()
            self.newExprWindowRef.show()
            self.newExprWindowRef.activateWindow()
            # When the user exits the creation window, resume this code
            self.newExprWindowRef.destroyed.connect(waitForFinishedLoop.quit)
            waitForFinishedLoop.exec()
            # return to the expression mode
            self.exprMenuSelected()
            
    def deleteCurrentItem(self):
        if not DeleteWarningDialog().exec():
            return

        for item in self.mainTable.selectedIndexes():
            self._deleteCurrentItem(
                int(self.mainTable.item(item.row(), 0).text())
            )
            
        
        if self.isProjectMode:
            self.projMenuSelected()
        else:
            self.exprMenuSelected()
    
    def _deleteCurrentItem(self, deleteID:int) -> None:
    
        if self.isProjectMode:
            self.databaseRef.executeMultipleQueries([
                f"DELETE FROM Projects WHERE projectID = {deleteID}",
                f"DELETE FROM ProjHandler WHERE projectID = {deleteID}"
            ])
        else:
            self.databaseRef.executeMultipleQueries([
                f"DELETE FROM Expressions WHERE expressionID = {deleteID}",
                f"DELETE FROM ProjHandler WHERE expressionID = {deleteID}",
            ])

    def deleteDB(self):
        # WARNING THIS FUNCTION RESETS THE ENTIRE DATABASE!!!!
        if DeleteWarningDialog("WARNING! This will delete all items in the database FOREVER with NO rollback. The program will be closed. Are you sure?").exec():
            if self.databaseRef.executeMultipleQueries([
                "DELETE FROM Projects",
                "DELETE FROM Expressions",
                "DELETE FROM ProjHandler"
            ]):
                self.databaseRef.resetExprIncrement()
                self.databaseRef.resetProjectIncrement()
                self.close()
                sys.exit()
            else:
                errorLogging.raiseGenericFatalError(28)
                
class NewExprEditorWindow(QtWidgets.QMainWindow):
    def __init__(self, databaseRef : databaseHandler.databaseHandler):
        # load ui components this inherits 
        super(NewExprEditorWindow, self).__init__()
        # load ui file
        uic.loadUi("UI/UI_NewExprEditor.ui", self)
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))
        # stop window resizing
        self.setFixedSize(self.size())
        
        # refernece to the database manager
        self.databaseRef = databaseRef
        # are we yet to show the name validation error?
        self.showValidationError = True
        
        # referneces to ui children 
        self.exprCloneComboBox = self.findChild(QComboBox,  "cloneBox")
        self.exprCloneCheckBox = self.findChild(QCheckBox,  "useClone")
        self.exprIdLbl         = self.findChild(QLabel,     "exprIdLbl")
        self.exprNameEdit      = self.findChild(QLineEdit,  "nameEdit")
        self.executeBtn        = self.findChild(QPushButton, "saveBtn")
        
        # when changing the name of the expression, always validate its contents
        self.exprNameEdit.textChanged.connect(self.validateText)
        
        # cannot yet finish creating
        self.executeBtn.setEnabled(False)
        self.executeBtn.clicked.connect(self.create)
    
    def validateText(self):
        # if any of the characters in the expressions name are not alphanumeric or an "_"
        if any((not (c.isalnum() or c == "_")) for c in self.exprNameEdit.text()):
            # if we havent warned the user before
            if self.showValidationError:
                # now we warn the user their name is invalid
                errorLogging.raiseError("Create Expression Error", "Expression name cannot contain non-alphanumeric characters other than '_'")
                # dont show this again
                self.showValidationError = False
            
            # invalid name, can't create Expression
            self.executeBtn.setEnabled(False)
            # exit
            return
        
        # if the string isn't empty, and since thr string passed the test above, the string is valid
        # therefore, the expression can be created
        self.executeBtn.setEnabled(len(self.exprNameEdit.text()) > 0)
    
    def update(self):
        self.exprNameEdit.clear()
        self.updateComboBox()
        self.updateIDLabel()
    
    def updateIDLabel(self):
        nextID = self.databaseRef.readSQLQuery("SELECT seq FROM sqlite_sequence WHERE name = 'Expressions'")
        if nextID == []:
            self.exprIdLbl.setText("Expression will be saved with ID: 0")
        else:
            self.exprIdLbl.setText(f"Expression will be saved with ID: {int(nextID[0][0])+1}")
    
    def updateComboBox(self):
        self.exprCloneComboBox.clear()
        existingExpressions : list = self.databaseRef.readSQLQuery("SELECT * FROM Expressions")

        self.exprCloneCheckBox.setEnabled(existingExpressions.__len__())
        self.exprCloneComboBox.setEnabled(existingExpressions.__len__())
    
        if existingExpressions:
            for i in range(len(existingExpressions)):
                self.exprCloneComboBox.addItem(f"ID#{existingExpressions[i][0]} - {existingExpressions[i][1]}")

    def create(self):
        if self.exprCloneCheckBox.isChecked():
            # create expression as a clone of an existing expression (same expression data)
            
            # this is the expression we are cloning. The text will be in the format "ID#x - name"
            # and we can use this to extract the ID as an integer
            cloneID = self.exprCloneComboBox.currentText() #   'ID#x - name'
            cloneID = cloneID[3:] #Remove the 'ID#' prefix: "x - name"
            splitPosition = cloneID.find(" -") # Find where the ID and name are split
            cloneID = cloneID[:splitPosition] # remove the name section to just leave the ID: "x"
            cloneID = int(cloneID) # turn the string into an integer
            
            # get the data of the cloned expression for this new expression
            defaultData = self.databaseRef.readSQLQuery(f"SELECT ExpressionData FROM Expressions WHERE expressionID = {cloneID}")
            defaultData = defaultData[0][0] # retrive the data from the tuple and list SQL returns it in (god i hate sqlite)
            
            defaultData = json.loads(defaultData)
            defaultData["ME"][0] = self.exprNameEdit.text()
            defaultData = json.dumps(defaultData)
        
        else:
            # we dont need to validate expression name since this has already been handled.
            
            # NOTE: See the design section for a detailed description of what any of this means!
            defaultData = json.dumps(
                {
                    "ME":[self.exprNameEdit.text(),[]],
                    "TT":[1,"00",1,1,0],
                    "EV":[False,  None,None,None,None, 1,1,1],
                    "EX":[False,  1, None, None, None, 0],
                    "BV":[False,[True,True],False,True,0.5,0.5,0,[],0.00,False]
                }
            ) # this dictionary is the default data for a new blank expression. we use json.dumps to convert it to a formatted string
              # that can be placed in the SQL database without any additional processing needed (saves time and my brain cells)
        
        timeStamp = databaseHandler.generateTimeStamp() # Get the current time to update the lastUpdated field
        self.databaseRef.executeSQLQuery(f"""
        INSERT INTO Expressions (expressionName, expressionData, lastUpdated)
        VALUES (\"{self.exprNameEdit.text()}\", \'{defaultData}\', \"{timeStamp}\")
        """) # commit the new data to the SQL database
        
        self.close() # close the create pop-up window
    
    def closeEvent(self, event):
        self.destroyed.emit()
        super().closeEvent(event)
    
class NewProjectEditorWindow(QtWidgets.QMainWindow):
    def __init__(self, databaseRef : databaseHandler.databaseHandler):
        # set up UI components this inherits from
        super(NewProjectEditorWindow, self).__init__()
        
        # the validation error should only show once, and we haven't shown it yet
        self.showValidationError = True
        # current project id
        self.projectID : int = None
        # are we cloning any expressions into this project
        self.cloneExpressions = []
    
        uic.loadUi("UI/UI_NewProjectEditor.ui", self)   # load the UI elements from the corresponding UI file
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))
        self.setFixedSize(self.size())              # this stops the window from being resized.
        
        # internal reference to the database
        self.databaseRef = databaseRef              
        
        # formatted strings for cloning expressions, linking expressions and creating the new project
        self.cloneExprSQL   = "INSERT INTO Expressions (expressionName, expressionData) SELECT expressionName, expressionData FROM Expressions WHERE expressionID = {ID}"
        self.linkExprSQL    = "INSERT INTO ProjHandler (projectID, expressionID) VALUES (PROJ_ID, EXPR_ID)"
        self.newProjectSQL  = "INSERT INTO Projects (projectName, lastUpdated) VALUES ('PROJ_NAME','DATE')"
        
        # references to the UI components we need to control
        self.outputTable    = self.findChild(QTableWidget, "outputTable")
        self.comboBox       = self.findChild(QComboBox, "exprBox")
        self.projectNameBox = self.findChild(QLineEdit, "projectName")
        self.addExprBtn     = self.findChild(QPushButton, "addBtn")
        self.createBtn      = self.findChild(QPushButton, "createProjBtn")
        self.titeLbl        = self.findChild(QLabel, "titleLabel")
        self.projIDLbl      = self.findChild(QLabel, "projIDLbl")

        # add the signals/slots methods to the create and add buttons
        self.addExprBtn.clicked.connect(self.onExpressionAdded)
        self.createBtn.clicked.connect(self.onCreated)
        
        # stop the user editing the values in the table widget (readonly mode)
        self.outputTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        # refresh the available expressions that can be added to this project
        
        self.addExpressionsToComboBox()
        # stop the create button being enabled since we have not made changes yet
        self.createBtn.setEnabled(False)
        # add the validate method to the string input to ensure the values are ok
        self.projectNameBox.textChanged.connect(self.validateText)
        
    def updateIDLabel(self, id=None):
        if id != None:
            self.projIDLbl.setText(f"Project ID: {id}")
            self.projectID = id
            return
            # no need to validate this ID since it can only be called from a place where the ID must exist (since the ID
            # is taken directly from the SQL db with a continuous connection, the db can't have changed so this ID must exist)
            
        nextID = self.databaseRef.readSQLQuery("SELECT seq FROM sqlite_sequence WHERE name = 'Projects'")
        if nextID == []:
            self.projectID = 0
        else:
            self.projectID = int(nextID[0][0]) + 1 # This gives the current highest ID so we add 1 for the next available
        
        self.projIDLbl.setText(f"Project ID: {self.projectID}")
    
    def setMode(self, mode:int):
        if mode not in [1,2]:
            errorLogging.raiseGenericFatalError(45, additionalDbgInfo=f"MOD: {mode}")
            return
        
        self.mode = mode    # in case other parts of the code depend on the mode used, make it a class-wide variable
        
        if mode == 1:       # create a new project mode
            # If editing an existing project we only need to change the labels to say 'create' instead of 'edit'
            self.createBtn.setText("Create")
            self.titeLbl.setTextFormat(Qt.TextFormat.RichText)
            self.titeLbl.setText("<p align=\"center\"><span style=\" font-size:11pt; font-weight:600;\">New Project Editor</span></p></body></html>")
        
        else:               # edit an existing project mode
            
            # If editing an existing project 2 things happen: change the labels to say 'edit' and not 'create' and get the existing data
            # to check if anything changes
            self.setWindowTitle("Edit Existing Project")
            self.createBtn.setText("Edit")
            self.titeLbl.setTextFormat(Qt.TextFormat.RichText)
            self.titeLbl.setText("<p align=\"center\"><span style=\" font-size:11pt; font-weight:600;\">Project Editor</span></p></body></html>")

            self.existingProjectData = []
            self.existingProjectData.append(self.databaseRef.readSQLQuery(f"SELECT ProjectName FROM Projects WHERE projectID = {self.projectID}")[0][0]) # add the project name (only iece of project data that can change, ID is fixed and lastupdated not managed from here) 
            self.existingProjectData.append(self.databaseRef.readSQLQuery(f"SELECT expressionID FROM ProjHandler WHERE projectID = {self.projectID}")) # add the project expression links

            self.projectNameBox.setText(self.existingProjectData[0])
            formattedProjects = []
            
            # This loop does 2 things: it gets the names of the connected expressions so they can be added to the table
            # and it also fancies up the formatting of the linked expression's IDs because SQL itself formats them badly (I can't control that) 
            for existingExpression in self.existingProjectData[1]:          # iterate over linked expression 
                name = self.databaseRef.readSQLQuery(f"SELECT expressionName from Expressions WHERE expressionID = {existingExpression[0]}") # get the name of the expression
                self.addExpression(existingExpression[0], name[0][0])       # add the expression to the table (existingExpression[0] is the ID and name[0][0] will be the name)
                formattedProjects.append(existingExpression[0])
            
            self.existingProjectData[1] = formattedProjects
            
            self.loadRemainingExpressions()
            self.validateExecuteBox()
                
    def loadRemainingExpressions(self):
        exprToIgnore = [] # Don't add these to the dropdown because they're already in the project
        for exprIn in self.existingProjectData[1]: # add all the previously added projects
            exprToIgnore.append(exprIn)
            
        self.addExpressionsToComboBox(exprToIgnore)
        
    def addExpressionsToComboBox(self, addedAlready=[]):
        # this method adds all the available expressions to the select expressions dropdown box
        # clear the box to ensure we don't have duplicates
        self.comboBox.clear()
        # get all expression names and IDs from the database
        existingExpressions = self.databaseRef.readSQLQuery("SELECT expressionID, expressionName FROM Expressions")
    
        # if there are expressions to evaulate
        if existingExpressions:
            for i in range(len(existingExpressions)):
                # if the ID of this expression hasn't already been added to the current project
                if existingExpressions[i][0] not in addedAlready:
                    # then add this item to the available options
                    self.comboBox.addItem(f"ID#{existingExpressions[i][0]} - {existingExpressions[i][1]}")
    
        # refresh the validation since we may have made changes
        self.validateComboButtons()
        
    def validateComboButtons(self):
        # This method checks if the "add to project" buttons should be enabled, i.e. there are expressions still
        # in the dropdown box that can be selected 
        enabled = (self.comboBox.count() > 0)
        self.addExprBtn.setEnabled(enabled)
    
    def validateExecuteBox(self):
        # this checks that at least 1 expression is linked to the project.
        enabled = (self.outputTable.rowCount() > 0)
        self.createBtn.setEnabled(enabled)

    def onExpressionAdded(self):
        # get the item to add
        exprToAdd = self.comboBox.currentText()
        # it will be in the format ID#x - name so we split at the - 
        deliminator = exprToAdd.find("-")
        try:
            # then we get the 3rd item to the - (the id) and convert it to an integer
            exprID = int(exprToAdd[3:deliminator].strip())
        except TypeError:
            # if we can't do this something has gone very wrong (invalid id) so we 
            # generate a crash report
            errorLogging.raiseGenericFatalError(48)

        # get all the projects this expression is linked to
        partOfProjects = self.databaseRef.readSQLQuery(
            f"SELECT Projects.* FROM Projects INNER JOIN ProjHandler ON Projects.ProjectID = ProjHandler.projectID WHERE ProjHandler.expressionID = {exprID}"
        )
        
        # neatly format this SQL query
        projectUsedString = ""                                              #  initialise new empty output string
        for projectUsed in partOfProjects:                                  # iterate over projects used
            projectUsedString += f"{projectUsed[0]}: {projectUsed[1]}, "    # add the required string e.g. 1: my Project
        projectUsedString = projectUsedString[:-2]                          # remove trailing ', '

        # Remove the expression from the available options to stop the same expression being added twice
        self.comboBox.removeItem(self.comboBox.currentIndex())
        self.validateComboButtons()
        
        # update the table which shows all the Expressions in this Project
        self.outputTable.setRowCount(self.outputTable.rowCount() + 1)
        self.outputTable.setItem(self.outputTable.rowCount()-1 , 0, QTableWidgetItem(str(exprID)))
        self.outputTable.setItem(self.outputTable.rowCount()-1 , 1, QTableWidgetItem(exprToAdd[deliminator+2:]))
        self.outputTable.setItem(self.outputTable.rowCount()-1 , 2, QTableWidgetItem(projectUsedString))
        
        # There should be a button to remove an expression from a project. We generate it, link it to the remove function and then add it to the table
        removeBtn = QPushButton()
        removeBtn.setText("Remove")
        removeBtn.clicked.connect(self.onExpressionRemoved)
        self.outputTable.setCellWidget(self.outputTable.rowCount()-1 ,3, removeBtn)
        
        # check whether the finish box can still be enabled since we have made changes
        self.validateExecuteBox()
    
    def addExpression(self, exprID, exprName):
        partOfProjects = self.databaseRef.readSQLQuery(
            f"SELECT Projects.* FROM Projects INNER JOIN ProjHandler ON Projects.ProjectID = ProjHandler.projectID WHERE ProjHandler.expressionID = {exprID}"
        )
        
        projectUsedString = ""          # initialise new empty output string
        for projectUsed in partOfProjects:                  # iterate over projects used
            projectUsedString += f"{projectUsed[0]}: {projectUsed[1]}, "    # add the required string e.g. 1: my Project
        projectUsedString = projectUsedString[:-2]  # remove trailing ', '
        
        self.outputTable.setRowCount(self.outputTable.rowCount() + 1)
        self.outputTable.setItem(self.outputTable.rowCount()-1 , 0, QTableWidgetItem(str(exprID)))
        self.outputTable.setItem(self.outputTable.rowCount()-1 , 1, QTableWidgetItem(exprName))
        self.outputTable.setItem(self.outputTable.rowCount()-1 , 2, QTableWidgetItem(projectUsedString))
        
        # There should be a button to remove an expression from a project. We generate it, link it to the remove function and then add it to the table
        removeBtn = QPushButton()
        removeBtn.setText("Remove")
        removeBtn.clicked.connect(self.onExpressionRemoved)
        self.outputTable.setCellWidget(self.outputTable.rowCount()-1 ,3, removeBtn)
    
    def onCreated(self):
        if self.mode == 1:
            projectName = self.projectNameBox.text() # ValidateText has already been working to ensure this is valid, no need to check again
            SQLLinkQueries = [self.newProjectSQL.replace("PROJ_NAME",projectName).replace("DATE", databaseHandler.generateTimeStamp())]

            # For each expression used, add a new link in the ProjHandler table to link this new project with the expression
            for i in range(self.outputTable.rowCount()):
                SQLLinkQueries.append(self.linkExprSQL.replace("PROJ_ID", str(self.projectID)).replace("EXPR_ID",self.outputTable.item(i,0).text()))
                
            # with all SQL queries now ready, run them in sequence. This works better becasue it means we cannot make half a project and then
            # crash, either everything works ok or the database is never changed. 
            self.databaseRef.executeMultipleQueries(SQLLinkQueries)
            
            # Check if this Project is empty
            noOfProjects = self.databaseRef.readSQLQuery(f"SELECT ProjectID from ProjHandler WHERE ProjectID = {self.projectID}")
            if not len(noOfProjects): # no Expressions in Project:
                errorLogging.raiseInfoDlg("Warning! (Code 71)", "There are no Expressions linked to this Project!")
            
            # close this window
            self.close()
        
        else:
            SQLtoExecute = []               # list of all queries that need to be executed
            if self.projectNameBox.text() != self.existingProjectData[0]:
                SQLtoExecute.append(f"UPDATE Projects SET ProjectName = '{self.projectNameBox.text()}' WHERE ProjectID = {self.projectID}")
            
            # To find out what needs changing expression wise, convert the lists to sets so order doesn't matter
            # Then, existing - new gives the expressions to remove and new - existing gives those to add
            # Expressions in new expressions and existing expressions haven't been changed
            
            existingSet = set(self.existingProjectData[1]) # set of existing expressions
            newSet = set() # new empty set
            
            # add the IDs of all the expressions that have been put in the project
            for i in range(self.outputTable.rowCount()):
                newSet.add(int(self.outputTable.item(i, 0).text()))
            
            # existing - new gives the Expressions that were in the Project but no longer are
            for element in existingSet.difference(newSet):
                # add the SQL query to remove the link
                SQLtoExecute.append(f"DELETE FROM ProjHandler WHERE ProjectID = {self.projectID} AND ExpressionID = {element}")
            
            # new - existing gives the Expressions that weren't in the Project but now are
            for element in newSet.difference(existingSet):
                # add the SQL query to insert a new Project-Expression link
                SQLtoExecute.append(f"INSERT INTO ProjHandler (ProjectID, ExpressionID) VALUES ({self.projectID}, {element})")
            
            # Execute all of these queries concurrently to ensure that no corruption occurs
            self.databaseRef.executeMultipleQueries(SQLtoExecute)
            # we're done with this window, so close it
            
            noOfProjects = self.databaseRef.readSQLQuery(f"SELECT ProjectID from ProjHandler WHERE ProjectID = {self.projectID}")
            if not len(noOfProjects): # no Expressions in Project:
                errorLogging.raiseInfoDlg("Warning! (Code 71)", "There are no Expressions linked to this Project!")
            
            self.close()
                                
    def onExpressionRemoved(self):
        # the expression removed will be the current row of the output table since when the user clicks the remove button it will cause that row to be active
        # we then add this back to the dropdown box so it can be added back (stops it being removed from the options permenantly)
        exprText = f"ID#{self.outputTable.item(self.outputTable.currentRow(), 0).text()} - {self.outputTable.item(self.outputTable.currentRow(), 1).text()}"
        self.comboBox.addItem(exprText)
        # recheck the validations of the combo box (since now there is an item they may be able to be active again)
        self.validateComboButtons()
        # remove the current row from the output table to mark this Expression as removed
        self.outputTable.removeRow(self.outputTable.currentRow())
    
    def saveExpression(self, expressionID:int, expressionData:dict):
        self.databaseRef.executeSQLQuery(f""""
        UPDATE Expressions
        SET expressionData = \'{json.dumps(expressionData)}\', lastUpdated = {datetime.datetime().now()}
        WHERE expressionID = {expressionID}
        """
        )
    
    def validateText(self):
        # if any of the characters are not alphanumeric or a '_'
        if any((not (c.isalnum() or c == "_")) for c in self.projectNameBox.text()):
            # if we have not shown the validation error before
            if self.showValidationError:
                # display the validation error to the user
                errorLogging.raiseError("Create Project Error", "Project name cannot contain non-alphanumeric characters other than '_'")
                # don't need to show this again
                self.showValidationError = False
            # stop the user from saving with this error
            self.createBtn.setEnabled(False)
            return
        # also dont allow the user to create / finish editing a project if there is no text in the box
        self.createBtn.setEnabled(len(self.projectNameBox.text()) > 0)
    
    def closeEvent(self, event):
        self.destroyed.emit()
        super().closeEvent(event)

# This class is responsible for the system tray icon feature
class ProjectSysTrayIcon(QSystemTrayIcon):
    # main window is the reference to the project manager, icon is the image to display
    # and winParent is used to keep Qt happy with me
    def __init__(self, mainWindow:QMainWindow, icon:QIcon, winParent=None):
        # intiialise components this depends on
        super().__init__(icon, winParent)
        # reference to proj manager
        self.mainWindow = mainWindow
        
        # create a new tray menu
        systemTray = QMenu()
        # on hover message
        self.setToolTip("Boolean Logic Calculator")
    
        # option to open the project manager
        open1 = QAction("Open Project Manager")
        open1.triggered.connect(partial(reactivateMainWindow, mainWindow)) 
        
        # option to open the previous expression
        open2 = QAction("Open Previous Expression") 
        open2.triggered.connect(window.openPrevious)
        
        # option to quit the system
        quit = QAction("Quit") 
        quit.triggered.connect(app.quit) 

        # add these options to the tray
        systemTray.addActions([open1, open2, quit])
        self.setContextMenu(systemTray)
        
        # if clicked, reopen the project manager
        self.activated.connect(partial(reactivateMainWindow, mainWindow))

class SingleInstanceApp(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shared_memory = QSharedMemory("BooleanBacus")  # Unique identifier
        self.server = None

        if self.shared_memory.attach():
            # Another instance is running; send a signal to bring it to the foreground
            self.sendReactivateSignal()
            sys.exit(0)
        else:
            # Create the shared memory segment
            self.shared_memory.create(1)
            # Set up a local server to listen for reactivation signals
            self.server = QLocalServer()
            self.server.newConnection.connect(self.handleReactivateSignal)
            self.server.listen("BooleanBacus")

    def sendReactivateSignal(self):
        """Send a signal to the running instance."""
        socket = QLocalSocket()
        socket.connectToServer("BooleanBacus")
        if socket.waitForConnected(1000):
            socket.write(b"Reactivate")
            socket.flush()
            socket.disconnectFromServer()

    def handleReactivateSignal(self):
        try:
            # bring the main window to the front
            if self.window:
                reactivateMainWindow(self.window)
        except Exception as e:
            # something went wrong
            errorLogging.raiseError(72, f"Couldn't reinstate main window, non-fatal error: {e}")

    def setMainWindow(self, window):
        # Set the main window
        self.window = window

    def cleanup(self):
        # clean up and then exit
        if self.shared_memory.isAttached():
            self.shared_memory.detach()
        if self.server:
            self.server.close()
        
if __name__ == "__main__":                      
    # This section should only run if this is the entrypoint to the system
    # E.g. if this code is imported to another file, this shouldn't run
    # This ensures the code must be run with this as the main entrypoint,
    # which is better for the UI handling and system as a whole
    app = SingleInstanceApp(sys.argv)
    
    
    # formatting
    #  =========================== Dark Blue Pallete ===================== #
    app.setStyleSheet("""
    QMainWindow, QDialog {
        background-color: #2b3c6b;
    }
    QMenuBar, QTableWidget {
        background-color: #7b92d1;
    }
    QPushButton {
        background-color: #0078D7;
        color: white;
        border-radius: 5px;
        padding: 5px 10px;
    }
    QPushButton:hover {
        background-color: #005A9E;
    }
    QLabel, QCheckBox {
        color: #b5b5b5;
    }
    
    QScrollBar:vertical, QScrollBar:horizontal {
        background: #f0f0f0;
        width: 12px;
        margin: 2px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
        background: #0078D7;
        min-height: 20px;
        border-radius: 6px;
    }
    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
        background: #005A9E; 
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        background: none; 
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical, QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none; 
    }
    """)

    # veryify the system's UI and key items are unchanged
    # things to hash:
    # 1. SOP dll file -> correct hash is: F1819DD02358527AB3B53E70235A81F7BBE4636BA5840EDDAC304D36FF553204
    
    dllHash = hashlib.new("SHA256")
    
    if not os.path.exists("SOP.dll"):
        errorLogging.raiseGenericFatalError(35)
    
    with open("SOP.dll", 'rb') as f:
        while chunk := f.read(8192):  # Read the file in chunks of 8192 bytes
            dllHash.update(chunk)     # add this data to the hash
    
    if dllHash.hexdigest().upper() != SOP_DLL_HASH and not DEV:
        errorLogging.raiseGenericFatalError(68, ".dll libraries failed integrity check. Please contact the developers", additionalDbgInfo=f"VERSION: {VERSION}\n REFHASH: F1819DD02358527AB3B53E70235A81F7BBE4636BA5840EDDAC304D36FF553204")
    elif DEV:
        # if in DEV mode, give the resultant calculations
        print(f"DLLRef:  {SOP_DLL_HASH}\nDLLCalc: {dllHash.hexdigest().upper()}")
        
    # 2. UI folder -> correct hash is: B8DF938FEC08E5CC868A75C5A7BAC8F86495CB8F37902123D71004F58F21E106
    UIHash = hashlib.new("SHA256")
    for path in os.listdir(os.getcwd() + "\\UI"):
        if path.find(".png"):                   # binary photo file
            with open(os.getcwd()+"\\UI\\"+path, "rb") as f:
                while chunk := f.read(8192):  # Read the file in chunks of 8192 bytes
                    UIHash.update(chunk)
        else:
            with open(os.getcwd()+"\\UI\\"+path, "r") as f: # text UI file
                while chunk := f.read(8192):  # Read the file in chunks of 8192 bytes
                    UIHash.update(chunk)        # add to the hash    
    
    # on the right is the correct hash, the left is what we computed
    if UIHash.hexdigest().upper() != UI_FOLDER_HASH and not DEV:
        errorLogging.raiseInfoDlg("Integrity Check Failed", "UI failed integrity check. Please contact the developers.")
        errorLogging.raiseGenericFatalError(69, additionalDbgInfo=f"VERSION: {VERSION}\n REFHASH: 8295FC03C4CC33E1DC1A6436C0D225D1CC0D9FC78A300998F3F04E181B47B946")
    elif DEV:
        # if in DEV mode, give the resultant calculations
        print(f"UIRef:   {UI_FOLDER_HASH}\nUICalc:  {UIHash.hexdigest().upper()}")
    
    # begin running
    handler = databaseHandler.databaseHandler()
    if not os.path.exists("main.db"):
        errorLogging.raiseInfoDlg("Database Info", "The main database file is missing - a new blank one has been generated")
        handler.connectToMain()
        handler.createDatabase()
    else:
        handler.connectToMain()

    app.setQuitOnLastWindowClosed(False) 

    window = MainProjectEditorWindow(handler)
    
    app.setMainWindow(window)
    
    # create a system tray icon and set it to visible
    trayIcon = QSystemTrayIcon(QIcon("UI/iconDarkTheme.ico"), app)  # Set a valid path to your icon
    trayMenu = QMenu()
    
    open1    = QAction("Open Project Manager")
    open2    = QAction("Open Previous Expression")
    quit1    = QAction("Shutdown System")
    
    open1.triggered.connect(partial(reactivateMainWindow, window))
    open2.triggered.connect(window.openPrevious)
    quit1.triggered.connect(app.quit)
    
    trayMenu.addActions([open1, open2, quit1]) 
    trayIcon.setContextMenu(trayMenu)
    trayIcon.activated.connect(partial(reactivateMainWindow,window))   
    trayIcon.show()
    
    window.show()
    app.aboutToQuit.connect(app.cleanup)
    sys.exit(app.exec())