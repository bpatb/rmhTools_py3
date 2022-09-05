

from __future__ import absolute_import
from __future__ import print_function
from importlib import reload
from six.moves import map
from six.moves import range
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

import os, random, math, shutil, subprocess
import __main__
import rmhTools_widgets as pw




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
        