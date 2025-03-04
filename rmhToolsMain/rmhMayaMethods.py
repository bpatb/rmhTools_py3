

from __future__ import absolute_import
from __future__ import print_function
from importlib import reload

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

import maya.cmds as mc
import maya.mel as mel
import maya.OpenMaya as om
import maya.OpenMayaUI as omUI
import MASH.api as mapi

import os, random, math, shutil, subprocess
import __main__
import rmhTools_widgets as pw


def getBBPos(obj = None, achse = 'y', offset = 0): #getBBPos()
    if not obj:
        obj = mc.ls(selection = True)[0]
    if achse == 'x':
        bb = mc.xform(obj, q = True, bb = True)
        return (bb[3] + offset,  bb[1] + (bb[4] - bb[1]) / 2, bb[2] + (bb[5]-bb[2]) / 2)
    elif achse == 'y':
        bb = mc.xform(obj, q = True, bb = True)
        return (bb[0] + (bb[3] - bb[0]) / 2,  bb[4] + offset , bb[2] + (bb[5]-bb[2]) / 2)
    elif achse == 'z':
        bb = mc.xform(obj, q = True, bb = True)
        return (bb[0] + (bb[3] - bb[0]) / 2,  bb[1] + (bb[4] - bb[1]) / 2, bb[5] + offset)
    elif achse == '-x':
        bb = mc.xform(obj, q = True, bb = True)
        return (bb[0] + offset,  bb[1] + (bb[4] - bb[1]) / 2, bb[2] + (bb[5]-bb[2]) / 2)
    elif achse == '-y':
        bb = mc.xform(obj, q = True, bb = True)
        return (bb[0] + (bb[3] - bb[0]) / 2,  bb[1] + offset , bb[2] + (bb[5]-bb[2]) / 2)
    elif achse == '-z':
        bb = mc.xform(obj, q = True, bb = True)
        return (bb[0] + (bb[3] - bb[0]) / 2,  bb[1] + (bb[4] - bb[1]) / 2, bb[2] + offset)



def makeRevolveCut():
    crv = mc.ls(sl = True)[0]
    mc.hide(mc.duplicate(crv, n = '%s_orig'%crv))
    grp = mc.group(em = True, n = '%s_cutGrp'%crv)
    revSrf, revNode = mc.revolve(crv, degree = 3, ax = (0,1,0), n = '%s_nurbsRevolve'%crv)
    #revSrf = mc.rename(revSrf,'%s_nurbsRevolve'%crv)
    tx,ty,tz = getBBPos(revSrf, achse = 'y', offset = 10)
    ctrl = mc.circle( r = 20, d = 3, nr = (0,1,0), n = '%s_cutCtrl'%crv)[0]
    mc.move(tx,ty,tz,ctrl)
    mc.addAttr(ctrl, ln = 'sweep1', at = 'double', keyable = True)
    mc.addAttr(ctrl, ln = 'sweep2', at = 'double', dv = 360, keyable = True)
    mc.addAttr(ctrl, ln = 'uRes', at = 'double', dv = 55, keyable = True)
    mc.addAttr(ctrl, ln = 'vRes', at = 'double', dv = 90, keyable = True)
    mc.connectAttr('%s.sweep1'%ctrl, '%s.startSweep'%revNode, force = True)
    mc.connectAttr('%s.sweep2'%ctrl, '%s.endSweep'%revNode, force = True)
    
    polyObj, polyTess = mc.nurbsToPoly(revSrf, n = '%s_polyCut'%crv, mnd = 1, ch = 1, f= 2, pt= 1, pc =200, chr= 0.9815, ft =0.01, mel= 0.001, d =0.0565, ut =1, un =77, vt =1, vn= 90, uch= 0, ucr= 0, cht= 0.01 ,es =0, ntr =0,mrt= 0, uss =1)
    
    mc.polyCloseBorder(polyObj)
    
    mc.connectAttr('%s.uRes'%ctrl, '%s.uNumber'%polyTess, force = True)
    mc.connectAttr('%s.vRes'%ctrl, '%s.vNumber'%polyTess, force = True)
    
    mc.hide(revSrf)
    mc.parent(crv, revSrf, ctrl,polyObj, grp)


def checkIfVisible(obj = None):
    if not obj:
        obj = mc.ls(sl = True, long = True)[0]
        if not obj:
            return
    if not mc.objExists(obj):
        return False
    
    if not mc.attributeQuery('visibility', node = obj, exists = True):
        return False
    if not mc.getAttr('%s.visibility'%obj):
        return False
    if mc.attributeQuery('intermediateObject', node = obj, exists = True) and mc.getAttr('%s.intermediateObject'%obj):
        return False
    if mc.attributeQuery('overrideEnabled', node = obj, exists = True) and mc.getAttr('%s.overrideEnabled'%obj) and not mc.getAttr('%s.overrideVisibility'%obj):
        return False
    parent = mc.listRelatives(obj, p = True, f = True)
    vis = True
    parentRenderLayer = []
    while parent:
        if parent:
            parent = parent[0]
            vis = vis and mc.getAttr('%s.visibility'%parent)
            rLayer = mc.listConnections(parent, type = 'renderLayer') or []
            parentRenderLayer = parentRenderLayer + rLayer
        parent = mc.listRelatives(parent, p = True, f =True)
    if not vis:
        return False
    
    currentLayer= mc.editRenderLayerGlobals(q=True, currentRenderLayer= True)
    if  currentLayer != 'defaultRenderLayer':
        shape = mc.listRelatives(obj, s = True, f = True)
        shapeRL = []
        if shape:
            shapeRL = mc.listConnections(shape[0], type = 'renderLayer') or []
        rLayer = mc.listConnections(obj, type = 'renderLayer') or []
        #print 'check', parentRenderLayer+shapeRL+rLayer, currentLayer
        if currentLayer in parentRenderLayer+shapeRL+rLayer:
            return True
        else:
            return False
        
    return True


