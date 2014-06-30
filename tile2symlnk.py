# -*- encoding: utf-8 -*-
import os
import sys
import shutil
import pwd
import fnmatch
from PIL import Image
import ConfigParser

class Tile2Symlnk(object):
    def __init__(self):
        """
        Constructor
        """
        config = ConfigParser.ConfigParser()
        config.readfp(open('config.cfg'))
        self.startDir = config.get('Config','startDir')
        self.symlinkDir = config.get('Config','symlinkDir')
        self.imgFormat = config.get('Config','imgFormat')
        self.user = config.get('Config','user')
        self.group = config.get('Config','group')

        self.imgFiles = self.getAllImageFiles()
        self.singleImageDict = self.getAllSingleColorFiles()

        self.userID = None
        self.groupID = None

    def getAllImageFiles(self):
        """
        Gets absolute path of all images (tiles) from defined directory (recursively)

        Returns:
            a list with all of the image files (tiles) in directory
            defined in startDir variable.
        """
        f = [os.path.join(dirpath, f)
            for dirpath, dirnames, files in os.walk(self.startDir)
            for f in fnmatch.filter(files, '*.' + self.imgFormat)]

        return f

    def getAllSingleColorFiles(self):
        """
        Gets absolute path of all existing single color files (tiles) in directory
        defined in symlinkDir variable.
        Single color files are named for example blank_254255255.jpeg

        Returns:
            a dictionary with all of the existing single color files (tiles).
            key -- 255255255
            value -- absolute path of tile
        """
        singleDict = {}
        for file in os.listdir(self.symlinkDir):
            if 'blank_' in file:
                ## ex. blank_254255255.jpeg
                rgbColor = file.split('_')[1].split('.')[0]

                singleDict[rgbColor] = os.path.join(self.symlinkDir, file)

        return singleDict


    def update_progress(self, progress):
        """
        Displays or updates a console progress bar.
        From http://stackoverflow.com/a/15860757

        Any int will be converted to a float.
        A value under 0 represents a 'halt'.
        A value at 1 or bigger represents 100%

        Args:
            progress: float between 0 and 1.
        Returns:
            updates a console progress bar by
        """
        ## Modify this to change the length of the progress bar
        barLength = 10
        status = ""
        if isinstance(progress, int):
            progress = float(progress)
        if not isinstance(progress, float):
            progress = 0
            status = "error: progress var must be float\r\n"
        if progress < 0:
            progress = 0
            status = "Halt...\r\n"
        if progress >= 1:
            progress = 1
            status = "Done...\r\n"
        block = int(round(barLength*progress))
        text = "\rPercent: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), progress*100, status)
        sys.stdout.write(text)
        sys.stdout.flush()

    def isEverthingOk(self):
        """
        Checks if everything is in right place

        Returns:
            False if something is wrong
            True if everything is ok
        """

        ## chech if user and group exist on system
        try:
            self.userID = pwd.getpwnam(self.user)
            self.groupID = pwd.getpwnam(self.group)
        except KeyError:
            print "User %s or group %s does not exist. Script stopped !"%(self.user, self.group)
            return False

        ## chech if starting directory and directory containing single color tiles exist
        if not os.path.exists(self.startDir) or not os.path.exists(self.symlinkDir):
            print "%s or %s does not exist. Script stopped !"%(self.startDir, self.symlinkDir)
            return False

        ## if everything is ok, return True
        return True

    def run(self):
        """
        Starting point of script.
        """

        ## if there is something wrong with setup, exit script
        if self.isEverthingOk() is False:
            sys.exit()

        numOfFiles = len(self.imgFiles)

        ## get an ID of user and group
        userid = pwd.getpwnam(self.user)[2]
        groupid = pwd.getpwnam(self.group)[3]

        if numOfFiles == 0:
            print "No tiles found in %s !"%(self.startDir, )
            sys.exit()

        print "Number of tiles found: %s"%(str(numOfFiles), )

        counter = 0.0
        counterForLinked = 0

        for file in self.imgFiles:
            ## check if file is a link allready or not
            ## skip if it is allready link
            if not os.path.islink(file):
                img = Image.open(file)

                ## ex. tileColors[0] = (65536, (254, 255, 255))
                tileColors = img.getcolors()

                ## tiles with many colors will result in None and tiles with single color
                ## will result in list with only one element
                if tileColors and len(tileColors) == 1:
                    ## first we convert RGB integers to string then join
                    ## ex. colorKey = '254255255'
                    colorKey = ''.join([str(i) for i in tileColors[0][1]])
                    if not self.singleImageDict.has_key(colorKey):
                        newBlankImage = os.path.join(self.symlinkDir, 'blank_%s.jpeg'%(colorKey, ))
                        ## copy newly found single color tile to SYMLINK_DIR
                        shutil.copy2(file, newBlankImage)
                        self.singleImageDict[colorKey] = newBlankImage

                        # ## we set ownership of newly created single color tile
                        os.chown(newBlankImage, userid, groupid)
                        os.chmod(newBlankImage, 0644)

                    os.remove(file)
                    os.symlink(self.singleImageDict[colorKey], file)

                    counterForLinked += 1

            counter += 1
            self.update_progress(counter/numOfFiles)

        print 'Number of tiles symlinked: %s'%(str(counterForLinked), )


#-------------------------------
if __name__ == "__main__":
    tile2SymlnkObj = Tile2Symlnk()

    tile2SymlnkObj.run()


