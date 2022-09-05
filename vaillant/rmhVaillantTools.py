
from __future__ import absolute_import
from __future__ import print_function
import os, subprocess, threading, math, random,shutil
import __main__
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

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin, MayaQDockWidget
import maya.api.OpenMayaUI  as omui
import maya.OpenMaya as api
import maya.OpenMayaUI as apiUI
import maya.cmds as mc
import maya.mel as mel

import rmhTools_methods as rtm
reload(rtm)


displayLayerPostfix = '_DL'
renderLayerPostfix = '_RL'
groupPostfix = '_grp'
masterGroupPostfix = '_geraet' + groupPostfix
inactivePrefix = 'OFF_'

casingName = 'casing'
brandShieldName = casingName + '_brandshield'
tecInsideName = 'tec_inside'
logoName = 'logo'
environmentName = 'environment'
notNeededName = 'not_needed'

RL_xray_beauty = 'xray_beauty' + renderLayerPostfix
RL_xray_AO = 'xray_AO' + renderLayerPostfix
RL_Schatten = 'Schatten' + renderLayerPostfix
RL_Schatten_AO = 'Schatten_AO' + renderLayerPostfix
RL_acryl_casing_beauty = 'acryl_casing_beauty' + renderLayerPostfix
RL_acryl_casing_blurry = 'acryl_casing_blurry' + renderLayerPostfix
RL_acryl_casing_clear = 'acryl_casing_clear' + renderLayerPostfix
RL_acryl_casing_AO = 'acryl_casing_AO' + renderLayerPostfix
RL_acryl_logo = 'logo' + renderLayerPostfix
RL_brandshield = 'brandshield' + renderLayerPostfix

licht_setup_acryl_casing = 'licht_setup_acryl_casing'
licht_setup_acryl_casingBlurry = 'licht_setup_acryl_casingBlurry'
licht_setup_acryl_casingClear = 'licht_setup_acryl_casingClear'
licht_setup_xray_beauty = 'licht_setup_beauty_xray'
licht_setup_acryl_logo = 'licht_setup_logo'
licht_setup_schatten = 'licht_setup_schatten'
licht_setup_acryl_brandshield = 'licht_setup_acryl_brandshield'

def vai_error(message):
    mc.confirmDialog(title='vaillant tools',message=message,button=['Fine.'], defaultButton='Fine.')
    
def vai_setupRenderer():
    # fixMayaRenderGlobals()
    if not mc.objExists('redshiftOptions'):
        mc.createNode('redshiftOptions')
    mc.setAttr('redshiftOptions.imageFormat', 1)
    mc.setAttr('redshiftOptions.exrForceMultilayer', 1)
    mc.setAttr('defaultRenderGlobals.imageFilePrefix', '<Scene>/<Scene>_<RenderLayer>', type = 'string')
    mc.setAttr('defaultResolution.width', 4252)
    mc.setAttr('defaultResolution.height', 5669)
    mc.setAttr('defaultResolution.pixelAspect', 1)
    try:
        mel.eval('setTestResolutionVar(3);')
    except:
        pass
def vai_importAllMaterials():
    # if len(mc.fileInfo('vai_materialsImported', q=True)) != 0:
    #     mc.warning('vai_importAllMaterials already executed...')
    #     return 0
    
    before = set(mc.ls(mat = True))
    beforeDag = set(mc.ls(dag = True))
    
    fileDir = os.path.dirname(os.path.realpath(__file__))
    fileDir = fileDir.replace('\\', '/')
    matDir = fileDir + '/materials'
    if not os.path.isdir(matDir):
        vai_error('directory %s not found ! '%matDir)
        return
        
    files = [f for f in os.listdir(matDir) if f.split('.')[-1].lower() in ['ma', 'mb']]
    for f in files:
        base = f.split('.')[0]
        if mc.objExists(base):
            print('%s exists - skipping'%base)
            continue
        mc.file(matDir + '/' + f, i = True, ignoreVersion = True, ra = False, mergeNamespacesOnClash = False ,  options = "v=0;" , pr = True)
    
    after = set(mc.ls(mat = True))
    afterDag = set(mc.ls(dag = True))
    newMats = list(after.difference(before))
    newDags = list(afterDag.difference(beforeDag))
    
    matNodeGrp = '_materialNodes'
    if newDags:
        if not mc.objExists(matNodeGrp):
            mc.group(n = matNodeGrp, em = True)
            mc.hide(matNodeGrp)
        for n in newDags:
            mc.parent(n, matNodeGrp)
    
    if newMats:
        print('imported:\n', '\n'.join(newMats))
    else:
        print('imported nothing.')

