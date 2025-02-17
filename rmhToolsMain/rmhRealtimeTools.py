from __future__ import absolute_import
from __future__ import print_function
import maya.cmds as mc
import maya.mel as mel
import random, os, pickle, subprocess, __main__, shutil
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


exportSetName = 'exportSet'

imgExts = ['jpg', 'png', 'jpeg', 'tif', 'tga']

def subs_createPlacementNodes(fileNodes = None, setVals = {'wrapU':False, 'wrapV':False}  , connectIndividualUV = False):
    if not fileNodes:
        fileNodes = mc.ls(type = 'file')
    
    if connectIndividualUV:
        attrs = ( ('outU', 'uCoord'), ('outV', 'vCoord'))
    else:
        attrs = [['outUV', 'uvCoord']]
    out = []
    for fn in fileNodes:
        pn = mc.createNode('place2dTexture', n = '%s_p2d'%fn)
        mc.setAttr('%s.wrapU'%pn, 1)
        mc.setAttr('%s.wrapV'%pn, 1)
        for von,nach in attrs:
            if nach in mc.listAttr(fn):
                mc.connectAttr('%s.%s'%(pn, von), '%s.%s'%(fn, nach) , force = True)
        for attrName in setVals.keys():
            mc.setAttr('%s.%s'%(pn,attrName), setVals[attrName] )
        out.append(pn)
    
    return out


def subs_importSubstanceTextures_PBS(texFolder = None):
    def getExt(f):
        return f.split('.')[-1].lower()
    def createFileNodeAndConnect(name, imgPath, destPlug):
        if not mc.objExists(name):
            mc.shadingNode('file', n = name, asTexture = True )
            p2d = subs_createPlacementNodes([name], connectIndividualUV = False)[0]
        mc.connectAttr('%s.outColor'%name, destPlug, f = 1)
        mc.setAttr('%s.fileTextureName'%name, imgPath, type = 'string')
        
    if not texFolder:
        texFolder = mc.fileDialog2(fm = 3)
        if not texFolder:
            return
    texFolder=texFolder[0]
    
    fileList = os.listdir(texFolder)
    fileList = [f for f in fileList if getExt(f) in imgExts]
    
    for imgName in fileList:
        base = imgName.split('.')[0]
        fullPath = os.path.join(texFolder, imgName).replace('\\', '/')
        spl = base.split('_')
        if len(spl) < 2:
            print('file %s too short after _ split'%imgName)
            continue
        
        
        ######## PBS
        matName, channelName = spl[-2],spl[-1]
        if not mc.objExists(matName):
            sg, _ = subs_createPBSShader(name = matName)
        else:
            if not mc.objectType(matName) == 'StingrayPBS':
                matName = matName + '_PBS'
                if not mc.objExists(matName):
                    sg, _ = subs_createPBSShader(name = matName)
        
        channelMapping = {'BaseColor':'TEX_color_map','Metallic':'TEX_metallic_map','Normal':'TEX_normal_map','Roughness':'TEX_roughness_map', 'Emission':'TEX_emissive_map', 'AO':'TEX_ao_map'}
        channelMapping_bool = {'BaseColor':'use_color_map','Metallic':'use_metallic_map','Normal':'use_normal_map','Roughness':'use_roughness_map', 'Emission':'use_emissive_map', 'AO':'use_ao_map'}
        
        if channelName in channelMapping:
            createFileNodeAndConnect(name = '%s_%s_f'%(matName, channelName), imgPath = fullPath, destPlug = '%s.%s'%(matName, channelMapping[channelName]))
            if channelName in channelMapping_bool:
                mc.setAttr('%s.%s'%(matName, channelMapping_bool[channelName]), True)


def subs_createPBSShader(name = 'PBS_Mat'):
    mtl = mc.shadingNode('StingrayPBS', n = name, asShader = True )
    sg = mc.sets(renderable = True ,noSurfaceShader = True, empty = True, name = '%sSG'%name)
    mc.connectAttr('%s.outColor'%mtl, '%s.surfaceShader'%sg, force = True)
    mc.setAttr('%s.initgraph'%mtl, True)
    mel.eval('shaderfx -sfxnode %s -edit_int 6 "numlights" 3;'%mtl)
    return sg, name


def rmh_setupGridForCm():
    mc.grid(spacing=100, s = 500)

def rmh_adjustCameraSettingsForCm():
    all_cams = [c for c in mc.ls(type = 'camera') if not mc.getAttr('%s.orthographic'%c)]
    for cam in all_cams:
        mc.setAttr('%s.nearClipPlane'%cam, 0.1)
        mc.setAttr('%s.farClipPlane'%cam, 100000)
        mc.setAttr('%s.locatorScale'%cam, 2000)
    

