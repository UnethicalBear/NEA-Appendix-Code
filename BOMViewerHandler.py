# These are builtin modules needed to run this file
import os, shutil, random, math, sys, requests, csv

# These are imports for PyQt5 that are used to build the UI
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets    import *
from PyQt5.QtGui        import *

# These imports are for the Reportlab library that is used to write PDF exports
import reportlab
from reportlab.lib          import *
from reportlab.platypus     import *
from reportlab.lib.styles   import (ParagraphStyle, getSampleStyleSheet)

# Other files I've written that this file relies on
import errorLogging
import BOM_MouserAPI, BOM_DigikeyAPI, BOM_ComponentClass


### =============== CUSTOM PDF STYLES ================== ###
style = getSampleStyleSheet()
customTextStyle = ParagraphStyle(
    'subtext',
    fontName="Helvetica-Bold",
    fontSize=8,
    parent=style['Heading2'],
    alignment=0,
    spaceAfter=14
)
customHeadingStyle = ParagraphStyle(
    'titletext',
    fontName="Helvetica-Bold",
    fontSize=15,
    parent=style['Heading2'],
    alignment=0,
    spaceAfter=20
)
customTableStyle = TableStyle([
    ('GRID', (0, 0), (-1, -1), 1, reportlab.lib.colors.black),  # Add grid lines to all cells
])

### END ###

# Supported logic families and what we need to append to the search to get correct results
SUPPORTED_LOGIC_LEVELS = {
    "Standard TTL (5.0V) (*default)":["SN",""],
    "High Speed CMOS (TTL Compatible) (2.0-6.0V)":["","HC"],
    "Low Voltage CMOS (2.0-3.6V)":["","LVC"],
}