def vai_importAllLights():
    fileDir = os.path.dirname(os.path.realpath(__file__))
    fileDir = fileDir.replace('\\', '/')
    matDir = fileDir + '/lights'
    if not os.path.isdir(matDir):
        vai_error('directory %s not found ! '%matDir)
        return
        
    files = [f for f in os.listdir(matDir) if f.split('.')[-1].lower() in ['ma', 'mb']]
    for f in files:
        base = f.split('.')[0]
        if mc.objExists(base):
            print('%s exists - skipping'%base)
            continue
        mc.file(matDir + '/' + f, i = True, ignoreVersion = True, ra = False, mergeNamespacesOnClash = False ,  options = "v=0;" , pr = True)
    
    
    # mc.fileInfo('vai_materialsImported', 1)

def vai_importMiscAssets():
    fileDir = os.path.dirname(os.path.realpath(__file__))
    fileDir = fileDir.replace('\\', '/')
    matDir = fileDir + '/misc'
    if not os.path.isdir(matDir):
        vai_error('directory %s not found ! '%matDir)
        return
        
    files = [f for f in os.listdir(matDir) if f.split('.')[-1].lower() in ['ma', 'mb']]
    for f in files:
        base = f.split('.')[0]
        if mc.objExists(base):
            print('%s exists - skipping'%base)
            continue
        mc.file(matDir + '/' + f, i = True, ignoreVersion = True, ra = False, mergeNamespacesOnClash = False ,  options = "v=0;" , pr = True)
    
    
    
def vai_tecInsideDL():
    if not len(mc.fileInfo('vaiScnInit', q=True)):
        vai_error('Scene is not initialized...')
        return
    if len(mc.ls(sl=True)) > 0:
        if len(mc.ls(tecInsideName + groupPostfix)) == 0:
            mc.group(n=tecInsideName + groupPostfix)
            mc.createDisplayLayer(n=tecInsideName + displayLayerPostfix)
        else:
            objs = mc.ls(sl=True, l=True)
            for obj in objs:
                par = mc.listRelatives(obj, p=True)
                if par is None or not tecInsideName + groupPostfix in par:
                    mc.parent(obj, tecInsideName + groupPostfix)
                    mc.editDisplayLayerMembers(tecInsideName + displayLayerPostfix, mc.ls(sl=True, l=True))

        #mg = deviceName + masterGroupPostfix
        mg = mc.ls('*'+masterGroupPostfix+ '*')[0]
        gr = tecInsideName + groupPostfix
        par = mc.listRelatives(gr, p=True)
        if par is None or not mg in par:
            mc.parent(gr, mg)
            
    else:
        vai_error('Nothing selected')
    
def vai_casingDL():
    if not len(mc.fileInfo('vaiScnInit', q=True)):
        vai_error('Scene is not initialized...')
        return
    if len(mc.ls(sl=True)) > 0:
        if len(mc.ls(casingName + groupPostfix)) == 0:
            mc.group(n=casingName + groupPostfix)
            mc.createDisplayLayer(n=casingName + displayLayerPostfix)
        else:
            objs = mc.ls(sl=True, l=True)
            for obj in objs:
                par = mc.listRelatives(obj, p=True)
                if par is None or not casingName + groupPostfix in par:
                    mc.parent(obj, casingName + groupPostfix)
                    mc.editDisplayLayerMembers(casingName + displayLayerPostfix, mc.ls(sl=True, l=True))

        #mg = deviceName + masterGroupPostfix
        mg = mc.ls('*'+masterGroupPostfix+ '*')[0]
        gr = casingName + groupPostfix
        par = mc.listRelatives(gr, p=True)
        if par is None or not mg in par:
            mc.parent(gr, mg)
            
    else:
        vai_error('Nothing selected')
    