def checkMayaUnits(shouldBe = 'm'):
    currentUnit = mc.currentUnit(q = True, linear = True)
    if currentUnit != shouldBe:
        check = mc.confirmDialog( title='exportToUnity', message='currentUnit is %s and not %s - change first?'%(currentUnit, shouldBe), button=['Yes', 'No', 'Cancel'],\
                                 defaultButton='Yes', cancelButton='Cancel', dismissString='No' )
        if check == 'Yes':
            # mc.currentUnit(linear = 'm') #### macht mist mit grid, in prefs anpassen
            return
        elif check == 'Cancel':
            return
        else:
            return True
    else:
        return True

def exportToUnity(outPath = None):
    currentUnit = mc.currentUnit(q = True, linear = True)
    # if not checkMayaUnits():
    #     return
    
    exportUnit = 'cm' if currentUnit == 'm' else 'm'
    
    # ,"FBXExportBakeComplexStart -v "+str(minTime),"FBXExportBakeComplexEnd -v "+str(maxTime))
    opts = "FBXExportBakeComplexAnimation -v true","FBXExportBakeComplexStep -v 1","FBXExportUseSceneName -v false","FBXExportQuaternion -v euler","FBXExportShapes -v true",\
            "FBXExportSkins -v true","FBXExportConstraints -v false","FBXExportCameras -v true","FBXExportLights -v false","FBXExportConvertUnitString "+exportUnit,"FBXExportEmbeddedTextures -v true",\
            "FBXExportInputConnections -v false","FBXExportUpAxis y"
    for o in opts:
        mel.eval(o)
    
    sel = mc.ls(sl =True)
    
    storeAttr = 'lastUnityExportPath'
    if not storeAttr in mc.listAttr('time1'):
        mc.addAttr('time1', ln = storeAttr, dt = 'string')
    
    storedPath = mc.getAttr('time1.'+storeAttr)
    if storedPath:
        res = mc.confirmDialog(title='exportToUnity',message='use %s?'%storedPath,button=['Yes', 'No', 'Cancel'], defaultButton='No',cancelButton='Cancel', dismissString='Cancel')
        if res == 'Cancel':
            return
        res = True if res == 'Yes' else False
        if res:
            outPath = storedPath
    
    if not outPath:
        outPath = mc.fileDialog2(fm = 0)
        if not outPath:
            return
        else:
            outPath = outPath[0].replace('/','\\')
    
    mc.editRenderLayerGlobals( currentRenderLayer='defaultRenderLayer' )
    all_as = mc.ls(assemblies = True)
    tempRL = 'expotTemp_RL'
    if mc.objExists(tempRL):
        mc.delete(tempRL)
    mc.createRenderLayer(noRecurse=True, name=tempRL, e = True)
    mc.editRenderLayerMembers(tempRL, all_as )
    mc.editRenderLayerGlobals( currentRenderLayer=tempRL )
    
    all_trans = mc.ls(type = 'transform')
    path_objs = [o for o in all_trans if 'colPath' in mc.listAttr(o)]
    for obj in path_objs:
        if 'exportTexture' in mc.listAttr(obj):
            val = mc.getAttr('%s.exportTexture'%obj)
            if not val:
                pmm.assignSG('initialShadingGroup', [obj])
    
    mc.select(sel)
    fbxPath = outPath.split('.')[0] + '.fbx'
    # xmlPath = outPath.split('.')[0] + '.xml'
    mc.file(fbxPath, force = 1, options = "" ,typ = "FBX export" ,pr=1 ,es = 1 )
    # saveXMl(xmlPath = xmlPath)
    mc.setAttr('time1.%s'%storeAttr, fbxPath, type = 'string')
    
    if '_exp' in sel[0]:
        orig = sel[0].replace('_exp','')
        if mc.objExists(orig):
            res = mc.confirmDialog(title='exportToUnity',message='delete export group?',button=['Yes', 'No'], defaultButton='Yes',cancelButton='No', dismissString='No')
            if res == 'Yes':
                mc.delete(sel[0])
                mc.setAttr('%s.v'%orig, 1)
    
    mc.editRenderLayerGlobals( currentRenderLayer='defaultRenderLayer' )
    mc.delete(tempRL)
    print(fbxPath)


def rmh_gameExporter_setAll():
    sceneName = mc.file( q = True, sn = True, shn = True).split('.')[0]
    if not sceneName:
        mc.confirmDialog(title='gameExporter_setAll',message='file needs to be saved first',button=['Ok'])
        return
    rmh_setGameExporterPath()
    rmh_setGameExporterOptions()
    
