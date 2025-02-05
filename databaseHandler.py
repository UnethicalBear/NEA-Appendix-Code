import sqlite3
import datetime
import errorLogging

def generateTimeStamp(): # This function returns a timestamp of the current time to update when the Project/Expression was last updated
    time = datetime.datetime.now() # Get the current time using the datetime library
    return time.strftime("%d/%m/%Y %H:%M") # This returns the time in an easy-to-read format e.g. 01/09/2024 09:35

class databaseHandler:
  def __init__(self) -> None:
    self.connection = None
    
    self.createProjectTable = """
    CREATE TABLE IF NOT EXISTS Projects (
      projectID INTEGER PRIMARY KEY AUTOINCREMENT,
      projectName TEXT NOT NULL,
      lastUpdated TEXT
    );
    """
    self.createExprTable = """
    CREATE TABLE IF NOT EXISTS Expressions (
      expressionID INTEGER PRIMARY KEY AUTOINCREMENT,
      expressionName TEXT NOT NULL,
      expressionData TEXT NOT NULL,
      lastUpdated TEXT
    );
    """
    self.createLinkTable = """
    CREATE TABLE IF NOT EXISTS ProjHandler (
      projectID INTEGER NOT NULL,
      expressionID INTEGER NOT NULL,
      FOREIGN KEY (projectID) REFERENCES Projects(projectID),
      FOREIGN KEY (expressionID) REFERENCES Expressions(expressionID)
    );
    """

  def isConnectionOpen(self):
    try:
      self.connectToMain()
      return True
    except:
      return False

  def connectToMain(self):
    self.connectToDatabase("main.db")

  def connectToDatabase(self, path):
    self.dbpath = path
    try:
      self.connection = sqlite3.connect(path)
    except sqlite3.Error:
      errorLogging.raiseGenericFatalError(4)
          
  def executeSQLQuery(self, query : str, isReadQuery : bool = False, dontCommit : bool = False):
    SQLcursor = self.connection.cursor()
    try:
      SQLcursor.execute(query)
      if isReadQuery:
        return SQLcursor.fetchall()
      elif not dontCommit:
        self.connection.commit()
      return 1
    except sqlite3.Error:
      errorLogging.raiseGenericFatalError(5, additionalDbgInfo=f"QRY: {query}\nDC: {dontCommit}")
      
  def readSQLQuery(self, query : str):
    return self.executeSQLQuery(query, True)

  def executeMultipleQueries(self, queries:list[str]):
    for query in queries:
      self.executeSQLQuery(query, False, True)  # execute write-only query and don't commit to database yet
    
    self.connection.commit() # all queries were executed successfully, commit all to database
    return 1  # return 1 to show all queries were executed successfully

  def createDatabase(self):
    self.executeSQLQuery(self.createProjectTable)
    self.executeSQLQuery(self.createExprTable)
    self.executeSQLQuery(self.createLinkTable)
    self.connection.commit()
    self.closeConnection()
    self.connectToDatabase(self.dbpath)
    
  def resetExprIncrement(self):
    self.executeSQLQuery("UPDATE SQLITE_SEQUENCE SET SEQ=0 WHERE NAME='Expressions';")
  def resetProjectIncrement(self):
    self.executeSQLQuery("UPDATE SQLITE_SEQUENCE SET SEQ=0 WHERE NAME='Projects';")
    
  def saveExpression(self, exprID:int, newData:str):
    self.executeSQLQuery(f"UPDATE Expressions SET ExpressionData = '{newData}' WHERE ExpressionID = {exprID}")
    self.executeSQLQuery(f"UPDATE Expressions SET LastUpdated = '{generateTimeStamp()}' WHERE ExpressionID = {exprID}")
    
  def closeConnection(self):
    if self.connection:
      self.connection.close()
  