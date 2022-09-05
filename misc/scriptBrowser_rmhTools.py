from __future__ import absolute_import
from __future__ import print_function
import maya.cmds as mc
import maya.OpenMaya as om

from importlib import reload
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget
import maya.api.OpenMayaUI  as omui


import random, os, math, pickle
import __main__
import sys
from os import walk
from six.moves import range
from six.moves import zip

try:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
    # print "Using PySide2"
except:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from shiboken import wrapInstance
    # print "Using PySide"
    
import rmhTools_widgets as pw
import PatsMayaMethods as pmm

# folderPaths = [r'C:\_dbDataTmp\_projekte\09_drawWalk\03_mayafiles\scripts',r'C:\_dbDataTmp\_scripts\office_scripts',\
#                                   r'Q:\19_party\03_mayafiles\scripts',r'Q:\20_stutter\03_mayafiles\scripts',\
#                                   r'X:\_dbData\_projekte\14_robot\03_mayafiles\scripts',\
#                                   r'C:\_dbDataTmp\_projekte\14_robot_tmp\03_mayafiles\scripts',\
#                                   r'C:\_dbDataTmp\_projekte\expandedVFX\tutorials\03_mayafiles\scripts']

walkBaseDir = os.path.expanduser('~/maya/scripts/rmhTools')

def walkFolders():
    out = []
    for root, dirs, files in walk(walkBaseDir):
        out.append(root)
    return out

def analyzeFile(filePath = r'Q:\19_party\03_mayafiles\scripts\pfxStrokeTools.py'):
    
    with open(filePath) as fid:
        lines = fid.readlines()
    
    dirName, fName, base, ext  = pw.splitPath(filePath)
    
    out = {'fileName': fName, 'fileDir':dirName, 'functions':[], 'classes':[]}
    for line in lines:
        if len(line) < 3:
            continue
        if line[:3] == 'def':
            spl01 = line.split('(')
            name = spl01[0].split()[-1]
            opts = spl01[-1].split(')')[0]
            out['functions'].append([name, opts, fName])
        
        if line[:3] == 'class':
            spl01 = line.split('(')
            name = spl01.split()[-1]
            out['classes'].append(name, fName)
    return out

def analyzeFolders(folderPaths = [r'C:\_dbDataTmp\_projekte\09_drawWalk\03_mayafiles\scripts',r'C:\_dbDataTmp\_scripts\office_scripts',\
                                  r'Q:\19_party\03_mayafiles\scripts',r'Q:\20_stutter\03_mayafiles\scripts', r'X:\_dbData\_projekte\14_robot\03_mayafiles\scripts',\
                                  r'C:\_dbDataTmp\_projekte\14_robot_tmp\03_mayafiles\scripts',r'C:\_dbDataTmp\_projekte\expandedVFX\tutorials\03_mayafiles\scripts']):
    
    # if os.path.isdir(r'Q:\19_party\03_mayafiles\scripts'):
    #     folderPaths = [r'Q:\20_stutter\03_mayafiles\scripts', r'C:\_dbDataTmp\_projekte\18_remix\03_mayafiles\scripts', r'Q:\19_party\03_mayafiles\scripts', r'C:\_dbDataTmp\_projekte\_tmpScripts', \
    #              r'Q:\20_stutter\03_mayafiles\scripts', r'Q:\expandedVFX\tutorials\03_mayafiles\scripts', r'Q:\19_party\03_mayafiles\scripts']
    # else:
    #     folderPaths = [r'C:\_dbDataTmp\_projekte\17_mmaps\03_mayafiles\scripts', r'C:\_dbDataTmp\_projekte\14_robot_tmp\03_mayafiles\scripts', r'C:\_dbDataTmp\_scripts\office_scripts', \
    #              r'C:\_dbDataTmp\_projekte\14_robot_tmp\03_mayafiles\scripts\clipNotator', r'C:\_dbDataTmp\_projekte\14_robot_tmp\03_mayafiles\scripts\roboUI', r'C:\_dbDataTmp\_projekte\09_drawWalk\03_mayafiles\scripts',\
    #              r'C:\_dbDataTmp\_projekte\18_remix\03_mayafiles\scripts', r'C:\_dbDataTmp\_projekte\_tmpScripts', \
    #              r'C:\_dbDataTmp\_projekte\x_tmpProject\03_mayafiles\scripts',r'C:\_dbDataTmp\_projekte\expandedVFX\tutorials\03_mayafiles\scripts', r'C:\_dbDataTmp\_projekte\19_party\03_mayafiles\scripts', \
    #              r'C:\_dbDataTmp\_projekte\20_stutter\03_mayafiles\scripts']
    # 
    print(folderPaths)
    out = {}
    for folderPath in folderPaths:
        if not os.path.isdir(folderPath):
            mc.warning('%s does not exist'%folderPath)
            continue
        # print folderPath
        os.chdir(folderPath)
        files = [f for f in os.listdir(folderPath) if f[-3:] == '.py' and not '- Kopie' in f]
        # print files
        for f in files:
            # print f
            fpath = os.path.join(folderPath, f)
            dc = analyzeFile(fpath)
            # print dc
            out[f] = dc
    # print out
    return out