def rmh_openGameExporter():
    currentUnit = mc.currentUnit(q = True, linear = True)
    if currentUnit != 'm' and not mc.optionVar( exists='openGameExporter_dontShowUnitWarning' ):
        res = mc.confirmDialog(title='openGameExporter',message='current unit is not m, you will have to set the asset scale in Unity',button=['Ok', 'Don\'t show again'])
        if res != 'Ok':
            mc.optionVar( iv=('openGameExporter_dontShowUnitWarning', 1))
    
    mel.eval('gameFbxExporter')
    
def rmh_getAssetDir():
    sceneName = mc.file( q = True, sn = True, shn = True).split('.')[0]
    if not sceneName:
        mc.confirmDialog(title='gotoAssetExportFolder',message='file needs to be saved first',button=['Ok'])
        return False, False
    spl = sceneName.split('_')
    
    if len(spl) > 1:
        sceneBase = '_'.join(spl[:-1])
    else:
        sceneBase = spl[0]
    
    workspacePath = mc.workspace(q= True, rd = True)
    workspacePath = os.path.normpath(workspacePath)
    metaDir = os.path.dirname(workspacePath)
    assetDir = os.path.join(metaDir, '04_assetExport\\%s\\'%sceneBase )
    if not os.path.isdir(assetDir):
        res = mc.confirmDialog(title='gotoAssetExportFolder',message='%s does not exist, create?'%assetDir,button=['Ok', 'Cancel'], defaultButton='No',cancelButton='Cancel', dismissString='Cancel')
        if res == 'Cancel':
            return
        os.makedirs(assetDir)
    print(assetDir)
    return assetDir, sceneBase
    
def rmh_createExportSet():
    setNames = [exportSetName]
    for s in setNames:
        if not mc.objExists(s):
            mc.sets(name = s, em = True)
            print('%s created'%s)

def rmh_addToExportSet():
    rmh_createExportSet()
    sel = mc.ls(sl = True)
    mc.undoInfo(ock = True)
    for obj in sel:
        mc.sets(obj, addElement = exportSetName, e = True)
    mc.undoInfo(cck = True)
    print('added to %s'%exportSetName)
    

def rmh_gotoAssetExportFolder():
    assetDir,_ = rmh_getAssetDir()
    if assetDir:
        subprocess.Popen('explorer \"%s\"'%os.path.normpath(assetDir))
    
def rmh_setGameExporterPath(openGE = True):
    assetDir, sceneBase = rmh_getAssetDir()
    if assetDir:
        try:
            mc.setAttr('gameExporterPreset1.exportPath', assetDir, type = 'string')
            mc.setAttr('gameExporterPreset2.exportPath', assetDir, type = 'string')
            mc.setAttr('gameExporterPreset3.exportPath', assetDir, type = 'string')
            mc.setAttr('gameExporterPreset1.exportFilename', sceneBase, type = 'string')
            mc.setAttr('gameExporterPreset2.exportFilename', sceneBase, type = 'string')
            mc.setAttr('gameExporterPreset3.exportFilename', sceneBase, type = 'string')
        except:
            mc.confirmDialog(title='rmh_setGameExporterExportPath',message='couldnt set path, try opening Game Exporter first',button=['Ok'])
        if openGE:
            mel.eval('gameFbxExporter')

def rmh_setGameExporterOptions():
    info = 'the following will be set: \n- export Type to set \n- copy the files to be exported in the set \"%s\"'%exportSetName
    res = mc.confirmDialog(title='rmh_setGameExporterOptions',message=info,button=['Ok', 'Cancel'])
    if res == 'Cancel':
        return
    rmh_createExportSet()
    try:
        mc.setAttr('gameExporterPreset1.exportSetIndex', 3)
        mc.setAttr('gameExporterPreset2.exportSetIndex', 3)
        mc.setAttr('gameExporterPreset3.exportSetIndex', 3)
        mc.setAttr('gameExporterPreset1.selectionSetName', exportSetName, type = 'string')
        mc.setAttr('gameExporterPreset2.selectionSetName', exportSetName, type = 'string')
        mc.setAttr('gameExporterPreset3.selectionSetName', exportSetName, type = 'string')
    except:
        mc.confirmDialog(title='rmh_setGameExporterExportPath',message='couldnt set path, try opening Game Exporter first',button=['Ok'])
    
        #setAttr  -type "string" "gameExporterPreset2.selectionSetName" "set1"
    mc.setAttr('gameExporterPreset3.selectionSetName', "exportSet", type = 'string')
    return