# This class allows the user to view the BOM and interacts with the main editor, but does not create the BOM.
class BVWindow(QtWidgets.QMainWindow):
    def __init__(self):
        # setup UI
        super(BVWindow, self).__init__()
        uic.loadUi("UI/UI_BOMViewer.ui",self)
        self.setFixedSize(self.size())
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))

        # child UI references that we need
        self.generatorWindowRef = BGWindow()
        self.generatorWindowRef.destroyed.connect(self.getGeneratedBOMData)    
        
        self.createBOM = self.findChild(QAction, "actionExecute")
        self.createBOM.triggered.connect(self.regenerateBOM)
        
        self.findChild(QAction, "actionClose"       ).triggered.connect(self.hide)
        self.findChild(QAction, "actionRescan"      ).triggered.connect(self.rescanForInternet)
        self.findChild(QAction, "actionExportCSV"   ).triggered.connect(self.exportCSV)
        self.findChild(QAction, "actionExportPDF"   ).triggered.connect(self.exportPDF)
        
        self.findChild(QPushButton, "exportCSVBtn"  ).clicked.connect(self.exportCSV)
        self.findChild(QPushButton, "exportPDFBtn"  ).clicked.connect(self.exportPDF)
        
        # get the main table and set it up
        self.mainTable = self.findChild(QTableWidget, "outputTable")
        self.mainTable.resizeColumnsToContents()
        
        # reset the grand total calculations and the result
        self.grandTotalLabel = self.findChild(QLabel, "outputLbl")
        self.grandTotalLabelStr = "<html><head/><body><p><span style=\" font-size:10pt; font-weight:600;\">Grand Total: £{PRICE}*</span></p><p><span style=\" font-size:6pt;\">\
        *Total price is an estimate and doesn't cover shipping, VAT, etc.</span></p></body></html>"
        self.grandTotal = 0
        self.exprRef = ""
        self.BOMResult = [None]
        self.completed = False
        self.generatorWindowRef.executeBtn.clicked.connect(self.setCompleted)
        
    def rescanForInternet(self):
        self.createBOM.setEnabled(
            self.generatorWindowRef.checkForInternet() and BOM_MouserAPI.API_KEY != None and BOM_DigikeyAPI.CLIENT_ID != None and BOM_DigikeyAPI.CLIENT_SECRET != None
        )

    # set completed from save data
    def setCompleted(self):
        self.completed = True    
    
    # returns a list of data that can be printed from a BOMComponent
    def fillItemsInTable(self, component:BOM_ComponentClass.BOMComponent):
        return [
            component.mfn, component.function, component.manufacturer, component.distributor,
            round(component.costPerUnit,2), component.unitsNeeded, component.totalCost
        ]

    # open the generator window from the viewer window
    def regenerateBOM(self):
        self.generatorWindowRef.activateBOM()
    
    # get the generated data from the BOM generator
    def getGeneratedBOMData(self):
        fetchedData = self.generatorWindowRef.getOuput()
        self.BOMResult = fetchedData
        
        # if there is data to show
        if fetchedData:
            self._getGeneratedBOMData(fetchedData)
    
    def _getGeneratedBOMData(self, fetchedData):
        self.grandTotal = 0
        # no of rows = length of data
        self.mainTable.setRowCount(len(fetchedData))
        
        # iterate over the components
        for count, component in enumerate(fetchedData):
            # get the data for this row
            dataToFill = self.fillItemsInTable(component)
            
            # add it to the table
            for i in range(7):
                self.mainTable.setCellWidget(count, i, QLabel(text=str(dataToFill[i])))

            # add to the grand total
            self.grandTotal += component.totalCost

        
        # round grand total to 2 dp
        self.grandTotal = round(self.grandTotal, 2)
        
        # set the grand total label to the grand total
        self.grandTotalLabel.setText(
            self.grandTotalLabelStr.replace("{PRICE}", str(self.grandTotal))
        )
        # resize table for neatness
        self.mainTable.resizeColumnsToContents()
    
    # set the expression from the expression editor
    def registerExpr(self, newExpression:str) -> str:
        self.exprRef = newExpression
        self.generatorWindowRef.registerExpr(newExpression)
    
    # load from the sql database string
    def loadSaveDataDict(self, savedData):
        # ignore index 0
        # basically everything up to list of components is for the generator
        
        # is this section done
        self.completed = savedData[0]
        
        # which APIs to use
        useDatabases = savedData[1]
        self.generatorWindowRef.useMouser.setChecked(useDatabases[0])
        self.generatorWindowRef.useDigikey.setChecked(useDatabases[1])
        
        # search filters to use
        self.generatorWindowRef.useROHS.setChecked(savedData[2])
        self.generatorWindowRef.useInStock.setChecked(savedData[3])
        
        # set the weighting sliders
        self.generatorWindowRef.priceSlider.setValue(int(savedData[4] * 100))
        self.generatorWindowRef.circuitSlider.setValue(int(savedData[5] * 100))
        
        self.generatorWindowRef.registerSavedLogicFamily(savedData[6])
        
        # set the row count to the length of data
        self.mainTable.setRowCount(len(savedData[7]))
        
        # iterate over components
        self.BOMResult = []
        for count, component in enumerate(savedData[7]):
            for i in range(7):
                # fill the table row
                self.mainTable.setCellWidget(count, i, QLabel(text=str(component[i])))
            
            self.BOMResult.append(
                BOM_ComponentClass.BOMComponent(
                    component[3],
                    component[0],
                    component[2],
                    component[1],
                    component[4],
                    component[5],
                    round(component[6]/component[4])
                )
            )
                
        # get the grand total
        self.grandTotal = savedData[8]
        # update the grand total label
        self.grandTotalLabel.setText(
                self.grandTotalLabelStr.replace("{PRICE}", str(self.grandTotal))
        )
        
    def getSaveData(self):
        # out is the list of save data we need to return
        out = [
            self.completed,  # if this seciton is done
            [
                self.generatorWindowRef.useMouser.isChecked(), # APIs to use
                self.generatorWindowRef.useDigikey.isChecked()
            ],
            self.generatorWindowRef.useROHS.isChecked(), # search filters
            self.generatorWindowRef.useInStock.isChecked(),
            self.generatorWindowRef.priceSlider.value(), # slider default values
            self.generatorWindowRef.circuitSlider.value(),
            self.generatorWindowRef.logicLevelList.currentIndex(), # logic family
            [], # items we have searched for and found 
            self.grandTotal,            # grand total
            self.grandTotal != 0        # done if grand total != 0
        ]
        
        if self.BOMResult != None:
            for item in self.BOMResult:
                out[7].append(
                    self.fillItemsInTable(item)
                )
        
        return out
    
    def exportCSV(self):
        # get a random suffix to ensure export is unique name
        randomSuffix = random.randint(0, 99999)
        # open the csv file for writing
        with open('BOMExport.csv', 'w', newline='', encoding="utf-8") as csvFile:
            csvWriter = csv.writer(csvFile, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)
            # write the table converted to a 2D array
            csvWriter.writerows(self.tableTo2DArray())
            
        # move the file to downloads folder
        currentFileString = f"{os.getcwd()}\\BOMExport.csv"
        newFileString = f"{os.path.expanduser("~")}\\Downloads\\BOMExport{randomSuffix}.csv"
        shutil.move(currentFileString,newFileString)
        
        # alert user
        errorLogging.raiseInfoDlg("Info",f"Exported BOMExport{randomSuffix}.csv to downloads.")

    def tableTo2DArray(self):
        # get the header rows 
        output = [[self.mainTable.horizontalHeaderItem(x).text() for x in range(self.mainTable.columnCount())]]
        
        # for every item in the tab;e
        for row in range(self.mainTable.rowCount()):
            rowData = []
            
            # add the component's value
            for col in range(self.mainTable.columnCount()):
                # get the item at the current location
                item = self.mainTable.cellWidget(row, col)
                if item:
                    # if the item isn't empty, add the item
                    rowData.append(item.text())
            # add the row to the list
            output.append(rowData)
        return output        

    def exportPDF(self):
        # create a new pdf export item 
        pdfExport = SimpleDocTemplate("BOMExport.pdf", pagesize=reportlab.lib.pagesizes.A4)
        # add the heading to the pdf
        objects = [
            Paragraph("BOM Export", style=customHeadingStyle),
            Paragraph("Made using <i><b>Boolean Bacus</b></i> Logic Calculator"),
            Spacer(0,25),
            Paragraph("<b><u>Input Settings</u></b>"),
            Paragraph(f"Expression Input: Q={self.exprRef}"),
            Paragraph(f"Use Mouser?         {"yes" if self.generatorWindowRef.useMouser.isChecked() else "no"}"),
            Paragraph(f"Use Digikey?        {"yes" if self.generatorWindowRef.useDigikey.isChecked() else "no"}"),
            Paragraph(f"Require RoHS?       {"yes" if self.generatorWindowRef.useROHS.isChecked() else "no"}"),
            Paragraph(f"Require Stock?      {"yes" if self.generatorWindowRef.useInStock.isChecked() else "no"}"),
            Spacer(0,50),
            Paragraph("<b><u>Output:</u></b>"),
            Spacer(0,25),
            ]
        # get the export table 
        tableToExport = self.tableTo2DArray()
        # turn it into a pdf object
        objects.append(Table(tableToExport, style=customTableStyle))
        
        # add the grand total to the BOM
        objects += [
            Spacer(0,50),Paragraph(f"Grand Total: £{self.grandTotal}"), 
            Paragraph("Pricing is an approximate. Always check before purchasing.", style=customTextStyle)
        ]
        
        # "compile" the pdf
        pdfExport.build(objects)
        
        # rename to a unique name and move to downloads
        randomSuffix = random.randint(0, 99999)
        currentFileString = f"{os.getcwd()}\\BOMExport.pdf"
        newFileString = f"{os.path.expanduser("~")}\\Downloads\\BOMExport{randomSuffix}.pdf"
        shutil.move(currentFileString,newFileString)
        
        errorLogging.raiseInfoDlg("Info",f"Exported BOMExport{randomSuffix}.pdf to downloads.")

