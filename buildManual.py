#! /usr/bin/env python
# -*- coding: utf-8 -*-
#elyxer.py post processing to ensure equation numbers can jump from page to page (eqref)
#Also includes macros from lyx, delete list of macros from top of main html file.
#Finally fix TOC to have collapsible lists
#Add necessary scripts for style like for toc
#Format from collapsible list site
#Remove the TOC from regular files
#Allow to work with index.html
#Fix mathjax in toc
#Make all links https, make sure css files for toc and lyx correctly linked to parent folder
#Make sure links in main pages work properly and affect whole page not just frame
#Change title in toc files
#Now included YAML front stuff, removed old html lines
#Run AFTER running Gerard's version of elyxer.py
#Jay Shim 2019.10.25

# This is ugly, but it's the simplest way to call this from another script
# without needing to refactor
import glob, os, copy
from elyxer import convertdoc

lyxFiles = glob.glob("*.lyx")

if len(lyxFiles) == 0:
    print("Could not find .lyx file in current directory.")
    exit()
else:
    manualName = lyxFiles[0].split('.lyx')[0]
    
# Remove old html files
oldHtmlFiles = glob.glob("*.html")
for oldFile in oldHtmlFiles:
    os.remove(oldFile)
    
# Make html name
if "FEBioStudio" in manualName:
    htmlName = "FSM"
elif "Theory" in manualName:
    htmlName = "TM"
else:
    htmlName = "UM"
    
# Get Version number from lyx file
with open(manualName + ".lyx", "r") as manual:
    lines = manual.readlines()
    
    found = False
    for line in lines:
        if "Version" in line:
            splitVersion = line.split("Version")
            htmlName += splitVersion[-1].strip().replace(".", "")
            found = True
            break
            
    if not found:
        print("Could not version number in " + manualName + ".lyx")
        exit()
    
# Run elyxer on this file
args = ["", "--splitpart", "4", "--mathjax", "remote", "--nofooter", manualName + ".lyx", htmlName + ".html"]
convertdoc(args)

#Get file names for all html files (assuming they are all relevant. Is a list
files = glob.glob('*.html')
files.sort()
if 'index.html' in files:
    files.remove('index.html')


####################################################
#Reference should be in format:
#<a href="test-2.html#mjx-eqn-eqideal-fluid">(30)</a>
#originally \eqref{eq:ideal-fluid}
#Above is representative example
####################################################

#Make class for inserting entries to master list (make tuple list)
class EquationList:
    def __init__(self, filename, equationref, number):
        self.name = filename
        self.eqn = equationref
        self.number = number
    def __repr__(self):
        return repr((self.name, self.eqn, self.number))
    def __getitem__(self, index):
        return

#Initialize master list
masterList = []

#Get masterlist
#Run for each html file
#Scan each line, check to see if there is label for eqn
#Extract eqn reference
#Add file name, eqn reference, number of eqn of page tuple to master list
for i in range(len(files)):
    htmlfile = files[i]
    with open(htmlfile) as fp:
        line = fp.readline()
        eqnCount = 1
        while line:
            if (line.find('label{eq') > 0):
                splitLine = line.split('label{')
                if len(splitLine)>1:
                    splitLine = splitLine[1][0:-2]
                else:
                    splitLine = splitLine[0][0:-2]
                masterList.append(EquationList(htmlfile,splitLine,eqnCount))
                eqnCount += 1
            line = fp.readline()

#Check master list, test code
#print masterList

#Make second master list, change eqn ref to one valid in html using math jax
masterList2 = copy.deepcopy(masterList)

for j in range(len(masterList2)):
    newEqn = masterList[j].eqn
    newEqn = newEqn.split(':')
    if len(newEqn) > 1:
        newEqn2 = 'mjx-eqn-' + newEqn[0] + newEqn[1]
    else:
        newEqn2 = 'mjx-eqn-' + newEqn[0]
    masterList2[j].eqn = newEqn2

#Check master list 2, test code
#print masterList2

#Find the main page name
numberSplits = 10000000
mainPage = files[0]
for j in range(len(files)):
    page = files[j]
    num = len(page.split('-'))
    if numberSplits > num:
        numberSplits = num
        mainPage = page
#print mainPage

