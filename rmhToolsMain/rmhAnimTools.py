from __future__ import absolute_import
import maya.cmds as mc
import maya.mel as mel
import random, os, pickle, subprocess, __main__, shutil
from six.moves import range
from importlib import reload

try:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
except:
    from PySide.QtGui import *
    from PySide.QtCore import *
    from shiboken import wrapInstance





    
def attachLocatorsToObjects(objs = None):
    mc.undoInfo (ock = True)
    if not objs:
        objs = mc.ls(sl = True)
    
    metaGrp = '_attachLocs' if mc.objExists('_attachLocs') else mc.group(n = '_attachLocs', em = True)
    for obj in objs:
        loc = mc.spaceLocator(n = '%s_attachLoc'%obj)[0]
        mc.pointConstraint(obj, loc, mo = False)
        mc.parent(loc, metaGrp)
    
    mc.undoInfo (cck = True)

def MASH_connectBlendDeformerTarget():
    sel = mc.ls(sl = True)
    
    tgt, baseObj= sel[:2]
    
    hist = mc.listHistory(baseObj)
    bdef = mc.ls(hist, type = 'MASH_BlendDeformer')
    if not bdef:
        mc.error('no mash blend deformer found in %s'%baseObj)
    
    tgtSh = mc.listRelatives(tgt, s = 1)[0]
    
    mc.connectAttr('%s.worldMesh[0]'%tgtSh, '%s.blendMesh'%bdef[0], f = 1)
    
    
def MASH_initialStateFromObjects(objs = None, mashWaiters = None):
    if not objs or not mashWaiters:
        sel = mc.ls(sl = True)
        objs = [o for o in sel if mc.objectType(o) == 'transform']
        mashWaiters = [o for o in sel if mc.objectType(o) == 'MASH_Waiter']
    
    for waiter in mashWaiters:
        num = len(objs)
        dist = mc.listConnections('%s.waiterMessage'%waiter, s = 1, d = 0)[0]
        mc.setAttr('%s.pointCount'%dist, num)
        mc.setAttr('%s.arrangement'%dist, 7)
        for i,obj in enumerate(objs):
            mc.connectAttr('%s.worldMatrix[0]'%obj, '%s.initialStateMatrix[%d]'%(dist, i), f = 1)

def MASH_breakoutAll(mashWaiters = None, translate = True, rotate = True, scale = True):
    if not mashWaiters:
        sel = mc.ls(sl = True)#
        mashWaiters = [o for o in sel if mc.objectType(o) == 'MASH_Waiter']
    if not mashWaiters:
        mc.warning('MASH_breakoutAll: gotta select the MASH waiter!')
    
    metaGrp = '_MASHattachLocs' if mc.objExists('_MASHattachLocs') else mc.group(n = '_MASHattachLocs', em = True)
    for waiter in mashWaiters:
        grp = mc.group(n = '%s_locGrp'%waiter, em = True)
        mc.parent(grp, metaGrp)
        count = mc.getAttr('%s.pointCount'%waiter)
        
        breakout = mc.createNode('MASH_Breakout')
        mc.connectAttr('%s.outputPoints'%waiter, '%s.inputPoints'%breakout)
        
        for i in range(count):
            loc = mc.spaceLocator(n = '%s_loc%03d'%(waiter, i))[0]
            mc.parent(loc, grp)
            mc.connectAttr('%s.outputs[%d].translate'%(breakout, i), '%s.translate'%loc, f = 1)
            mc.connectAttr('%s.outputs[%d].rotate'%(breakout, i), '%s.rotate'%loc, f = 1)
            mc.connectAttr('%s.outputs[%d].scale'%(breakout, i), '%s.scale'%loc, f = 1)

def MASH_toggleColorNodes(colorNodes = None):
    if not colorNodes:
        colorNodes = mc.ls(type = 'MASH_Color')
    
    firstVal = mc.getAttr('%s.enable'%colorNodes[0])
    for col in colorNodes:
        mc.setAttr('%s.enable'%col, not firstVal)

def MASH_setTargetForAll(orientNodes = None):
    if not orientNodes:
        orientNodes = mc.ls(type = 'MASH_Orient')
    sel = mc.ls(sl = True)
    obj = sel[0]
    
    for node in orientNodes:
        mc.connectAttr('%s.translate'%obj, '%s.targetInput'%node, f= 1)
    