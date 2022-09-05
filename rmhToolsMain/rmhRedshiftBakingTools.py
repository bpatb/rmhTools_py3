from __future__ import absolute_import
from __future__ import print_function
from six.moves import range
try:
    from PySide2.QtGui import *
from importlib import reload
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
    # print "Using PySide2"
except:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from shiboken import wrapInstance
    # print "Using PySide"

import __main__
import maya.cmds as mc
import maya.mel as mel
import os, subprocess, pickle
import PatsWidgets as pw
import PatsMayaMethods2 as pmm
import projectionTools as pt
reload(pmm)

def RS_storeOptions(dc, storeNode = 'time1', attrName = 'RSBakeOpts'):
    if not attrName in mc.listAttr(storeNode):
        mc.addAttr(storeNode, ln = attrName, dt = 'string')
    
    dc_old = {}
    tx = mc.getAttr('%s.%s'%(storeNode, attrName))
    if tx:
        dc_old = pickle.loads(tx)
    
    dc_old.update(dc)
    tx = pickle.dumps(dc_old)
    mc.setAttr('%s.%s'%(storeNode, attrName), tx, type = 'string')
    # print 'rs bake opts stored'

def RS_getOptions(storeNode = 'time1', attrName = 'RSBakeOpts'):
    if not attrName in mc.listAttr(storeNode):
        return {}
    dc = {}
    tx = mc.getAttr('%s.%s'%(storeNode, attrName))
    if tx:
        dc = pickle.loads(tx)
    return dc

def RS_setupForBaking(dirName = '_bakeTest'):
    mc.setAttr('redshiftOptions.imageFormat', 2)
    mc.setAttr('defaultRenderGlobals.imageFilePrefix', '_baking/%s/<object>'%dirName, type = 'string')

    
def RS_assignRedshiftBakeSet(name = None, resolution = None, addSel = True):
    sel = mc.ls(sl = True)
    if resolution == None:
        result = mc.confirmDialog(title='createRedshiftBakeSet',message='resolution:',button=['256','512','1024','2048','4096', 'Cancel'], defaultButton='OK',cancelButton='Cancel', dismissString='Cancel')
        if result != 'Cancel':
            resolution = int(result)
        else:
            return
    if name == None:
        name = 'rsBakeSet_%d'%resolution
        # result = mc.promptDialog(title='createRedshiftBakeSet',message='name:',button=['OK', 'Cancel'], defaultButton='OK',cancelButton='Cancel', dismissString='Cancel', text = 'rsBakeSet_%d'%resolution)
        # if result == 'OK':
        #     name = mc.promptDialog(query=True, text=True)
        # else:
        #     return
    if mc.objExists(name):
        print(name, 'exists')
        # mc.select(name)
    else:
        mc.createNode('RedshiftBakeSet', n = name)
        if type(resolution) in [tuple, list]:
            resolutionX, resolutionY = resolution
        else:
            resolutionX, resolutionY = resolution,resolution
            
        mc.setAttr('%s.width'%name, resolutionX)
        mc.setAttr('%s.height'%name, resolutionY)
        
    if addSel:
        RS_createBakeUVSet(sel)
        mc.sets( sel, add = name)
                    
def RS_createBakeUVSet(objs = None):
    if not objs:
        objs = mc.ls(sl = True)
    
    for obj in objs:
        allSets = mc.polyUVSet(obj, allUVSets = True, q = True)
        if allSets:
            if not 'bakeSet' in allSets:
                mc.polyUVSet(obj, nuv = 'bakeSet', uvs = allSets[0], copy = True)
    

def RS_setStandardMaterialValues(objs = None):
    for obj in objs:
        if not mc.listAttr(obj, ud = True) :
            continue
        memAttrs = [a for a in mc.listAttr(obj, ud = True) if 'matValue_' in a]
        mat = pmm.getMaterial(obj)
        if not mat:
            continue
        for at in memAttrs:
            val = mc.getAttr('%s.%s'%(obj, at))
            attr = at.replace('matValue_','')
            if attr in mc.listAttr(mat):
                mc.setAttr('%s.%s'%(mat, attr), val)
        
