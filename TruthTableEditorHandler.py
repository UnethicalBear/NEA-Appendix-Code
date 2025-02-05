from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
import sys, csv, errorLogging, os

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# pop up to load a CSV file 
class CSVImportDialog(QDialog):
    def __init__(self):
        # start the UI components this inherits from
        super().__init__()

        # set the window title and icon as required
        self.setWindowTitle("Truth Table CSV Loader")
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))

        # This button option can be Yes or No
        QBtn = QDialogButtonBox.Yes | QDialogButtonBox.No

        # This is a box that contains a button, which keeps it in line
        self.buttonBox = QDialogButtonBox(QBtn)
        # self.accept and self.reject allow us to see which button (Yes or No) was clicked
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Create a new layout to stop things moving around (fix their UI positions)
        self.layout = QVBoxLayout()
        message = QLabel("Is the top row of the CSV file variable names?")

        # add all the UI elements of this pop-up to the window layout
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
    
class TTWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(TTWindow, self).__init__()
        
        uic.loadUi("UI/UI_TruthTableEditor.ui", self)
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))
        
        self.noVarsSpinBox   = self.findChild(QSpinBox, "noSpinBox")          # reference to the master spin box
        self.inputScrollArea = self.findChild(QScrollArea, "scrollArea")    # reference to the scroll area
        self.generateSOPBtn  = self.findChild(QCommandLinkButton, "generateBtn") # button to submit data
        self.importFileBtn   = self.findChild(QCommandLinkButton, "importBtn")  # button to import file
        
        self.importFileBtn.clicked.connect(self.loadInputFile)              # button to import file
        
        # Menu Actions / Shortcuts
        
        self.actClearTable = self.findChild(QAction, "actionClear_table")
        self.actImportFile = self.findChild(QAction, "actionImport_file")
        self.actGenExpr    = self.findChild(QAction, "actionGenerate_expression")
        self.actSaveExpr   = self.findChild(QAction, "actionSave_Expression_File")
        self.actClose      = self.findChild(QAction, "actionClose")
        self.actCloseAll   = self.findChild(QAction, "actionClose_completely")
        
        # Options
        
        self.actAutoCloseWin    = self.findChild(QAction, "actionAuto_close_this_window")
        self.actAutoOpenExpr    = self.findChild(QAction, "actionAuto_open_expr_window")
        
        self.actClearTable.triggered.connect(self.createInputBoxes)
        self.actImportFile.triggered.connect(self.loadInputFile)
        
        self.noVarsSpinBox.valueChanged.connect(self.createInputBoxes)      # when the spin box value changes, call this function
        self.setFixedSize(self.size())                                      # this stops the window from being resized.
        
        self.variableInputGuideLabel = QLabel(self)                         
        self.inputScrollArea.setWidget(self.variableInputGuideLabel)
        self.inputScrollArea.setMinimumWidth(200)
        
        self.scrollContainerWidget   = QWidget()
        self.gridLayout              = QGridLayout(self.scrollContainerWidget)
        self.inputScrollArea.setWidget(self.scrollContainerWidget)
        
        self.outputSpinBoxes = []
        self.createInputBoxes()
        
        self.isDone = False
    
    def stageFileName(self, fN:str, topRowHeader:bool):
        # this is a project that has been saved loading previous data back in.
        # we stage the filename into a variable and wait for it to be called
        self.stagedFile = [fN, topRowHeader]
        
    def loadInputFile(self):
        # Create a new set of options
        options = QFileDialog.Options()
        # Funky windows thing we put here because otherwise it breaks
        options |= QFileDialog.DontUseNativeDialog
        
        # downloads folder:
        downloadsFolder = os.path.expanduser("~") + "\\Downloads"
        
        #                                               window title prompt           # default folder       types of files allowed      options we defined earlier
        fileName, _ = QFileDialog.getOpenFileName(self,"Select Truth Table import...", downloadsFolder,"CSV Files (*.csv);;All Files (*)", options=options)
        # the first returned variable is the file name and the second isn't needed
        
        if fileName: # check if we got a file name (i.e. the user didn't click the x button)
            self.loadCSVIntoGrid(fileName) # load the file name
            
    def loadCSVIntoGrid(self, fileName=None):
        topRowIsHeaders = False # the top row of the CSV can be the variable labels
        
        # if we already have the filename, we just need to check the format of the file
        if fileName:            
            dlg = CSVImportDialog()
            topRowIsHeaders = dlg.exec()  # check if the top row of the CSV is data using 
            # ... the pop up window defined earlier
        else:
            # if file name is not given by user, we have been sent the data by another section of the program
            # format data as required
            fileName = self.stagedFile[0]
            topRowIsHeaders = self.stagedFile[1]
        
        try:
            with open(fileName, newline = '') as csvFile: 
                csvReader = csv.reader(csvFile)
                for count, row in enumerate(csvReader):
                    if topRowIsHeaders and not count:
                        # ignore top row of the csv if it is a label row
                        continue
                    
                    # if we are in the first row of actual data
                    if (count == 0 and not topRowIsHeaders) or (count == 1 and topRowIsHeaders):
                        # the length of the row includes the output variable so subtract 1
                        noVariables = len(row) - 1
                        # update spinbox
                        self.noVarsSpinBox.setValue(noVariables)
                        
                    # this row contains elements other than 1 or 0
                    if row.count("0") + row.count("1") != len(row):
                        errorLogging.raiseError("Error! (Code 37)", "Truth Table Editor (CSV Loading): Corrupted data!\nCharacters in the CSV are not 0 or 1, or the header row was incorrectly disabled.")
                        return
                    
                    try:
                        # Try to set the output box at the current index to the current value
                        self.outputSpinBoxes[count - topRowIsHeaders].setValue(int(row[-1]))
                    except IndexError:
                        # if this doesn't work the CSV is missing data
                        errorLogging.raiseError("Error! (Code 38)", f"Truth Table Editor (CSV Loading): Row length is not correct - too much or too little data on line {count+1}.")
                        return
        except Exception as e:
            errorLogging.raiseError("Error! (Code 73)", f"Couldn't open this file. Please try again later.\nException: {e}")
            
    def clearMainGrid(self):
        while self.gridLayout.count():
            nextItem = self.gridLayout.takeAt(0)
            toDelete = nextItem.widget()
            
            if toDelete is not None:
                toDelete.deleteLater()
        
        return True
    
    def submitData(self):
        item : QSpinBox = None # defining this as a QSpinBox means we get IDE features even tho python's dynamic, just a little workaround
        
        data = "" # output string to be sent to SOP generator
        cols = self.noVarsSpinBox.value() # number of variables input 
        
        for count, item in enumerate(self.outputSpinBoxes):
            data += (f"{bin(count)[2:].rjust(cols,"0")}{item.value()}")
            # for every item in the 2D array:
            #   get the binary value of the inputs and pad it to the number of columns
            #   e.g. 0 => 0000 if there were 4 inputs
            #   add the output box's value to the end
            #   add this to the data 
             
            
        # this section is done (used for save data)
        self.isDone = True
        # return the output string and the number of variables + 1 (to account for the output data)
        return [data, cols + 1]     
            
    def createInputBoxes(self):
        # number of variables being entered
        cols = self.noVarsSpinBox.value() 
        
        # Create a label with the variable names
        inputVarChars = QLabel("    ".join(ALPHABET[:cols]), self)
        #clear input boxes
        self.clearMainGrid()
        #create a new list of output boxes - .copy() ensures that we dont have memory issues with the UI.
        self.outputSpinBoxes = [].copy()
        
        # add the grid of boxes to the UI handler
        self.gridLayout.addWidget(inputVarChars,0, 0)
        
        # cols no of variables implies 2^cols possible input combinations, e.g. 3 variables -> 8 possible input combos
        for i in range(2**cols):
            nextInputLine = ("    ".join(list(bin(i)[2:].rjust(cols,"0"))))
            # what does this line do?
            #   bin(i) converts the number to a binary string
            #   [2:] removes the 0b prefix that shows this number is binary - we know it is so we don't need it
            #   .rjust(cols,"0") pads the string so that it is always the number of cols long, e.g. with 3 input variables, 1 is converted to 001
            #   list(...) converts the whole thing into a list, e.g. 101 would become [1,0,1]
            #   " ".join() turns the list into a string with each element seperated by a space, e.g. [1,0,1] becomes "1 0 1"
            #   this is then added as a line to the box input.
            nextLabel = QLabel(self)
            nextLabel.setText(nextInputLine)
            nextLabel.show()
            
            # add each widget to the grid
            self.gridLayout.addWidget(nextLabel, i+1, 0)
            
            # create a new output box
            nextBox = QSpinBox(self)
            # make it so that only 0 and 1 (binary) is supported.
            nextBox.setRange(0,1)
            # make sure the input box is shown to the user
            nextBox.show()
            # add the next box to the main UI to keep it inline
            self.gridLayout.addWidget(nextBox, i+1, 1)
            
            nextBox.setStyleSheet("""
            QSpinBox {
                background-color: white;
            }
            """)
            
            # add the next output box to the list of boxes            
            self.outputSpinBoxes.append(nextBox)
            
    def getSaveData(self) -> str:
        outputSpinBoxText = "".join([str(box.value()) for box in self.outputSpinBoxes])
        return [self.noVarsSpinBox.value(), outputSpinBoxText, self.actAutoCloseWin.isChecked(), self.actAutoOpenExpr.isChecked(), self.isDone]


if __name__ == '__main__':
    _truthTableEditorApp = QtWidgets.QApplication(sys.argv)
    _truthTableEditorWin = TTWindow()
    _truthTableEditorWin.show()
    sys.exit(_truthTableEditorApp.exec_())