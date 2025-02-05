import requests, BOM_ComponentClass, os, errorLogging

# Digikey API Url
API_BASE_URL        = "https://api.digikey.com/products/v4/search/keyword"
# Digikey security Url
AUTHENTICATE_URL    = "https://api.digikey.com/v1/oauth2/token"


CLIENT_ID     = os.environ.get("BB_DIGIKEY_CLIENT")
CLIENT_SECRET = os.environ.get("BB_DIGIKEY_SECRET")

# try:
#   # My project's id
#   CLIENT_ID           = os.environ["BB_DIGIKEY_CLIENT"]
#   # my project's secret (password)
#   CLIENT_SECRET       = os.environ["BB_DIGIKEY_SECRET"]
# except (IndexError, KeyError):
#   errorLogging.raiseGenericFatalError(74)
  
# filter to only show logic circuits (which is what we want)
LOGIC_ICS_FILTER    = 32

# method to get a new security token as they are only valid for a short time
def getNewToken():
  # required data
  data = {
    "client_id":CLIENT_ID,
    "client_secret":CLIENT_SECRET,
    "grant_type":"client_credentials"
  }

  # send to digikey
  response = requests.post(url=AUTHENTICATE_URL, data=data, headers={"Content-Type":"application/x-www-form-urlencoded"})
  # if the response was ok
  if response.status_code == 200:
    # return the new secure token
    return response.json()["access_token"]

# method to search for components by their name
def searchByKeyword(
  clientID, clientToken, 
  searchKeyword, searchLimit, categoryFilter, 
  useInStock, useROHS,
  _componentFunction, _noNeeded, _noCircuits
) -> list[BOM_ComponentClass.BOMComponent]:
  
  # search data
  data = {
    "Keywords":searchKeyword,
    "Limit":searchLimit,
    "Offset":0,
    "FilterOptionsRequest":{
      "CategoryFilter": [
        {
          "Id":categoryFilter
        }
      ],
      "SearchOptions":[]
    }
  }
  
  # if all our components need to be of RoHS safety standard
  if useROHS:
    data["FilterOptionsRequest"]["SearchOptions"].append("RohsCompliant")
  # if all components need to be in stock
  if useInStock:
    data["FilterOptionsRequest"]["SearchOptions"].append("InStock")

  # add the header with the security token and the type of request
  headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {clientToken}",
    "X-DIGIKEY-Client-Id": clientID,
    "X-DIGIKEY-Locale-Language": "en",
    "X-DIGIKEY-Locale-Currency": "GBP",
    "X-DIGIKEY-Locale-Site": "UK",
    "Content-Type": "application/json",
  }
  # send to API and get results
  response = requests.post(API_BASE_URL, headers=headers, json=data)
  componentsGenerated = []
  
  responseData = response.json()["Products"]
  # iterate over the products retrived
  for product in responseData:
    # get the information
    mf = product["Manufacturer"]["Name"]
    mfn = product["ManufacturerProductNumber"]
    unitPrice = float(product["UnitPrice"])
    # convert to BOMComponent class
    componentsGenerated.append(
      BOM_ComponentClass.BOMComponent("DIGIKEY", mfn, mf, _componentFunction, unitPrice, _noNeeded, _noCircuits)
    )
  
  return componentsGenerated