#Find number of chapters (get Bib order)
numChaps = 0
for j in range(len(files)):
    page = files[j]
    if ('Chapter' in page):
        numChaps += 1
#print numChaps

#Find number of chapters (get Bib order)
numAppx = 0
for j in range(len(files)):
    page = files[j]
    if ('Appendix' in page):
        numAppx += 1
#print numChaps


#Get title of toc html
splitMain = mainPage.split('.')
tocFile = splitMain[0] + '-toc.' + splitMain[1]
outputTocFile = splitMain[0] + '-toc-edited.' + splitMain[1]

#Remove toc file from list of files, toc file changed later.
if tocFile in files:
    files.remove(tocFile)

#Find the macros and make a list to include in other pages
macrosList = []
with open(mainPage) as mp:
    keepLooking = 1
    isMacro = 0
    while keepLooking == 1:
        line = mp.readline()
        if (line.find('Unindented') > 0):
            isMacro = 1
        while isMacro == 1:
            if (line.find('text{') < 0):
                macrosList.append(line)
            if (line.find('/div') > 0):
                isMacro = 0
                keepLooking = 0
            line = mp.readline()

#Delete macro list if they are not MathJax macros
if (macrosList[1].find('MathJax')<0):
    del macrosList[:]
#print macrosList

#If we have equation reference string, find index in master list
def findMasterIndex(eqnRef):
    index = 0
    for k in range(len(masterList)):
        if eqnRef == masterList[k].eqn:
            index = k
            break
    return index