def RS_bakeRedshiftSet(rsSets = None, assignOrig = True, assignBaked = True):
    def setUVSetForBakeSets():
        sets = mc.ls(type = 'RedshiftBakeSet')
        for st in sets:
            mc.setAttr('%s.uvSet'%st, 'bakeSet', type = 'string')
        
    if not rsSets:
        allSets = ['all'] + mc.ls(type = 'RedshiftBakeSet')
        if len(allSets) == 2:
            rsSets = [allSets[-1]]
        if not rsSets:
            setName, ok = QInputDialog.getItem(None, 'bakeRedshiftSet', 'name', allSets, current = 0, editable = False)
            if not ok:
                return
            setName = str(setName)
            if setName == 'all':
                rsSets = mc.ls(type = 'RedshiftBakeSet')
            else:
                rsSets = [setName]
    
    prefix =mc.getAttr('defaultRenderGlobals.imageFilePrefix')
    if not prefix or not '<object>' in prefix:
        RS_setupForBaking()
        mc.warning('RS_bakeRedshiftSet: auto changed render settings!')
    
    setUVSetForBakeSets()
    
    makeZeroAttrs = ['refl_weight', 'refr_weight']
    
    allObjs=  [] 
    for bakeSet in rsSets:
        objs = mc.listConnections(bakeSet+'.dagSetMembers') if mc.listConnections(bakeSet+'.dagSetMembers') else []
        print('baking', bakeSet, '...')
        if not objs:
            continue
        mc.displaySmoothness(objs, polygonObject = 1)
        RS_createBakeUVSet(objs)
        if assignOrig:
            RS_assignOriginalMaterial(objs)
        
        for obj in objs:
            mat = pmm.getMaterial(obj)
            if not mat:
                continue
            for attr in makeZeroAttrs:
                if attr in mc.listAttr(mat):
                    memAttr = 'matValue_%s'%attr
                    val = mc.getAttr('%s.%s'%(mat, attr))
                    if not memAttr in mc.listAttr(obj):
                        mc.addAttr(obj, ln = memAttr, at = 'double', k = 1)
                    mc.setAttr('%s.%s'%(obj, memAttr), val)
                    val = mc.setAttr('%s.%s'%(mat, attr), 0)
                    
        mc.rsRender(bake = 1, bakeSet = bakeSet)
        RS_setStandardMaterialValues(objs)
        allObjs = allObjs + objs
    if assignBaked:
        print('assigning baked materials...')
        opts = RS_getOptions()
        bakePath = opts.get('bakePath', None)
        RS_assignBakedTextures(allObjs, bakePath = bakePath, bakePath_dontAsk = True)
        # RS_assignBakedMaterial(allObjs)
    
    mc.select(clear = True)

