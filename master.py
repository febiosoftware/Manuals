import subprocess, os, shutil, glob
# from buildManual import buildMan 

# Clone the FEBio and FEBioStudio repositories
FEBIO_GIT = "https://github.com/febiosoftware/FEBio.git"
FBS_GIT = "https://github.com/febiosoftware/FEBioStudio.git"

subprocess.call(["git", "clone", "--branch", "master", "--depth", "1", FEBIO_GIT])
subprocess.call(["git", "clone", "--branch", "master", "--depth", "1", FBS_GIT])

# Get the version numbers
out = subprocess.check_output(["git", "-C", "FEBio", "describe"]).replace("v", "").split('.')
FEBIO_MAJOR = out[0].strip()
FEBIO_MINOR = out[1].strip()

out = subprocess.check_output(["git", "-C", "FEBioStudio", "describe"]).replace("v", "").split('.')
FBS_MAJOR = out[0].strip()
FBS_MINOR = out[1].strip()

# Set up the directory structure for lyx to html conversion
BASEDIR = os.getcwd() + "/"
LYX_DIR = BASEDIR + "lyx/"
FBS_LYX_DIR = LYX_DIR + "FEBioStudio/"
FU_LYX_DIR = LYX_DIR + "FEBioUser/"
FT_LYX_DIR = LYX_DIR + "FEBioTheory/"

os.mkdir(LYX_DIR)
os.mkdir(FBS_LYX_DIR)
os.mkdir(FU_LYX_DIR)
os.mkdir(FT_LYX_DIR)

shutil.copy("FEBioStudio/Documentation/FEBioStudio_User_Manual.lyx", FBS_LYX_DIR)
shutil.copy("FEBioStudio/Documentation/FEBioStudio.bib", FBS_LYX_DIR)
shutil.copytree("FEBioStudio/Documentation/Figures", FBS_LYX_DIR + "Figures")

shutil.copy("FEBio/Documentation/FEBio_User_Manual.lyx", FU_LYX_DIR)
shutil.copy("FEBio/Documentation/FEBio3.bib", FU_LYX_DIR)
shutil.copytree("FEBio/Documentation/Figures", FU_LYX_DIR + "Figures")

shutil.copy("FEBio/Documentation/FEBio_Theory_Manual.lyx", FT_LYX_DIR)
shutil.copy("FEBio/Documentation/FEBio3.bib", FT_LYX_DIR)
shutil.copytree("FEBio/Documentation/Figures", FT_LYX_DIR + "Figures")

# If elyxer is called more than once in a script, it crashes. 
# So we have to call it as a subprocess
os.chdir(FBS_LYX_DIR)
os.system("python2 " + BASEDIR + "buildManual.py")

os.chdir(FU_LYX_DIR)
os.system("python2 " + BASEDIR + "buildManual.py")

os.chdir(FT_LYX_DIR)
os.system("python2 " + BASEDIR + "buildManual.py")

# Set up the directory structure jekyll
JEKYLL_TEMPLATE_DIR = BASEDIR + "JekyllTemplate/"
JEKYLL_DIR = BASEDIR + "jekyll/"
FBS_JEKYLL_DIR = JEKYLL_DIR + "FEBioStudio-" + FBS_MAJOR + "-" + FBS_MINOR + "/"
FU_JEKYLL_DIR = JEKYLL_DIR + "FEBioUser-" + FEBIO_MAJOR + "-" + FEBIO_MINOR + "/"
FT_JEKYLL_DIR = JEKYLL_DIR + "FEBioTheory-" + FEBIO_MAJOR + "-" + FEBIO_MINOR + "/"

os.mkdir(JEKYLL_DIR)

def copyHTMLFiles(srcDir, destDir):
    for file in glob.glob(srcDir + "*.html"):
        shutil.copy(file, destDir)

shutil.copytree(JEKYLL_TEMPLATE_DIR, FBS_JEKYLL_DIR)
shutil.copy(FBS_LYX_DIR + "FEBioStudio.bib", FBS_JEKYLL_DIR)
shutil.copytree(FBS_LYX_DIR + "Figures", FBS_JEKYLL_DIR + "Figures")
shutil.copy(BASEDIR + "febioLogo.png", FBS_JEKYLL_DIR + "Figures")
shutil.copy(BASEDIR + "FBSIndex.md", FBS_JEKYLL_DIR + "index.md")
copyHTMLFiles(FBS_LYX_DIR, FBS_JEKYLL_DIR)

shutil.copytree(JEKYLL_TEMPLATE_DIR, FU_JEKYLL_DIR)
shutil.copy(FU_LYX_DIR + "FEBio3.bib", FU_JEKYLL_DIR)
shutil.copytree(FU_LYX_DIR + "Figures", FU_JEKYLL_DIR + "Figures")
shutil.copy(BASEDIR + "febioLogo.png", FU_JEKYLL_DIR + "Figures")
shutil.copy(BASEDIR + "FUIndex.md", FU_JEKYLL_DIR + "index.md")
copyHTMLFiles(FU_LYX_DIR, FU_JEKYLL_DIR)

shutil.copytree(JEKYLL_TEMPLATE_DIR, FT_JEKYLL_DIR)
shutil.copy(FT_LYX_DIR + "FEBio3.bib", FT_JEKYLL_DIR)
shutil.copytree(FT_LYX_DIR + "Figures", FT_JEKYLL_DIR + "Figures")
shutil.copy(BASEDIR + "febioLogo.png", FT_JEKYLL_DIR + "Figures")
shutil.copy(BASEDIR + "FTIndex.md", FT_JEKYLL_DIR + "index.md")
copyHTMLFiles(FT_LYX_DIR, FT_JEKYLL_DIR)

# edit the index.md files to include the version numbers

def editIndexFile(indexFile):
    with open(indexFile, 'r') as file:
        data = file.readlines()

    for i in range(len(data)):
        data[i] = data[i].replace("${fbs_major}", FBS_MAJOR)
        data[i] = data[i].replace("${fbs_minor}", FBS_MINOR)
        data[i] = data[i].replace("${feb_major}", FEBIO_MAJOR)
        data[i] = data[i].replace("${feb_minor}", FEBIO_MINOR)

    with open(indexFile, 'w') as file:
        file.writelines(data)

editIndexFile(FBS_JEKYLL_DIR + "index.md")
editIndexFile(FU_JEKYLL_DIR + "index.md")
editIndexFile(FT_JEKYLL_DIR + "index.md")

# Run jekyll

def runJekyll(jekyllDir, baseURL):
    os.chdir(jekyllDir)
    os.system("bundle install")
    os.system("bundle exec jekyll serve -b" + baseURL)

runJekyll(FBS_JEKYLL_DIR, "/")
# runJekyll(FU_JEKYLL_DIR, "/")
# runJekyll(FT_JEKYLL_DIR, "/")

# runJekyll(FBS_JEKYLL_DIR, "/docs/FEBioStudio-" +  FBS_MAJOR + "-" + FBS_MINOR)
# runJekyll(FU_JEKYLL_DIR, "/docs/FEBioUser-" + FEBIO_MAJOR + "-" + FEBIO_MINOR)
# runJekyll(FT_JEKYLL_DIR, "/docs/FEBioTheory-" + FEBIO_MAJOR + "-" + FEBIO_MINOR)