#Write new reference for html files, replacing old \eqref
#For now even if eqref in same page as original equation
#Put each line in a temp file that replaces old file.
for i in range(len(files)):

    #Make output file names, files that will eventually replace original
    htmlfile = files[i]
    splitHtml = htmlfile.split('.html')
    outputFile = splitHtml[0] + '-edited.html'
    placeMacro = 0
    deleteToc = 0

    #Info about each page
    pageTitle = ''
    parent = ''
    child = ''
    mainPageTitle = ''

    #print htmlfile

    #Get Main Page title
    if ('TM' in mainPage):
        mainPageTitle = 'FEBio Theory Manual'
        mainNavOrder = 3
    elif ('UM' in mainPage):
        mainPageTitle = 'FEBio User Manual'
        mainNavOrder = 4
    else:
        mainPageTitle = 'FEBio Studio Manual'
        mainNavOrder = 2

    #For parent file and bibliography
    if (htmlfile == mainPage):
        pageTitle = mainPageTitle
        parent = ''
        child = 'Chapter'

    #For all other cases, go through files once
    ##Get page title and if have children/what is parent
    with open(htmlfile) as fp:
        scanLine = fp.readline()
        while scanLine:
        #Get name of page
            if ((htmlfile != mainPage) and 'Bibliography' not in htmlfile):
                if (('<a class="toc' in scanLine) and ('Paragraph' not in scanLine)):
                    splitscanLine = scanLine.split('-')
                    levelSec = splitscanLine[1]
                    splitscanLine2 = splitscanLine[2].split('">')
                    levelNum = splitscanLine2[0]
                    levelName = ''
                    #print levelSec
                    #print levelNum
                    
                    #Take into account if there is Mathjax or not
                    if ('<span class="MathJax_Preview">' in scanLine):
                        
                        splitscanLineName = scanLine.split('</a> ')
                        levelName = splitscanLineName[1].strip('\n')
                        
                        scanLine2 = fp.readline()
                        
                        while('<a class="Label"' not in scanLine2 and '</h' not in scanLine2):
                            levelName += scanLine2.strip()
                            scanLine2 = fp.readline()
                            
                            
                        if('<a class="Label"' in scanLine2):
                            levelName += scanLine2.split('<a')[0]
                            
                    else:
                        splitscanLineName = scanLine.split('</a> ')
                        #print splitscanLine
                        splitscanLineName2 = splitscanLineName[1].split('<a class="Label"')
                        levelName = splitscanLineName2[0]
                    
                    pageTitle = levelSec + ' ' + levelNum + ' ' +  levelName
                    
                #get parent name
                if ('<span class="up"><a class="up" name="up" href=' in scanLine):
                    #print scanLine
                    splitParent = scanLine.split('</a> ')
                    #print splitParent
                    splitParent2 = splitParent[1].split('</span>')
                    parent = splitParent2[0]
                    if ('MathJax_Preview' in parent):
                        parent = parent + '</span>'
                
                #get child level
                if ('<span class="next' in scanLine):
                    splitParent = scanLine.split('>')
                    splitParent2 = splitParent[1].split(' ')
                    child = splitParent2[0]
            
            scanLine = fp.readline()

    #print pageTitle
    #print mainPageTitle
    #print parent
    #print child

    #If parent has colon, remove
    if (':' in parent):
        parent2 = parent.split(':')
        parent = parent2[0] + parent2[1]

    #If pageTitle has colon remove
    if (':' in pageTitle):
        pageTitle2 = pageTitle.split(':')
        pageTitle = pageTitle2[0]
        if (len(pageTitle2) > 1):
            for i in range(1,len(pageTitle2)):
                pageTitle = pageTitle + pageTitle2[i]

    #Remove Section/subsection names
    parent = parent.replace("Section ", "")
    parent = parent.replace("Subsection ", "")
    parent = parent.replace("Subsubsection ", "")
    parent = parent.replace("Subsubssubection ", "")
    
    pageTitle = pageTitle.replace("Section ", "")
    pageTitle = pageTitle.replace("Subsection ", "")
    pageTitle = pageTitle.replace("Subsubsection ", "")
    pageTitle = pageTitle.replace("Subsubssubection ", "")

    #Open original files, go through each line
    with open(htmlfile) as fp:
        line = fp.readline()
        while line:
            wholeLine = line

            #check to see if lines have xml,html headding
            #replace with yaml
            if ('<?xml version' in wholeLine):
                wholeLine = '---\n'

            if ('!DOCTYPE html' in wholeLine):
                wholeLine = 'layout: page\n'

            #Fill in rest of YAML lines, using info about page extracted before
            if ('html xmlns' in wholeLine):
                if (htmlfile == htmlName + ".html"):
                    wholeLine = 'title: ' + pageTitle + '\n' + 'nav_order: ' + str(mainNavOrder) + '\n' + 'has_children: ' + 'true\n' + '---\n'
                        #print wholeLine
                else:
                    splitName = htmlfile.split(htmlName + "-")
                    splitName = splitName[1].split('.html')
                    
                    if ('Chapter' in splitName[0]):
                        splitName2 = splitName[0].split('-')
                        navOrder = int(splitName2[-1])
                        hadChild = 'false'
                        parent = mainPageTitle
                        if (child == 'Section'):
                            hadChild = 'true'
                        wholeLine = 'title: ' + pageTitle.strip('\n') + '\n' + 'parent: ' + parent + '\n' + 'nav_order: ' + str(navOrder) + '\n' + 'has_children: ' + hadChild + '\n' + '---\n'
                        #print wholeLine
                    elif ('Appendix' in splitName[0]):
                        # Get navOrder
                        # This gets the appendix letter
                        currentAppx = pageTitle.split(" ")[1]
                        # ord('A') is 65
                        navOrder = numChaps + ord(currentAppx) - 64

                        parent =  mainPageTitle
                        hadChild = 'false'
                        if (child == 'Section'):
                            hadChild = 'true'
                        
                        wholeLine = 'title: ' + pageTitle.strip('\n') + '\n' + 'parent: ' + parent + '\n' + 'nav_order: ' + str(navOrder) + '\n' + 'has_children: ' + hadChild + '\n' + '---\n'
                        #print wholeLine
                    elif ('Bibliography' in splitName[0]):
                        navOrder = numChaps + numAppx +1
                        parent =  mainPageTitle
                        pageTitle = "Bibliography"
                        wholeLine = 'title: ' + pageTitle.strip('\n') + '\n' + 'parent: ' + parent + '\n' + 'nav_order: ' + str(navOrder) + '\n' + 'has_children: ' + 'false\n' + '---\n'
                        #print wholeLine
                    else:
                        splitName2 = splitName[0].split('-')
                        splitName3 = splitName[0].split('.')
                        
                        #Fix for ones without names
                        navOrder = int(splitName3[-1])
                        hadChild = 'false'
                        
                        if (splitName2[0] in child):
                            hadChild = 'true'
                        elif (len(splitName3)==3 and ('Subsubsection' in child)):
                            hadChild = 'true'
                        elif (len(splitName3)==4 and ('Subsubsubsection' in child)):
                            hadChild = 'true'
                        elif (len(splitName3)==5 and ('Subsubsubsubsection' in child)):
                            hadChild = 'true'
                        wholeLine = 'title: ' + pageTitle.strip('\n') + '\n' + 'parent: ' + parent + '\n' + 'nav_order: ' + str(navOrder) + '\n' + 'has_children: ' + hadChild + '\n' + '---\n'
                        #print wholeLine

            if ('</html>' in wholeLine):
                wholeLine = ''

            #If there is an eqref, replace with above reference
            #Takes into account different numbers of eqref in the line.
            if (line.find('eqref') > 0):
                splitLine = line.split('\eqref{')
                if len(splitLine)>2:
                    for i in range(1,len(splitLine)):
                        splitLine2 = splitLine[i].split('}')
                        eqnRef = splitLine2[0]
                        index = findMasterIndex(eqnRef)
                        secName1 = masterList2[index].name.split('-')
                        secName2 = secName1[len(secName1)-1].split('.h')
                        secName = secName2[0]
                        if i == 1:
                            wholeLine = splitLine[0] + '<a href="'+ masterList2[index].name + '#' + masterList2[index].eqn + '">(' + secName + '-' + str(masterList2[index].number) + ')</a>' + splitLine2[1]
                        else:
                            wholeLine += '<a href="'+ masterList2[index].name + '#' + masterList2[index].eqn + '">(' + secName + '-' + str(masterList2[index].number) + ')</a>' + splitLine2[1]
                elif len(splitLine) == 2:
                    splitLine2 = splitLine[1].split('}')
                    eqnRef = splitLine2[0]
                    index = findMasterIndex(eqnRef)
                    secName1 = masterList2[index].name.split('-')
                    secName2 = secName1[len(secName1)-1].split('.h')
                    secName = secName2[0]
                    wholeLine = splitLine[0] + '<a href="'+ masterList2[index].name + '#' + masterList2[index].eqn + '">(' + secName + '-' + str(masterList2[index].number) + ')</a>' + splitLine2[1]
                else:
                    splitLine2 = splitLine[0].split('}')
                    eqnRef = splitLine2[0]
                    index = findMasterIndex(eqnRef)
                    secName1 = masterList2[index].name.split('-')
                    secName2 = secName1[len(secName1)-1].split('.h')
                    secName = secName2[0]
                    wholeLine = '<a href="'+ masterList2[index].name + '#' + masterList2[index].eqn + '">(' + secName + '-' + str(masterList2[index].number) + ')</a>' + splitLine2[1]

            #Remove the \text for macros (meant for main page)
            if (wholeLine.find('text{') > 0) and placeMacro>0 and htmlfile==mainPage:
                wholeLine = ''

            #Make sure links to URL on main pages are fixed and change whole page not just frame
            if (wholeLine.find('a href="http') > 0) and (wholeLine.find('mathjax') < 0) and htmlfile==mainPage:
                linkSplit = wholeLine.split('">')
                n = 0
                wholeLine = ''
                while n < (len(linkSplit)-1):
                    wholeLine = wholeLine + linkSplit[n] + '" ' + 'target="_top' + '">'
                    n = n+1
                wholeLine = wholeLine + linkSplit[len(linkSplit)-1]

            #Ensure that all links start with https not just http. Except for lyx.css
            if (wholeLine.find('http:')>0) and (wholeLine.find('lyx.css')<0):
                httpSplit = wholeLine.split('http')
                wholeLine = ''
                for n in range(len(httpSplit)-1):
                    wholeLine = wholeLine + httpSplit[n] + 'https'
                wholeLine = wholeLine + httpSplit[len(httpSplit)-1]

            #Use local lyx.css
            if (wholeLine.find('http:')>0) and (wholeLine.find('lyx.css')>0):
                httpSplit = wholeLine.split('http://elyxer.nongnu.org')
                wholeLine = httpSplit[0] + '..' + httpSplit[1]

            #Remove the toc from regular pages, turn on bool, start deleting each line
            if (deleteToc == 0) and (wholeLine.find('div class="fulltoc"') > 0):
                deleteToc = 1
                wholeLine = ''
            #Turn off delete toc at this point
            if (deleteToc == 1) and (wholeLine.find('div class="splitheader"') > 0):
                deleteToc = 0
            #Delete lines after fulltoc, but before splitheader
            if (deleteToc == 1):
                wholeLine = ''


            #Make sure all titles have mathjax fixed, without ruining formatting
            if(line.find('<span class="MathJax_Preview">\\')>0):
                splitToc1 = wholeLine.split('<span class="MathJax_Preview">')
                splitToc2 = splitToc1[-1].split('</span>')
                wholeLine = splitToc1[0] + '<span class="MathJax_Preview"><script type="math/tex">' +splitToc2[0] + '</script></span>'
                for n in range(1,len(splitToc2)):
                    wholeLine = wholeLine + splitToc2[n] + '</span>'

            #Remove \thinspace
            if (wholeLine.find('thinspace') > 0):
                tempSplit = wholeLine.split('thinspace')
                wholeLine = tempSplit[0][:-1]
                for n in range(1,len(tempSplit)):
                    if n == len(tempSplit)-1:
                        wholeLine += tempSplit[n]
                    else:
                        wholeLine += tempSplit[n][:-1]
                        
            #Fix \obslash symbol
            if("\\obslash" in wholeLine):
                wholeLine = wholeLine.replace("\\obslash", "⦸")
                
            #Remove \mathnormal instruction
            if("\\mathnormal" in wholeLine):
                wholeLine = wholeLine.replace("\\mathnormal", "")

            #Change macro counter. once reach 2, delay by one line
            if (wholeLine.find('class="up"') > 0) and placeMacro == 0:
                placeMacro = 1
            if (wholeLine.find('/div') > 0) and placeMacro == 1:
                placeMacro = 2

            #Write wholeline into new file, also macros in the right place
            with open(outputFile, 'a') as fop:
                fop.write(wholeLine)
                if placeMacro == 2 and htmlfile!=mainPage:
                    fop.writelines(macrosList)
                    placeMacro = -1
            #Keep going through original html file
            line = fp.readline()

    #Replace old html files with new one
    os.remove(htmlfile)
    os.rename(outputFile,htmlfile)

