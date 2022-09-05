from __future__ import absolute_import
from __future__ import print_function
from six.moves import range
from importlib import reload
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

import maya.cmds as mc
import maya.mel as mel
import maya.OpenMaya as om
import maya.OpenMayaUI as omUI

# import os, random
# import __main__
# import rmhTools_widgets as pw


def searchObjectsInNamespaces(objs, objType = 'blendShape'):
    out = []
    allObjs = mc.ls(type = objType)
    for obj in objs:
        if mc.objExists(obj):
            out.append(obj)
            continue
        for _obj in allObjs:
            if obj == _obj.split(':')[-1]:
                out.append(_obj)
                break
    return out

# def connectToFaceCapData_showInfo():
#     tx = ['OneMessage Robo Checklist:', '-]
#     return mc.confirmDialog( title='createCameraDofLocator', message='vray?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
    
def connectToFaceCapData(sourceBlendShape = 'shapes', targetBlendShapes = ['eyeL_blendShape', 'eyeR_blendShape', 'mouth_blendShape'], headSourceTrans = 'grp_transform', headDestTrans = 'headCtrl' ):
    targetBlendShapes = searchObjectsInNamespaces(targetBlendShapes)
    if not targetBlendShapes:
        mc.error('targetBlenshapes not found')
        return
    
    headDestTrans = searchObjectsInNamespaces([headDestTrans], objType = 'transform')
    if not headDestTrans:
        mc.error('headDestTrans not found')
        return
    headDestTrans = headDestTrans[0] if type(headDestTrans) in [list, tuple] else headDestTrans
    
    # attrList_source = mc.aliasAttr(sourceBlendShape, q = True)
    attrList_source = mel.eval('aliasAttr -q %s'%sourceBlendShape)
    attrList_source = [a for a in attrList_source if a and not '[' in a]
    
    mc.undoInfo(ock = True)
    
    ########## connect head transform
    
    for attr in ['translate', 'rotate']:
        mc.connectAttr('%s.%s'%(headSourceTrans,attr),'%s.%s'%(headDestTrans,attr), f = 1)
    
    ####### connect blendshape attrs
    
    for bs in targetBlendShapes:
        # attrList_dest = mc.aliasAttr(bs, q = True)
        attrList_dest = mel.eval('aliasAttr -q %s'%bs)
        attrList_dest = [a for a in attrList_dest if not '[' in a]
        for attr in attrList_source:
            if attr in attrList_dest:
                mc.connectAttr('%s.%s'%(sourceBlendShape, attr),'%s.%s'%(bs, attr), f = 1)
                print('connected:', '%s.%s'%(sourceBlendShape, attr), ' to ', '%s.%s'%(bs, attr))
    mc.undoInfo(cck = True)
    
    
        
def matchCurveShape(srcCrv = None, destCrv = None):
    if not srcCrv or not destCrv:
        srcCrv , destCrv = mc.ls(sl = True)[:2]
        
    numCv_src = mc.getAttr('%s.spans'%srcCrv) + mc.getAttr('%s.degree'%srcCrv)
    numCv_dest = mc.getAttr('%s.spans'%destCrv) + mc.getAttr('%s.degree'%destCrv)
    
    mc.undoInfo(ock = True)
    
    for i in range(numCv_src):
        if i >= numCv_dest:
            break
        pos = mc.pointPosition('%s.cv[%d]'%(srcCrv, i) , l = 1)
        mc.move(pos[0],pos[1],pos[2], '%s.cv[%d]'%(destCrv, i), ls = 1)
        
    mc.undoInfo(cck = True)
    