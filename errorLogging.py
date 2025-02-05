import random, time
import sys, shutil, os
import zipfile
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon

def writeErrorLog(errorCode, includeDB = True, additionalInfo=None):
    additionalCode = None
    try:
        errorType, errorObject, errorTraceBack = sys.exc_info()
        fname = os.path.split(errorTraceBack.tb_frame.f_code.co_filename)[1]
        errorLine = errorTraceBack.tb_lineno
    except:
        errorType = errorObject = errorLine = fname = None
        additionalCode = "COULD NOT GENERATE SYS.EXC_INFO -> LIMITED TB AVAILABLE (USE DB!)"
        
    with open("tmp_dbg.txt","w") as f:
        f.write(f"EC: {errorCode}\n")
        if additionalCode:
            f.write(additionalCode+"\n")
        f.write(f"ET: {errorType}\n")
        f.write(f"EL: {errorLine}\n")
        f.write(f"EO: {errorObject}\n")
        f.write(f"SF: {fname}\n")
        if additionalInfo:
            f.write(additionalInfo)
        
    fileNames = ["tmp_dbg.txt"]
    if includeDB:
        fileNames.append("main.db")
    
    randomSuffix = str(random.randint(0, 99999)).rjust(5,"0")
    with zipfile.ZipFile(f"SYSTEM_LOG_{randomSuffix}.zip", "w") as archive:
        for file in fileNames:
            archive.write(file)
    
    currentFileString = f"{os.getcwd()}\\SYSTEM_LOG_{randomSuffix}.zip"
    newFileString = f"{os.path.expanduser("~")}\\Downloads\\SYSTEM_LOG_{randomSuffix}.zip"
    shutil.move(currentFileString,newFileString)
    os.remove("tmp_dbg.txt")
    
def raiseInfoDlg(title:str, error:str, blockMe = True):
    ErrorDialog(title, error, QDialogButtonBox.Ok, blockMe=blockMe)
    
def raiseError(title:str, error:str, overrideBtn=None):
    errorPopUp = ErrorDialog(title, error, overrideBtn)
    errorPopUp.activateWindow()
    
def raiseFatalError(title:str, error: str):
    raiseError(title, error)
    sys.exit()

def raiseGenericFatalError(code:int, includeDBInLog=True, additionalDbgInfo=None):
    writeErrorLog(code, includeDBInLog, additionalDbgInfo)
    raiseFatalError(f"Fatal Error {code}", f"A fatal error (Code {code}) occured. A file containing debug info has been written to your Downloads folder. Please refer to the help guide or contact the developers.")

class ErrorDialog(QDialog):
    def __init__(self, titleMsg, infoMsg, overrideBtn=None, blockMe = True):
        super().__init__()

        self.setWindowTitle(titleMsg)
        self.setMinimumSize(300,100)
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))
        
        if overrideBtn != None:
            QBtn = overrideBtn
        else:
            QBtn = QDialogButtonBox.Abort

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel(infoMsg)
        message.setWordWrap(True)
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        
        if blockMe:
            self.exec()
        else:
            self.show()
            time.sleep(1)