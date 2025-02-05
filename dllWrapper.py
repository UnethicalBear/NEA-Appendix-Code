import ctypes
import os
import errorLogging

pathToDLL = os.getcwd() + "\\SOP.dll"
os.add_dll_directory(os.getcwd())

_SOPDLL = None

"""
The DLL sends info back in the following form:

OPERATION_STATUS, DATA_GENERATED, DEBUG_INFO

where each of these is seperated by @@. In case of error, the return format is:

0, NULL, ERROR INFO

"""

def dllInit():
    global _SOPDLL
    try:
        # try to open the DLL file
        _SOPDLL = ctypes.WinDLL(pathToDLL)

        # assign the input and output types of the DLL functions 
        _SOPDLL.sumOfProducts.argtypes = [ctypes.c_char_p, ctypes.c_int]
        _SOPDLL.sumOfProducts.restype = ctypes.c_char_p
        
        # assign the input and output types of the DLL functions 
        _SOPDLL.simplifyBooleanExpr.argtypes = [ctypes.c_char_p]
        _SOPDLL.simplifyBooleanExpr.restype = ctypes.c_char_p
        
    except FileNotFoundError:
        # The DLL has been moved or deleted
        errorLogging.raiseGenericFatalError(35)
    except Exception:
        # another reason is stopping the program opening the file
        errorLogging.raiseGenericFatalError(36)
        
def sumOfProducts(strIn: str, size:int) -> str:
    # reference to the DLL sumOfProducts command
    global _SOPDLL
    try:
        # start by encoding the input string so it can be sent across to the dll
        _strIn = strIn.encode("utf-8")
        
        # call the dll function and decode the results
        output = str(_SOPDLL.sumOfProducts(_strIn, size).decode())
        # output is seperated by @@ so we use the split command to collect all parts in a list
        output = output.split("@@")
        
        # operation stauts
        status = output[1]
        
        if status == "0":
            # an error occured while evaulating the input (inside the dll)
            errorLogging.raiseGenericFatalError(39,additionalDbgInfo=f"SOP: {output}")
        elif status == "1":
            # generated successfully
            return output[0]             
        else:
            # SOP library returned an invalid status -> internal runtime error
            errorLogging.raiseGenericFatalError(40, additionalDbgInfo=f"SOP_DBG: {output[2]}")
        
    except Exception:
        # could not run the SOP calculation
        errorLogging.raiseGenericFatalError(41)
        
def simplifyBooleanExpr(strIn: str):
    global _SOPDLL
    try:
        # encode the input to bytes
        _strIn = strIn.encode("utf-8")
        # send to dll and decode result and split at deliminator
        output = str(bytes(_SOPDLL.simplifyBooleanExpr(_strIn)).decode())
        output = output.split("@@")
        
        status = output[0]
        if status == "0":
            # an error occured
            errorLogging.raiseGenericFatalError(42,additionalDbgInfo=f"SMP_DBG: {output[2]}")
        elif status == "1":
            # generated successfully
            # return the parts of the output excluding the status since it must be 1 ("OK") to get to this point.
            return output[1:]             
        else:
            # SOP library returned an invalid status -> internal runtime error
            errorLogging.raiseGenericFatalError(43, additionalDbgInfo=f"SMP_DBG: {output}")
    except Exception as e:
        errorLogging.raiseGenericFatalError(44, additionalDbgInfo=e)
        