# #Get lines for script
# scriptList = []
# scriptList.append('<script>var runOnLoad=function(c,o,d,e){function x(){for(e=1;c.length;)c.shift()()}o[d]?(document[d](\'DOMContentLoaded\',x,0),o[d](\'load\',x,0)):o.attachEvent(\'onload\',x);return function(t){e?o.setTimeout(t,0):c.push(t)}}([],window,\'addEventListener\');</script>\n')
# scriptList.append('<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Patua+One%7COpen+Sans:400,400italic" type="text/css">\n')
# #Make sure style sheet is in right place edit dd, dl indent, also clip overflow, add scroll bar
# scriptList.append('<link rel="stylesheet" href="../stylesheet.css" type="text/css">\n')
# scriptList.append('<script type="text/javascript" src="../CollapsibleLists.js"></script>\n')
# scriptList.append('<script type=\"text/javascript\">\nrunOnLoad(function(){ CollapsibleLists.apply(); });\n</script>\n')
# # adds treeview, kept the same
# scriptList.append('<style type="text/css">\n.treeView{\n-moz-user-select:none;\nposition:relative;\n}\n.treeView ul{\nmargin:0 0 0 -1.5em;\npadding:0 0 0 1.5em;\n}\n.treeView ul ul{\nbackground:url(\'../list-item-contents.png\') repeat-y left;\n}\n.treeView li.lastChild > ul{\nbackground-image:none;\n}\n.treeView li{\nmargin:0;\npadding:0;\nbackground:url(\'../list-item-root.png\') no-repeat top left;\nlist-style-position:inside;\nlist-style-image:url(\'../button.png\');\ncursor:auto;\n}\n.treeView li.collapsibleListOpen{\nlist-style-image:url(\'../button-open.png\');\ncursor:pointer;\n}\n.treeView li.collapsibleListClosed{\nlist-style-image:url(\'../button-closed.png\');\ncursor:pointer;\n}\n.treeView li li{\nbackground-image:url(\'../list-item.png\');\npadding-left:1.5em;\n}\n.treeView li.lastChild{\nbackground-image:url(\'../list-item-last.png\');\n}\n.treeView li.firstElement{\nurl(\'../list-item-root.png\') no-repeat top left;\n}\n.treeView li.collapsibleListOpen{\nbackground-image:url(\'../list-item-open.png\');\n}\n.treeView li.collapsibleListOpen.lastChild{\nbackground-image:url(\'../list-item-last-open.png\');\n}\n.treeView li.collapsibleListOpen.firstElement{\nbackground:url(\'../list-item-root.png\') no-repeat top left;\n}\n</style>\n')


