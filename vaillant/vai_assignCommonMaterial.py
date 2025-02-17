#### Assign common material - Patrick B 22.09.13, RMH

from __future__ import absolute_import
from __future__ import print_function
import maya.cmds as mc
from importlib import reload
import rmhTools_widgets as pw

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

# def assignAOShader(objs = None, AOShaderName = 'AO_VRayMtl'):
#     if not objs:
#         objs = mc.ls(sl = True, type = 'transform')
#     if not mc.objExists(AOShaderName):
#         sg, AOShaderName = createAmbientOcclusionMaterial(AOShaderName)
#         if not sg:
#             return
#     else:
#         sg = mc.listConnections(AOShaderName, type = 'shadingEngine')[0]
#     mc.setAttr('%s.compensateCameraExposure'%AOShaderName, 1)
#     if objs:
#         mc.select(objs, r = True)
#     assignSG(sg, objs)
# 
# def createAmbientOcclusionMaterial(name = 'AO_VRayMtl'):
#     if mc.objExists(name):
#         mc.select(name)
#         return name
#     radius, ok = QInputDialog.getInt(None, 'AO Material erstellen', 'Radius Wert', value = 160, min = 0,max = 5000)
#     if not ok:
#         return None,None
#     mtl = mc.shadingNode('VRayLightMtl', n = name, asShader = True )
#     dirt = mc.shadingNode('VRayDirt', n = name + '_dirt', asTexture = True)
#     mc.connectAttr('%s.outColor'%dirt, '%s.color'%mtl, force = True)
#     mc.setAttr('%s.radius'%dirt, radius)
#     sg = mc.sets(renderable = True ,noSurfaceShader = True, empty = True, name = '%sSG'%name)
#     mc.connectAttr('%s.outColor'%mtl, '%s.surfaceShader'%sg, force = True)
#     return sg, name

def vai_error(message):
    mc.confirmDialog(title='vaillant tools',message=message,button=['Fine.'], defaultButton='Fine.')


def getShadingGroup(obj = None, select = False):
    if not obj:
        obj = mc.ls(sl = True)[0]
    if mc.objectType(obj) == 'transform':
        shape = mc.listRelatives(obj, s = True, f = True)[0]
        sg = mc.listConnections(shape, type = 'shadingEngine')[0]
        if select:
            getObjects_SG(sg, select = True)
        return sg
    elif 'vray' in mc.objectType(obj).lower() or 'lambert' in mc.objectType(obj).lower() or 'blinn' in mc.objectType(obj).lower():
        sg = mc.listConnections(obj, type = 'shadingEngine')
        print(obj)
        return sg if not type(sg) == list else sg[0] 
    

def getObjects_SG(sg, select = False):
    objs  = [obj for obj in mc.listConnections(sg) if mc.objectType(obj) == 'transform']
    if select:
        mc.select(objs, r = True)
    return objs

def assignSG(sg, objs = None):
    if type(sg) in [list, tuple]:
        sg = sg[0]
    if not objs:
        objs = mc.ls(sl = True)
    for obj in objs:
        mc.select(obj)
        mc.sets(e = True, forceElement = sg)

