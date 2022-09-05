

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
import maya.OpenMaya as api
import maya.OpenMayaUI as apiUI

import os, random, math, shutil, subprocess
import __main__
import rmhTools_widgets as pw

import rmhMayaMethods as rmm
reload(rmm)




def BWFpf_shootBullet(name = 'bulletAnim', numRings = None, animLen = None, initTime = None, ringTimeOffset = 0, lineFadeTime = 25, lineThickness = 1):
    def checkExistence(oList):
        out = []
        for o in oList:
            if not mc.objExists(o):
                out.append(o)
        if out:
            mc.warning('following objects not found: \n%s ... will try to import from script dir'%'\n'.join(out))
        else:
            return True
    def getTrans(obj):
        ga = mc.getAttr
        return [['translateX', ga('%s.translateX'%obj)],['translateY', ga('%s.translateY'%obj)],['translateZ', ga('%s.translateZ'%obj)],  ['rotateX', ga('%s.rotateX'%obj)],['rotateY',ga('%s.rotateY'%obj)],['rotateZ',ga('%s.rotateZ'%obj)]]
    def setTrans(obj, vals):
        for at, val in vals:
            mc.setAttr('%s.%s'%(obj, at) , val)
    def setKey(obj, vals, time, skipRotate = False):
        for at, val in vals:
            if skipRotate and 'rotate' in at:
                continue
            mc.setKeyframe('%s.%s'%(obj, at) , v= val, t = time, itt = 'linear', ott = 'linear')
    def setScaleKey(obj, time, val, ats = ['scaleX','scaleY','scaleZ'], tan = 'step'):
        for at in ats:
            mc.setKeyframe('%s.%s'%(obj, at), v = val, t = time, itt = tan, ott = tan)
    
    if not numRings:
        numRings, ok = QInputDialog.getInt(None, 'BWFpf_shootBullet', 'numRings: ', value = 15, min = 1, max = 1000)
        if not ok:
            return
        
    if not animLen:
        animLen, ok = QInputDialog.getInt(None, 'BWFpf_shootBullet', 'animLen (frames): ', value = 100, min = 1, max = 1000)
        if not ok:
            return
        
        
    sel = mc.ls(sl = True)
    
    if initTime == None:
        initTime = mc.currentTime(q = True)
    
    bulletObj = 'bulletGrp'
    ringObj = 'ringGrp'
    lineObj = 'lineObj'
    
    if not checkExistence([bulletObj, ringObj, lineObj]):
        fileDir = os.path.dirname(os.path.realpath(__file__))
        # print fileDir
        # fileDir = fileDir.replace('\\', '/')
        # baseDir = '/'.join(fileDir.split('/')[:-1])
        assetPath = '%s/assets/bulletSetup.mb'%fileDir
        try:
            mc.file(assetPath, i = True, ignoreVersion = True, ra = False, mergeNamespacesOnClash = False ,  options = "v=0;" , pr = True)
        except:
            mc.error('couldnt find bullet objects and couldnt import asset file %s'%assetPath)
            return
    
    if mc.objExists('bulletSetup'):
        mc.hide('bulletSetup')
    
    mc.undoInfo(ock = True)
    for crv in sel:
        metaGrp = rmm.findUniqueName(name)
        mc.group(n = metaGrp, em = True)
        sh = mc.listRelatives(crv, s = 1)
        if not sh or not mc.objectType(sh[0]) == 'nurbsCurve':
            mc.warning('%s is not a nurbsCurve, skipping'%crv)
            continue
        bullet_d = mc.duplicate(bulletObj, rr = 1, rc = 1)[0]
        # ring = mc.duplicate(ringObj, rr = 1, rc = 1, un = 1)[0]
        line_d = mc.duplicate(lineObj, rr = 1, rc = 1)[0]
        # crv_d = mc.duplicate(crv, rr = 1, rc = 1)[0]
        
        mc.setAttr('%s.v'%bullet_d, 1)
        # mc.setAttr('%s.v'%ring_d, 1)
        mc.setAttr('%s.v'%line_d, 1)
        
        ####### animate bullet
        
        mpath = mc.pathAnimation(bullet_d, crv, fm = True, follow = True, fa = 'z', ua = 'y', worldUpType = 'vector', worldUpVector = (0,1,0))#, iu = False, if = False, bank = False, startTimeU = 0)
        mc.cutKey('%s.uValue'%mpath, t = (-1,10000))
        mc.setAttr('%s.uValue'%mpath, 0)
        mc.refresh()
        vals01 = getTrans(bullet_d)
        mc.setAttr('%s.uValue'%mpath, 1)
        mc.refresh()
        vals02 = getTrans(bullet_d)
        mc.delete(mpath)
        setKey(bullet_d, vals01, time = initTime)
        setKey(bullet_d, vals02, time = initTime+animLen, skipRotate = True)
        setScaleKey(bullet_d, initTime-1, 0, tan = 'clamped')
        setScaleKey(bullet_d, initTime, 1, tan = 'clamped')
        setScaleKey(bullet_d, initTime+animLen, 1, tan = 'clamped')
        setScaleKey(bullet_d, initTime+animLen+1, 0, tan = 'clamped')
        ######## attach rings
        
        dc = rmm.distributeAlongCurve(srcObjs = [ringObj], destObjs = [crv], randomDist = False, follow = True,\
                                 num = numRings, uvRange = [0,1], frontRange = [0,220], upRange = [0,110], sideRange= [0,0], scaleRange = [1,1], upstreamNodes = True, stayAttached = 1)
        ring_dups = dc['dups']
        dupGrp = dc['roots'][0]
        
        mc.delete(ring_dups.pop(0))
        
        frameDelta = float(animLen) / len(ring_dups)
        rmm.successiveKeyOffset(objs = ring_dups, frameRange = None, timeOffset = initTime+ringTimeOffset, offsetDeltaRange = [frameDelta,frameDelta], shuffleArray = False, hierarchy = True)
        
        ######## attach line
        
        mpath = mc.pathAnimation(line_d, crv, fm = True, follow = True, fa = 'y', ua = 'z', worldUpType = 'vector', worldUpVector = (0,1,0))#, iu = False, if = False, bank = False, startTimeU = 0)
        mc.cutKey('%s.uValue'%mpath, t = (-1,10000))
        mc.setAttr('%s.uValue'%mpath, 0)
        mc.refresh()
        mc.delete(mpath)
        crvLen = mc.arclen(crv)
        mc.setKeyframe('%s.scaleY'%line_d, v = 0, t = initTime, itt = 'linear', ott = 'linear')
        mc.setKeyframe('%s.scaleY'%line_d, v = crvLen, t = initTime+animLen, itt = 'linear', ott = 'linear')
        
        setScaleKey(line_d, initTime+animLen-lineFadeTime/2, lineThickness, tan = 'flat', ats = ['scaleX','scaleZ'])
        setScaleKey(line_d, initTime+animLen+lineFadeTime/2, 0, tan = 'flat', ats = ['scaleX','scaleZ'])
        
        
        mc.parent(bullet_d, metaGrp)
        mc.parent(line_d, metaGrp)
        mc.parent(dupGrp, metaGrp)
        # mc.parent(crv_d, metaGrp)
        
        
    mc.undoInfo(cck = True)


def BW_scaleNonVisibleToZero():
    mc.undoInfo(ock = True)

    for obj in mc.ls(sl = True):
        keysAt = [k for k in mc.keyframe('%s.v'%obj, q = True) if mc.getAttr('%s.v'%obj, t = k) == 0]
        for k in keysAt:
            for at in ['scaleX','scaleY','scaleZ']:
                val = mc.getAttr('%s.%s'%(obj, at))
                mc.setKeyframe('%s.%s'%(obj, at), t = k-1, v = val, itt = 'linear', ott = 'linear')
                mc.setKeyframe('%s.%s'%(obj, at), t = k, v = 0, itt = 'linear', ott = 'linear')
                
    mc.undoInfo(cck = True)

            
            
            
            
        