# -*- coding: iso-8859-1 -*-
from __future__ import absolute_import
import six
from importlib import reload
try:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
    import shiboken2
    # print "Using PySide2"
except:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from shiboken import wrapInstance
    # print "Using PySide"

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget

import maya.cmds as mc
import maya.mel as mel
import maya.OpenMaya as api
import maya.OpenMayaUI as apiUI
import MASH.api as mapi

import os, random, math, shutil, subprocess
import binascii
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

def BWInf_makeLetterGroups():
    abc = [l for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']
    abc_plus = ['AE', 'OE', 'UE', 'SS', '_STR', '_PKT', '_SLH']#'ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜß-./'
    
    letterList = abc + abc_plus
    
    
    mc.undoInfo(ock = True)
    metaGrp = 'BWInf_letterGrp'
    if not mc.objExists(metaGrp):
        mc.group(n = metaGrp, em = True)
    for lt in letterList:
        g = '%s_grp'%lt
        if not mc.objExists(g):
            mc.group(n = g, em = True)
            mc.parent(g, metaGrp)
    
    mc.undoInfo(cck = True)
    
    return metaGrp
    
def BWInf_distributeObjectsToLetterGroups():
    sel = mc.ls(sl = True)
    metaGrp = BWInf_makeLetterGroups()
    grps = mc.listRelatives(metaGrp)
    
    mc.undoInfo(ock = True)
    for i,obj in enumerate(sel):
        if i > len(grps):
            break
        grp = grps[i]
        mc.parent(obj, grp)
    mc.undoInfo(cck = True)

def BWInf_renameAbc():
    abc = [l for l in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']
    sel = mc.ls(sl = True)
    
    mc.undoInfo(ock = True)
    for i,obj in enumerate(sel):
        let = abc[i%len(abc)]
        mc.rename(obj, 'tx_%s'%let)
    
    mc.undoInfo(cck = True)

def BWInf_makeGyroConnections(srcObj = None, destObjs = None):
    if not srcObj or not destObjs:
        sel = mc.ls(sl = True)
        srcObj = sel[0]
        destObjs = sel[1:]
    
    mc.undoInfo(ock = True)
    
    for obj in destObjs:
        attrs = ['offsetX','offsetY','offsetZ', 'multX','multY','multZ']
        attrs_da = ['outRotateX','outRotateY','outRotateZ']
        
        for attr in attrs:
            if not attr in mc.listAttr(obj):
                mc.addAttr(obj, ln = attr, at = 'double', k = 1)
        for attr in attrs_da:
            if not attr in mc.listAttr(obj):
                mc.addAttr(obj, ln = attr, at = 'doubleAngle', k = 1)
                
        off = mc.createNode('plusMinusAverage', n = '%s_off'%obj)
        mult = mc.createNode('multiplyDivide', n = '%s_mult'%obj)
        
        mc.connectAttr('%s.rotateX'%srcObj, '%s.input1.input1X'%mult, f = 1)
        mc.connectAttr('%s.rotateY'%srcObj, '%s.input1.input1Y'%mult, f = 1)
        mc.connectAttr('%s.rotateZ'%srcObj, '%s.input1.input1Z'%mult, f = 1)
        
        mc.connectAttr('%s.multX'%obj, '%s.input2.input2X'%mult, f = 1)
        mc.connectAttr('%s.multY'%obj, '%s.input2.input2Y'%mult, f = 1)
        mc.connectAttr('%s.multZ'%obj, '%s.input2.input2Z'%mult, f = 1)
        
        mc.connectAttr('%s.outputX'%mult, '%s.input3D[0].input3Dx'%off, f = 1)
        mc.connectAttr('%s.outputY'%mult, '%s.input3D[0].input3Dy'%off, f = 1)
        mc.connectAttr('%s.outputZ'%mult, '%s.input3D[0].input3Dz'%off, f = 1)
        
        mc.connectAttr('%s.offsetX'%obj, '%s.input3D[1].input3Dx'%off, f = 1)
        mc.connectAttr('%s.offsetY'%obj, '%s.input3D[1].input3Dy'%off, f = 1)
        mc.connectAttr('%s.offsetZ'%obj, '%s.input3D[1].input3Dz'%off, f = 1)
        
        mc.connectAttr('%s.output3D.output3Dx'%off, '%s.outRotateX'%obj,  f = 1)
        mc.connectAttr('%s.output3D.output3Dy'%off, '%s.outRotateY'%obj,  f = 1)
        mc.connectAttr('%s.output3D.output3Dz'%off, '%s.outRotateZ'%obj,  f = 1)
        
        mc.connectAttr('%s.outRotateX'%obj, '%s.rotateX'%obj, f = 1)
        mc.connectAttr('%s.outRotateY'%obj, '%s.rotateY'%obj, f = 1)
        mc.connectAttr('%s.outRotateZ'%obj, '%s.rotateZ'%obj, f = 1)
        
    mc.undoInfo(cck = True)

def BWInf_gyro_setRandomValues():
    result = mc.promptDialog(title='BWInf_gyro_setRandomValues',message='offset range:',button=['OK', 'Cancel'], defaultButton='OK',cancelButton='Cancel', dismissString='Cancel', text = '-180,180')
    if result != 'OK':
        return
    tx = mc.promptDialog(query=True, text=True)
    range_off = list(map(float, tx.split(',')))
    
    result = mc.promptDialog(title='BWInf_gyro_setRandomValues',message='mult range:',button=['OK', 'Cancel'], defaultButton='OK',cancelButton='Cancel', dismissString='Cancel', text = '-4,4')
    if result != 'OK':
        return
    tx = mc.promptDialog(query=True, text=True)
    range_mult = list(map(float, tx.split(',')))
    
    mc.undoInfo(ock = True)
    for obj in mc.ls(sl = True):
        if not 'multX' in mc.listAttr(obj):
            continue
        for d in ['X','Y','Z']:
            rnd_o = random.uniform(range_off[0], range_off[1])
            rnd_m = random.uniform(range_mult[0], range_mult[1])
            mc.setAttr('%s.mult%s'%(obj, d), rnd_m)
            mc.setAttr('%s.offset%s'%(obj, d), rnd_o)
        
    mc.undoInfo(cck = True)

def BWInf_textToSpacedHex(text = 'test ahahaha 345345'):
    hx = str(text.encode("iso-8859-1").hex())
    hx = " ".join([hx[i:i+2] for i in range(0, len(hx), 2)] )
    return hx

def BWInf_setOptsByType(obj, opts):
    for key in opts.keys():
        val = opts[key]
        if not key in mc.listAttr(obj):
            continue
        if type(val) in [str,six.text_type]:
            mc.setAttr('%s.%s'%(obj, key), val, type = 'string')
        else:
            mc.setAttr('%s.%s'%(obj, key), val)

def BWInf_textListToType(textList = None, importType = None, t_opts = {'currentFont':'BundesSans', 'fontSize':12, 'alignmentMode':2 }, extrudeOpts = {'extrudeDistance':0.1, 'extrudeDivisions':1 }, attachToSel = False):
    if textList == None:
        result = mc.promptDialog(title='BWInf_textListToType',message='textList:',button=['OK', 'Cancel'], defaultButton='OK',cancelButton='Cancel', dismissString='Cancel', text = 'text1;text2')
        if result != 'OK':
            return
        textList = mc.promptDialog(query=True, text=True)
        textList = textList.split(';')
    
    if importType == None:
        importType = mc.confirmDialog(title='BWInf_textListToType',message='importType:',button=['pure', 'split', 'visCtrl', 'mash', 'Cancel'], defaultButton='OK',cancelButton='Cancel', dismissString='Cancel')
        if importType == 'Cancel':
            return
        
    t3dnodes = []
    t3dtranses = []
    sel = mc.ls(sl = True)
        
    mc.undoInfo(ock = True)
    for text in textList:
        hx = BWInf_textToSpacedHex(text)
        mel.eval('CreatePolygonType')
        t3d_trans = mc.ls(sl = True)[0]
        t3d_node = mc.listConnections('%s.message'%t3d_trans)[0]
        t3d_extrude = mc.listConnections('%s.outputMesh'%t3d_node)[0]
        mc.setAttr('%s.textInput'%t3d_node, hx, type = 'string')
        
        BWInf_setOptsByType(t3d_node, t_opts)
        BWInf_setOptsByType(t3d_extrude, extrudeOpts)
        
        txt_t = text.replace(' ','')
        txt_t = txt_t.replace('-','')
        newName = rmm.findUniqueName(txt_t[:8]+'_tx')
        t3d_trans = mc.rename(t3d_trans, newName)
        newName = rmm.findUniqueName('type_'+txt_t[:8])
        t3d_node = mc.rename(t3d_node, newName)
        
        t3dnodes.append(t3d_node)
        t3dtranses.append(t3d_trans)
    
    if importType == 'split':
        BWInf_splitObjects(t3dtranses)
    elif importType == 'visCtrl':
        # try:
        import partyRigTools
        for t3dtrans in t3dtranses:
            ctrl = BWInf_createControl('%s_ctrlt'%t3dtrans, addToGroup = 'ctrl_g')
            splitObjs = BWInf_splitObjects([t3dtrans])
            mc.parentConstraint(ctrl, t3dtrans)
            mc.scaleConstraint(ctrl, t3dtrans)
            mc.addAttr(ctrl, ln = 'visAnim', at = 'double', minValue = -1, maxValue = len(splitObjs) + 1 , k = 1, dv = len(splitObjs))
            partyRigTools.createMultiVisibilityControl(objs = splitObjs, ctrl = ctrl, ctrlName = False, attrName = 'visAnim', limitValues = False)
        # except:
        #     print('partyRigTools not available')
            
    elif importType == 'mash':
        for t3dtrans in t3dtranses:
            splitObjs = BWInf_splitObjects([t3dtrans])
            BWInf_createMashFromObjects(splitObjs)
    
    mc.undoInfo(cck = True)
        
    return t3dnodes, t3dtranses

def BWInf_createControl(name, addToGroup = None):
    pts = [[0.0,4.0,0.0],[0.0,3.696,1.532],[0.0,2.828,2.828],[0.0,1.532,3.696],[0.0,0.0,4.0],[0.0,-1.532,3.696],[0.0,-2.828,2.828],[0.0,-3.696,1.532],[0.0,-4.0,0.0],[0.0,-3.696,-1.532],[0.0,-2.828,-2.828],[0.0,-1.532,-3.696],[0.0,0.0,-4.0],[0.0,1.532,-3.696],[0.0,2.828,-2.828],\
    [0.0,3.696,-1.532],[0.0,4.0,0.0],[1.532,3.696,0.0],[2.828,2.828,0.0],[3.696,1.532,0.0],[4.0,0.0,0.0],[3.696,-1.532,0.0],[2.828,-2.828,0.0],[1.532,-3.696,0.0],[0.0,-4.0,0.0],[-1.532,-3.696,0.0],[-2.828,-2.828,0.0],[-3.696,-1.532,0.0],[-4.0,0.0,0.0],\
    [-3.696,1.532,0.0],[-2.828,2.828,0.0],[-1.532,3.696,0.0],[0.0,4.0,0.0],[0.0,3.696,-1.532],[0.0,2.828,-2.828],[0.0,1.532,-3.696],[0.0,0.0,-4.0],[-1.532,0.0,-3.696],[-2.828,0.0,-2.828],[-3.696,0.0,-1.532],[-4.0,0.0,0.0],[-3.696,0.0,1.532],\
    [-2.828,0.0,2.828],[-1.532,0.0,3.696],[0.0,0.0,4.0],[1.532,0.0,3.696],[2.828,0.0,2.828],[3.696,0.0,1.532],[4.0,0.0,0.0],[3.696,0.0,-1.532],[2.828,0.0,-2.828],[1.532,0.0,-3.696],[0.0,0.0,-4.0]]

    c = mc.curve(p = pts, d = 3)
    name = rmm.rename_individual(c, name)
    rmm.setCurveColor(crvs = name, col = [255,255,0])
    
    if addToGroup:
        rmm.rmh_createGroupIfNonExistent(addToGroup)
        mc.parent(name, addToGroup)
        
    return name.replace('|', '')
    
def BWInf_createInitialTransforms(objs = None, addToGroup = None, addControl = True):
        
    if not objs:
        objs = mc.ls(sl = True)
    
    if addToGroup and not mc.objExists(addToGroup):
        mc.group(n = addToGroup, em = True)
    
    out = []
    out_groups = []
    out_controls = []
    out_origGroups_dc = {}
    
    mc.undoInfo(ock = True)
    for obj in objs:
        t = '%s_init'%obj
        if mc.objExists(t):
            print('%s exists'%t)
            out.append(t)
            continue
        p = mc.listRelatives(obj, p = True)
        mc.createNode('transform', n = t)
        c = mc.parentConstraint(obj, t, mo = False)
        mc.delete(c)
        grpName = None
        if addToGroup:
            mc.parent(t, addToGroup)
            grpName = addToGroup
        elif p:
            rig_g = rmm.rmh_createGroupIfNonExistent('rig_g')
            p_group = rmm.rmh_createGroupIfNonExistent('%s_initGrp'%p[0], rig_g)
            mc.parent(t, p_group)
            grpName = p_group
        else:
            rig_g = rmm.rmh_createGroupIfNonExistent('rig_g')
            stdGrp = rmm.rmh_createGroupIfNonExistent('%s_initGrp'%objs[0], rig_g)
            mc.parent(t, stdGrp)
            grpName = stdGrp
            
        if not grpName in out_groups:
            out_groups.append(grpName)
            if p:
                out_origGroups_dc[grpName] = p[0]
        out.append(t)
    
    if addControl:
        ctrl_g = rmm.rmh_createGroupIfNonExistent('ctrl_g')
        for grp in out_groups:
            ctrl = BWInf_createControl('%s_ctrl'%(grp.split('_')[0]) )
            
            orig_grp = out_origGroups_dc.get(grp, None)
            if orig_grp:
                objs = mc.listRelatives(orig_grp, type = 'transform')
                for obj in objs:
                    rmm.connectMessageAttribute(srcs = ctrl, target = obj, messageAttr = 'typeCtrl')
                rmm.connectMessageAttribute(srcs = objs, target = ctrl, messageAttr = 'typeObjs')
            
            mc.parentConstraint(ctrl, grp, mo = False)
            mc.scaleConstraint(ctrl, grp, mo = False)
            out_controls.append(ctrl)
            mc.parent(ctrl, ctrl_g)
            
    mc.undoInfo(cck = True)
    
    return out, out_groups, out_controls
    
def BWInf_splitObjects(objs = None, triangulate = True):
    mc.undoInfo(ock = True)
    out = []
    for obj in objs:
        mc.select(obj)
        mel.eval('DeleteHistory;')
        mc.xform(obj, cp = True)
        if triangulate:
            mc.polyTriangulate(obj, ch = 0)
        try:
            mc.polySeparate(obj, ch = 0)
        except:
            print(' split failed for %s'%obj)
            continue
        chs = mc.listRelatives(obj)
        for i,ch in enumerate(chs):
            new = mc.rename(ch, '%s_p%03d'%(obj, i))
            mc.xform(new, cp = True)
            out.append(new)
    mc.undoInfo(cck = True)
    return out

def BWInf_createMashFromObjects(objs = None, initGroup = None, mashName = None):
    if not objs:
        objs = mc.ls(sl = True)
        
    mc.undoInfo(ock = True)
    
    msh_g = rmm.rmh_createGroupIfNonExistent('MSH_g', hide = True)
    
    initObjs, initGrps, ctrls = BWInf_createInitialTransforms(objs, addToGroup = initGroup, addControl = True)
    
    if mashName == None:
        if ctrls:
            mashName = ctrls[0].split('_')[0] + '_Mash'
        else:
            mashName = 'splMash'
    
    tmpCube = 'mash_tmpCube'
    if not mc.objExists(tmpCube):
        tmp_t = rmm.rmh_createGroupIfNonExistent('TMP_g', hide = True)
        mc.polyCube(n = tmpCube, ch = 0)
        mc.parent(tmpCube, tmp_t)
    
    mc.select(clear = True)
    mashNetwork = mapi.Network()
    mashNetwork.createNetwork(name=mashName)
    mashNetwork.setPointCount(len(initObjs))
    
    id_node = mashNetwork.addNode("MASH_ID")
    rnd_node = mashNetwork.addNode("MASH_Random")
    
    mash = mashNetwork.waiter
    dist = mashNetwork.distribute
    
    reproMesh = mash + '_ReproMesh'
    mc.parent(reproMesh, msh_g)
        
    rmm.rmh_MASH_addObjectsToRepro([tmpCube], mash, replace = True)
    rmm.rmh_MASH_initialStateFromObjects(objs = initObjs, mashWaiters = [mash])
    
    # mashNetwork.setData(mashNetwork.getData())
    
    breakouts, b_locs = rmm.rmh_MASH_breakoutAll(mashWaiters = [mash], locNameBase = None, translate = True, rotate = True, scale = True, connect = True, toGroup = None)
    
    for loc,obj in zip(b_locs, objs):
        mc.parentConstraint(loc, obj)
        mc.scaleConstraint(loc, obj)
    
    stdVals = {'randEnvelope':0,'randomSeed':1, 'scatterAmpPosX':150,'scatterAmpPosY':50,'scatterAmpPosZ':150, 'scatterAmpRot':100}
    minmaxVals =  {'randEnvelope':[0,1], 'randomSeed':[1,3453454]}
    if ctrls:
        ctrl = ctrls[0]
        for attr in ['randEnvelope', 'randomSeed', 'scatterAmpPosX', 'scatterAmpPosY', 'scatterAmpPosZ', 'scatterAmpRot']:
            if not attr in mc.listAttr(ctrl):
                mc.addAttr(ctrl, ln = attr, at = 'double', k = 1, dv = stdVals.get(attr, 0), minValue = minmaxVals.get(attr, [-10000,10000])[0], maxValue = minmaxVals.get(attr, [-10000,10000])[1])
            
        mc.connectAttr('%s.scatterAmpPosX'%ctrl, '%s.positionX'%rnd_node.name)
        mc.connectAttr('%s.scatterAmpPosY'%ctrl, '%s.positionY'%rnd_node.name)
        mc.connectAttr('%s.scatterAmpPosZ'%ctrl, '%s.positionZ'%rnd_node.name)
        mc.connectAttr('%s.scatterAmpRot'%ctrl, '%s.rotationX'%rnd_node.name)
        mc.connectAttr('%s.scatterAmpRot'%ctrl, '%s.rotationY'%rnd_node.name)
        mc.connectAttr('%s.scatterAmpRot'%ctrl, '%s.rotationZ'%rnd_node.name)
        mc.connectAttr('%s.randEnvelope'%ctrl, '%s.randEnvelope'%rnd_node.name)
        mc.connectAttr('%s.randomSeed'%ctrl, '%s.randomSeed'%rnd_node.name)
            
    
    mc.undoInfo(cck = True)

def BWInf_changeTextOptions(objs = None, t_opts = {'currentFont':'BundesSans' }):
    if not objs:
        objs = mc.ls(sl = True)
    
    for obj in objs:
        t3d_node = mc.listConnections('%s.message'%obj)[0]
        # t3d_extrude = mc.listConnections('%s.outputMesh'%obj)[0]
        BWInf_setOptsByType(t3d_node, t_opts)

def BWInf_text_addScaleControl(textCtrls = None):
    if not textCtrls:
        textCtrls = mc.ls(sl = True)
        
    mc.undoInfo(ock = True)
    
    for ctrl in textCtrls:
        if not 'typeObjs' in mc.listAttr(ctrl):
            continue
        objs = mc.listConnections('%s.typeObjs'%ctrl, d = 0, s = 1)
        if not objs:
            continue
        for obj in objs:
            cons = mc.listConnections('%s.scaleX'%obj, s = 1, d = 0)
            if cons:
                print('BWInf_text_addScaleControl: skip %s'%obj)
                continue
            mc.scaleConstraint(ctrl, obj, mo = False)

    mc.undoInfo(cck = True)

def BWInf_MASH_addScaleControl_breakouts(objs = None, mo = False, asConnection = False):
    def getConnectedLoc(obj):
        pcs = mc.listRelatives(obj, type = 'parentConstraint')
        if pcs:
            cons = mc.listConnections('%s.target'%pcs[0])
            cons = mc.ls(cons, type = 'transform')
            if cons:
                return cons[0]
            
        
    if not objs:
        objs = mc.ls(sl = True)
        
    mc.undoInfo(ock = True)
    
    for obj in objs:
        loc = getConnectedLoc(obj)
        if not loc:
            continue
        
        cons = mc.listConnections('%s.scaleX'%obj, s = 1, d = 0)
        if cons:
            print('BWInf_text_addScaleControl: skip %s'%obj)
            continue
        if asConnection:
            mc.connectAttr('%s.scale'%loc, '%s.scale'%obj)
        else:
            mc.scaleConstraint(loc, obj, mo = mo)

    mc.undoInfo(cck = True)

def BWInf_createConnection(objs = None):
    try:
        import partyCurveTools
    except:
        print('function unavailable')
        return
    if not objs:
        objs = mc.ls(sl = True)
    
    # for i in range(0,len(objs) / 2, 2):
    # obj01, obj02 = objs[i], objs[i+1]
    
    out = []
    for obj in objs:
        if 'nLoc_rot' in mc.listAttr(obj):
            con = mc.listConnections('%s.nLoc_rot'%obj, s = 1, d = 0)
            if con:
                out.append(con[0])
                continue
            out.append(obj)
    objs = out
    
    mc.undoInfo(ock = True)
    outCrv = partyCurveTools.createCurveBetweenObjects(objs = objs, makeSubCurve = True, createClusters = True, returnClusters = False)
    outCrv_sub = outCrv + '_sub'
    rmm.setCurveColor(crvs = [outCrv_sub], col = [255,255,255])
    rmm.rmh_addSubCurveClipControl([outCrv_sub])
    
    centerLoc = partyCurveTools.attachLocatorsAtCurvePoints(follow = False, uValues = [0.5], obj = outCrv, asTransform = False)[0]
    mc.setAttr('%s.uValue'%centerLoc, 0.5)
    rmm.connectMessageAttribute(srcs = [outCrv], target = centerLoc, messageAttr = 'crv_main')
    rmm.connectMessageAttribute(srcs = [outCrv_sub], target = centerLoc, messageAttr = 'crv_sub')
    
    stdVals = {'minCurve':0,'maxCurve':1}
    for attr in ['minCurve','maxCurve']:
        mc.addAttr(centerLoc, ln = attr, at = 'double',  minValue = 0, maxValue = 1, dv = stdVals.get(attr,0), k = 1)
        mc.connectAttr('%s.%s'%(centerLoc, attr), '%s.%s'%(outCrv_sub, attr), f = 1)
    
    mc.undoInfo(cck = True)
    
    
def BWInf_createUValueOffsetAttr(objs = None):
    if not objs:
        objs = mc.ls(sl = True)
    
    mc.undoInfo(ock = True)
    
    for obj in objs:
        if not 'uValue' in mc.listAttr(obj):
            continue
        val = mc.getAttr('%s.uValue'%obj)
        for attr in ['uInValue', 'uOffset']:
            if not attr in mc.listAttr(obj):
                mc.addAttr(obj, ln = attr, at = 'double', k = 1)
        mc.setAttr('%s.uInValue'%obj, val)
        expTx = 'uValue = uInValue + uOffset;'
        mc.expression(n = '%s_uvalExp'%obj, s = expTx, o = obj)
        
    mc.undoInfo(cck = True)
    
def BWInf_connectUValueToOffsetObject(srcObj = None, objs = None):
    if not objs or not srcObj:
        srcObj = mc.ls(sl = True)[0]
        objs = mc.ls(sl = True)[1:]
    
    mc.undoInfo(ock = True)
    
    for obj in objs:
        print(obj, ':...')
        if not 'uInValue' in mc.listAttr(obj):
            continue
        mc.connectAttr('%s.uValue'%srcObj, '%s.uInValue'%obj , f = 1)

    mc.undoInfo(cck = True)

class ModelPanelWrapper(QWidget):
    def __init__(self, parent = None, name = "customModelPanel#", label="caveCam01", cam='caveCam01', mbv = False, aspect_ratio = [1,1]):
        super(ModelPanelWrapper, self).__init__(parent)
        
        self.aspect_ratio = aspect_ratio
        self.w = QWidget()
        self.verticalLayout = QVBoxLayout(self.w)
        self.verticalLayout.setContentsMargins(0,0,0,0)
        
        layname = "modelPanelLayout%06d"%random.randint(0,3553455)
        self.verticalLayout.setObjectName(layname)
        
        layout = apiUI.MQtUtil.fullName(int(shiboken2.getCppPointer(self.verticalLayout)[0]))
        mc.setParent(layname)
        self.panel = mc.modelPanel(name, label=label, cam=cam, mbv = mbv)
    
        self.setLayout(self.verticalLayout)
        
    # def resizeEvent(self, event):
    #     width = event.size().width()
    #     height = width * self.aspect_ratio[1] / self.aspect_ratio[0]
    #     self.resize(width, height)
        


class RMH_CavePreviewUI(MayaQWidgetDockableMixin, QDialog):
    toolName = 'RMH_CavePreviewUI'
    def __init__(self, parent, **kwargs):
        super(RMH_CavePreviewUI, self).__init__(parent, **kwargs)
        
        refBut = pw.makeButton('refresh', self.setCaveCams)
        #self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.w = QWidget()
        self.verticalLayout = QHBoxLayout(self.w)
        # self.verticalLayout = QVBoxLayout(self.w)
        # self.verticalLayout.setContentsMargins(2,2,2,2)

        # self.verticalLayout.setObjectName("mainLayoutCave")
        
        # First use SIP to unwrap the layout into a pointer
        # Then get the full path to the UI in maya as a string
        # layout = apiUI.MQtUtil.fullName(int(shiboken2.getCppPointer(self.verticalLayout)[0]))
        # mc.setParent("mainLayoutCave")
        
        self.panelLayoutGrid = QGridLayout()
        # panelLayoutWidget = AspectRatioWidget(aspect_ratio = [3.6, 1])
        # panelLayoutWidget.setLayout(self.panelLayoutGrid)
        
        self.panel01 = ModelPanelWrapper(self,"customModelPanel#", label="caveCam02", cam='caveCam02', mbv = False, aspect_ratio = [3.536, 2.21])
        self.panel02 = ModelPanelWrapper(self,"customModelPanel#", label="caveCam01", cam='caveCam01', mbv = False, aspect_ratio = [1, 1])
        self.panel03 = ModelPanelWrapper(self,"customModelPanel#", label="caveCam03", cam='caveCam03', mbv = False, aspect_ratio = [1, 1])
        self.panel04 = ModelPanelWrapper(self,"customModelPanel#", label="caveCam04", cam='caveCam04', mbv = False, aspect_ratio = [3.536, 2.21])
        
        self.cams = ['caveCam02','caveCam01','caveCam03','caveCam04']
        
        # self.panelLayoutGrid.addWidget(self.panel01, 0,0, stretch = 0.5)
        # self.panelLayoutGrid.addWidget(self.panel02, 0,1, stretch = 1.6)
        # self.panelLayoutGrid.addWidget(self.panel03, 0,2, stretch = 0.5)
        # self.panelLayoutGrid.addWidget(self.panel01, 0,0)
        # self.panelLayoutGrid.addWidget(self.panel02, 0,1)
        # self.panelLayoutGrid.addWidget(self.panel03, 0,2)
        # self.panelLayoutGrid.addWidget(self.panel04, 1,3)
        
        # self.verticalLayout.addWidget(self.panel02,1)
        # self.verticalLayout.addWidget(self.panel01,1)
        # self.verticalLayout.addWidget(self.panel03,1)
        # self.verticalLayout.addWidget(self.panel04,1)
        
        # mainLayout = pw.makeBoxLayout([self.panelLayoutGrid, QWidget()])
        
        self.setCaveCams()
        
        # self.setLayout(mainLayout)
        # self.setObjectName("CavePreview")
        self.resize(400, 900)
        self.setWindowTitle("RMH_CavePreviewUI")
        
    def setCaveCams(self):
        for i,panel in enumerate( [self.panel01.panel,self.panel02.panel,self.panel03.panel,self.panel04.panel]):
            me = mc.modelPanel(panel,me = True, q = True)
            mc.modelEditor( me, edit=True, grid = False , hud = False)
            mc.modelPanel(panel, e = True,  mbv = False)
            
            bar = mc.modelPanel(panel, q=True, barLayout=True)
            mc.frameLayout(bar, e=True, collapse=True)
            
            try:
                # mc.modelPanel(panel, e = True, cam='caveCam%02d'%(i+1))
                mc.modelPanel(panel, e = True, cam=self.cams[i])
            except:
                mc.warning('coulnd set caveCam%02d'%(i+1))
    
    def resizeEvent(self, event):
        w,h = self.width(), self.height()
        pctArray = [ [0*w,0,0.27777777*w,0.27777777*w], [0.27777777*w,0, 0.44783*w, 0.27777777*w], [(1-0.27777777)*w,0,0.27777777*w,0.27777777*w],\
                                                        [0.27777777*w,0.27777777*w, 0.44783*w, 0.27777777*w] ]
        
        self.panel01.setGeometry(pctArray[0][0],pctArray[0][1],pctArray[0][2],pctArray[0][3])
        self.panel02.setGeometry(pctArray[1][0],pctArray[1][1],pctArray[1][2],pctArray[1][3])
        self.panel03.setGeometry(pctArray[2][0],pctArray[2][1],pctArray[2][2],pctArray[2][3])
        self.panel04.setGeometry(pctArray[3][0],pctArray[3][1],pctArray[3][2],pctArray[3][3])
        
        
        

def showCavePreviewDialog():
    mayaWin = rmm.getMainWindow()
    if mc.lsUI(type = 'dockControl') and hasattr(__main__, 'CavePreviewUI') and __main__.CavePreviewUI_UI in mc.lsUI(type = 'dockControl'):
        mc.deleteUI(__main__.CavePreviewUI_UI)
    if hasattr(__main__, 'CavePreviewUIDialog'):
        try:
            __main__.CavePreviewUIDialog.close()
        except Exception:
            pass
        
    __main__.CavePreviewUIDialog = RMH_CavePreviewUI(mayaWin)
    
    if (mc.dockControl('CavePreviewUI', q=1, ex=1)):
        mc.deleteUI('CavePreviewUI')
    __main__.CavePreviewUIDialog.show(dockable = True, area=None,  width=400, floating=False)
    __main__.CavePreviewUI_UI = __main__.CavePreviewUIDialog