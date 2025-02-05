from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
import os
import errorLogging

class ProgrammingLanguageExport:
    def __init__(self, 
            languageID:int, languageName:str,                                               # id and name
            functionDef:str, functionVariable:str, functionEndCode:str,                     # packaging code
            andCode:str, trailingAndCode:str, orCode:str, trailingOrCode:str, notCode:str,  # logical syntax
            bracketCode:bool, popLastComma:bool, remSingleLenBracket:bool=True              # settings
        ):
        
        self.languageID = languageID
        self.languageName = languageName
        self.funcDef = functionDef
        self.funcVar = functionVariable
        self._AND2 = andCode
        self._AND1 = trailingAndCode
        self._OR2 = orCode
        self._OR1 = trailingOrCode
        self._NOT = notCode
        self.funcEnd = functionEndCode
        self.addBrackets = bracketCode
        self.popComment = popLastComma
        self.removeSingle = remSingleLenBracket
    
    # NOT A
    def NOT(self, variable : str) -> str:
        return self._NOT.replace("{V1}", variable)
    
    # A AND B
    def AND(self, v1 : str, v2: str) -> str:
        tmp = self._AND2.replace("{V1}", v1)
        tmp = tmp.replace("{V2}", v2)
        return tmp
    
    # __ AND B (used for ANDing more than 2 items, e.g. a <and b and c>)
    def ANDTrail(self, v1 : str) -> str:
        return self._AND1.replace("{V1}", v1)
    
    # A OR B
    def OR(self, v1 : str, v2: str) -> str:
        tmp = self._OR2.replace("{V1}", v1)
        tmp = tmp.replace("{V2}", v2)
        return tmp
    
    # __ OR B (used for ANDing more than 2 items, e.g. a <or b or c>)
    def ORTrail(self, v1 : str) -> str:
        return self._OR1.replace("{V1}", v1)
    
    # NOT this token if applicable 
    def negate(self, token : str, shouldNegate : bool) -> str:
        if shouldNegate:
            return self.NOT(token)
        return token
            
    # turn logical expression into code
    def computeExpression(self, exprIn : str):
        exprIn = exprIn.replace(" ", "")    # remove whitespace 
        exprList = []
        
        # single term, simplify down
        if "+" not in exprIn:
            exprList = [exprIn] 
        else:
            # do this term by term
            exprList = exprIn.split("+")
        
        termsOut = []
        
        for term in exprList:
            varsFound = 0                   # no of vairables in ter,
            tmpTermOut = ""                 # current term 
            isNegated = False               # makes dealing with # much easier
            exprOutput = ""                 # entire expression
            
            # only 1 variable and a not e.g. NOT A 
            if "#" in term and len(term.replace("#","")) == 1: # just need to negate this term and then add it to the list
                termsOut.append(self.NOT(term.replace("#","")))       
                # skip to next term   
                continue
        
            # only 1 variable and nothing else e.g. A
            elif len(term) == 1:
                termsOut.append(term)
                # skip to next term
                continue
            
            for i in range(len(term)):
                isNegated = False               
                
                if term[i] == "#":          # don't need to deal with this character directly, so skip it
                    continue
                else:
                    varsFound += 1          # otherwise, increment the number of variables found
                    
                if i + 1 != len(term):      # to validate input, this checks if there is another char before the end of the term 
                    if term[i+1] == "#":
                        isNegated = True   # if the next char is #, this char is inverted to add a not to the output
                        
                if i > 0:
                    # 2nd index and onwards to the 2nd to last (stops index errors)
                    prevVar = ""            
                    # previous index was a not (this term should be negated)
                    if term[i-1] == "#":
                        prevVar = self.NOT(term[i-2])
                        
                    else:
                        # this is the previous variable
                        prevVar = term[i-1]
                     
                    # only one and
                    if varsFound <= 2:
                        tmpTermOut += self.AND(prevVar, self.negate(term[i], isNegated))
                    else:
                        # trail the ands for more than 2 variables in a term
                        tmpTermOut += self.ANDTrail(self.negate(term[i], isNegated))
            
            # add to the list of terms
            termsOut.append(tmpTermOut)
                    
        # This if statment is used if we have an expression like Q=A. Here, there is only 1 term so there's no point
        # trying to add stuff to the front or the end since there won't be anything.
        if len(termsOut) == 1:
            return termsOut[0]
        
        # For every term in the expression we have...
        for count, term in enumerate(termsOut):
            # ignore the first term since we don't need to process it
            if count == 0:
                continue
            
            if count == 1:
                # need to add brackets for operator precedence
                if self.addBrackets:
                    t1 = t2 = ""
                    if (len(termsOut[count-1]) == 1 and self.removeSingle) or not self.addBrackets:
                        t1 = termsOut[count-1]
                    else:
                        t1 = f"({termsOut[count-1]})"
                    
                    if (len(term) == 1 and self.removeSingle) or not self.addBrackets:
                        t2 = term
                    else:
                        t2 = f"({term})"
                    
                    exprOutput += self.OR(t1, t2)
                else:
                    exprOutput += self.OR(termsOut[count-1], term)
            else:
                # add the OR operator in trailing mode
                if self.addBrackets:
                    if not self.removeSingle or len(term) > 1:
                        exprOutput += self.ORTrail(f"({term})")
                    else:
                        exprOutput += self.ORTrail(term)
                else:
                    # no brackets needed
                    exprOutput += self.ORTrail(term)
        
        return exprOutput

    def prettyPrintFunction(self, functionName, booleanLogic):
        ALPHABET = "QWERTYUIOPASDFGHJKLZXCVBNM"
        # varaibles we've alrady used
        variablesUsed = ""
        # pretty printed output
        ppOutput = ""
        
        # get the expression we are working with 
        programCode = self.computeExpression(booleanLogic)
        
        # iterate over the logic
        for char in booleanLogic:
            if char in ALPHABET:
                # this is a variable
                # add to variables used the formatted variable
                # remove this variable to prevent duplicates
                variablesUsed += self.funcVar.replace("{V1}", char) # add the variable definition for this character
                ALPHABET = ALPHABET.replace(char,"")               # stop duplicate entries
        
        # no whitepsace / trailing comments allowed            
        variablesUsed = variablesUsed.rstrip()            
        if self.popComment:
            variablesUsed = variablesUsed[:-1]

        # add the function defintiion formatted code and the function code and the function end code to the string
        ppOutput += self.funcDef.replace("{NAME}", functionName).replace("{VARS}", variablesUsed) + "\n"
        ppOutput += f"\t{self.funcEnd.replace("{RESULT}", programCode).replace("{NAME}", functionName)}"
        # finish and return
        return ppOutput
    
