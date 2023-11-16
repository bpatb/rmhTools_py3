from __future__ import absolute_import
from __future__ import print_function
import maya.cmds as mc
import maya.mel as mel


from importlib import reload
import random, pickle, os
import __main__

import rmhTools_widgets as pw
import rmhMayaMethods as rmm
import six

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
    
def returnMeshesInHierarchy(grps = None, select = False):
    if not grps:
        grps = mc.ls(sl = True)
    grps = [grps] if type(grps) in [str,six.text_type] else grps
    mc.undoInfo(ock = True)
    out = []
    for grp in grps:
        chs = mc.listRelatives(grp, ad = True)
        for c in chs:
            sh = mc.listRelatives(c, s = 1)
            if not sh or not mc.objectType(sh[0]) in ['mesh']:
                continue
            out.append(c)
    if select:
        mc.select(out)
    mc.undoInfo(cck = True)
    return out
    
def getMaterial(obj = None):
    if not obj:
        obj = mc.ls(sl = True)[0]
    sg = getShadingGroup(obj)
    if not sg:
        return False
    return mc.listConnections('%s.surfaceShader'%(sg))[0]

def getObjects_SG(sg, select = False):
    objs  = [obj for obj in mc.listConnections(sg) if mc.objectType(obj) == 'transform']
    if select:
        mc.select(objs, r = True)
    return objs

def assignSG(sg, objs = None):
    if not objs:
        objs = mc.ls(sl = True)
    if type(objs) not in [list, tuple]:
        objs = [objs]
    for obj in objs:
        if not mc.objExists(obj):
            continue
        mc.select(obj)
        try:
            mc.sets(e = True, forceElement = sg)
        except Exception:
            mc.warning('%s konnte nicht auf %s nicht zugewiesen werden'%(sg, obj))

def rememberSG(objs = None):
    if not objs:
        objs = mc.ls(sl = True)
    
    for obj in objs:
        if not 'rememberedSG' in mc.listAttr(obj):
            mc.addAttr(obj, ln = 'rememberedSG', dt = 'string')
        sg = getShadingGroup(obj)
        mc.setAttr('%s.rememberedSG'%obj, sg, type = 'string')
        
def selectAssignedObjects(mats = None, select = True): ### materialien auswaehlen , weil select assigned im hypershade das nicht fuer mehr als ein material macht
    if not mats:
        mats = mc.ls(sl = True)
    allObjs = []
    for obj in mats:
        sg = getShadingGroup(obj)
        sgobjs = getObjects_SG(sg)
        allObjs += sgobjs
    if select:
        mc.select(allObjs)
    return allObjs


def duplicateMaterialAndSG(obj = None, assign = False, nameSuffix = 'dup'): # Objekt auswaehlen, nicht Material, wenn Name mit suffix vorhanden wird nicht dupliziert
    if not obj:
        obj = mc.ls(sl = True)[0]
    sg = getShadingGroup(obj)
    mat = getMaterial(obj)
    dup_sg = '%s_%s'%(sg, nameSuffix)
    dup_mat = '%s_%s'%(mat, nameSuffix)
    if not mc.objExists(dup_sg):
        dup_sg = mc.sets(renderable = True ,noSurfaceShader = True, empty = True, name = dup_sg)
    if not mc.objExists(dup_mat):
        dup_mat = mc.duplicate(mat)[0]
    mc.connectAttr('%s.outColor'%dup_mat, '%s.surfaceShader'%(dup_sg), force = True)
    if assign:
        assignSG(dup_sg, obj)
    return dup_sg, dup_mat

def copyShaderAssignment(objs = None):
    import __main__
    if not objs:
        objs = mc.ls(sl = True)
    dc = dict()
    for obj in objs:
        dc[obj] = getShadingGroup(obj)
    __main__.tmp_csa_dict = dc
    print(dc)
    return dc
    
def pasteShaderAssignment():
    import __main__
    dc  = __main__.tmp_csa_dict
    for obj in dc.keys():
        assignSG(dc[obj], [obj])



def renameDuplicates():
    import re
    #Find all objects that have the same shortname as another
    #We can indentify them because they have | in the name
    duplicates = [f for f in mc.ls() if '|' in f]
    #Sort them by hierarchy so that we don't rename a parent before a child.
    duplicates.sort(key=lambda obj: obj.count('|'), reverse=True)
     
    #if we have duplicates, rename them
    if duplicates:
        for name in duplicates:
            # extract the base name
            m = re.compile("[^|]*$").search(name) 
            shortname = m.group(0)
 
            # extract the numeric suffix
            m2 = re.compile(".*[^0-9]").match(shortname) 
            if m2:
                stripSuffix = m2.group(0)
            else:
                stripSuffix = shortname
             
            #rename, adding '#' as the suffix, which tells maya to find the next available number
            try:
                newname = mc.rename(name, (stripSuffix + "#")) 
                print("renamed %s to %s" % (name, newname))
            except:
                pass
             
        return "Renamed %s objects with duplicated name." % len(duplicates)
    else:
        return "No Duplicates"
    

