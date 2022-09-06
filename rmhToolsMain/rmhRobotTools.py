from __future__ import absolute_import
from __future__ import print_function
from six.moves import range
from importlib import reload
import os
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
    
def rmhRobo_connectToFaceCapData(sourceBlendShape = 'shapes', targetBlendShapes = ['eyeL_blendShape', 'eyeR_blendShape', 'mouth_blendShape'], headSourceTrans = 'grp_transform', headDestTrans = 'headCtrl' ):
    def createOffsetControl():
        pts = [-3.03,5.677,0.0],[-3.03,6.419,0.0],[-3.35,7.561,0.0],[-3.641,7.937,0.0],[-3.936,8.323,0.0],[-4.773,8.709,0.0],[-5.294,8.709,0.0],[-5.835,8.709,0.0],[-6.642,8.333,0.0],\
        [-6.953,7.937,0.0],[-7.248,7.556,0.0],[-7.564,6.404,0.0],[-7.564,5.677,0.0],[-7.564,4.209,0.0],[-6.331,2.651,0.0],[-5.294,2.651,0.0],[-4.257,2.651,0.0],[-3.03,4.209,0.0],\
        [-3.03,5.677,0.0],[-2.894,8.553,0.0],[-3.315,9.034,0.0],[-4.538,9.565,0.0],[-5.299,9.565,0.0],[-6.051,9.565,0.0],[-7.268,9.049,0.0],[-7.699,8.553,0.0],[-8.13,8.042,0.0],\
        [-8.596,6.619,0.0],[-8.596,5.677,0.0],[-8.596,4.761,0.0],[-8.135,3.308,0.0],[-7.704,2.812,0.0],[-7.268,2.306,0.0],[-6.056,1.794,0.0],[-5.299,1.794,0.0],[-4.568,1.794,0.0],[-3.35,2.291,0.0],\
        [-2.894,2.812,0.0],[-2.458,3.308,0.0],[-1.998,4.771,0.0],[-1.998,5.677,0.0],[-1.998,6.609,0.0],[-2.469,8.062,0.0],[-2.894,8.553,0.0],[3.554,9.41,0.0],[3.554,9.41,0.0],[-0.91,9.41,0.0], \
        [-0.91,1.95,0.0],[0.082,1.95,0.0],[0.082,5.542,0.0],[3.408,5.542,0.0],[3.408,6.424,0.0],[0.082,6.424,0.0],[0.082,8.528,0.0],[3.554,8.528,0.0],[8.905,9.41,0.0],[8.905,9.41,0.0],[4.441,9.41,0.0],\
        [4.441,1.95,0.0],[5.433,1.95,0.0],[5.433,5.542,0.0],[8.759,5.542,0.0],[8.759,6.424,0.0],[5.433,6.424,0.0],[5.433,8.528,0.0],[8.905,8.528,0.0],[-9.0,0.435,0.0],[-9.0,-3.565,0.0],[-3.0,-3.565,0.0],\
        [-3.0,0.435,0.0],[-9.0,0.435,0.0],[9.0,0.435,0.0],[9.0,-3.565,0.0],[3.0,-3.565,0.0],[3.0,0.435,0.0],[3.0,-5.565,0.0],[7.0,-7.565,0.0],[-5.0,-7.565,0.0],[-5.0,-9.565,0.0],[7.0,-9.565,0.0],[7.0,-7.565,0.0]

        ctrl = 'roboOffsetControl'
        if not mc.objExists(ctrl):
            mc.curve(n = ctrl, p = pts, d = 1)
            mc.move(60,170,0)
            sh = mc.listRelatives(ctrl, s = 1)[0]
            mc.setAttr('%s.overrideEnabled'%sh, 1)
            mc.setAttr('%s.overrideRGBColors'%sh, 1)
            mc.setAttr('%s.lineWidth'%sh,3)
            col = [255,255,0]
            for i,ch in enumerate(['R','G','B']):
                mc.setAttr('%s.overrideColor%s'%(sh,ch), col[i]/ 255.0)
            
            stdVals = {'eyeMultX':0.3, 'eyeMultY':0.1}
            for attr in ['eyeMultX', 'eyeMultY', 'transOffsetX','transOffsetY','transOffsetZ']:
                if not attr in mc.listAttr(ctrl):
                    mc.addAttr(ctrl, ln = attr, at = 'double', k = 1,dv = stdVals.get(attr, 0))
            for attr in ['rotateOffsetX','rotateOffsetY','rotateOffsetZ']:
                if not attr in mc.listAttr(ctrl):
                    mc.addAttr(ctrl, ln = attr, at = 'doubleAngle', k = 1)
        return ctrl
    
    sourceBlendShape = searchObjectsInNamespaces([sourceBlendShape])[0]
    headSourceTrans = searchObjectsInNamespaces([headSourceTrans], 'transform')[0]
    
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
    
    offCtrl = createOffsetControl()
    
    add = mc.createNode('plusMinusAverage',n = '%s_pmaT'%offCtrl)
    
    mc.connectAttr('%s.translate'%(headSourceTrans), '%s.input3D[0]'%add, f = 1)
    mc.connectAttr('%s.transOffsetX'%(offCtrl), '%s.input3D[1].input3Dx'%add, f = 1)
    mc.connectAttr('%s.transOffsetY'%(offCtrl), '%s.input3D[1].input3Dy'%add, f = 1)
    mc.connectAttr('%s.transOffsetZ'%(offCtrl), '%s.input3D[1].input3Dz'%add, f = 1)
    mc.connectAttr('%s.output3D'%add, '%s.translate'%headDestTrans, f = 1)
    
    add = mc.createNode('plusMinusAverage',n = '%s_pmaR'%offCtrl)
    
    mc.connectAttr('%s.rotate'%(headSourceTrans), '%s.input3D[0]'%add, f = 1)
    mc.connectAttr('%s.rotateOffsetX'%(offCtrl), '%s.input3D[1].input3Dx'%add, f = 1)
    mc.connectAttr('%s.rotateOffsetY'%(offCtrl), '%s.input3D[1].input3Dy'%add, f = 1)
    mc.connectAttr('%s.rotateOffsetZ'%(offCtrl), '%s.input3D[1].input3Dz'%add, f = 1)
    mc.connectAttr('%s.output3D'%add, '%s.rotate'%headDestTrans, f = 1)
    
    # mc.connectAttr('%s.%s'%(headSourceTrans,attr),'%s.%s'%(headDestTrans,attr), f = 1)
    # for attr in ['translate', 'rotate']:
    #     mc.connectAttr('%s.%s'%(headSourceTrans,attr),'%s.%s'%(headDestTrans,attr), f = 1)
    
    ########## connect eyes
    
    
    sourceEyeTransL = searchObjectsInNamespaces(['grp_eyeLeft'], 'transform')[0]
    sourceEyeTransR = searchObjectsInNamespaces(['grp_eyeRight'], 'transform')[0]
    
    destEyeTransL = searchObjectsInNamespaces(['eyeL_moveCtrl_bind'], 'transform')[0]
    destEyeTransR = searchObjectsInNamespaces(['eyeR_moveCtrl_bind'], 'transform')[0]
    
    mdiv = mc.createNode('multiplyDivide',n = '%s_eyeMdiv'%offCtrl)
    mc.connectAttr('%s.eyeMultX'%offCtrl, '%s.input1.input1X'%(mdiv), f = 1)
    mc.connectAttr('%s.eyeMultY'%offCtrl, '%s.input1.input1Y'%(mdiv), f = 1)
    mc.connectAttr('%s.rotateY'%sourceEyeTransL, '%s.input2.input2X'%(mdiv), f = 1)
    mc.connectAttr('%s.rotateX'%sourceEyeTransR, '%s.input2.input2Y'%(mdiv), f = 1)
    mc.connectAttr('%s.outputX'%mdiv, '%s.translateX'%destEyeTransL, f = 1)
    mc.connectAttr('%s.outputY'%mdiv, '%s.translateY'%destEyeTransL, f = 1)
    mc.connectAttr('%s.outputX'%mdiv, '%s.translateX'%destEyeTransR, f = 1)
    mc.connectAttr('%s.outputY'%mdiv, '%s.translateY'%destEyeTransR, f = 1)
    
    ####### connect blendshape attrs
    
    for bs in targetBlendShapes:
        # attrList_dest = mc.aliasAttr(bs, q = True)
        attrList_dest = mel.eval('aliasAttr -q %s'%bs)
        attrList_dest = [a for a in attrList_dest if not '[' in a]
        for attr in attrList_source:
            if attr in attrList_dest:
                rng = '%s_%s_rng'%(offCtrl, attr)
                if not mc.objExists(rng):
                    mc.createNode('setRange', n = rng)
                try:
                    mc.setAttr('%s.maxX'%rng,1)
                    mc.setAttr('%s.oldMaxX'%rng,1)
                except:
                    pass
                inVal, rngMinAttr, rngMaxAttr = '%s_val'%attr, '%s_clampMin'%attr,'%s_clampMax'%attr
                for _attr in [inVal, rngMinAttr, rngMaxAttr ]:
                    if not _attr in mc.listAttr(offCtrl):
                        mc.addAttr(offCtrl, ln = _attr, at = 'double', k = 1)
                mc.setAttr('%s.%s'%(offCtrl, rngMaxAttr), 1)
                mc.connectAttr('%s.%s'%(sourceBlendShape, attr), '%s.%s'%(offCtrl, inVal), f = 1)
                mc.connectAttr('%s.%s'%(sourceBlendShape, attr), '%s.valueX'%(rng), f = 1)
                mc.connectAttr( '%s.%s'%(offCtrl, rngMinAttr), '%s.oldMinX'%rng, f = 1)
                mc.connectAttr( '%s.%s'%(offCtrl, rngMaxAttr), '%s.oldMaxX'%rng, f = 1)
                
                # mc.connectAttr('%s.%s'%(sourceBlendShape, attr),'%s.%s'%(bs, attr), f = 1)
                mc.connectAttr('%s.outValueX'%(rng),'%s.%s'%(bs, attr), f = 1)
                print('connected:', '%s.%s'%(sourceBlendShape, attr), ' to ', '%s.%s'%(bs, attr))
    mc.undoInfo(cck = True)
    
def rmhRobo_importFbxAndSound(fbxPath = None):
    if not fbxPath:
        fbxPath = mc.fileDialog2(fm = 1, cap = 'RMH Robo: select faceCap fbx file (sound will be added if samename.wav in same directory)')
        if not fbxPath:
            return
        fbxPath = fbxPath[0]
    
    soundPath = fbxPath.split('.')[0] + '.wav'
    
    mc.file(fbxPath, r = True, type = "FBX",ignoreVersion=1,gl =1, mergeNamespacesOnClash = False,  namespace = "fbxFaceCap", options = "fbx")
    
    if os.path.isfile(soundPath):
        try:
            mc.file(soundPath, i= True, type = "audio", ignoreVersion = 1, mergeNamespacesOnClash = False, options = "o=0" , pr = True)
        except:
            mc.warning('couldnt import sound from %s'%soundPath)
        mc.playbackOptions(ps = 1)
    # file -import -type "audio"  -ignoreVersion -mergeNamespacesOnClash false -rpr "FC_2022_9_5_16_59_47_p3" -options "o=0"  -pr "%s";

        
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
    