def returnAllFunctions(pyFileDict, sort = True, returnOnlyNames = True, excludeList = ['add', 'sub', 'magnitude', 'normalize', 'multiply']):
    allNames = list(pyFileDict.keys())
    allNames.sort()
    
    out = []
    for name in allNames:
        if not pyFileDict[name]['functions']:
            continue
        # print pyFileDict[name]['functions']
        functions = pyFileDict[name]['functions']
        out = out + functions
    
    if sort:
        out.sort(key = lambda x:x[0])
    if returnOnlyNames:
        out = [v[0] for v in out]
        return out
    else:
        return out

def returnDuplicatesInList(inList):
    previous = []
    found = []
    for a in inList:
        if a in previous:
            found.append(a)
        previous.append(a)
    return found

def returnFilesContainingFunction(pyFileDict, fct):
    allNames = list(pyFileDict.keys())
    allNames.sort()
    
    out = []
    for name in allNames:
        functionNames = [v[0] for v in  pyFileDict[name]['functions']]
        if fct in functionNames:
            out.append(name)
    return out

def generateIncludeTextForAll(pyFileDict):
    if type(pyFileDict) == str:
        print('aha')
        pyFileDict = analyzeFile(pyFileDict)
    if 'fileName' in list(pyFileDict.keys()):
        pyFileDict = {pyFileDict['fileName']:pyFileDict}
    print(pyFileDict)
    allNames = list(pyFileDict.keys())
    allNames.sort()
    
    out = []
    for name in allNames:
        functionNames = [v[0] for v in  pyFileDict[name]['functions']]
        
        opts = [v[1] for v in  pyFileDict[name]['functions']]
        moduleName = name.split('.')[0]
        for fct, opt in zip(functionNames, opts):
            inc = ['def %s(self):'%fct, \
                   '    reload(%s)'%moduleName, \
                   '    %s.%s(%s)'%(moduleName,fct, opt) ]
            incTx = '\n'.join(inc)
            out.append(incTx)
    return out

class FunctionsListWidget(QListWidget):
    def __init__(self,mainWidget = None, parent = None):
        super(FunctionsListWidget, self).__init__(parent)
        
        self.mainWidget = mainWidget
        self.itemDoubleClicked.connect(self.showExecuteDialog)
        
        self.currentItemChanged.connect(self.currentItemChangedProc)
        self.loadList()
    
    def pathChangeProc(self, new,prev):
        try:
            self.pathChange.emit(new.fullPath)
        except:
            pass
        
    def selectItem(self, name):
        for row in range(self.count()):
            item = self.item(row)
            if item and item.fname == name:
                self.setCurrentItem(item)
                return
        
    def loadList(self):
        dc01 = analyzeFolders(walkFolders())
        # print ' dsfasf' walkFolders()
        allFunctions = returnAllFunctions(dc01, returnOnlyNames = False)
        self.clear()
        for ar in allFunctions:
            name, opts, fName = ar
            item = QListWidgetItem(name)
            item.functionName = name
            item.opts = opts
            item.pyFileName = fName
            self.addItem(item)
            
        # self.mainWidget.update()
    
    def showAll(self):
        for row in range(self.count()):
            item = self.item(row)
            item.setHidden(0)
        
        
    def filterList(self, filterText):
        for row in range(self.count()):
            item = self.item(row)
            name = str(item.text())
            if filterText.lower() in name.lower():
                item.setHidden(0)
            else:
                item.setHidden(1)
            
    def returnNameList(self):
        out = []
        for row in range(self.count()):
            item = self.item(row)
            name = str(item.text()) 
            out.append(name)
        return out
    
    def getCurrentItemText(self):
        if self.count() > 0:
            item = self.item(self.currentRow())
            return str(item.text())
    
    def selectObjectFromItem(self, item):
        if item:
            mc.select(str(item.text()))
        
    def currentItemChangedProc(self, current, previous):
        name = str(current.text())
        opts = current.opts
        pyFileName = current.pyFileName
        tx = '\n'.join([name, opts, pyFileName])
        self.mainWidget.updateInfo(tx)
    
    def returnExecuteText(self):
        current = self.item(self.currentRow())
        name = str(current.text())
        opts = current.opts
        libName = current.pyFileName.split('.')[0]
        
        spl = ['import %s'%libName, 'reload (%s)'%libName, '%s.%s(%s)'%(libName, name, opts)]
        
        return '\n'.join(spl)

    def showExecuteDialog(self, item):
        showExecuteDialog(tx  = self.returnExecuteText())

