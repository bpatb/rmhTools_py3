# import os, subprocess, threading, math, random,re,shutil
from __future__ import absolute_import
import os, subprocess, threading, math, random,shutil
# from six.moves import map
from importlib import reload
# from six.moves import range

try:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
    from PySide2.QtCore import Signal as pyqtSignal
except ImportError:
    from PySide6.QtGui import *
    from PySide6.QtCore import *
    from PySide6.QtWidgets import *
    from PySide6.QtCore import Signal as pyqtSignal
    from shiboken6 import wrapInstance

def createButtonList(butLabelsAndProcs = [[],[]], spacing = 0, margin = 0, label = 'Morph', cols = None):
    if not cols:
        buts = []
        for ar in butLabelsAndProcs:
            if len(ar) == 2:
                butLabel,proc = ar
                but = makeButton(butLabel,proc)
                buts.append(but)
            elif len(ar) == 3:
                butLabel,proc,itemList = ar
                but = makeButton_contextMenu(butLabel,proc,itemList)
                buts.append(but)
            
        butLayout = makeBoxLayout([QLabel(label)] + buts, spacing = spacing, margin = margin)
    else:
        gridLayout = QGridLayout()
        try:
            gridLayout.setMargin(0)
        except:
            gridLayout.setContentsMargins(0,0,0,0)
        gridLayout.setSpacing(0)
        
        count = 0
        for ar in butLabelsAndProcs:
            row, col = int(count / float(cols)), count%cols
            if len(ar) == 2:
                butLabel,proc = ar
                but = makeButton(butLabel,proc)
                gridLayout.addWidget(but, row, col)
            elif len(ar) == 3:
                butLabel,proc,itemList = ar
                but = makeButton_contextMenu(butLabel,proc,itemList)
                gridLayout.addWidget(but, row, col)
            count+=1
                
        butLayout = makeBoxLayout([QLabel(label), gridLayout], spacing = spacing, margin = margin)
        
    return butLayout


class ContextMenuButton(QPushButton):
    def __init__(self, label = None):
        QPushButton.__init__(self, label)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)
        self.popMenu = QMenu(self)
        
    def on_context_menu(self, point):
        if len(self.popMenu.actions()):
            self.popMenu.exec_(self.mapToGlobal(point))
    
    def setMenuFromList(self, itemList = []):
        self.popMenu.clear()
        for label,proc in itemList:
            self.popMenu.addAction(QAction(QIcon(),label, self, shortcut="",statusTip="", triggered=proc))
    

def makeButton_contextMenu(label, proc, itemList = None, expanding = False, checkable = False, maxSize = None, minSize = None, butClass = ContextMenuButton):
    but = butClass(label)
    if itemList:
        but.setMenuFromList(itemList)
    if proc:
        but.clicked.connect(proc)
    if expanding:
        but.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
    but.setCheckable(checkable)
    if maxSize:
        but.setMaximumSize(maxSize[0],maxSize[1])
    if minSize:
        but.setMinimumSize(minSize[0],minSize[1])
    return but

    
def makeBoxLayout(widgetArray, vertical = True, alsWidget = False, margin = None, spacing = None, stretchArray = [1]):
    if vertical:
        layout = QVBoxLayout()
    else:
        layout = QHBoxLayout()
    if margin != None:
        layout.setContentsMargins(margin,margin,margin,margin)
    if spacing != None:
        layout.setSpacing(spacing)
    for i, w in enumerate(widgetArray):
        if type(w) in [ QVBoxLayout ,QHBoxLayout,QGridLayout,QStackedLayout]:
            layout.addLayout(w, stretchArray[i%len(stretchArray)])
        elif w == 'stretch':
            layout.addStretch()
        else:
            layout.addWidget(w, stretchArray[i%len(stretchArray)])
    if alsWidget:
        lWidget = QWidget()
        lWidget.setLayout(layout)
        return lWidget
    else:
        return layout

def splitPath(path, ohnePunkt = True): #dirName, fName, base, ext
    path = str(path).replace('\\','/').replace('//','/')
    fName = path.split('/')[-1]
    dirName = os.path.dirname(path).replace('\\','/').replace('//','/')
    base, ext = os.path.splitext(fName)
    if ohnePunkt and ext:
        ext = ext[1:]
    return dirName, fName, base, ext
    

def createDock(self, label, widget, menu = None, close = False, floating = False, area = Qt.RightDockWidgetArea, allowed = Qt.AllDockWidgetAreas, style = None, palette = None):
    dock = QDockWidget(label, self)
    if style and palette:
        dock.setStyle(style)
        dock.setPalette(palette)
    dock.setWidget(widget)
    dock.setFloating(floating)
    dock.setAllowedAreas(allowed)
    self.addDockWidget(area , dock)
    action = dock.toggleViewAction()
    if menu:
        menu.addAction(action)
    if close:
        dock.close()
    return dock, action