def setCurveColor(crvs = None, col = [1,1,0], rememberPrevious = 1): ### assume 255 col range
    if not crvs:
        crvs = mc.ls(sl = True)
    if type(crvs) in [str]:
        crvs = [crvs]
    for crv in crvs:
        shs = mc.listRelatives(crv, s = True) or []
        for sh in shs:
            if mc.objectType(sh) != 'nurbsCurve':
                continue
            try:
                mc.setAttr('%s.overrideEnabled'%sh, 1)
                mc.setAttr('%s.overrideRGBColors'%sh, 1)
                for i,ch in enumerate(['R','G','B']):
                    # print col
                    mc.setAttr('%s.overrideColor%s'%(sh,ch), col[i]/ 255.0)
            except:
                mc.warning('couldnt set color for %s'%crv)
        
    mc.select(crvs)


def rename_individual(obj = None, name = 'rename', shapeFix = True): ## unique name
    if not mc.objExists(name):
        mc.rename(obj, name)
        return name
    i = 0
    nameRef = name
    while mc.objExists(name):
        name = '%s_%02d'%(nameRef, i)
        i += 1
    name = mc.rename(obj, name)
    if shapeFix:
        sh = mc.listRelatives(name, s = 1)
        if sh:
            mc.rename(sh[0], '%sShape'%name)
    return name

def rmh_createGroupIfNonExistent(grp, parent = None, hide = False, relativeGroup = False):
    if not mc.objExists(grp):
        mc.group(n = grp, em = True)
        if parent:
            mc.parent(grp, parent, r = relativeGroup)
        if hide:
            mc.hide(grp)
    return grp

def rmh_createGroupIfNonExistent(grp, parent = None, hide = False):
    if not mc.objExists(grp):
        mc.group(n = grp, em = True)
        if parent:
            mc.parent(grp, parent)
        if hide:
            mc.hide(grp)
    return grp



# def rename_individual(obj = None, name = 'rename'): ## unique name
#     if not mc.objExists(name):
#         mc.rename(obj, name)
#         return name
#     i = 0
#     nameRef = name
#     while mc.objExists(name):
#         name = '%s_%02d'%(nameRef, i)
#         i += 1
#     mc.rename(obj, name)
#     return name

def findUniqueName(name = 'rename'): ## unique name
    if not mc.objExists(name):
        return name
    i = 0
    nameRef = name
    while mc.objExists(name):
        name = '%s_%02d'%(nameRef, i)
        i += 1
    return name

def connectMessageAttribute(srcs = None, target = None, messageAttr = None):
    def getFreeIdx(plug):
        _idx = 0
        test = '%s[%d]'%(plug, _idx)
        while mc.listConnections(test, s = 1):
            _idx+=1
            test = '%s[%d]'%(plug, _idx)
        return _idx
    
    if not srcs or not target:
        sel = mc.ls(sl = True)
        srcs, target = sel[:-1], sel[-1]
    
    srcs = [srcs] if type(srcs) == str else srcs
    
    if not messageAttr:
        udAttrs = mc.listAttr(target, ud= True) or []
        messageAttrs = [a for a in udAttrs if mc.getAttr('%s.%s'%(target, a), type = True) == 'message' ] or []
        messageAttr, ok = QInputDialog.getItem(None, 'connectMessageAttribute', 'message attr', messageAttrs, current = 0, editable = True)
        if not ok:
            return
        messageAttr = str(messageAttr)
    
    if not messageAttr in mc.listAttr(target):
        mc.addAttr(target, ln = messageAttr, at = 'message', m = True)
    
    found = mc.listConnections('%s.%s'%(target, messageAttr), s = 1) or []
    
    # mc.connectAttr('%s.%s'%(src, outMessageAttr), '%s.%s'%(target, messageAttr), f = 1)
    outMessageAttr = 'messageOut'
    for src in srcs:
        if src in found:
            continue
        if not outMessageAttr in mc.listAttr(src):
            mc.addAttr(src, ln = outMessageAttr, at = 'message')
            
        idx = getFreeIdx('%s.%s'%(target, messageAttr))
        mc.connectAttr('%s.%s'%(src, outMessageAttr), '%s.%s[%d]'%(target, messageAttr, idx), f = 1)
    
    
def rename_individual(obj = None, name = 'rename', shapeFix = True): ## unique name
    if not mc.objExists(name):
        mc.rename(obj, name)
        return name
    i = 0
    nameRef = name
    while mc.objExists(name):
        name = '%s_%02d'%(nameRef, i)
        i += 1
    name = mc.rename(obj, name)
    if shapeFix:
        sh = mc.listRelatives(name, s = 1)
        if sh:
            mc.rename(sh[0], '%sShape'%name)
    return name

def duplicateToParents(sourceObj = None, destParents = None, instance = False):
    if not sourceObj and not destParents:
        sel = mc.ls(sl = True)
        sourceObj = sel[0]
        destObjs = sel[1:]
    for destObj in destObjs:
        if not instance:
            dup = mc.duplicate(sourceObj, rr = True, rc = True)[0]
        else:
            dup = mc.instance(sourceObj)[0]
        mc.parent(sourceObj, destObj, r = True)