class ExecuteDialog( QDialog):
    def __init__(self, parent = None, tx = 'lines'):
        super(ExecuteDialog, self).__init__(parent)
        
        self.setModal(True)
        
        self.inText = QPlainTextEdit()
        if tx:
            self.inText.setPlainText(tx)
        
        exBut, cancelBut = pw.makeButton('Execute', self.execAndAccept),pw.makeButton('Cancel', self.reject)
        
        butLayout = pw.makeBoxLayout([exBut, cancelBut], vertical = False)
        mainLayout = pw.makeBoxLayout([self.inText, butLayout], vertical = 1)
        
        self.setLayout(mainLayout)
    
    def execAndAccept(self):
        tx = str(self.inText.toPlainText())
        exec(tx)
        self.accept()
        
        

class ScriptBrowser(MayaQWidgetDockableMixin, QDialog):
    toolName = 'ScriptBrowser'
    def __init__(self, parent = None):
        super(ScriptBrowser, self).__init__(parent)
        
        self.list = FunctionsListWidget(mainWidget = self)
        
        reloadBut = pw.makeButton('reload', self.list.loadList)
        
        filterLabel = QLabel('filter')
        self.filterLine = QLineEdit()
        self.filterLine.textChanged.connect(self.updateFilter)
        
        self.infoLabel = QLabel('info')
        
        sa = QScrollArea()
        sa.setWidget(self.infoLabel)
        sa.setWidgetResizable (True)
        sa.setFrameStyle(QFrame.NoFrame)
        
        filterLayout = pw.makeBoxLayout([filterLabel, self.filterLine], stretchArray = [0,1], vertical = False)
        mainLayout = pw.makeBoxLayout([reloadBut , filterLayout, self.list, sa], stretchArray= [0,0,1, 0.1])
        
        self.setLayout(mainLayout)
        self.setWindowTitle('Script Browser')
    
    def updateFilter(self): 
        self.list.filterList(str(self.filterLine.text()))
    
    def updateInfo(self, tx):
        self.infoLabel.setText(tx)
        
    def execute(self):
        pass
        
def showExecuteDialog(tx):
    dia = ExecuteDialog(tx = tx)
    ok = dia.exec_()
    

def showScriptBrowser():
    mayaWin = pmm.getMainWindow()
    if mc.lsUI(type = 'dockControl') and hasattr(__main__, 'ScriptBrowserT') and __main__.ScriptBrowserTUI in mc.lsUI(type = 'dockControl'):
        mc.deleteUI(__main__.ScriptBrowserTUI)
    if hasattr(__main__, 'ScriptBrowserTDialog'):
        try:
            __main__.ScriptBrowserTDialog.close()
        except Exception:
            pass
        
    __main__.ScriptBrowserTDialog = ScriptBrowser(mayaWin)
    
    if (mc.dockControl('ScriptBrowserT', q=1, ex=1)):
        mc.deleteUI('ScriptBrowserT')
    __main__.ScriptBrowserTDialog.show(dockable = True, area='left',  width=400, floating=False)
    __main__.ScriptBrowserTUI = __main__.ScriptBrowserTDialog
    
        