def rmh_createMultipleDomeLights(imgPaths = None):
    if not imgPaths:
        imgPaths = mc.fileDialog2(fm = 4, cap = 'createMultipleDomeLights - choose hdr files')
        if imgPaths:
            print(imgPaths)
        else:
            return
    
    mc.undoInfo(ock = True)
    newLights = []
    for i, imgPath in enumerate(imgPaths):
        name = os.path.basename(imgPath).split('.')[0]
        domeShape = mc.createNode('RedshiftDomeLight')
        domeTrans = mc.listRelatives(domeShape, p = 1)[0]
        newLights.append(domeTrans)
        mc.setAttr('%s.tex0'%domeShape, imgPath, type = 'string')
        mc.rename(domeTrans, 'dome_%s'%(name))
        # mc.rename(domeShape, 'domeLight_%02dShape'%i)
    
    rmh_linkSelectedLightsToAll(newLights)
    
    mc.undoInfo(cck = True)
    
def rmh_linkSelectedLightsToAll(lights = None, objs = None):
    if not lights:
        lights = mc.ls(sl = True)
    if not objs:
        objs = mc.ls(type = 'mesh')
        
    shs = [mc.listRelatives(light, s =1)[0] for light in lights]
    mc.lightlink( light=shs, object=objs)
    

def rmh_convertRedshiftLights():
    # Get selected transform nodes in the scene
    selected_transforms = mc.ls(selection=True, transforms=True)

    # Filter out transforms that have RedshiftPhysicalLight shape nodes
    redshift_lights = [trans for trans in selected_transforms if mc.listRelatives(trans, shapes=True, type='RedshiftPhysicalLight')]
    
    mc.undoInfo(ock = True)
    for light in redshift_lights:
        # Get the shape node
        shape_node = mc.listRelatives(light, shapes=True, type='RedshiftPhysicalLight')[0]

        # Get the light type of the RedshiftPhysicalLight
        light_type = mc.getAttr(shape_node + '.lightType')

        # Create a new Maya light based on the light type
        # 0 - point, 1 - directional, 2 - spot, 3 - area, 4 - photometric, 5 - infinite
        if light_type == 0:
            new_light = mc.pointLight()
        elif light_type == 1:
            new_light = mc.directionalLight()
        elif light_type == 2:
            new_light = mc.spotLight()
        elif light_type == 3:
            new_light = mc.areaLight()
        else:
            print("Unsupported Redshift light type: {}".format(light_type))
            continue

        new_light_transform = mc.listRelatives(new_light, parent=True)[0]

        p = mc.parentConstraint(light, new_light_transform, mo = False)
        mc.delete(p)
        # Transfer specific light attributes
        attributes = ['intensity', 'colorR', 'colorG', 'colorB']

        for attr in attributes:
            try:
                val = mc.getAttr(shape_node + '.' + attr)
                mc.setAttr(new_light + '.' + attr, *val)
            except:
                print("Failed to transfer attribute: {}".format(attr))

        mc.hide(light)

    mc.undoInfo(cck = True)
    print("Redshift lights conversion completed.")
    
def rmh_importImagesAsMaterials(imgPaths = None, setName = 'droppedMaterialSet'):
    import PatsMayaMethods2 as pmm
    if not imgPaths:
        imgPaths = mc.fileDialog2(fm = 4, cap = 'rmh_importImagesAsMaterials')
        if not imgPaths:
            return
    
    mc.undoInfo(ock = True)
    
    if not mc.objExists(setName):
        mc.sets(name = setName, em = True)
    
    for imgPath in imgPaths:
        basename = os.path.basename(imgPath)
        basename = basename.split('.')[0]
        if len(basename) > 15:
            basename = basename[:8] + '_' + basename[-3:]
        matName = '%s_Mat'%basename
        if mc.objExists(matName):
            print('%s exists'%matName)
            continue
        sg, mat = pmm.createShader(shaderType = 'surfaceShader', assignToObjs = None, name = matName, colInput = imgPath, skipExisting = True, connectTransparency = False)
        mc.sets(mat, addElement = setName, e = True)
        
    mc.undoInfo(cck = True)

