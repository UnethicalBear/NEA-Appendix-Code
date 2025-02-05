import requests, os
import BOM_ComponentClass
import errorLogging

API_KEY = os.environ.get("BB_MOUSER_KEY")

# try:
#     # SECRET API key for my project 
#     API_KEY = os.environ["BB_MOUSER_KEY"]
# except (KeyError, IndexError):
#     errorLogging.raiseGenericFatalError(75)
# # Mouser API URL
BASE_URL = "https://api.mouser.com"

# function to search for parts given a keyword
def searchByKeyword(keyword:str, noItems:int, searchOptionKey:int, _componentFunction, _noNeeded, _noCircuits) -> list[BOM_ComponentClass.BOMComponent]:
    
    # Validate input
    if noItems not in range(0, 51):
        errorLogging.raiseGenericFatalError(55)
    if searchOptionKey not in [1,2,4,8]:
        errorLogging.raiseGenericFatalError(54)
    
    # Dictionary of options in the format required for mouser
    searchDictionary = {
    "SearchByKeywordRequest": {
        "keyword": keyword,
        "records": noItems,
        "startingRecord": 0,
        "searchOptions": searchOptionKey,
        }  
    }
    # send a POST request to the mouser API with the information we have processed
    response = requests.post(f"{BASE_URL}/api/v1.0/search/keyword?apiKey={API_KEY}", json=searchDictionary, headers={"Content-Type":"application/json"})
    # get the response code
    responseCodeInfo = str(response.status_code)[0]
    
    # response OK
    if responseCodeInfo == "2":
        componentsFound = []
        # iterate over each component from the search
        for component in response.json()["SearchResults"]["Parts"]:
            try:
                # try to get the relevant information
                mf = component["Manufacturer"]
                mfn = component["ManufacturerPartNumber"]
                unitPrice = float(component["PriceBreaks"][0]["Price"][1:])
                
                # turn into BOMComponent class and add to found list 
                componentsFound.append(
                    BOM_ComponentClass.BOMComponent("MOUSER",mfn,mf,_componentFunction, unitPrice, _noNeeded, _noCircuits)
                )
            except:
                # this component contained invalid results
                errorLogging.raiseError("Error! (Code 59)",f"Could not parse component search for {keyword}. If this persists, contact the developers.")
                return
        return componentsFound
    # generic HTTPS error => no internet, wrong API key etc.
    elif responseCodeInfo in ['4','5']:
        errorLogging.raiseGenericFatalError(51)
    # something went weirdly and wonderfully wrong
    else:
        errorLogging.raiseGenericFatalError(52,True,f"MOSR_KWD: {keyword}\nHTTP_RSP: {responseCodeInfo}")
        