def RS_assignBakedTextures(objs = None, bakePath = None, bakePath_dontAsk = False, prefix = 'baked', filterForSubstring = None): #useExistingShader gerade nur fuer VRay Baking
    def _createAndAssign(matType, name, objs, assignToObjs):
        mtl = mc.shadingNode(matType, n = name, asShader = True )
        sg = mc.sets(renderable = True ,noSurfaceShader = True, empty = True, name = '%sSG'%name)
        mc.connectAttr('%s.outColor'%mtl, '%s.surfaceShader'%sg, force = True)
        if assignToObjs:
            if type(assignToObjs) in [list,tuple]:
                objs2 = assignToObjs
            else:
                objs2 = objs
            for s in objs2:
                pmm.assignSG(sg, [s])
                pmm.connectViaMessage(sg, obj, 'bakedSG')
        
        if 'specularColor' in mc.listAttr(name):
            mc.setAttr('%s.specularColor'%name,1,1,1, type = 'double3')
        if 'specularRollOff' in mc.listAttr(name):
            mc.setAttr('%s.specularRollOff'%name,0)
        
        selSet = 'autoCreatedNodes'
        if not mc.objExists(selSet):
            mc.sets(name = selSet, em = True)
            
        mc.sets(mtl, addElement = selSet, e = True)
        mc.select(mtl)
        
    mc.undoInfo(ock = True)
    if not objs:
        objs = mc.ls(sl =True)
    
    opts = RS_getOptions()
    
    ######  get path
    bakePath = opts.get('bakePath', None)
    if bakePath and not bakePath_dontAsk:
        result = mc.confirmDialog(title='RS_assignBakedTextures',message='use %s?'%bakePath,button=['Yes','No', 'Cancel'], defaultButton='OK',cancelButton='Cancel', dismissString='Cancel')
        if result == 'Cancel':
            return
        bakePath = bakePath if result == 'Yes' else None
        
    if not bakePath:
        bakePath = mc.fileDialog2(fm = 3)
        if not bakePath:
            return
        bakePath = bakePath[0]
    
    bakePath = bakePath.replace('\\', '/')
    
    RS_storeOptions({'bakePath':bakePath})
    
    ###### check files
    print(bakePath)
    fileList = os.listdir(bakePath)
    # print fileList
    for obj in objs:
        shape = mc.listRelatives(obj, s = True)
        if not shape:#
            print('skip %s -> no shape'%obj)
            continue
        shape = shape[0]
        sg_current = pmm.getShadingGroup(obj, False)
        if not '_baked' in sg_current:
            pmm.connectViaMessage(sg_current, obj, 'origSG')
        for fileName in fileList:
            if filterForSubstring and not filterForSubstring in fileName:
                continue
                
            if fileName.split('.')[0] in [obj, '%s-%s'%(prefix,shape)] :
                fullPath = str(bakePath + '/%s'%fileName)
                matName = '%s_bakedMat'%obj
                fileNode = '%s_bakedFile'%obj
                
                #### create file
                if not mc.objExists(fileNode):
                    mc.shadingNode('file', n = fileNode, asTexture = True )
                    p2d = pt.createPlacementNodes([fileNode], connectIndividualUV = False)[0]
                    mc.setAttr('%s.wrapU'%p2d, 1)
                    mc.setAttr('%s.wrapV'%p2d, 1)
                mc.setAttr('%s.fileTextureName'%fileNode, fullPath, type = 'string')
                pmm.connectViaMessage(fileNode, obj, 'bakedFileNode')
                
                ###### uv linking
                allSets = mc.polyUVSet(obj, allUVSets = True, q = True)
                idx = allSets.index('bakeSet') if 'bakeSet' in allSets else False
                if idx != False:
                    mc.uvLink( uvSet='%s.uvSet[%d].uvSetName'%(obj,idx), texture=fileNode )
                else:
                    mc.warning('RS_assignBakedTextures: uvSet bakeSet not found in %s'%obj)
                
                #### create material
                if not mc.objExists(matName):
                    _createAndAssign('blinn', matName, [obj], True)
                    mc.setAttr('%s.color'%matName, 0,0,0, type = 'double3')
                    mc.connectAttr('%s.outColor'%fileNode, '%s.incandescence'%matName, force = True)
                pmm.connectViaMessage(matName, obj, 'bakedMaterial')
                
                ###### assign material
                if 'bakedSG' in mc.listAttr(obj):
                    con = mc.listConnections('%s.%s'%(obj, 'bakedSG'), d = 0, s = 1)
                    if con:
                        pmm.assignSG(con[0], [obj])
                
                print(matName, 'auf', obj, 'zugewiesen')
                continue
    mc.undoInfo(cck = True)
    
def RS_getAllBakeObjects():
    allSets =  mc.ls(type = 'RedshiftBakeSet')
    allObjs=  [] 
    for bakeSet in allSets:
        objs = mc.listConnections(bakeSet+'.dagSetMembers') if mc.listConnections(bakeSet+'.dagSetMembers') else []
        allObjs = allObjs + objs
    return allObjs
    
def RS_deleteBakeNodes(objs = None):
    mc.undoInfo(ock = True)
    if not objs:
        objs = mc.ls(sl = True)
    
    for obj in objs:
        attrs = ['bakedSG', 'bakedFileNode', 'bakedSG']
        for attr in attrs:
            cons = mc.listConnections('%s.%s'%(obj, attr), s = 1, d = 0)
            if cons:
                mc.delete(cons)
    mc.undoInfo(cck = True)
    
def RS_setOriginalMaterial(objs = None):
    if not objs:
        objs = mc.ls(sl = True)
    mc.undoInfo(ock = True)
    for obj in objs:
        sg_current = pmm.getShadingGroup(obj, False)
        if sg_current and not '_baked' in sg_current:
            pmm.connectViaMessage(sg_current, obj, 'origSG')
        
    mc.undoInfo(cck = True)
        
    
