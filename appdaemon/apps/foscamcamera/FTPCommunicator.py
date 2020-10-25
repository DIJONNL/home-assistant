# https://stackoverflow.com/questions/10042838/delete-all-files-and-folders-after-connecting-to-ftp
# https://stackoverflow.com/questions/17204276/python-ftplib-specify-port

from ftplib import FTP

class FTPCommunicator():

    def __init__(self, server, port, user password):cm 
        self.ftp = FTP()
        self.ftp.connect(server, port=port, timeout=30)
        self.ftp.login(user=user, passwd=password)

    def getDirListing(self, dirName):
        listing = self.ftp.nlst(dirName)
        # If listed a file, return.
        if len(listing) == 1 and listing[0] == dirName:
            return []
        subListing = []
        for entry in listing:
            subListing += self.getDirListing(entry)
        listing += subListing
        return listing

    def removeDir(self, dirName):
        listing = self.getDirListing(dirName)
        # Longest path first for deletion of sub directories first.
        listing.sort(key=lambda k: len(k), reverse=True)
        # Delete files first.
        for entry in listing:
            try:
                self.ftp.delete(entry)
            except:
                pass

        # Delete empty directories.
        for entry in listing:
            try:
                self.ftp.rmd(entry)
            except:
                pass
        self.ftp.rmd(dirName)

    def quit(self):
        self.ftp.quit()

#ftp = FTPCommunicator()
#ftp.removeDir("/Untitled")
#ftp.quit()