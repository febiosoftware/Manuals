import ftplib, os

server = os.environ['FTP_SERVER']
username = os.environ['FTP_USERNAME']
password = os.environ['FTP_PASSWORD']


def putRecursive(path, remoteDirname):
    ftp = ftplib.FTP(server, username, password)

    try:
        ftp.mkd(remoteDirname)
    except ftplib.error_perm:
        print("Warning: " + remoteDirname + " already exists")

    ftp.cwd(remoteDirname)

    currentDir = os.getcwd()
    os.chdir(path)

    for root, dirs, files in os.walk('.'):
        for dir in dirs:
            try:
                ftp.mkd(os.path.join(root, dir))
            except ftplib.error_perm:
                print("Warning: " + os.path.join(root, dir) + " already exists")

        for file in files:
            print(os.path.join(root, file))
            ftp.storbinary('STOR ' + os.path.join(root, file), open(os.path.join(root, file), 'rb'))

    os.chdir(currentDir)

    ftp.quit()

def deleteDirRecursive(ftp, path):
    try:
        ftp.cwd(path)
        for name in ftp.nlst():
            deleteDirRecursive(ftp, name)
    except ftplib.error_perm:
        ftp.delete(path)
        return
    
    ftp.cwd('..')
    ftp.rmd(path)    

def deleteRemoteDir(path):
    ftp = ftplib.FTP(server, username, password)
    deleteDirRecursive(ftp, path)
    ftp.quit()