def RS_assignOriginalMaterial(objs = None):
    if not objs:
        objs = mc.ls(sl = True)
    mc.undoInfo(ock = True)
    if not objs:
        result = mc.confirmDialog(title='RS_assignOriginalMaterial',message='none selected, for all?',button=['Yes', 'Cancel'], defaultButton='OK',cancelButton='Cancel', dismissString='Cancel')
        if result == 'Cancel':
            return
        objs = RS_getAllBakeObjects()
        
        
    for obj in objs:
        if not 'origSG' in mc.listAttr(obj):
            continue
        
        sg_current = pmm.getShadingGroup(obj, False)
        if sg_current and not '_baked' in sg_current:
            pmm.connectViaMessage(sg_current, obj, 'origSG')
        
        cons = mc.listConnections('%s.origSG'%obj, s = 1, d = 0)
        if cons:
            pmm.assignSG(cons[0], [obj])
    mc.select(clear = True)
    
    mc.undoInfo(cck = True)
    
def RS_assignBakedMaterial(objs = None):
    mc.undoInfo(ock = True)
    if not objs:
        objs = mc.ls(sl = True)
    if not objs:
        result = mc.confirmDialog(title='RS_assignBakedMaterial',message='none selected, for all?',button=['Yes', 'Cancel'], defaultButton='OK',cancelButton='Cancel', dismissString='Cancel')
        if result == 'Cancel':
            return
        objs = RS_getAllBakeObjects()
        
    for obj in objs:
        if not 'bakedSG' in mc.listAttr(obj):
            continue
        sg_current = pmm.getShadingGroup(obj, False)
        if sg_current and not '_baked' in sg_current:
            pmm.connectViaMessage(sg_current, obj, 'origSG')
        cons = mc.listConnections('%s.bakedSG'%obj, s = 1, d = 0)
        if cons:
            pmm.assignSG(cons[0], [obj])
    mc.select(clear = True)
    mc.undoInfo(cck = True)

def RS_automaticMappingForSelected(normalize = True, toSet = 'bakeSet'):
    sel = mc.ls(sl = True)
    RS_createBakeUVSet(sel)
    for obj in sel:
        mc.polyAutoProjection(obj + '.f[*]', uvs = toSet)
        if normalize:
            mc.polyNormalizeUV(obj, pa = False)
        mc.u3dLayout(obj, res = 512, scl = 1,spc =0.0078125,mar = 0.0078125)

def RS_createExportGroup(objs = None):
    mc.undoInfo(ock = True)
    if not objs:
        objs = mc.ls(sl = True)
    origGrp = objs[0]
    
    dup = mc.duplicate(origGrp, rr = True, rc = True, ic = True, name = '%s_exp'%origGrp )
    mc.hide(origGrp)
    allTrans = mc.listRelatives(dup, ad = True, type = 'transform')
    
    for obj in allTrans:
        sh = mc.listRelatives(obj, s = 1)
        print(sh)
        if not sh or mc.objectType(sh[0]) != 'mesh':
            continue
        
        allSets = mc.polyUVSet(sh[0], allUVSets = True, q = True)
        print(obj, allSets)
        if allSets:
            if not 'bakeSet' in allSets or len(allSets) == 1:
                continue
            mc.delete(obj , ch = 1)
            mc.polyUVSet(sh[0], uvs = 'bakeSet', nuv = allSets[0], copy = True)
            for i in range(1,len(allSets)):
                uvSet = allSets[i]
                mc.polyUVSet(obj, uvs = uvSet, delete = True)
    
    
    newGrp = mc.undoInfo(cck = True)
    
    
    
    