def assignCommonShader_xray():
    if not len(mc.fileInfo('vaiScnInit', q=True)):
        vai_error('Scene is not initialized...')
        return
    
    sgData = {'messing':'Messing_Mtl_SG', \
              'kupfer':'kupfer_Mtl_SG', \
              'plastik (schwarz)':'PlastikS_Mtl_SG', \
              'plastik (weiss)':'PlastikW_Mtl_SG', \
              'alu':'Alu_Mtl_SG', \
              'silvermetallic':'Silvermetallic_Mtl_SG', \
              'edelstahl':'Edelstahl_Mtl_SG'}
    sgNames = ['messing', 'kupfer', 'plastik (schwarz)','plastik (weiss)', 'alu', 'edelstahl']
    
    dialog = MaterialChooser(mats = sgNames)
    ok = dialog.exec_()#QInputDialog.getItem(None, 'welches Material?', '', sgNames, current = 0, editable = False)
    if ok:
        sgName, allCheck = dialog.getVals()
        print(sgData[sgName], 'wird zugewiesen...')
    else:
        return
    sg = sgData[sgName]
    # sg = [sgn for sgn in mc.ls(type ='shadingEngine') if sg in sgn ][0]
    if not mc.objExists(sg):
        vai_error('%s does not exist'%sg)
        return
    
    if not allCheck:
        assignSG(sg)
    else:
        selected_sgs = list(set([getShadingGroup(obj) for obj in mc.ls(sl = True)]))
        all_sg_objs = []
        for current_sg in selected_sgs:
            objs = getObjects_SG(current_sg)
            if not objs:
                print('nein', current_sg)
                continue
            all_sg_objs  = list(set(all_sg_objs + objs))
        assignSG(sg, all_sg_objs)
    
def assignCommonShader_set(setName = 'commonMaterialSet'):
    mats =  [obj for obj in mc.listConnections(setName)]
    sgNames, sgObjects = [],[]
    for mat in mats:
        if not ('vray' in mc.objectType(mat).lower() or  'lambert' in mc.objectType(mat).lower() or 'blinn' in mc.objectType(mat).lower()):
            print('nein:', mat , mc.objectType(mat))
            continue
        if 'commonName' in mc.listAttr(mat):
            name = mc.getAttr('%s.commonName')
        else:
            name = mat
        sg = getShadingGroup(mat)
        if sg:
            sgNames.append(mat)
            sgObjects.append(sg)
        else:
            mc.warning('ACM Warnung: %s hat keine SG'%mat)
    dialog = MaterialChooser(mats = sgNames)
    ok = dialog.exec_()#QInputDialog.getItem(None, 'welches Material?', '', sgNames, current = 0, editable = False)
    if ok:
        sgName, allCheck = dialog.getVals()
        idx = sgNames.index(sgName)
        print(sgObjects[idx], 'wird zugewiesen...')
        if idx in [None, False]:
            print('fehler', idx , sgObjects)
            return
    else:
        return
    sg = sgObjects[idx]
    if not allCheck:
        assignSG(sg)
    else:
        selected_sgs = list(set([getShadingGroup(obj) for obj in mc.ls(sl = True)]))
        all_sg_objs = []
        for current_sg in selected_sgs:
            objs = getObjects_SG(current_sg)
            if not objs:
                print('nein', current_sg)
                continue
            all_sg_objs  = list(set(all_sg_objs + objs))
        assignSG(sg, all_sg_objs)

def assignToCommonSet(objs = None):
    if not objs:
        objs = mc.ls( sl = True )
    setName = 'commonMaterialSet'
    if not mc.objExists(setName):
        mc.sets(name = setName)
    for obj in objs:
        mc.select(obj)
        mc.sets(e = True, forceElement = setName)

class MaterialChooser(QDialog):
    def __init__(self, parent = None, mats = ['a','b']):
        QDialog.__init__(self, parent)
        
        self.outText= False
        self.allCheck = QCheckBox('auf alle mit gleichem Material anwenden')
        layout_oben = pw.makeBoxLayout([self.allCheck, pw.makeButton('<-selektieren', self.selectSameSg)], vertical = False)
        
        self.buts = [pw.makeButton(mat, self.doitProc) for mat in mats]
        self.buts.append(pw.makeButton('cancel', self.reject))
        layout = pw.makeBoxLayout(self.buts, vertical = False)
        mainLayout = pw.makeBoxLayout([layout_oben, layout])
        
        self.setLayout(mainLayout)
        self.setModal(True)
        self.setWindowTitle('xray Material')
    
    def doitProc(self):
        sender = self.sender()
        self.outText = str(sender.text())
        self.accept()
    
    def selectSameSg(self):
        sg = getShadingGroup(obj = None)
        getObjects_SG(sg, select = True)
    
    def getVals(self ):
        return self.outText, self.allCheck.isChecked()
    
    
    
    