def rmh_multiAssignMaterialsToObjects(objs = None, mats = None):
    import PatsMayaMethods2 as pmm
    if not objs or not mats:
        sel = mc.ls(sl = True)
        objs = [o for o in sel if mc.objectType(o) == 'transform']
        mats = [o for o in sel if mc.objectType(o) != 'transform']
    
    mc.undoInfo(ock = True)
    
    for i,obj in enumerate(objs):
        if len(mats) <= i:
            break
        mat = mats[i]
        pmm.assignMaterial(mat, [obj])
    
    mc.undoInfo(cck = True)

def RMH_setResolution():
    result = mc.confirmDialog(title='RS_setResolution',message='resolution:',button=['6710x4772','1810x1280','1728x720','1280x1024','1024x1280','1440x1080','1920x804','1920x1080', '1998x1080', 'Cancel'],\
                              defaultButton='OK',cancelButton='Cancel', dismissString='Cancel')
    if result == 'Cancel':
        return
    width, height = list(map(int, result.split('x')))
    
    mc.setAttr('defaultResolution.width', width)
    mc.setAttr('defaultResolution.height', height)
    mc.setAttr('defaultResolution.deviceAspectRatio', float(width) / height)
     
    
def rmh_afterCurveLoft_create(crvs = None, tangentType = 'linear', frameRange = None, animLength = 20, nthFrame = 5):
    import curveMorpher
    reload(curveMorpher)
    import PatsMayaMethods2 as pmm
    
    if not crvs:
        crvs = mc.ls(sl = True)
    
    frameRange = [1,50]
    mainCrv = crvs[0]
    targetCrvs = crvs[1:]
    
    print('targetss', targetCrvs)
    mc.undoInfo(ock = True)
    
    mainGrp =  pmm.createGroupIfNonExistent('crvLftAnim_g', hide = False)
    dupGrp = pmm.createGroupIfNonExistent('crvLft_frameCrvs', parent = mainGrp, hide = True, relativeGroup = False)
    
    animCrvGrp = mc.group(em = True)
    animCrvGrp = pmm.rename_individual(animCrvGrp, 'loftAnimCrv_grp')
    mc.parent(animCrvGrp, mainGrp)
    
    
    out = []
    for frame in range(frameRange[0],frameRange[1], nthFrame):
        mc.currentTime(frame)
        dup = mc.duplicate(mainCrv)[0]
        dup = pmm.rename_individual(dup, '%s_frame%03d'%(mainCrv, frame))
        mc.parent(dup, dupGrp)
        outDc = curveMorpher.morphCurves_createInbetweens_viaLoft(crvs = [dup] + targetCrvs, numTweens = 1, autoReverse = True, degree = 3, sortByDist = False, groupTo = animCrvGrp)
        srf, outCrv = outDc['loftSrf'],outDc['outCrvs'][0]
        
        mc.rebuildSurface(srf, ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kc=0, su=0, du=3, sv=0, dv=3, tol=0.01, fr=0, dir=2)

        out.append(outCrv)
        
        mc.setKeyframe('%s.uVal'%outCrv, t = frame, v = 0, itt = tangentType, ott = tangentType)
        mc.setKeyframe('%s.uVal'%outCrv, t = frame + animLength, v = 1, itt = tangentType, ott = tangentType)
        mc.setKeyframe('%s.v'%outCrv, t = frame-1 , v = 0)
        mc.setKeyframe('%s.v'%outCrv, t = frame, v = 1)
        mc.setKeyframe('%s.v'%outCrv, t = frame+animLength , v = 1)
        mc.setKeyframe('%s.v'%outCrv, t = frame+animLength+1, v = 0)

    mc.undoInfo(cck = True)
    

def rmh_addObjectTransparencyControl_SS():
    objs = mc.ls(sl = True)
    
    mc.undoInfo(ock = True)
    for obj in objs:
        if not 'matTransparency' in mc.listAttr(obj):
            mc.addAttr(obj, ln = 'matTransparency', at = 'double', dv = 0, minValue = 0, maxValue = 1, k = 1)
        mat = rmm.rmh_getMaterial(obj)
        if 'outTransparency' in mc.listAttr(mat):
            mc.connectAttr('%s.matTransparency'%obj , '%s.outTransparencyR'%mat, f = 1)
            mc.connectAttr('%s.matTransparency'%obj , '%s.outTransparencyG'%mat, f = 1)
            mc.connectAttr('%s.matTransparency'%obj , '%s.outTransparencyB'%mat, f = 1)
            print ('connected %s to %s'%(obj, mat))

    mc.undoInfo(cck = True)