class BT_ListWidget(QListWidget):
    def __init__(self,mainWidget = None, parent = None):
        super(BT_ListWidget, self).__init__(parent)
        
        self.mainWidget = mainWidget
        
        self.currentItemChanged.connect(self.pathChangeProc)
        
        self.reload()
    
    def pathChangeProc(self, new,prev):
        try:
            self.pathChange.emit(new.fullPath)
        except:
            pass
        
    def reload(self):
        node = 'time1'
        if not 'shaderAssignmentGroups' in mc.listAttr(node):
            mc.warning('no items in %s.shaderAssignmentGroups found'%node)
            return
        tx = mc.getAttr('%s.shaderAssignmentGroups'%node)
        if tx:
            sa_metaDict = pickle.loads(tx)
            self.loadFromDict(sa_metaDict)
        
    def selectFile(self, file):
        for row in range(self.count()):
            item = self.item(row)
            if item and item.fname == file:
                self.setCurrentItem(item)
                return
        
    def loadFromDict(self, sa_metaDict):
        for sa_name in sa_metaDict.keys():
            item = QListWidgetItem(sa_name)
            item.sa_dict = sa_metaDict[sa_name]
            self.addItem(item)
        

    def removeCurrentRow(self, item = None):
        self.takeItem(self.currentRow())
        self.writeOptions()
    
    def createNewAssignment(self, objs = None, name = None, sa_dict = None):
        if not sa_dict:
            sa_dict = copyShaderAssignment(objs = objs)
        if not name:
            name, ok = QInputDialog.getText(self, 'createNewAssignment', 'assignment name', text = 'shaderAssignment01')
            if not ok:
                return
            name = str(name)
            #### assure uniqe name
            i = 0
            nameRef = name
            nameList = self.returnNameList()
            while name in nameList:
                name = '%s_%02d'%(nameRef, i)
                i += 1
        item = QListWidgetItem(name)
        item.sa_dict = sa_dict
        self.addItem(item)
        self.writeOptions()
    
    def assignCurrentAssigment(self):
        item = self.item(self.currentRow())
        pasteShaderAssignment(item.sa_dict)
    
        
    def returnNameList(self):
        out = []
        for row in range(self.count()):
            item = self.item(row)
            name = str(item.text())
            out.append(name)
        return out
    
    def writeOptions(self):
        node = 'time1'
        if not 'shaderAssignmentGroups' in mc.listAttr(node):
            mc.addAttr(node, ln = 'shaderAssignmentGroups', dt = 'string')
        dc = {}
        
        for row in range(self.count()):
            item = self.item(row)
            name = str(item.text())
            sa_dict = item.sa_dict
            dc[name] = sa_dict
            
        tx = pickle.dumps(dc)
        mc.setAttr('%s.shaderAssignmentGroups'%node, tx, type = 'string')
    
    def loadOptions(self):
        node = 'time1'
        if not 'shaderAssignmentGroups' in mc.listAttr(node):
            return
        tx = mc.getAttr('%s.shaderAssignmentGroups'%node)
        if not tx:
            return
        sa_metaDict = pickle.loads(tx)
        self.loadFromDict(sa_metaDict)
        
    
    def getCurrentDict(self):
        item = self.item(self.currentRow())
        return item.sa_dict
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.assignCurrentAssigment()
            return
        super(BT_ListWidget, self).mouseDoubleClickEvent(event)
    
    