def vai_logoDL():
    if not len(mc.fileInfo('vaiScnInit', q=True)):
        vai_error('Scene is not initialized...')
        return
    if len(mc.ls(sl=True)) > 0:
        if len(mc.ls(logoName + groupPostfix)) == 0:
            mc.group(n=logoName + groupPostfix)
            mc.createDisplayLayer(n=logoName + displayLayerPostfix)
        else:
            objs = mc.ls(sl=True, l=True)
            for obj in objs:
                par = mc.listRelatives(obj, p=True)
                if par is None or not logoName + groupPostfix in par:
                    mc.parent(obj, logoName + groupPostfix)
                    mc.editDisplayLayerMembers(logoName + displayLayerPostfix, mc.ls(sl=True, l=True))

        #mg = deviceName + masterGroupPostfix
        mg = mc.ls('*'+masterGroupPostfix+ '*')[0]
        gr = logoName + groupPostfix
        par = mc.listRelatives(gr, p=True)
        if par is None or not mg in par:
            mc.parent(gr, mg)
            
    else:
        vai_error('Nothing selected')
    
def vai_notNeededDL():
    if not len(mc.fileInfo('vaiScnInit', q=True)):
        vai_error('Scene is not initialized...')
        return
    if len(mc.ls(sl=True)) > 0:
        if len(mc.ls(notNeededName + groupPostfix)) == 0:
            mc.group(n=notNeededName + groupPostfix)
            mc.createDisplayLayer(n=notNeededName + displayLayerPostfix)
        else:
            objs = mc.ls(sl=True, l=True)
            for obj in objs:
                par = mc.listRelatives(obj, p=True)
                if par is None or not notNeededName + groupPostfix in par:
                    mc.parent(obj, notNeededName + groupPostfix)
                    mc.editDisplayLayerMembers(notNeededName + displayLayerPostfix, mc.ls(sl=True, l=True))

        #mg = deviceName + masterGroupPostfix
        mg = mc.ls('*'+masterGroupPostfix+ '*')[0]
        gr = notNeededName + groupPostfix
        par = mc.listRelatives(gr, p=True)
        if par is None or not mg in par:
            mc.parent(gr, mg)
            
    else:
        vai_error('Nothing selected')

def vai_createRL_xray_beauty():
    if not mc.objExists(licht_setup_xray_beauty+groupPostfix) or not mc.objExists(tecInsideName + groupPostfix):#len(mc.ls(licht_setup_xray_beauty+groupPostfix)) == 0 or len(mc.ls(tecInsideName + groupPostfix)) == 0:
        mc.warning(RL_xray_beauty+" cannot be created.\n"+ licht_setup_xray_beauty+groupPostfix+ " and/or "+ tecInsideName + groupPostfix+" are missing!")
        return
    
    RS_opts = 'redshiftOptions'
    if len(mc.ls(RL_xray_beauty)) == 0:
        curRL = mc.createRenderLayer(licht_setup_xray_beauty + groupPostfix, tecInsideName + groupPostfix, name=RL_xray_beauty)
        mc.editRenderLayerGlobals(crl=curRL)
        mc.editRenderLayerAdjustment('%s.primaryGIEngine'%RS_opts)
        mc.setAttr('%s.primaryGIEngine'%RS_opts, 1)

def vai_createRL_casing_blurry():
    if not mc.objExists(licht_setup_acryl_casingBlurry+groupPostfix) or not mc.objExists(casingName + groupPostfix):#len(mc.ls(licht_setup_xray_beauty+groupPostfix)) == 0 or len(mc.ls(tecInsideName + groupPostfix)) == 0:
        mc.warning(RL_xray_beauty+" cannot be created.\n"+ licht_setup_acryl_casingBlurry+groupPostfix+ " and/or "+ casingName + groupPostfix+" are missing!")
        return
    
    objs = rtm.returnMeshesInHierarchy(casingName + groupPostfix)
    sg = 'CasingBlurry_MtlSG'
    if not mc.objExists(sg):
        mc.warning('Material %s not found!!!!'%sg)
        
    RS_opts = 'redshiftOptions'
    if len(mc.ls(RL_acryl_casing_blurry)) == 0:
        curRL = mc.createRenderLayer(licht_setup_acryl_casingBlurry + groupPostfix, casingName + groupPostfix, name=RL_acryl_casing_blurry)
        mc.editRenderLayerGlobals(crl=curRL)
        mc.editRenderLayerAdjustment('%s.primaryGIEngine'%RS_opts)
        mc.setAttr('%s.primaryGIEngine'%RS_opts, 0)
        if objs and mc.objExists(sg):
            rtm.assignSG(sg, objs)