# ~ #Get lines for toc, also allow for mathjax in toc entries
# ~ tocList = []
# ~ with open(tocFile) as mp:
    # ~ line = mp.readline()
    # ~ while line:

        # ~ #Ensure correct title MAY NEED TO CHANGE IN LATER ITERATIONS
        # ~ if (line.find('Converted document')>0):
            # ~ titleSplit = line.split('Converted document')
            # ~ line = titleSplit[0] + 'FEBio User Manual Version 2.9' + titleSplit[1]
        # ~ if (line.find('Version 2.1')>0):
            # ~ titleSplit = line.split('Version 2.1')
            # ~ line = titleSplit[0] + 'PreView Manual Version 2.1' + titleSplit[1]

        # ~ #Get each toc element for toc list
        # ~ if (line.find('a class="Link"')>0):
            # ~ if(line.find('span class')>0):
                # ~ splitToc1 = line.split('<span class="MathJax_Preview">')
                # ~ splitToc2 = splitToc1[-1].split('</span>')
                # ~ line = splitToc1[0] + '<span class="MathJax_Preview"><script type="math/tex">' +splitToc2[0] + '</script></span>' + splitToc2[-1]
            # ~ tocList.append(line)
        # ~ line = mp.readline()

# ~ #print tocList

# ~ #Get array for order of toc
# ~ #order based on order of what appears
# ~ tocListOrder = numpy.zeros(len(tocList))
# ~ for i in range(len(tocList)):
    # ~ if (tocList[i].find('-Chapter-')>0) or (tocList[i].find('Bibliography')>0) or (tocList[i].find('-Appendix-')>0):
        # ~ tocListOrder[i] = 1
    # ~ elif (tocList[i].find('-Section-')>0):
        # ~ tocListOrder[i] = 2
    # ~ elif (tocList[i].find('-Subsection-')>0):
        # ~ tocListOrder[i] = 3
    # ~ elif (tocList[i].find('-Subsubsection-')>0):
        # ~ tocListOrder[i] = 4
    # ~ elif (tocList[i].find('-Subsubsubsection-')>0):
        # ~ tocListOrder[i] = 5
    # ~ elif (tocList[i].find('-Subsubsubsubsection-')>0):
        # ~ tocListOrder[i] = 6
    # ~ else:
        # ~ tocListOrder[i] = 0