class EXWindow(QtWidgets.QMainWindow):
    def __init__(self):
        # load the UI
        super(EXWindow, self).__init__()
        uic.loadUi("UI/UI_ExprExporter.ui", self)
        self.setFixedSize(self.size())              # this stops the window from being resized.
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))
        
        # get UI children
        self.titleLabel     = self.findChild(QLabel, "titleLbl")
        self.langComboBox   = self.findChild(QComboBox, "langSelectBox")
        self.funcNameEdit   = self.findChild(QLineEdit, "funcNameEdit")
        self.fileNameEdit   = self.findChild(QLineEdit, "fileNameEdit")
        self.fileExtLbl     = self.findChild(QLabel, "fileExtLbl")
        self.saveToLbl      = self.findChild(QLabel, "saveToLbl")
        self.selectDirBtn   = self.findChild(QPushButton, "selectDirBtn")
        self.goBtn          = self.findChild(QCommandLinkButton, "goBtn")
        self.actionAutoClose = self.findChild(QAction, "actionAutoClose")
        
        # setup title menu actions 
        self.findChild(QAction, "actionExport"    ).triggered.connect(self.executeExport)
        self.findChild(QAction, "actionSelectDir" ).triggered.connect(self.selectDirectory)
        self.findChild(QAction, "actionClearAll"  ).triggered.connect(self.clearAllData)
        self.findChild(QAction, "actionChangeMode").triggered.connect(self.changeMode)
        self.findChild(QAction, "actionSetDefaultDir").triggered.connect(self.setDefaultDirectory)
        self.findChild(QAction, "actionSetDefault").triggered.connect(self.setDefaultLang)
        self.findChild(QAction, "actionSetDefaultMode").triggered.connect(self.setDefaultType)
        self.findChild(QAction, "actionClose").triggered.connect(self.close)
        
        # link to the direcotry pop-up
        self.selectDirBtn.clicked.connect(self.selectDirectory)
        # update the file extension when the user picks another language
        self.langComboBox.currentIndexChanged.connect(self.updateExtensionLabel)
        # execute when execute btn pressed...
        self.goBtn.clicked.connect(self.executeExport)
        
        # default save directory
        self.defaultDirectory = ""
        # dont assign these, wait for save data to do so for us
        self.defaultExportType = "Prog"
        self.defaultLanguage = 0
        # for saving purposes
        self.isGenerated = False
        
        # For an explanation of the constructor syntax see the class definition.
        self.languageDict = {
            "Prog":[ # These are the standard programming languages
                ProgrammingLanguageExport(                                  # Python3
                    0, "Python", 
                    "def {NAME}({VARS}) -> bool: ",
                    "{V1} : bool, ",
                    "return ({RESULT})",
                    "{V1} and {V2}",
                    " and {V1}",
                    "{V1} or {V2}",
                    " or {V1}",
                    "(not {V1})",
                    bracketCode = True,
                    popLastComma = True
                ),
                ProgrammingLanguageExport(                                  # C++
                    1, "C++",
                    "bool {NAME}({VARS}){",
                    "bool {V1}, ",
                    "return ({RESULT});\n}",
                    "{V1} && {V2}",
                    " && {V1}",
                    "{V1} || {V2}",
                    " || {V1}",
                    "(!{V1})",
                    bracketCode = True,
                    popLastComma = True
                ),
                ProgrammingLanguageExport(                                  # Javascript
                    2, "Javascript",
                    "function {NAME}({VARS}){",
                    "{V1}, ",
                    "return ({RESULT});\n}",
                    "{V1} && {V2}",
                    " && {V1}",
                    "{V1} || {V2}",
                    " || {V1}",
                    "(!{V1})",
                    bracketCode = True,
                    popLastComma = True
                )
            ],
            "HDL":[
                ProgrammingLanguageExport(                                  # VHDL export option
                    3, "VHDL",
                    "library IEEE;\nuse IEEE.std_logic_1164.all;\n\nentity {NAME} is\n\tport (\n{VARS}\n\t\tQ : out std_logic;\n\t);\nend {NAME};",
                    "\t\t{V1} : in std_logic;\n",
                    "architecture logic of {NAME} is begin\n\tQ <= {RESULT};\nend logic;",
                    "{V1} AND {V2}",
                    " AND {V1}",
                    "{V1} OR {V2}",
                    " OR {V1}",
                    "(NOT {V1})",
                    bracketCode=True,
                    popLastComma=False
                ),
                ProgrammingLanguageExport(                                  # Verilog export option
                    4, "Verilog",
                    "module {NAME} (input {VARS} output Q);",
                    "{V1},",
                    "assign Q = {RESULT};\nendmodule",
                    "{V1} & {V2}",
                    " & {V1}",
                    "{V1} | {V2}",
                    " | {V1}",
                    " ~{V1}",
                    bracketCode=True,
                    popLastComma=False
                )
            ]
        }
        
        # This dictionary tells the UI which language associates with each file type
        self.fileExtensionDict = {
            "Python"    :   ".py",
            "C++"       :   ".cpp",
            "Javascript":   ".js",
            "VHDL"      :   ".vhd",
            "Verilog"   :   ".v"
        }
        
        self.saveToDir = ""  # Where to save the file
        self.bannedFileNames = ["CON","PRN","AUX","NUL"]        # some file names are banned in windows
        for i in range(10):                                     # because the OS reserves them for internal
            self.bannedFileNames.append(f"LPT{i}")              # use. We need to check that none of these
            self.bannedFileNames.append(f"COM{i}")              # are entered by the user.
    
    def changeMode(self):
        # self.languageUsed is either "Prog" or "HDL" depending on the current mode
        newLanguage = "Prog" if (self.languageUsed == "HDL") else "HDL" 
        self.setLanguageMenu(newLanguage)
        
    def clearAllData(self):
        # clear all these input fields to make eveyrhting neat and tidy
        self.funcNameEdit.clear()
        self.fileNameEdit.clear()
        self.langComboBox.setCurrentIndex(self.defaultLanguage)
    
    def registerExpr(self, expr: str) -> None:
        self.exprToExport = expr
        
    def setLanguageMenu(self, language : str) -> None:
        # change between HDl and program modes
        if language not in ["Prog","HDL"]:
            errorLogging.raiseGenericFatalError(46, additionalDbgInfo=f"EX_MDE: {language}")

        else:
            self.languageUsed = language
            # use HTMl text format to make it look nicer
            styledTextTemplate = "<p><span style=\" font-size:11pt; font-weight:600;\">{LANG}</span></p>"
            _language = "Programming Language Exporter" if language == "Prog" else "HDL Exporter"
            self.titleLabel.setTextFormat(Qt.TextFormat.RichText)
            self.titleLabel.setText(styledTextTemplate.replace("{LANG}",_language))
        
        # update options for the new mode
        self.langComboBox.clear()
        for item in self.languageDict[language]:
            # add each available export option
            self.langComboBox.addItem(item.languageName)
        
    # e.g. when user clicks python change to .py
    def updateExtensionLabel(self):
        self.fileExtLbl.setText(self.fileExtensionDict.get(self.langComboBox.currentText(),""))

    # default / current directory save location
    def updateDirectoryLabel(self, dir):
        self.saveToDir = dir
        self.saveToLbl.setText(self.saveToDir)

    def selectDirectory(self):
        # use a pyqt5 popup dialog to get a directory to save in
        directorySelected = QFileDialog.getExistingDirectory(self, "Select a directory to save in...")
        if directorySelected:
            self.updateDirectoryLabel(directorySelected)

    def setDefaultDirectory(self):
        # set the defualt export directory
        self.defaultDirectory = self.saveToDir 
        self.updateDirectoryLabel(self.defaultDirectory)

    def setDefaultType(self):
        # set default export type
        self.defaultExportType = self.languageUsed
        
    def setDefaultLang(self, languageID:int=-1):
        # if optional argument provided
        if languageID >= 0:
            self.languageUsed = languageID
        # otherwise use the current language
        else:
            self.defaultLanguage = self.langComboBox.currentIndex()

    def executeExport(self):
        # function name, file name and export language chosen
        functionName = self.funcNameEdit.text()
        fileName = self.fileNameEdit.text()
        exportLang = self.langComboBox.currentIndex()
        # use the export language chosen to retrive the ProgrammingLanguageExport class associated with this language
        exportClassRef : ProgrammingLanguageExport = self.languageDict[self.languageUsed][exportLang]
        
        # validate the user's chosen names
        if not functionName:
            errorLogging.raiseError("Export Error! (Code 62)", "You did not provide a function / assembly name", QDialogButtonBox.Ok)
            return
        
        if any(not c.isalnum() for c in functionName):
            errorLogging.raiseError("Export Error! (Code 63)", "No special characters are allowed in the function/assembly name", QDialogButtonBox.Ok)
            return
        
        if functionName[0].isdigit():
            errorLogging.raiseError("Export Error! (Code 64)", "The function/assembly name cannot begin with a digit", QDialogButtonBox.Ok)
            return
        
        if not self.saveToDir:
            errorLogging.raiseError("Export Error! (Code 65)", "No output directory selected", QDialogButtonBox.Ok)
            return
        
        if len(set(list(fileName)).intersection(set(list("\\/:*?\"<>|")))) or fileName.upper() in self.bannedFileNames:
            # filename contains banned characters
            errorLogging.raiseError("Export Error! (Code 66)", "This filename is not allowed", QDialogButtonBox.Ok)
            return
        
        # empty file name
        if not len(fileName):
            errorLogging.raiseError("Export Error! (Code 67)", "Please provide a file name", QDialogButtonBox.Ok)
            return
        
        # to get here the filename must be valid
        outputPath = os.path.join(self.saveToDir, fileName) + self.fileExtLbl.text()
        
        # open the output file and write the generated function to it
        with open(outputPath, "w") as outputWriter:
            outputWriter.write(exportClassRef.prettyPrintFunction(functionName, self.exprToExport))
        
        # we have now finished this section
        self.registerGenerated(True)
        
        # if the user wants to close the window once completed
        if self.actionAutoClose.isChecked():
            self.hide()
    
    def registerGenerated(self, isGenerated):
        # used by the save/load system to move save data into this class
        self.isGenerated = isGenerated
    
    def getSaveData(self) -> str:
        # all the data to be put in the SQL database
        return [self.isGenerated, self.actionAutoClose.isChecked(), self.defaultExportType, self.defaultLanguage, self.defaultDirectory]