def vai_createRL_casing_clear():
    if not mc.objExists(licht_setup_acryl_casingClear+groupPostfix) or not mc.objExists(casingName + groupPostfix):#len(mc.ls(licht_setup_xray_beauty+groupPostfix)) == 0 or len(mc.ls(tecInsideName + groupPostfix)) == 0:
        mc.warning(RL_xray_beauty+" cannot be created.\n"+ licht_setup_acryl_casingClear+groupPostfix+ " and/or "+ casingName + groupPostfix+" are missing!")
        return
    
    objs = rtm.returnMeshesInHierarchy(casingName + groupPostfix)
    sg = 'CasingClear_MtlSG'
    if not mc.objExists(sg):
        mc.warning('Material %s not found!!!!'%sg)
        
    RS_opts = 'redshiftOptions'
    if len(mc.ls(RL_acryl_casing_clear)) == 0:
        curRL = mc.createRenderLayer(licht_setup_acryl_casingClear + groupPostfix, casingName + groupPostfix, name=RL_acryl_casing_clear)
        mc.editRenderLayerGlobals(crl=curRL)
        mc.editRenderLayerAdjustment('%s.primaryGIEngine'%RS_opts)
        mc.setAttr('%s.primaryGIEngine'%RS_opts, 0)
    if objs and mc.objExists(sg):
        rtm.assignSG(sg, objs)

def vai_createRL_logo():
    if not mc.objExists(licht_setup_acryl_logo+groupPostfix):#len(mc.ls(licht_setup_xray_beauty+groupPostfix)) == 0 or len(mc.ls(tecInsideName + groupPostfix)) == 0:
        mc.warning(RL_xray_beauty+" cannot be created.\n"+ licht_setup_acryl_logo+groupPostfix+" is missing!")
        return
    
    RS_opts = 'redshiftOptions'
    if len(mc.ls(RL_acryl_logo)) == 0:
        curRL = mc.createRenderLayer(licht_setup_acryl_logo + groupPostfix, name=RL_acryl_logo)
        mc.editRenderLayerGlobals(crl=curRL)
        mc.editRenderLayerAdjustment('%s.primaryGIEngine'%RS_opts)
        mc.setAttr('%s.primaryGIEngine'%RS_opts, 0)

def vai_createRLPasses():
    if not len(mc.fileInfo('vaiScnInit', q=True)):
        vai_error('Scene is not initialized...')
        return
    
    vai_createRL_xray_beauty()
    vai_createRL_casing_blurry()
    vai_createRL_casing_clear()
    # vai_createRL_acryl_casing_AO()
    vai_createRL_logo()

    mc.setAttr('defaultRenderLayer.renderable', 0)
    
    mc.editRenderLayerGlobals(crl='defaultRenderLayer')
    
    print('RLs created')


def vai_initialize(name = None):
    def makeInitGroup(deviceName):
        if len(mc.fileInfo('vaiScnInit', q=True)) != 0:
            vai_error('Init scene already executed...\nCommand ignored')
            return 0
        mc.fileInfo('vaiDevName', deviceName)
        mc.fileInfo('vaiScnInit', 1)
        if len(mc.ls(str(deviceName)+masterGroupPostfix)) == 0:
            #alle obj gruppieren in deviceName_geraet_grp
            allObjs = mc.ls(v=True, assemblies=True)
            grp = mc.group(allObjs, n=str(deviceName)+masterGroupPostfix)
            print('GROUP: ',grp)
            mc.select(grp, r=True)
    
    if not mc.ls(v=True, assemblies=True):
        mc.confirmDialog(title='vaillant_initialize',message='no objects in scene!!! Import CAD data first',button=['OK'], defaultButton='OK')
        return
    
    if not name:
        result = mc.promptDialog(title='vaillant_initialize',message='device name:',button=['OK', 'Cancel'], defaultButton='OK',cancelButton='Cancel', dismissString='Cancel')
        if result == 'OK':
            name = mc.promptDialog(query=True, text=True)
        else:
            return
    
    print('setting up group ...')
    makeInitGroup(name)
    print('done.')
    
    print('setting up renderer ...')
    vai_setupRenderer()
    print('done.')
    
    print('import all materials ...')
    vai_importAllMaterials()
    print('done.')
    
    print('import all lights ...')
    vai_importAllLights()
    print('done.')
    
    print('import the rest ...')
    vai_importMiscAssets()
    print('done.')
    

def vai_selectNonRedshiftMaterials():
    pass