# ~ #print tocListOrder

# ~ #Make new collapsible toc list
# ~ newTocList = []
# ~ #Check if certain levels have appeared (each ul)
# ~ highestNumList = 0
# ~ linkJava = 0
# ~ #Check each case and put in according html
# ~ for i in range(len(tocList)-1):
    # ~ if tocListOrder[i] == 0:
        # ~ #newTocList.append('<ul class="treeView collapsibleList">\n')
        # ~ newTocList.append('<ul class="treeView">\n')
        # ~ newTocList.append('<li class="firstElement">'+tocList[i])
    # ~ elif tocListOrder[i] < tocListOrder[i+1]:
        # ~ if highestNumList < tocListOrder[i]:
            # ~ if tocListOrder[i] == 1 and linkJava == 0:
                # ~ newTocList.append('<ul class="collapsibleList">\n')
                # ~ linkJava = 1
            # ~ else:
                # ~ newTocList.append('<ul>\n')
            # ~ highestNumList = highestNumList + 1
        # ~ # Check if last child
        # ~ isLastChild = 0
        # ~ for j in range(1,len(tocList)-i):
            # ~ if tocListOrder[i] == tocListOrder[i+j]:
                # ~ isLastChild = 0
                # ~ break
            # ~ elif tocListOrder[i] > tocListOrder[i+j]:
                # ~ isLastChild = 1
                # ~ break
            # ~ if j == len(tocList)-i-1:
                # ~ isLastChild = 1
        # ~ if isLastChild == 1:
            # ~ newTocList.append('<li class="lastChild">'+tocList[i])
        # ~ else:
            # ~ newTocList.append('<li>'+tocList[i])
    # ~ elif (tocListOrder[i] == tocListOrder[i+1]) and (tocListOrder[i-1] < tocListOrder[i]):
        # ~ if tocListOrder[i] == 1 and linkJava == 0:
            # ~ newTocList.append('<ul class="collapsibleList">\n')
            # ~ linkJava = 1
        # ~ else:
            # ~ newTocList.append('<ul>\n')
        # ~ newTocList.append('<li>'+tocList[i]+'</li>\n')
        # ~ highestNumList = highestNumList + 1
    # ~ elif (tocListOrder[i] == tocListOrder[i+1]) and (tocListOrder[i-1] >= tocListOrder[i]):
        # ~ newTocList.append('<li>'+tocList[i]+'</li>\n')
    # ~ elif tocListOrder[i] > tocListOrder[i+1]:
        # ~ if tocListOrder[i-1] < tocListOrder[i]:
            # ~ newTocList.append('<ul>\n')
            # ~ highestNumList = highestNumList + 1
        # ~ newTocList.append('<li class="lastChild">'+tocList[i]+'</li>\n')
        # ~ for j in range(abs(int(tocListOrder[i] - tocListOrder[i+1]))):
            # ~ newTocList.append('</ul>\n')
            # ~ newTocList.append('</li>\n')
            # ~ #List is "closed"
            # ~ highestNumList = highestNumList - 1
    # ~ else:
        # ~ newTocList.append('<li>'+tocList[i]+'</li>\n')