def makeButton(label, proc, expanding = False, checkable = False, maxSize = None, minSize = None, butClass = QPushButton):
    but = butClass(label)
    if proc:
        but.clicked.connect(proc)
    if expanding:
        but.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
    but.setCheckable(checkable)
    if maxSize:
        but.setMaximumSize(maxSize[0],maxSize[1])
    if minSize:
        but.setMinimumSize(minSize[0],minSize[1])
    return but




class LabelSpinSlide(QWidget):
    valueChanged = pyqtSignal(int)
    def __init__(self, label = None, range = [1,100], spinVal = 10, slider = True , proc = None, parent = None):
        QWidget.__init__(self, parent)
        
        self.spin = QSpinBox()
        self.spin.setRange(range[0], range[1])
        
        if slider:
            self.slider = QSlider(Qt.Horizontal)
            self.slider.setRange(range[0], range[1])
            self.slider.valueChanged.connect(self.spin.setValue)
            self.spin.valueChanged.connect(self.slider.setValue)
            self.spin.valueChanged.connect(self.valueChanged.emit)
        
        mainLayout = QHBoxLayout()
        if label:
            self.label = QLabel(label)
            mainLayout.addWidget(self.label,0)
        mainLayout.addWidget(self.spin,0)
        if slider:
            mainLayout.addWidget(self.slider,1)
        mainLayout.setContentsMargins(0,0,0,0)
        
        self.setLayout(mainLayout)
        
        self.spin.setValue(spinVal)
        self.setValue = self.spin.setValue
        
        if proc:
            self.valueChanged.connect(proc)
        
    def value(self):
        return self.spin.value()
        
    def setRange(self, range):
        self.spin.setRange(range[0], range[1])
        self.slider.setRange(range[0], range[1])
    
        
class FloatLabelSpin(QWidget):
    def __init__(self, label = 'label', range = [1.0,10.0], spinVal = 1.0, parent = None):
        QWidget.__init__(self, parent)
        
        self.label = QLabel(label)
        
        self.spin = QDoubleSpinBox()
        self.spin.setRange(range[0], range[1])
        
        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.label,0)
        mainLayout.addWidget(self.spin,0)
        mainLayout.setContentsMargins(0,0,0,0)
        
        self.setLayout(mainLayout)
        
        self.spin.setValue(spinVal)

class MediaListWidget(QListWidget):
    pathChange = pyqtSignal(str)
    def __init__(self, exts = None, parent = None):
        super(MediaListWidget, self).__init__(parent)
        self.exts = exts or ['*.jpg','*.jpeg','*.avi','*.png','*.3gp','*.bmp'] 
        self.currentDir = 'd:/'
        self.setAcceptDrops(True)
        self.currentItemChanged.connect(self.pathChangeProc)
        self.checkItemCol = QColor(55,122,0)
        
    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData is None:
            return
        out = []
        for format in mimeData.formats():
            if format == 'text/uri-list':
                files = [str(url.toString()) for url in mimeData.urls()]
            else:
                continue
            for file in files:
                file = file.replace('file:///','').replace('\\','/')
                ext = file.split('.')[-1]
                if os.path.isfile(file) and '*.%s'%ext in self.exts:
                    out.append(file)
        if len(out) > 0:
            self.loadList(out, append = True)
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        event.accept()
        
    def pathChangeProc(self, new,prev):
        try:
            self.pathChange.emit(new.fullPath)
        except:
            pass
        
    def nextItem(self):
        count = self.count()
        if count > 0:
            cr = self.currentRow()
            self.setCurrentRow((cr+1)%count)
        
    def prevItem(self):
        count = self.count()
        if count > 0:
            cr = self.currentRow()
            self.setCurrentRow((cr+-1)%count)
    
    def setExts(self, exts):
        self.exts = exts
        
    def reload(self):
        if not self.currentDir:
            return
        self.loadDir(self.currentDir)
        
    def loadFile(self, file):
        file = str(file)
        dir = os.path.dirname(file).replace('\\','/')
        fname = file.split('/')[-1]
        if dir == self.currentDir:
            self.selectFile(fname)
        else:
            self.loadDir(dir)
            self.selectFile(fname)
            
    def selectFile(self, file):
        for row in range(self.count()):
            item = self.item(row)
            if item and item.fname == file:
                self.setCurrentItem(item)
                return
        
    def loadDir(self, dir):
        exts = self.exts
        dir = str(dir).replace('\\','/')
        files = list(map(str, QDir(dir).entryList(exts, QDir.Files | QDir.NoSymLinks)))
        self.clear()
        
        for file in files:
            item = QListWidgetItem(file)
            #item.relPath = self.sqlQuery.convertPath(dir+'/'[+file, 'rel')
            item.fullPath = dir+'/'+file
            item.fname = file
            ext = os.path.splitext(file)[1][1:]#file.split('.')[-1]
            self.addItem(item)
        if len(files) > 0:
            self.setCurrentRow(0)
        self.currentDir = dir
        self.calcCols()
        
    def loadList(self, files, append = False): #fullpath liste!
        if not append:
            self.clear()
        for file in files:
            file = file.replace('\\', '/')
            fname = file.split('/')[-1]
            fpath = os.path.dirname(file)
            item = QListWidgetItem(fname)
            item.fullPath = file
            item.fname = fname
            ext = os.path.splitext(fname)[1][1:]#file.split('.')[-1]
            self.addItem(item)
        if len(files) > 0:
            self.setCurrentRow(0)
        self.currentDir = dir
        self.calcCols()
        
    def getAllFiles(self):
        out = []
        for row in range(self.count()):
            item = self.item(row)
            out.append(item.fullPath)
        return out
    
    def removeCurrentRow(self, item = None):
        #if item:
        #    self.takeItem(item.row())
        #    return
        self.takeItem(self.currentRow())
        
    def calcCols(self):
        stdCol = QColor(0,0,0)
        for row in range(self.count()):
            item = self.item(row)
            if self.colCheck(item):
                item.setTextColor(self.checkItemCol)
                #print 'ooooha!'
            else:
                item.setTextColor(stdCol)
            
    def colCheck(self, item):
        return False
        