def rmh_getTimeVar(attr):
    if attr in mc.listAttr('time1'):
        return mc.getAttr('time1.%s'%attr)

def rmh_setTimeVar(attr, val, atType = 'string'):
    if not attr in mc.listAttr('time1'):
        if atType == 'string':
            mc.addAttr('time1', ln = attr, dt = 'string')
        else:
            mc.addAttr('time1', ln = attr, at = atType, k = 1)
    
    if atType == 'string':
        mc.setAttr('time1.%s'%attr, val, type = 'string')
    else:
        mc.setAttr('time1.%s'%attr, val)
            
    
def rmh_copyToUnityFolder(unityDir = None):
    assetDir, sceneBase = rmh_getAssetDir()
    fileList = os.listdir(assetDir)
    fileList = [os.path.join(assetDir, f).replace('/', '\\') for f in fileList if f.split('.')[-1].lower() == 'fbx' and sceneBase in f]
    
    if not fileList:
        print('rmh_copyToUnityFolder --- no files with base %s found in %s'%(sceneBase, assetDir))
        return
    
    lastUnityDir = None
    if mc.optionVar( exists='unityExportDir' ):
        lastDir = rmh_getTimeVar('unityExportDir')
        lastUnityDir = mc.optionVar( q='unityExportDir' ) if not lastDir else lastDir
        res = mc.confirmDialog(title='copyToUnityFolder',message='use %s?'%lastUnityDir,button=['Yes', 'No', 'Cancel'])
        if res == 'Cancel':
            return
        if res == 'Yes':
            unityDir = lastUnityDir
            
    if not unityDir:
        unityDir = mc.fileDialog2(fm = 3, dir = lastUnityDir)
        if not unityDir:
            return
        else:
            unityDir = unityDir[0].replace('/','\\')
    
    rmh_setTimeVar('unityExportDir', unityDir, 'string')
    mc.optionVar( sv=('unityExportDir', unityDir))
    
    for sourcePath in fileList:
        fileName = sourcePath.split('\\')[-1]
        destPath = os.path.join(unityDir, fileName)
        shutil.copy2(sourcePath, destPath)
        print('copied from', sourcePath, 'to', destPath)
    
    
    
def rmh_addUnityLightControl(lights = None):
    if not lights:
        lights = mc.ls(sl = True)
    
    mc.undoInfo(ock = True)
    
    for light in lights:
        sh = mc.listRelatives(light, s = 1)
        if not sh:
            continue
        lightShape = sh[0]
        if not 'intensity' in mc.listAttr(lightShape):
            continue
        # if not 'unityRange' in mc.listAttr(lightShape):
        #     continue
        val = mc.getAttr('%s.intensity'%lightShape)
        plugs = mc.listConnections('%s.intensity'%lightShape, s = 1, d = 0, p = 1)
        
        attrs = ['intensityIn', 'intensityMult', 'unityMult', 'unityRange']
        stdAttrs = {'intensityIn':val, 'intensityMult':1, 'unityMult':0.01, 'unityRange':10}
        for attr in attrs:
            if not attr in mc.listAttr(lightShape):
                mc.addAttr(lightShape, ln = attr, at = 'double', dv = stdAttrs.get(attr, 0), k = 1)
        
        if plugs:
            mc.connectAttr(plugs[0], '%s.intensityIn'%lightShape, f = 1)
            mc.disconnectAttr(plugs[0], '%s.intensity'%lightShape)
            
        # mult = mc.shadingNode('multiplyDivide', n = '%s_mdiv'%lightShape, asUtility = True)
        # mc.connectAttr('%s.intensityIn'%lightShape, '%s.input1X'%mult)
        # mc.connectAttr('%s.intensityMult'%lightShape, '%s.input2X'%mult)
        # mc.connectAttr('%s.outputX'%mult, '%s.intensity'%lightShape, f = 1)
        
        expTx = 'intensity = intensityIn * intensityMult'
        mc.expression(n = '%s_uExp'%lightShape, s = expTx, o = lightShape)
    
    mc.select(lights)
    mc.undoInfo(cck = True)
        
def rmh_doGameExportWithLightMult():
    lights = mc.ls(type = 'light')
    
    mc.undoInfo(ock = True)
    
    for light in lights:
        if 'intensityMult' in mc.listAttr(light):
            val = mc.getAttr('%s.unityMult'%light)
            mc.setAttr('%s.intensityMult'%light, val)
    
    mel.eval('gameExp_DoExport;')
    
    for light in lights:
        if 'intensityMult' in mc.listAttr(light):
            mc.setAttr('%s.intensityMult'%light, 1)
    
    mc.undoInfo(cck = True)