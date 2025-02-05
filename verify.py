import os, hashlib
from ProjectManager import UI_FOLDER_HASH, SOP_DLL_HASH

print("verify.exe: start system\n-----\nverify.exe: begin verifying SOP.dll")

dllHash = hashlib.new("SHA256")

if os.path.exists(os.path.join(os.getcwd(), "SOP.dll")):
    with open("SOP.dll", 'rb') as f:
        while chunk := f.read(8192):  # Read the file in chunks of 8192 bytes
            dllHash.update(chunk)     # add this data to the hash
    
    if dllHash.hexdigest().upper() != SOP_DLL_HASH:
        print("verify.exe: SOP.dll failed integrity check")
    else:
        print("verify.exe: SOP.dll ok")
        
else:
    print("verify.exe: SOP.dll does not exist.")


print("-----\nverify.exe: begin verifying UI folder")

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

if UIHash.hexdigest().upper() != UI_FOLDER_HASH:
    print("verify.exe: UI folder failed integrity check")
else:
    print("verify.exe: UI folder ok")
    
print("-----")
print("verify.exe: check for system dlls")

r = []
for query in [
        # "C:\\Windows\\System32\\api-ms-win-crt-heap-l1-1-0.dll",
        # "C:\\Windows\\System32\\api-ms-win-crt-runtime-l1-1-0.dll",
        # "C:\\Windows\\System32\\VCRUNTIME140.dll",
        # "C:\\Windows\\System32\\MSVCP140.dll",
        # "C:\\Windows\\System32\\VCRUNTIME140_1.dll",
        "C:\\Windows\\System32\\KERNEL32.dll",
    ]:
        r.append(os.path.exists(query))
        print(f"verify.exe: target: {query} result: {"OK" if r[-1] else "FAIL"}")

if not all(r):
    print("WARNING! verify.exe found missing dll files, the system will not work without these.")

print("-----")
print("verify.exe: check for API keys")


alert = 0
if os.environ.get("BB_MOUSER_KEY"):
    print("verify.exe: Mouser API Key exists")
else:
    print("verify.exe: NO Mouser API Key")
    alert =1

if os.environ.get("BB_DIGIKEY_CLIENT"):
    print("verify.exe: Digikey Client ID exists")
else:
    print("verify.exe: NO Digikey Client ID")
    alert =1
    
if os.environ.get("BB_DIGIKEY_SECRET"):
    print("verify.exe: Digikey Secret exists")
else:
    print("verify.exe: NO Digikey Secret")
    alert =1
    
print("WARNING! verify.exe cannot check these API keys are valid.")
if alert:
    print("WARNING! API keys were missing entries. Please run APIENV.exe to fix this and then repeat this test. If this still fails, manually enter the API keys.")
    
print("-----")

print("verify.exe: done")
os.system("pause")