# This class generates the BOM
class BGWindow(QtWidgets.QMainWindow):
    def __init__(self):
        # setup the UI
        super(BGWindow, self).__init__()
        uic.loadUi("UI/UI_BOMCreator.ui", self)
        self.setWindowIcon(QIcon("UI/iconLightTheme.ico"))
        self.setFixedSize(self.size())

        # references to child components
        self.priceSlider    = self.findChild(QSlider, "WPSlider")
        self.circuitSlider  = self.findChild(QSlider, "WMSlider")
        self.priceSliderLbl = self.findChild(QLabel, "WPLbl")
        self.matchSliderLbl = self.findChild(QLabel, "WMLbl")
        
        self.logicLevelList = self.findChild(QComboBox, "logicComboBox")
        
        # set slots and triggers
        self.executeBtn = self.findChild(QCommandLinkButton, "executeBtn")
        self.executeBtn.clicked.connect(self.execute)
        self.priceSlider.valueChanged.connect(self.updateSliders)
        self.circuitSlider.valueChanged.connect(self.updateSliders)
        
        # set default generation values
        self.logicFamily = None
        self.useROHS = self.findChild(QCheckBox, "UseROHS")
        self.useInStock = self.findChild(QCheckBox, "UseInStock")
        
        self.useMouser = self.findChild(QCheckBox,"DBUseMouser")
        self.useDigikey= self.findChild(QCheckBox,"DBUseDigikey")
        
        self.BOMResult = None
        self.__expr : str = None        
    
    # set the expression to evaulate
    def registerExpression(self, expr):
        self.__expr = expr
    
    # return the BOM result to the viewer window
    def getOuput(self):
        return self.BOMResult
    
    def execute(self):
        # hide this window        
        self.hide()
        
        # we need to search at least one API to get any results
        if not (self.useMouser.isChecked() or self.useDigikey.isChecked()):
            errorLogging.raiseInfoDlg("Error!", "You have selected no database to search. Therefore, there will be no output. Please select either Mouser, Digikey or both.")
            return
        
        mouserSearchKey = int({
            "00":1,         # no restriction
            "10":2,         # use ROHS
            "01":4,         # only in stock
            "11":8          # ROHS & in stock
        }[f"{int(self.useROHS.isChecked())}{int(self.useInStock.isChecked())}"])
        
        # components found, and the best ones to show to the user
        componentsFound     : list[BOM_ComponentClass.BOMComponent] = []
        bestComponentsFound : list[BOM_ComponentClass.BOMComponent] = []
        
        # component family 
        self.logicFamily = family = self.logicLevelList.currentText()
        componentsToSearch = ["74{}04","74{}08","74{}32"]
        familyData = []
        
        # try and get the logic family data
        try:
            familyData = SUPPORTED_LOGIC_LEVELS[family]
        except (KeyError, IndexError):
            # invalid logic family
            errorLogging.raiseGenericFatalError(58)
        
        # format the component search data with the family data, e.g. with 
        for i, component in enumerate(componentsToSearch):
            component = (familyData[0] * (i!=1)) + component
            component = component.replace("{}",(familyData[1]*(i!=1) + "F"*(i==1))) 
            componentsToSearch[i] = component
         
        # each function and the number on a chip
        circuitsToSearch = [6,2,2]
        functionsToSearch = ["NOT","AND","OR"]

        # No expression to evaulate
        if self.__expr is None:
            errorLogging.raiseGenericFatalError(57)
        
        # 2 inputs per OR, so we just need to get the number of ORs and divide by 2
        OR_GATE_COUNT  = math.ceil(self.__expr.count("+")/2)
        # 1 input per NOT, 6 per chip so just divide by 6
        NOT_GATE_COUNT = math.ceil(self.__expr.count("#")/6)
        # And is more complicated because:
        #    A AND B needs 1 AND gate
        #    A AND B AND C needs 2
        #    A AND B AND C AND D needs 4 <= this isn't linear
        AND_GATE_COUNT = 0

        # iterate over the terms
        for term in self.__expr.split("+"):
            # if we need an and gate in this term
            if len(term) > 1:
                # remove the nots because we dont need those
                # then add the number of ands in that term
                AND_GATE_COUNT += math.ceil(len(term.replace("#",""))/2)
        
        # now we have the number needed once we divide by 4 (4 ANDs per chip)
        noNeeded = [NOT_GATE_COUNT, math.ceil(AND_GATE_COUNT/4), OR_GATE_COUNT]
        
        # if no components are needed at all
        if any(noNeeded) == False:
            errorLogging.raiseInfoDlg("BOM Generation Error", f"The expression you have generated (Q={self.__expr}) requires no logic to implement.")
            return
        
        # need to search and sort components
        
        # get new digkey auth token
        securityToken = BOM_DigikeyAPI.getNewToken()           
        for i in range(3):      # 3 searches, 1 for OR, 1 for AND, 1 for NOT
            if noNeeded[i] == 0:# no need to search
                errorLogging.raiseInfoDlg(f"Search {i+1}/3 Done", f"Search {i+1} done", blockMe=False)
                continue
            
            # we do need to search for components
            results = []
            
            # if we're using digikey
            if self.useDigikey.isChecked():
                
                # search for the current item, with the correct information applied and return to the list
                results += BOM_DigikeyAPI.searchByKeyword(
                    BOM_DigikeyAPI.CLIENT_ID, securityToken, componentsToSearch[i], 
                    2, BOM_DigikeyAPI.LOGIC_ICS_FILTER, True, True, functionsToSearch[i], noNeeded[i], circuitsToSearch[i]
                )
            
            # if we're using mouser, 
            if self.useMouser.isChecked():
                # search for the current item, with the correct information applied and return to the list
                results += BOM_MouserAPI.searchByKeyword(componentsToSearch[i], 2, mouserSearchKey, functionsToSearch[i], noNeeded[i], circuitsToSearch[i])
            
            # tell the user this search is complete
            errorLogging.raiseInfoDlg(f"Search {i+1}/3 Done", f"Search {i+1} completed, Debug: S{componentsToSearch[i]}F{functionsToSearch[i]}C{circuitsToSearch[i]}N{noNeeded[i]}", blockMe=False)
            
            # get the max price of all the components (needed for Z score)
            maxPrice = max([r.totalCost for r in results])
            
            # iterate over the components we found
            for j, _component in enumerate(results):
                _component.setRankingInfo(
                    # rank them with the required info
                    self.rankComponent(_component.getRankingParameters(), noNeeded[i], maxPrice)
                )
                # update in the list
                results[j] = _component
            
            # add to all components found
            componentsFound.append(results)
        
        for searchResultType in componentsFound:
            bestComponentsFound.append(self.mergeSortComponents(searchResultType)[0])
            # sort the components found for each boolean function by their rank
            # the one with the lowest rank will be first
            # this is the best suited component
        
        # the result is the best components found
        self.BOMResult = bestComponentsFound
        # this window is done
        self.close()
        
    def rankComponent(self, data, noNeeded, maxPrice):
        # this follows the formula defined in the analysis and design sections for component ranking
        
        # default x value
        x = 1.5
        if noNeeded == data[1]:
            # exact number of items => x = 1
            x = 1
        else:
            # otherwise x is defined as -1 or 1
            x = (data[0]-noNeeded)/abs(data[0]-noNeeded)
        
        # price weighting and match weighting
        wP = self.priceSlider.value()/100
        wM = self.circuitSlider.value()/100
        
        # Z score formula
        Z = wP*(data[1]/maxPrice) + wM*(1 - 0.25*x + 0.75*x*x)
        # round to 4dp
        Z = round(Z,4)
        return Z
        
    def updateSliders(self):
        # set the text on the slider labels from the values of the sliders
        self.priceSliderLbl.setText(f"{round(self.priceSlider  .value()/100, 2)}")
        self.matchSliderLbl.setText(f"{round(self.circuitSlider.value()/100, 2)}")
        
    def refreshSettings(self):
        # refresh the sliders and settings in the generator
        self.updateSliders()
        self.logicLevelList.clear()
        self.logicLevelList.addItems(SUPPORTED_LOGIC_LEVELS.keys())
        
    def checkForInternet(self=None):
        # we need an internet connection to use the BOMGenerator
        # self=none becuase this doesn't need any arguments
        try:
            # try to contact a website within 5 seconds
            requests.get("https://www.google.com", timeout=5)
            # internet is on
            if self:
                self.executeBtn.setEnabled(True)
            return True
        except:
            # no internet -> can't use APIs
            errorLogging.raiseError("Check your internet!","Error (Code 49): No internet connection. Please try again later.")
            if self:
                self.executeBtn.setEnabled(False)
            
            return False
    
    def _merge(self, left:list, right:list):
        # get a new copy to stop immutable types being a pain
        mergedList = left.copy()
        # add the right to the left
        mergedList += right
        # sort them
        mergedList.sort()
        # merge is now done
        return mergedList
    
    def mergeSortComponents(self, components:list):
        # if the list is one long it is sorted
        if len(components) == 1:
            return components
        
        # get the left and right lists from the midpoint
        middlePosition = int(len(components)/2)
        left = components[:middlePosition]
        right = components[middlePosition:]
        
        # recursively split and then merge the 2 lists until we're done
        return self._merge(self.mergeSortComponents(left),self.mergeSortComponents(right)) 
    
    def registerExpr(self, newExpression:str) -> None:
        # set the expression to search for to this new expression
        self.__expr = newExpression
    
    # Reinstate the saved logic family
    def registerSavedLogicFamily(self, logicFamily:int) -> None:
        # this family doesnt exist
        if logicFamily < 0 or logicFamily > len(SUPPORTED_LOGIC_LEVELS) - 1:
            errorLogging.raiseError("Error! (Code 70)", "BOM save data's logic family is invalid, using default instead", QDialogButtonBox.Ok)
            self.logicLevelList.setCurrentIndex(0)
            return
                    
        # otherwise add the logiclevellist
        self.logicLevelList.setCurrentIndex(logicFamily)
    
    def activateBOM(self):
        # refresh the window and settings
        self.refreshSettings()
        self.show()
        self.activateWindow()
    
    def closeEvent(self, a0):
        # this means we can tell when the window is done
        self.destroyed.emit()
        return super().closeEvent(a0)

if __name__ == "__main__":                      
    # This section should only run if this is the entrypoint to the system
    # E.g. if this code is imported to another file, this shouldn't run
    # This ensures the code must be run with this as the main entrypoint,
    # which is better for the UI handling and system as a whole
    
    app = QtWidgets.QApplication(sys.argv)
    
    if BGWindow.checkForInternet():
        window = BVWindow()
        window.show()
        sys.exit(app.exec())