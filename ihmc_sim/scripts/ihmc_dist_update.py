#!/usr/bin/python

try:
    import semantic_version
except ImportError, e:
    sys.stderr.write("ihmc_dist_update.py requires the semantic_version Python package. Try pip install semantic_version or sudo pip install semantic_version\n")
    sys.exit(1)
try:
    import requests
except ImportError, e:
    sys.stderr.write("ihmc_dist_update.py requires the requests Python package. Try pip install requests or sudo pip install requests\n")
    sys.exit(1)
try:
    import rospkg
except ImportError, e:
    sys.stderr.write("ihmc_dist_update.py cannot import rospkg Python package. Check your ROS and rospy installation.\n")
    sys.exit(1)

import os, sys, tarfile
from xml.etree import ElementTree

def main():

    bucket_url="http://ihmc.s3.amazonaws.com/"

    latestVersion = getNewestVersionNumber(bucket_url)

    response = requests.get(bucket_url, params={'prefix': 'api_releases'})

    root = ElementTree.fromstring(response.content)

    response.close()

    namespace =  root.tag.rsplit('}')[0] + '}'

    newTar = getNewestTarFileName(namespace, root, latestVersion)

    rospack = rospkg.RosPack()
    ihmcSimDir = rospack.get_path('ihmc_sim')

    currentVersion = 0

    for f in os.listdir(ihmcSimDir):
        if "IHMCAtlasAPI" in f and os.path.isdir(os.path.join(ihmcSimDir, f)):
            currentVersion = semantic_version.Version(f.split("IHMCAtlasAPI-")[1])

    if latestVersion > currentVersion:
        print "Update Available! Preparing to download " + newTar
        updateDistribution(newTar, bucket_url, ihmcSimDir)
    else:
        print "IHMCAtlasApi is at the most current version."

    return 0

def getNewestVersionNumber(bucket_url):
    response = requests.get(bucket_url + "api_releases/version")
    versionText = response.text
    version = semantic_version.Version(versionText)
    response.close()
    return version

def getNewestTarFileName(namespace, root, latestVersion):
    for child in root.findall(namespace+'Contents'):
        for childKey in child.findall(namespace+'Key'):
            if not childKey.text.endswith('/'):
                keyName = childKey.text.split("api_releases/")[1]
                if ".tar" in keyName and str(latestVersion) in keyName:
                    return keyName


def updateDistribution(newTarName, bucket_url, ihmcSimDir):
    for f in os.listdir(ihmcSimDir):
        if "IHMCAtlasAPI" in f and os.path.isdir(os.path.join(ihmcSimDir, f)):
            sys.stderr.write('WARNING: Found pre-existing' + f + ' in ihmc_sim package. Remove all old versions of the distribution before launching anything.\n')

    destFile = os.path.join(ihmcSimDir, newTarName)

    print "Downloading " + newTarName + " to ihmc_sim package..."
    fileResponse = requests.get(bucket_url + "api_releases/" + newTarName, stream=True)

    with open(destFile, 'wb') as tarFile:
        for chunk in fileResponse.iter_content(chunk_size=1024):
            if chunk:
                tarFile.write(chunk)
                tarFile.flush()
        tarFile.close

    fileResponse.close()

    print "Untarring distribution and cleaning up..."
    archiveHandle = tarfile.TarFile(tarFile)
    archiveHandle.extractall(ihmcSimDir)
    os.remove(destFile)

    print "Distribution update complete!"
    return

main()