class DirListWidget(QListWidget):
    pathChange = pyqtSignal(str)
    def __init__(self, exts = None, parent = None):
        super(DirListWidget, self).__init__(parent)
        self.exts = exts or ['*.jpg','*.jpeg','*.avi','*.png','*.3gp','*.bmp']
        self.tags = []
        self.currentDir = 'd:/'
        self.setAcceptDrops(True)
        self.currentItemChanged.connect(self.pathChangeProc)
        self.checkItemCol = QColor(55,122,0)
        
    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData is None:
            return
        out = []
        for format in mimeData.formats():
            if format == 'text/uri-list':
                files = [str(url.toString()) for url in mimeData.urls()]
            else:
                continue
            for file in files:
                file = file.replace('file:///','').replace('\\','/')
                ext = file.split('.')[-1]
                if os.path.isdir(file):
                    out.append(file)
        if len(out) > 0:
            self.addDirs(out)
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        event.accept()
        
    def pathChangeProc(self, new,prev):
        try:
            self.pathChange.emit(new.fullPath)
        except:
            pass
        
    def nextItem(self):
        count = self.count()
        if count > 0:
            cr = self.currentRow()
            self.setCurrentRow((cr+1)%count)
        
    def prevItem(self):
        count = self.count()
        if count > 0:
            cr = self.currentRow()
            self.setCurrentRow((cr+-1)%count)
    
    def setTags(self, tags):
        self.tags = tags
    
    def checkAgainstTags(self, checkText):
        for tag in self.tags:
            if tag in checkTags:
                return True
        return False
        
    def reload(self):
        if not self.currentDir:
            return
        self.loadDir(self.currentDir)
        
    def getCurrentPath(self):
        item = self.item(self.currentRow())
        return item.fullPath
        
    def selectFile(self, file):
        for row in range(self.count()):
            item = self.item(row)
            if item and item.fname == file:
                self.setCurrentItem(item)
                return
        
    def loadDir(self, metaDir, append = False):
        exts = self.exts
        metaDir = str(metaDir).replace('\\','/')
        dirs = list(map(str, QDir(metaDir).entryList(['*'], QDir.Dirs | QDir.NoSymLinks | QDir.NoDot | QDir.NoDotDot)))
        if not append:
            self.clear()
        
        for dir in dirs:
            item = QListWidgetItem(dir)
            #item.relPath = self.sqlQuery.convertPath(dir+'/'[+file, 'rel')
            item.fullPath = metaDir + '/' + dir
            item.dirname = dir
            self.addItem(item)
        if len(dirs) > 0:
            self.setCurrentRow(0)
        self.currentDir = metaDir
        self.calcCols()
        
    def addDir(self, dir):
        item = QListWidgetItem(dir)
        item.fullPath = dir
        item.dirname = dir
        self.addItem(item)
        
    def addDirs(self, dirs):
        for dir in dirs:
            self.addDir(dir)
        
    def getAllDirs(self):
        out = []
        for row in range(self.count()):
            item = self.item(row)
            out.append(item.fullPath)
        return out
    
    def removeCurrentRow(self, item = None):
        self.takeItem(self.currentRow())
        
    def calcCols(self):
        stdCol = QColor(0,0,0)
        for row in range(self.count()):
            item = self.item(row)
            if self.colCheck(item):
                item.setTextColor(self.checkItemCol)
                #print 'ooooha!'
            else:
                item.setTextColor(stdCol)
            
    def colCheck(self, item):
        return False


