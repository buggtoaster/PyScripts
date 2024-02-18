# Script to remove artifacts related to the ClearBar and ClearBrowser.
# No arguments need to be passed, just run the script and it will report what was removed

import psutil
import subprocess
import re
import json
import glob
import shutil
import os

script_results = {
    "Processes Killed": [],
    "Registry Keys Found": [],
    "Registry Keys Deleted": [],
    "File Path Deleted": [],
    "Process Kill Failures": [],
    "Registry Key Deletion Errors": [],
    "File Path Deletion Errors": [],
    "Scheduled Tasks": [],
    "Scheduled Tasks Errors": [],
    }


def procKill():
    process_names = ["Clear.exe", "ClearBar.exe", "clearbrowser.exe"]
    process_count = 0
    for proc in psutil.process_iter():
        if proc.name() in process_names:
            process_count += 1
            try:
                proc.kill()
                script_results["Processes Killed"].append(proc.name())
            except Exception as e:
                script_results["Process Kill Failures"].append(f"{proc.name()} - ERROR: {e}")
    if process_count == 0:
        script_results["Processes Killed"].append("No running processes found!") 


def del_regKey(regkey):   
    command = f"reg delete {regkey} /f"
    try:
        runcmd = subprocess.run(command, capture_output=True)
        cmdout = str(runcmd.stdout)
        if "The operation completed successfully" in cmdout:
            script_results["Registry Keys Deleted"].append(regkey)
        elif "ERROR" in cmdout:
            script_results["Registry Key Deletion Errors"].append(f"{regkey} - ERROR: {cmdout}")
    except Exception as e:
        script_results["Registry Key Deletion Errors"].append(f"{regkey} - ERROR: {e}")


def reg_enum():
    i = 0
    regkeys = []
    regex = re.compile(r'(HKEY[\w\d\\\-\:\/\.]+)')
    searchterm = ["ClearBar", "ClearBrowser", "Clear.exe"]
    for term in searchterm:
        command = f"reg query HKU /s /f {term} /k"
        runcmd = subprocess.run(command, capture_output=True)
        cmdresults = str(runcmd.stdout)
        cleancmdresults = re.sub(r"\\r\\n", "\\r \\n", cmdresults)
        regstrings = regex.findall(cleancmdresults)
        for reg in regstrings:
            regkeys.append(reg)
    return regkeys


def cleanregkeys(regkeys):
    cleankeys = []
    for key in regkeys:
        clnkey = key.replace("\\\\", "\\")
        cleankeys.append(clnkey)
    script_results["Registry Keys Found"] = cleankeys   
    return cleankeys
       

def file_removal():
    paths = [
        "C:\\Users\\*\\AppData\\Local\\ClearBrowser", 
        "C:\\Users\\*\\AppData\\Local\\Programs\\Clear",
        "C:\\Users\\*\\AppData\\Local\\Clear",
	"C:\\Users\\*\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Clear.lnk",
	"C:\\Users\\*\\Desktop\\Clear.lnk",
	"C:\\Users\\*\\AppData\\Local\\Temp\\clearbrowser_topsites"
        ]
    for folder in paths: 
        dir_path = glob.glob(folder)
        if dir_path:
            for path in dir_path:
                try:
                    shutil.rmtree(path)
                    script_results["File Path Deleted"].append(path)
                except Exception as e:
                    script_results["File Path Deletion Errors"].append(f"{path} - ERROR: {e}")
                    
def schtasks():
    keylist = ["ClearStartAtLoginTask", "ClearUpdateChecker"]

    for key in keylist:
        cmd = f"schtasks /query /fo LIST /tn {key}"
        out = subprocess.run(cmd, capture_output=True)
        output = str(out.stdout)
        if output == "b''":
            script_results["Scheduled Tasks"].append(f"Scheduled Task: {key}, Not Found.")
        elif output:
            cmd2 = f"schtasks /delete /tn \"{key}\" /f"
            out2 = subprocess.run(cmd2, capture_output=True)
            output2 = str(out2.stdout)
            if "SUCCESS" in output2:
                script_results["Scheduled Tasks"].append(f"Scheduled Task: {key}, was deleted.")
            elif "ERROR" in output2:
                    script_results["Scheduled Tasks"].append(f"Scheduled Task: {key}, Errored during deletion.")
                    script_results["Scheduled Tasks Errors"].append(f"Scheduled Task: {key}, ERROR - {output2}.")



def main():
   
    procKill()
    regkeys = reg_enum()
    cleankeys = cleanregkeys(regkeys)
    for reg in cleankeys:
        del_regKey(reg)
    file_removal()
    schtasks()
    pretty_dict = json.dumps(script_results, indent=4)
    print(pretty_dict)
    
main()