# ~ newTocList.append('<li class="lastChild">'+tocList[len(tocList)-1]+'</li>\n')

# ~ #Last toc item
# ~ for j in range(int(tocListOrder[len(tocList)-1])):
    # ~ newTocList.append('</ul>\n')
    # ~ newTocList.append('</li>\n')
# ~ newTocList.append('</ul>\n')
# ~ newTocList.append('</body>\n')
# ~ newTocList.append('</html>\n')

# ~ #print newTocList

# ~ placeScript = 0
# ~ placeToc = 0
# ~ #Open original files, go through each line
# ~ with open(tocFile) as fp:
    # ~ line = fp.readline()
    # ~ while line:
        # ~ wholeLine = line

        # ~ #Look for this line that use old toc.css or lyx.css and make comment
        # ~ if (wholeLine.find('toc.css') > 0):
            # ~ wholeLine = '\n'
        # ~ if (wholeLine.find('lyx.css') > 0):
            # ~ wholeLine = '\n'

        # ~ #Ensure that all links start with https not just http. Except for lyx.css
        # ~ if (wholeLine.find('http:')>0) and (wholeLine.find('lyx.css')<0):
            # ~ httpSplit = wholeLine.split('http')
            # ~ wholeLine = ''
            # ~ for n in range(len(httpSplit)-1):
                # ~ wholeLine = wholeLine + httpSplit[n] + 'https'
            # ~ wholeLine = wholeLine + httpSplit[len(httpSplit)-1]

        # ~ #Look for where we have to add scripts
        # ~ if (wholeLine.find('</title>')>0) and placeScript == 0:
            # ~ placeScript = 1

        # ~ #Look for where we have to add toc
        # ~ if (wholeLine.find('/noscript')>0) and placeToc == 0:
            # ~ placeToc = 1

        # ~ if placeToc == 2:
            # ~ wholeLine = ''

        # ~ #Write wholeline into new file, also scripts in right place
        # ~ with open(outputTocFile, 'a') as fop:
            # ~ fop.write(wholeLine)

            # ~ if placeScript == 1:
                # ~ fop.writelines(scriptList)
                # ~ placeScript = 2

            # ~ if placeToc == 1:
                # ~ fop.writelines(newTocList)
                # ~ placeToc = 2
        # ~ #Keep going through original html file
        # ~ line = fp.readline()

# ~ #Replace old toc files with new one
# ~ os.remove(tocFile)
# ~ os.rename(outputTocFile,tocFile)