def duplicateToParents_constraint(sourceObj = None, destParents = None, instance = False, scaleConstraint = None, deleteConstraints = False, inputGraph = None):
    if scaleConstraint == None:
        result = mc.confirmDialog( title='duplicateToParents_constraint', message='scaleConstraint?', button=['Yes','No','Cancel'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        if result == 'Cancel':
            return
        scaleConstraint = result == 'Yes'
    
    if inputGraph == None:
        result = mc.confirmDialog( title='duplicateToParents_constraint', message='duplicate inputGraph?', button=['Yes','No','Cancel'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        if result == 'Cancel':
            return
        inputGraph = result == 'Yes'
        
        
    if not sourceObj and not destParents:
        sel = mc.ls(sl = True)
        if len(sel) == 1:
            sourceObj = sel[0]
            if not mc.objExists('constraintTargets'):
                mc.sets(n = 'constraintTargets')
            destObjs = mc.listConnections('constraintTargets.dagSetMembers')
        else:
            sourceObj = sel[0]
            destObjs = sel[1:]
    
    mc.undoInfo(ock = True)
    
    grp = mc.group(n = 'dupGrp', em = True)
    for destObj in destObjs:
        if not instance:
            dup = mc.duplicate(sourceObj, rr = True, rc = True, un = inputGraph)[0]
        else:
            dup = mc.instance(sourceObj)[0]
        delC = []
        c = mc.parentConstraint(destObj,dup, mo = False)[0]
        delC.append(c)
        if scaleConstraint:
            c = mc.scaleConstraint(destObj,dup, mo = False)[0]
            delC.append(c)
        mc.parent(dup, grp)
        if deleteConstraints:
            mc.delete(delC)
    mc.undoInfo(cck = True)


def distributeAlongCurve(srcObjs = None, destObjs = None, randomDist = False, follow = None, num = None,\
                         uvRange = [0,1], frontRange = [0,220], upRange = [0,110], sideRange= [0,0], scaleRange = [0.1,0.5], upstreamNodes = False, stayAttached = True):
    sel= mc.ls(sl = True)
    
    if num == None:
        num, ok =  QInputDialog.getInt(None, 'distributeAlongCurve', 'num', value = 15, min = 1, max = 40000)
        if not ok:
            return
        
    if follow == None:
        res = mc.confirmDialog( title='distributeAlongCurve', message='follow?', button=['Yes','No','Cancel'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        if res == 'Cancel':
            return
        follow = res == 'Yes'
    
    tmpLoc = None
    sel = mc.ls(sl = True)
    
    destObjs = [o for o in sel if (mc.listRelatives(o, s=1) and mc.objectType(mc.listRelatives(o, s=1)[0]) == 'nurbsCurve') ] if not destObjs else destObjs
    srcObjs =  [o for o in sel if not (mc.listRelatives(o, s=1) and mc.objectType(mc.listRelatives(o, s=1)[0]) == 'nurbsCurve') ] if not srcObjs else srcObjs
    
    mpDict = {}
    delta = 1.0 / num
    
    mc.undoInfo(ock = True)
    
    out , out_groups = [], []
    count = 1
    for destObj in destObjs:
        dGrp = mc.group(n = '%s_dupGrp'%destObj, em = True)
        out_groups.append(dGrp)
        if not srcObjs:
            tmpLoc = mc.spaceLocator(n = '%sLoc'%destObj)[0]
            srcObjs = [tmpLoc]
        for srcObj in srcObjs:
            for i in range(num):
                dup = mc.duplicate(srcObj, n = '%s_dup%03d'%(srcObj, i) , un = upstreamNodes, rc = True, rr = True)[0]
                grp = mc.group(em = True, n = '%sGrp'%dup)
                for at in ['translateX', 'translateY', 'translateZ']:
                    mc.setAttr('%s.%s'%(dup, at), 0)
                mc.parent(dup ,grp)
                if follow:
                    mpath = mc.pathAnimation(grp , destObj, fm = True, follow = follow, fa = 'z', ua = 'y', worldUpType = 'vector', worldUpVector = (0,1,0))#, iu = False, if = False, bank = False, startTimeU = 0)
                else:
                    mpath = mc.pathAnimation(grp , destObj, fm = True, follow = False)
                mc.cutKey('%s.uValue'%mpath, t = (-1,10000))
                mpDict[grp] = mpath
                if not 'uValue' in mc.listAttr(grp):
                    mc.addAttr(grp, ln = 'uValue', at = 'double', minValue = 0, maxValue = 1, k = 1)
                mc.connectAttr('%s.uValue'%grp, '%s.uValue'%mpath)
                mc.setAttr('%s.uValue'%grp, i * delta)
                mc.parent(grp, dGrp)
                count+=1
                out.append(dup)
        if tmpLoc:
            mc.delete(tmpLoc)
            srcObjs = None
    
    if randomDist:
        outObjs = []
        for i in range(num):
            srcObj = random.choice(srcObjs)
            if randomDist:
                uVal = random.uniform(uvRange[0], uvRange[1])
            else:
                uVal = i * delta
            mc.setAttr('%s.uValue'%mpDict[srcObj], uVal)
            mc.setAttr('%s.frontTwist'%mpDict[srcObj], random.uniform(frontRange[0], frontRange[1]))
            mc.setAttr('%s.upTwist'%mpDict[srcObj], random.uniform(upRange[0], upRange[1]))
            mc.setAttr('%s.sideTwist'%mpDict[srcObj], random.uniform(sideRange[0], sideRange[1]))
            mc.refresh()
            dup = mc.duplicate(srcObj, un = upstreamNodes, rc = True, rr = True)[0]
            mc.scale(*[random.uniform(scaleRange[0],scaleRange[1]) ]*3 )
            outObjs.append(dup)
        grp = mc.group(em = True, n = '%s_dups'%destObj)
        mc.parent(outObjs, grp)
        mc.delete(list(mpDict.values()))
        mpDict = {}
        mc.select(srcObjs)
        mc.move(0,0,0)
        mc.rotate(0,0,0)
        mc.scale(1,1,1)
    
    if not stayAttached:
        mc.refresh()
        mc.delete(list(mpDict.values()))
        mpDict = {}
    mc.undoInfo(cck = True)
    return {'roots': out_groups, 'dups': out, 'mpaths':list(mpDict.values())}
    

def successiveKeyOffset(objs = None, frameRange = None, timeOffset = 0, offsetDeltaRange = None, shuffleArray = False, hierarchy = True):
    attrs = ['tx', 'ty', 'tz', 'rx', 'ry','rz', 'sx', 'sy', 'sz']
    
    if not objs:
        objs = mc.ls(sl = True)
    
    if shuffleArray:
        objs = random.shuffle(objs)
    
    if offsetDeltaRange == None:
        result = mc.promptDialog(title='successiveKeyOffset',message='offsetDeltaRange:',button=['OK', 'Cancel'], defaultButton='OK',cancelButton='Cancel', dismissString='Cancel', text = '5,5')
        if result == 'OK':
            tx = mc.promptDialog(query=True, text=True)
            offsetDeltaRange = list(map(float, tx.split(',')))
        else:
            return
        
    if not frameRange:
        aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider')
        frameRange = list(map(int, mc.timeControl(aPlayBackSliderPython, ra = True, q = True)))
        if not frameRange or abs(frameRange[0] - frameRange[1])<=2:
            # mc.error('bakeTransferValues: keine Range selected')
            # return
            frameRange = [0,1000000000]
    
    mc.undoInfo(ock = True)
    
    currentDelta = timeOffset
    for i,obj in enumerate(objs):
        if hierarchy:
            objs2 = mc.listRelatives(obj, ad = True, type = 'transform')+mc.listRelatives(obj, ad = True, type = 'joint')
            objs2 = list(set(objs2))
        else:
            objs2 = [obj]
        
        for obj2 in objs2:
            mc.keyframe(obj2, e = True, iub = False, t = (frameRange[0],frameRange[1]), r = True, o = 'over', tc = currentDelta)
        currentDelta += random.randint(offsetDeltaRange[0],offsetDeltaRange[1]) if offsetDeltaRange[0] != offsetDeltaRange[1] else offsetDeltaRange[0]
    
    mc.undoInfo(cck = True)


def reconnectTransformToConstraints(objs = None):
    def removeConnecions(obj, attrs):
        for attr in attrs:
            if not attr in mc.listAttr(obj):
                continue
            plugs = mc.listConnections('%s.%s'%(obj,attr), s = 1, d = 0, p = 1)
            if plugs:
                mc.disconnectAttr(plugs[0], '%s.%s'%(obj,attr))
        
    mc.undoInfo(ock = True)
    if not objs:
        objs = mc.ls(selection = True)
    
    for obj in objs:
        pointConstraints = mc.listRelatives(obj, type = 'pointConstraint') or []
        parentConstraints = mc.listRelatives(obj, type = 'parentConstraint') or []
        orientConstraints = mc.listRelatives(obj, type = 'orientConstraint')  or []
        scaleConstraints = mc.listRelatives(obj, type = 'scaleConstraint') or []
        # print 'cs', scaleConstraints
        for const in parentConstraints:
            removeConnecions(obj, ['translate', 'translateX', 'translateY', 'translateZ', 'rotate', 'rotateX', 'rotateY', 'rotateZ'])
            mc.connectAttr('%s.constraintTranslate'%const, '%s.translate'%obj, f = 1)
            mc.connectAttr('%s.constraintRotate'%const, '%s.rotate'%obj, f = 1)
            mc.connectAttr('%s.rotateOrder'%obj, '%s.constraintRotateOrder'%const, f = 1)
            mc.connectAttr('%s.rotatePivot'%obj, '%s.constraintRotatePivot'%const, f = 1)
            mc.connectAttr('%s.rotatePivotTranslate'%obj, '%s.constraintRotateTranslate'%const, f = 1)
        for const in orientConstraints:
            removeConnecions(obj, ['rotate', 'rotateX', 'rotateY', 'rotateZ'])
            mc.connectAttr('%s.constraintRotate'%const, '%s.rotate'%obj, f = 1)
            mc.connectAttr('%s.parentInverseMatrix[0]'%obj, '%s.constraintParentInverseMatrix'%const, f = 1)
            mc.connectAttr('%s.rotateOrder'%obj, '%s.constraintRotateOrder'%const, f = 1)
            mc.connectAttr('%s.rotatePivot'%obj, '%s.constraintRotatePivot'%const, f = 1)
            mc.connectAttr('%s.rotatePivotTranslate'%obj, '%s.constraintRotateTranslate'%const, f = 1)
        for const in scaleConstraints:
            removeConnecions(obj, ['scale', 'scaleX', 'scaleY', 'scaleZ'])
            mc.connectAttr('%s.constraintScale'%const, '%s.scale'%obj, f = 1)
            mc.connectAttr('%s.parentInverseMatrix[0]'%obj, '%s.constraintParentInverseMatrix'%const, f = 1)
            # mc.connectAttr('%s.rotateOrder'%obj, '%s.constraintRotateOrder'%const, f = 1)
            # mc.connectAttr('%s.rotatePivot'%obj, '%s.constraintRotatePivot'%const, f = 1)
            # mc.connectAttr('%s.rotatePivotTranslate'%obj, '%s.constraintRotateTranslate'%const, f = 1)
            print('con ', const, 'to', obj)
            
            

    mc.undoInfo(cck = True)

def rmh_exportNukeAssets_createExportSets():
    setNames = ['nukeSet_objects','nukeSet_alembic']
    for s in setNames:
        if not mc.objExists(s):
            mc.sets(name = s, em = True)
            print('%s created'%s)

def rmh_exportNukeAssets_addToSet(exportSetName = None):
    if not exportSetName:
        exportSetName = mc.confirmDialog(title='rmh_exportNukeAssets_addToSet',message='add selection to set:',button=['nukeSet_objects','nukeSet_alembic', 'Cancel'], defaultButton='No',cancelButton='Cancel', dismissString='Cancel')
        if exportSetName == 'Cancel':
            return
        
    rmh_exportNukeAssets_createExportSets()
    sel = mc.ls(sl = True)
    mc.undoInfo(ock = True)
    for obj in sel:
        mc.sets(obj, addElement = exportSetName, e = True)
    mc.undoInfo(cck = True)
    print('added to %s'%exportSetName)
    

def rmh_exportNukeAssets(frameRange = None):
    sceneName = mc.file( q = True, sn = True, shn = True).split('.')[0]
    noVersionName = '_'.join(sceneName.split('_')[:-1])
    outDir = mc.workspace(q= True, rd = True) + 'exportToNuke/%s'%noVersionName
    
    if not os.path.isdir(outDir):
        os.makedirs(outDir)
        
    if not frameRange :
        fmin = mc.playbackOptions(q = 1, minTime = 1)
        fmax = mc.playbackOptions(q = 1, maxTime = 1)
        frameRange = [fmin, fmax]
    objs = mc.ls(sl = True)
    
    ########## nuke objs
    setName = 'nukeSet_objects'
    if mc.objExists(setName):
        objs = mc.listConnections('%s.dagSetMembers'%setName)
        for obj in objs:
            outFile = '%s_%s.fbx'%(noVersionName, obj)
            outPath = os.path.join(outDir, outFile)
            mc.select(obj)
            mc.file(outPath, force = 1, options = "" ,typ = "FBX export" ,pr=1 ,es = 1 )
            print('toNuke ------ > %s exported'%outPath)
            
    cameras = mc.ls(type = 'camera')
    cameras_t = [mc.listRelatives(c, p = 1)[0] for c in cameras if mc.getAttr('%s.renderable'%c)]
    
    ########## nuke cams
    setName = 'nukeSet_objects'
    for obj in cameras_t:
        outFile = '%s_%s.fbx'%(noVersionName, 'cameras')
        outPath = os.path.join(outDir, outFile)
        mc.select(obj)
        mc.file(outPath, force = 1, options = "" ,typ = "FBX export" ,pr=1 ,es = 1 )
        print('toNuke ------ > %s exported'%outPath)
    
    ######## nuke abc
    setName = 'nukeSet_alembic'
    if mc.objExists(setName):
        objs = mc.listConnections('%s.dagSetMembers'%setName)
        if objs:
            outFile = '%s_animObjs.abc'%(noVersionName)
            outPath = os.path.join(outDir, outFile)
            
            rootTx = ''
            for obj in objs:
                rootTx = rootTx + ' -root ' + obj
                
            command = '-frameRange %d %d -worldSpace -writeVisibility -dataFormat ogawa'%(frameRange[0],frameRange[1]) + rootTx  + ' -file \"' + outPath.replace('\\','/') + '\"'
            print(objs, command)
            mc.AbcExport(j = command)
            print('toNuke ------ > %s exported'%outPath)

def rmh_copyObjectPosToNuke(obj = None):
    if not obj:
        obj = mc.ls(sl = True)[0]
    
    pos = mc.xform(obj, q = True, t = True, ws = True)
    nukeTx = 'set cut_paste_input [stack 0]',\
    'version 12.2 v3',\
    'push $cut_paste_input',\
    'push 0',\
    'Reconcile3D {',\
    ' inputs 2',\
    ' point {%.3f %.3f %.3f}'%(pos[0],pos[1],pos[2]),\
    ' calc_output true',\
    ' name Reconcile3D1',\
    ' selected true',\
    ' xpos 2670',\
    ' ypos -245',\
    '}',\
    
    print('\n'.join(nukeTx))
    cb = QApplication.clipboard()
    cb.clear(mode=cb.Clipboard)
    cb.setText('\n'.join(nukeTx), mode=cb.Clipboard)
    
def rmh_getCurrentCamera():
    view = omUI.M3dView.active3dView()
    cam = om.MDagPath()
    view.getCamera(cam)
    sh = cam.partialPathName()
    p = mc.listRelatives(sh, p = 1)[0]
    return p, sh

def rmh_worldSpaceToScreenSpace(camera, worldPoint, invertY = True):
    # get current resolution
    resWidth = mc.getAttr('defaultResolution.width')
    resHeight = mc.getAttr('defaultResolution.height')

    # get the dagPath to the camera shape node to get the world inverse matrix
    selList = om.MSelectionList()
    selList.add(camera)
    dagPath = om.MDagPath()
    selList.getDagPath(0,dagPath)
    dagPath.extendToShape()
    camInvMtx = dagPath.inclusiveMatrix().inverse()

    # use a camera function set to get projection matrix, convert the MFloatMatrix 
    # into a MMatrix for multiplication compatibility
    fnCam = om.MFnCamera(dagPath)
    mFloatMtx = fnCam.projectionMatrix()
    projMtx = om.MMatrix(mFloatMtx.matrix)

    # multiply all together and do the normalisation
    mPoint = om.MPoint(worldPoint[0],worldPoint[1],worldPoint[2]) * camInvMtx * projMtx;
    x = (mPoint[0] / mPoint[3] / 2 + .5) * resWidth
    if invertY:
        y = (1-(mPoint[1] / mPoint[3] / 2 + .5)) * resHeight
    else:
        y = (mPoint[1] / mPoint[3] / 2 + .5) * resHeight

    return [x,y]

def rmh_exportWorldspaceKeyframesToAFX(obj = None, frameRange = None, fps = 25):
    if not obj:
        obj = mc.ls(sl = True)[0]
    
    if not frameRange:
        fmin = mc.playbackOptions(q = 1, minTime = 1)
        fmax = mc.playbackOptions(q = 1, maxTime = 1)
        frameRange = [fmin, fmax]
    
    cam, camSh = rmh_getCurrentCamera()
    
    posArray = []
    valLines = []
    for frame in range(int(frameRange[0]), int(frameRange[1]+1)):
        mc.currentTime(frame)
        pos = mc.xform(obj, q = True, t = True, ws = True)
        ssPos = rmh_worldSpaceToScreenSpace(cam, pos)
        posArray.append(ssPos)
        valLines.append('\t%d\t%.3f\t%.3f'%(frame, ssPos[0], ssPos[1]))
    
    afxTx = 'Adobe After Effects 6.5 Keyframe Data',\
    '',\
    '\tUnits Per Second	%d'%fps,\
    '\tSource Width	100',\
    '\tSource Height	100',\
    '\tSource Pixel Aspect Ratio	1.0',\
    '\tComp Pixel Aspect Ratio	1.0',\
    '',\
    '',\
    'Transform\tPosition',\
    '\tFrame	X pixels	Y pixels',\
    '\n'.join(valLines),\
    'End of Keyframe Data'
    
    print('\n'.join(afxTx))
    cb = QApplication.clipboard()
    cb.clear(mode=cb.Clipboard)
    cb.setText('\n'.join(afxTx), mode=cb.Clipboard)
    
    
def rmh_MASH_initialStateFromObjects(objs = None, mashWaiters = None):
    if not objs or not mashWaiters:
        sel = mc.ls(sl = True)
        objs = [o for o in sel if mc.objectType(o) == 'transform']
        mashWaiters = [o for o in sel if mc.objectType(o) == 'MASH_Waiter']
    
    for waiter in mashWaiters:
        num = len(objs)
        dist = mc.listConnections('%s.waiterMessage'%waiter, s = 1, d = 0)[0]
        countPlug = mc.listConnections('%s.pointCount'%dist, s = 1, d = 0, p = 1)
        if countPlug:
            mc.disconnectAttr(countPlug[0], '%s.pointCount'%dist)
        
        mc.setAttr('%s.pointCount'%dist, num)
        mc.setAttr('%s.arrangement'%dist, 7)
        for i,obj in enumerate(objs):
            mc.connectAttr('%s.worldMatrix[0]'%obj, '%s.initialStateMatrix[%d]'%(dist, i), f = 1)

def rmh_MASH_getMashFromList(returnIfOne = True):
    allMashes = mc.ls(type = 'MASH_Waiter')
    if len(allMashes) == 1:
        return allMashes[0]
    elif len(allMashes) > 1:
        mash, ok = QInputDialog.getItem(None, 'rmh_MASH_getMashFromList', 'MASH network', allMashes, current = 0, editable = True)
        if not ok:
            return
        if mc.objExists(mash):
            return mash
    else:
        print('no MASH networks')
        return

def rmh_MASH_addObjectsToRepro(objs = None, mash = None, replace = True):
    import mash_repro_utils
    import mash_repro_aetemplate
    
    def MASH_disconnectAllReproInputs(repro):
        data = mash_repro_utils.get_data_layout(repro)
        indices = list(data.keys())
        indices.sort()
        for index in reversed(list(range(len(indices)))):
            mash_repro_utils.remove_mesh_group(repro, index)
    
    if not objs:
        objs = mc.ls(sl = True)
    
    mash = rmh_MASH_getMashFromList() if not mash else mash
    if not mash:
        print('rmh_MASH_addObjectsToRepro: no MASH found')
        return
    
    mc.undoInfo(ock = True)

    repro = mc.listConnections('%s.instancerMessage'%mash, d = 1, s = 0)[0]
    
    if replace:
        MASH_disconnectAllReproInputs(repro)
    
    for obj in objs:
        # print repro, obj
        mash_repro_utils.connect_mesh_group(repro, obj) 
        mash_repro_aetemplate.refresh_all_aetemplates() 
    
    mashNetwork = mapi.Network(mash)
    nodes = mashNetwork.getAllNodesInNetwork() or []
    for node in nodes:
        if mc.objectType(node) == 'MASH_Id':
            mc.setAttr('%s.numObjects'%node, len(list(mash_repro_utils.get_data_layout(repro).keys())))
            
    mc.undoInfo(cck = True)
    
def rmh_MASH_breakoutAll(mashWaiters = None, locNameBase = None, translate = True, rotate = True, scale = True, connect = True, toGroup = None):
    if not mashWaiters:
        sel = mc.ls(sl = True)#
        mashWaiters = [o for o in sel if mc.objectType(o) == 'MASH_Waiter']
    if not mashWaiters:
        mc.warning('rmh_MASH_breakoutAll: gotta select the MASH waiter!')
    
    mc.undoInfo(ock = True)
    locs = []
    rig_g = rmh_createGroupIfNonExistent('rig_g', hide = True)
    metaGrp = rmh_createGroupIfNonExistent('_MASHattachLocs' ,rig_g, hide = True)
    # metaGrp = '_MASHattachLocs' if mc.objExists('_MASHattachLocs') else mc.group(n = '_MASHattachLocs', em = True)
    
    breakouts = []
    for waiter in mashWaiters:
        grp = mc.group(n = '%s_locGrp'%waiter, em = True) if not toGroup else toGroup
        mc.parent(grp, metaGrp)
        count = mc.getAttr('%s.pointCount'%waiter)
        
        breakout = mc.createNode('MASH_Breakout')
        mc.connectAttr('%s.outputPoints'%waiter, '%s.inputPoints'%breakout)
        breakouts.append(breakout)
        
        for i in range(count):
            loc = mc.spaceLocator()[0]
            if locNameBase:
                loc = rename_individual(loc, '%s_loc%03d'%(locNameBase, i))
            else:
                loc = rename_individual(loc, '%s_loc%03d'%(waiter, i))
            mc.parent(loc, grp)
            if connect:
                mc.connectAttr('%s.outputs[%d].translate'%(breakout, i), '%s.translate'%loc, f = 1)
                mc.connectAttr('%s.outputs[%d].rotate'%(breakout, i), '%s.rotate'%loc, f = 1)
                mc.connectAttr('%s.outputs[%d].scale'%(breakout, i), '%s.scale'%loc, f = 1)
            else:
                vals = mc.getAttr('%s.outputs[%d].translate'%(breakout, i))[0]
                mc.setAttr('%s.translate'%loc, vals[0], vals[1], vals[2] )
                vals = mc.getAttr('%s.outputs[%d].rotate'%(breakout, i))[0]
                mc.setAttr('%s.rotate'%loc, vals[0], vals[1], vals[2] )
                vals = mc.getAttr('%s.outputs[%d].scale'%(breakout, i))[0]
                mc.setAttr('%s.scale'%loc, vals[0], vals[1], vals[2] )
            locs.append(loc)
    mc.undoInfo(cck = True)
    return breakouts, locs

def rmh_addSubCurveClipControl(subCrvs = None):
    if not subCrvs:
        subCrvs = mc.ls(sl = True)
    
    mc.undoInfo(ock = True)
    for crv in subCrvs:#
        if not 'minCurve' in mc.listAttr(crv):
            continue
        if 'minClip' in mc.listAttr(crv):
            continue
        
        stdVals = {'minClip':0, 'maxClip':1}
        for attr in ['minClip', 'maxClip']:
            if not attr in mc.listAttr(crv):
                mc.addAttr(crv, ln = attr, at = 'double', minValue = 0, maxValue = 1, k = 1, dv = stdVals.get(attr))
        subNode = mc.listConnections('%s.minCurve'%crv, d = 1, s = 0)[0]
        sr = mc.createNode('setRange', n = '%s_range'%crv)
        mc.setAttr('%s.oldMinX'%sr,0)
        mc.setAttr('%s.oldMaxX'%sr,1)
        mc.setAttr('%s.oldMinY'%sr,0)
        mc.setAttr('%s.oldMaxY'%sr,1)
        mc.connectAttr('%s.minClip'%crv, '%s.minX'%sr, f = 1)
        mc.connectAttr('%s.minClip'%crv, '%s.minY'%sr, f = 1)
        mc.connectAttr('%s.maxClip'%crv, '%s.maxX'%sr, f = 1)
        mc.connectAttr('%s.maxClip'%crv, '%s.maxY'%sr, f = 1)
        mc.connectAttr('%s.valueX'%sr, '%s.minValue'%subNode, f = 1)
        mc.connectAttr('%s.valueY'%sr, '%s.maxValue'%subNode, f = 1)
        mc.connectAttr('%s.minCurve'%crv, '%s.valueX'%sr, f = 1)
        mc.connectAttr('%s.maxCurve'%crv, '%s.valueY'%sr, f = 1)
        
        mc.connectAttr('%s.outValueX'%sr, '%s.minValue'%subNode, f = 1)
        mc.connectAttr('%s.outValueY'%sr, '%s.maxValue'%subNode, f = 1)
        
    mc.undoInfo(cck = True)

def rmh_renameAfterParent(objs = None, suffix = '_o'):
    if not objs:
        objs = mc.ls(sl = True)
    
    sortDc = {}
    for obj in objs:
        p = mc.listRelatives(obj, p = 1)
        if not p:
            continue
        p = p[0]
        if not p in sortDc.keys():
            sortDc[p] = []
        sortDc[p].append(obj)
    
    mc.undoInfo(ock = True)
    for p in sortDc.keys():
        _objs = sortDc[p]
        for child in _objs:
            rename_individual(child, '%s%s'%(p,suffix))
    
    mc.undoInfo(cck = True)

def attachCubesToObjects(objs = None, cSize = 1): #weil nuke keine locator importiert
    if not objs:
        objs = mc.ls(sl = True)
    
    cubeGrp = rmh_createGroupIfNonExistent('attachCube_g', parent = None, hide = False)
    out = []
    mc.undoInfo(ock = True)
    for obj in objs:
        cube = mc.polyCube(w = cSize, h = cSize, d = cSize, ch = 0, n = findUniqueName('%s_cb'%obj))[0]
        
        sh = mc.listRelatives(cube ,s = 1)[0]
        for attr in ['castsShadows','receiveShadows','motionBlur','primaryVisibility','smoothShading','visibleInReflections','visibleInRefractions']:
            mc.setAttr('%s.%s'%(sh, attr), 0)
        pc = mc.parentConstraint(obj, cube, mo = False)
        mc.parent(cube, cubeGrp)
        out.append(cube)
    mc.undoInfo(cck = True)
    
    return out



def rmh_makeDistanceArray(refObject, objectArray, useScalePivot = False, useCurveCenter = True, maxDistance = None, skipConnected = False, skipArray = []): # von klein zu gross
    def magnitude(v):
        return math.sqrt(sum(v[i]*v[i] for i in range(len(v))))
    def sub(u, v):
        return [ u[i]-v[i] for i in range(len(u)) ]
    if useScalePivot:
        refPos = mc.xform('%s.scalePivot'%refObject, ws = True, q = True, t = True)
    else:
        refPos = mc.xform(refObject, ws = True, q = True, t = True)

    sortArray = []
    for obj in objectArray:
        if refObject == obj:
            continue
        if [refObject, obj] in skipArray:
            continue
        objSh = mc.listRelatives(obj, s = True)
        if useScalePivot:
            objPos = mc.xform('%s.scalePivot'%obj, ws = True, q = True, t = True)
        elif objSh and mc.objectType(objSh[0]) == 'nurbsCurve' and useCurveCenter:
            rng = mc.getAttr('%s.minMaxValue'%obj)[0][1]
            objPos = mc.pointPosition('%s.u[%.3f]'%(obj, rng/2), w = True)
        else:
            objPos = mc.xform(obj, ws = True, q = True, t = True)
        # print obj
        sh = mc.listRelatives(refObject, s = True)
        if sh and mc.objectType(sh[0]) == 'nurbsCurve' and useCurveCenter:
            rng = mc.getAttr('%s.minMaxValue'%refObject)[0][1]
            refPos = mc.pointPosition('%s.u[%.3f]'%(refObject, rng/2), w = True)
            # print 'using crv:' , refPos
        
        
        dist = magnitude(sub(objPos, refPos))
        if maxDistance and dist > maxDistance:
            continue
        # print obj, mc.listConnections('%s.translateX'%obj, s = 1, d = 0)
        if skipConnected and mc.listConnections('%s.translateX'%obj, s = 1, d = 0):
            continue
        sortArray.append([dist, obj])
    sortArray.sort(key=lambda x:x[0] )
    return [x[1] for x in sortArray]

def getMainWindow():
    global app
    app = QApplication.instance()
    
    ptr = omUI.MQtUtil.mainWindow()
    win = wrapInstance(int(ptr), QWidget)
    
    return win

def getMainWindow2(): # functions better in Maya 2017
    try:
        for obj in qApp.topLevelWidgets():
            if obj.objectName() == 'MayaWindow':
                return obj
    except:
        raise RuntimeError('Could not find MayaWindow instance')

def rmh_setMaterial_diffuse():
    mats = mc.ls(sl = True)
    
    mc.undoInfo(ock = True)
    for mat in mats:
        if not 'diffuse_weight' in mc.listAttr(mat):
            continue
        mc.setAttr('%s.diffuse_weight'%mat, 1)
        mc.setAttr('%s.emission_weight'%mat, 0)
    mc.undoInfo(cck = True)
        
def rmh_setMaterial_emission():
    mats = mc.ls(sl = True)
    
    mc.undoInfo(ock = True)
    for mat in mats:
        if not 'diffuse_weight' in mc.listAttr(mat):
            continue
        mc.setAttr('%s.diffuse_weight'%mat, 0)
        mc.setAttr('%s.emission_weight'%mat, 1)
    mc.undoInfo(cck = True)
        

def RMHSummit_createSweepMeshes(crvs = None, profile = 'wallProfile'):
    if not crvs:
        crvs = mc.ls(sl = True)
    
    mesh_g = rmh_createGroupIfNonExistent('curveMeshes')
    widthCtrl = 'tubeWidth_ctrl'
    out = []
    mc.undoInfo(ock = True)
    for crv in crvs:
        meshName = '%s_mesh'%crv
        if mc.objExists(meshName):
            print(meshName, 'exists - delete')
            mc.delete(meshName)
        mc.sweepMeshFromCurve(crv)
        crvShape = mc.listRelatives(crv, s = 1)[0]
        hist = mc.listHistory(crvShape, future = True)
        sweepShape = [s for s in hist if mc.objectType(s) == 'mesh' and 'sweep' in s.lower()][0]
        sweepNode = [s for s in hist if mc.objectType(s) == 'sweepMeshCreator'][0]
        mc.setAttr('%s.interpolationMode'%sweepNode, 0)
        mc.setAttr('%s.interpolationOptimize'%sweepNode, 1)
        mc.setAttr('%s.capsEnable'%sweepNode, 1)
        mc.setAttr('%s.alignProfileEnable'%sweepNode, 1)
        mc.setAttr('%s.alignProfileVertical'%sweepNode, 2)
        
        sweepTrans = mc.listRelatives(sweepShape, p = 1)[0]
        mc.xform(sweepTrans, cp = True)
        
        if mc.objExists(widthCtrl):
            mc.connectAttr('%s.outValue'%widthCtrl, '%s.scaleProfileX'%sweepNode, f = 1)
        
        sweepTrans = rename_individual(sweepTrans, meshName)
        mc.parent(sweepTrans, mesh_g)
        
        if profile:
            profileShape = mc.listRelatives(profile, s = 1)[0]
            prNode = mc.createNode('sweepProfileConverter', n = '%s_profNode'%meshName)
            mc.connectAttr('%s.worldMatrix[0]'%profileShape, '%s.inObjectArray[0].worldMatrix'%prNode, f = 1)
            mc.connectAttr('%s.local'%profileShape, '%s.inObjectArray[0].curve'%prNode, f = 1)
            mc.connectAttr('%s.sweepProfileData'%prNode, '%s.customSweepProfileData'%sweepNode, f = 1)
        out.append(sweepNode)
    
    mc.select(out)
    mc.undoInfo(cck = True)
    
def rmh_combineMeshes_diff(objs = None, cname = None):
    if not objs:
        objs = mc.ls(sl = True)
    if not cname:
        cname = objs[0]+'_cbool'
    pBool = mc.createNode('polyCBoolOp', n = '%s_bool'%cname)
    mc.setAttr('%s.operation'%pBool, 2)
    mc.setAttr('%s.classification'%pBool, 1)
    mesh = mc.createNode('mesh')
    meshTrans = mc.listRelatives(mesh, p = 1)[0]
    for i, obj in enumerate(objs):
        sh = mc.listRelatives(obj, s = 1)
        if not sh:
            continue
        sh = sh[0]
        mc.connectAttr('%s.worldMatrix[0]'%sh, '%s.inputMat[%d]'%(pBool,i), f = 1)
        mc.connectAttr('%s.outMesh'%sh, '%s.inputPoly[%d]'%(pBool,i), f = 1)
    mc.connectAttr('%s.output'%pBool, '%s.inMesh'%(mesh), f = 1)
    meshTrans = rename_individual(meshTrans, cname)
    return meshTrans

def rmh_getShadingGroup(obj = None, select = False, returnAllSgs = False):
    if not obj:
        obj = mc.ls(sl = True)[0]
    if mc.objectType(obj) == 'transform':
        shape = mc.listRelatives(obj, s = True, f = True)
        if not shape:
            return
        sg = mc.listConnections(shape[0], type = 'shadingEngine')
        if not sg:
            return
        if select:
            getObjects_SG(sg[0], select = True)
        if returnAllSgs:
            return list(set(sg))
        else:
            return sg[0]
    else:
        #elif 'vray' in mc.objectType(obj).lower() or 'lambert' in mc.objectType(obj).lower() or 'blinn' in mc.objectType(obj).lower() or 'sur' in mc.objectType(obj).lower():
        sg = mc.listConnections(obj, type = 'shadingEngine')
        return sg if not type(sg) == list else sg[0] 



def rmh_getMaterial(obj = None, returnAllMaterials = False):
    if not obj:
        obj = mc.ls(sl = True)[0]
    sgs = rmh_getShadingGroup(obj, returnAllSgs = True)
    if not sgs:
        return False
    if returnAllMaterials:
        out = []
        for _sg in sgs:
            out.append(mc.listConnections('%s.surfaceShader'%(_sg))[0])
        return out
    else:
        return mc.listConnections('%s.surfaceShader'%(sgs[0]))[0]
    
    
def rmh_makeBlendshapeProgressControl(objs = None, attrName = 'blendShapeProgress', additive = True, func = 'linstep'):
    if not objs:
        objs = mc.ls(sl = True)
    
    mc.undoInfo(ock = True)
    
    for obj in objs:
        if not attrName in mc.listAttr(obj):
            mc.addAttr(obj, ln = attrName, at = 'double', minValue = 0, dv = 0, k = 1)
        overlapAttr = '%s_overlap'%attrName
        if not overlapAttr in mc.listAttr(obj):
            mc.addAttr(obj, ln = overlapAttr, at = 'double', minValue = 0, maxValue = 1, dv = 0, k = 1)
            
        expName = '%s_bsProgress'%obj
        if mc.objExists(expName):
            mc.delete(expName)
        
        res = mc.listHistory(obj)
        res = mc.ls(res, type = 'blendShape')
        if not res:
            print(obj, 'has no blendshape')
            continue
        blendShape = res[0]
        weightAttrs = mc.listAttr(blendShape + '.w', multi=True)
        
        if not weightAttrs:
            print(obj, 'has no weight attrs')
            continue
        
        progPlug = '%s.%s'%(obj, attrName)
        overPlug = '%s.%s'%(obj, overlapAttr)
        exp = []
        for i,w in enumerate(weightAttrs):
            plug = '%s.%s'%(blendShape, w)
            if additive:
                exp.append(f'{plug} = {func}({i} - {overPlug},{i+1} + {overPlug}, {progPlug});')
            else:
                exp.append(f'{plug} = {func}({i} - {overPlug},{i+1} + {overPlug}, {progPlug}) - {func}({i+1} - {overPlug},{i+2} + {overPlug}, {progPlug});')
            
        mc.expression(s = '\n'.join(exp), n = expName)
        
    mc.undoInfo(cck = True)
    
    
    
    
    
    