class RS_BakingToolsDialog(QDialog):
    def __init__(self, parent = None):
        super(RS_BakingToolsDialog, self).__init__(parent)
        
        self.outputValue = None
        
        self.prefixLine, self.outPathLine = QLineEdit(),QLineEdit()
        self.prefixLine.setText('baked')
        self.prefixLine.textChanged.connect(self.saveBakingToolsPrefs)
        self.outPathLine.textChanged.connect(self.saveBakingToolsPrefs)
        updBut = pw.makeButton('upd', self.updateOutPath)
        # self.list = BT_ListWidget()
        
        outPathLayout = pw.makeBoxLayout([QLabel('images/_baking/'), self.outPathLine,updBut], stretchArray = [0,1,0], vertical = 0)
        
        # buts00 = [pw.makeButton('setup RS for baking', self.RS_setupForBaking_UI),pw.makeButton('assign baking set', RS_assignRedshiftBakeSet),\
        #           pw.makeButton('createBakeUVSet', RS_createBakeUVSet), pw.makeButton('autoUVs for Sel (-> bakeSet)', RS_automaticMappingForSelected), \
        #           pw.makeButton('assign baked textures', RS_assignBakedTextures)]
        buts00 = [pw.makeButton('assign baking set', RS_assignRedshiftBakeSet),\
                  pw.makeButton('createBakeUVSet', RS_createBakeUVSet), pw.makeButton('autoUVs for Sel (-> bakeSet)', RS_automaticMappingForSelected), \
                  pw.makeButton('show UV Editor', self.showUVEditor),pw.makeButton('assign baked textures', RS_assignBakedTextures)]
        butLayout00 = pw.makeBoxLayout(buts00, vertical = True, spacing = 0)
        
        
        buts01 = pw.makeButton('assign orig Mtl', RS_assignOriginalMaterial), pw.makeButton('assign baked Mtl', RS_assignBakedMaterial)
        butLayout01 = pw.makeBoxLayout(buts01, vertical = False, spacing = 0)
        
        buts02  = [pw.makeButton('bake Redshift Set...', self.RS_bakeRedshiftSet_UI)]
        butLayout02 = pw.makeBoxLayout(buts02, vertical = True, spacing = 3)
        
        buts03  = [pw.makeButton('duplicate group for export', RS_createExportGroup)]
        butLayout03 = pw.makeBoxLayout(buts03, vertical = True, spacing = 3)
        
        # mainLayout = pw.makeBoxLayout([butLayout00, bakeOptsLayout, butLayout01, butLayout02],stretchArray = [0,0,0,0,0])
        mainLayout = pw.makeBoxLayout([outPathLayout, butLayout00, butLayout01, butLayout02, QWidget(), butLayout03],stretchArray = [0,0,0,0,1,0])
        
        self.setLayout(mainLayout)
        self.setWindowTitle('RS BakingTools')
        self.loadBakingToolsPrefs()
        self.saveBakingToolsPrefs()
    
    def showUVEditor(self):
        mel.eval('TextureViewWindow')
    
    def updateOutPath(self):
        sceneName = mc.file( q = True, sn = True, shn = True).split('.')[0] if mc.file( q = True, sn = True, shn = True) else 'bakedScene'
        tx = '_'.join(sceneName.split('_')[:-1])
        self.outPathLine.setText(tx )
        self.saveBakingToolsPrefs()
        
    def RS_setupForBaking_UI(self):
        RS_setupForBaking(str(self.outPathLine.text()) )
    
    def RS_assignBakedTextures(self):
        tx = str(self.outPathLine.text())
        bakePath = mc.workspace(q= True, rd = True) + 'images/_baking/' + tx
        RS_assignBakedTextures(bakePath = bakePath)
        
    def RS_bakeRedshiftSet_UI(self):
        self.RS_setupForBaking_UI()
        RS_bakeRedshiftSet()
        
    def saveBakingToolsPrefs(self):
        tx = str(self.outPathLine.text())
        bakePath = mc.workspace(q= True, rd = True) + 'images/_baking/' + tx
        dc = {'outPath':str(self.outPathLine.text()), 'bakePath': bakePath}
        RS_storeOptions(dc)
    
    def loadBakingToolsPrefs(self):
        sceneName = mc.file( q = True, sn = True, shn = True).split('.')[0] if mc.file( q = True, sn = True, shn = True) else 'bakedScene'
        dc = RS_getOptions()
        if 'outPath' in list(dc.keys()) and type(dc['outPath']) == str:
            self.outPathLine.setText(dc['outPath'])
        else:
            self.updateOutPath()
    
    def createAssignmentForSelected(self, objs = None):
        if not objs:
            objs = mc.ls(sl = True)
        self.list.createNewAssignment(objs)
    
    def assignBakeOptions(self):
        prefix, outPath = str(self.prefixLine.text()), str(self.outPathLine.text())
        assignBakeOptions(prefix = prefix, outPath = outPath)
        
    def bakeWithRedshift(self):
        mel.eval('redshiftBakeOptions;')
    
    def assignBakedTextures(self):
        prefix = str(self.prefixLine.text())
        mats = pmm.assignBakedTextures(prefix = prefix)
        print(mats, 'yes!')
        pmm.replugMatInput(von = 'color', nach = 'incandescence',mats = mats)
    
    def unplugTranspareny(self):
        unplugTransparencyInput()
    

def RS_showBakingToolsDialog():
    if hasattr(__main__, 'bakingToolsDialog'):
        try:
            __main__.bakingToolsDialog.close()
        except Exception:
            pass
    mayaWin = pmm.getMainWindow2()
    __main__.bakingToolsDialog = RS_BakingToolsDialog(mayaWin)
    __main__.bakingToolsDialog.show()
    

