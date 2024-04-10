
from __future__ import absolute_import
from __future__ import print_function
import os, subprocess, threading, math, random,shutil
from importlib import reload
import __main__

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


import rmhTools_widgets as pw
import rmhMayaMethods as rmm
import rmhAnimTools as rat
import rmhVaillantTools as vai
import rmhBundeswehrTools as rmhBW
import vai_assignCommonMaterial as acm
import rmhRealtimeTools as rrt
import rmhRobotTools
reload(rmhRobotTools)
reload(pw)
reload(vai)
reload(acm)
reload(rrt)
reload(rmm)
reload(rmhBW)

class VaillantTab(QWidget):
    def __init__(self, parent = None):
        super(VaillantTab, self).__init__(parent)
        
        initContextMenu = [['step 01: Setup Renderer',vai.vai_setupRenderer],['step 02: Import All Materials',vai.vai_importAllMaterials],['step 03: Import All Lights',vai.vai_importAllLights],['step 04: Import Camera',vai.vai_importMiscAssets]]
        
        self.initLayout = pw.createButtonList([['initialize scene\n(right click for individual steps)', vai.vai_initialize, initContextMenu]], label = '01. Initialize', cols = 1)
        
        self.DL_Layout = pw.createButtonList([['Tech Inside', vai.vai_tecInsideDL],['Casing', vai.vai_casingDL],\
                                        ['Logo', vai.vai_logoDL],['Not Needed', vai.vai_notNeededDL]], label = '02. Assign DLs / groups', cols = 1)
        
        self.tools_layout = pw.createButtonList([['assign common material', acm.assignCommonShader_xray],['select non-Redshift materials', vai.vai_selectNonRedshiftMaterials],['selectObjectsWithNoMaterial', vai.vai_selectObjectsWithNoMaterial],\
                                                    ['select similar sized', vai.vai_selectSimilarObjects]], label = '03. Assign Materials / Edit Geometry', cols = 1)
        
        self.renderSetup_layout = pw.createButtonList([['create RLs and passes', vai.vai_createRLPasses]], label = '04. Render Setup', cols = 1)
        
        self.render_layout = pw.createButtonList([['render res.: switchWidthAndHeight', vai.vai_switchWidthAndHeight]], label = '05 Render', cols = 1)
        
        mainLayout = pw.makeBoxLayout([self.initLayout,self.DL_Layout,self.tools_layout,self.renderSetup_layout, self.render_layout, QWidget()], stretchArray = [0,0,0,0,0,1])
        
        self.setLayout(mainLayout)
    
    def testProc(self):
        print(' pass')
    

class RmhTools(MayaQWidgetDockableMixin, QDialog):
    toolName = 'RmhTools'
    def __init__(self, parent = None):
        super(RmhTools, self).__init__(parent)
        
        glbButtons = pw.createButtonList([['Export To GLB (Babylon)...', self.exportToGLB],['Redshift Baking Tools...', self.showRedshiftBakingToolsDialog]], \
                                            label = 'GLB / PBR Workflow', cols = 1, spacing = 2)
        
        
        mashButtons = pw.createButtonList([['Show MASH Outliner...', self.showMashOutliner],['Breakout Locators \n(select MASH Network)', rat.MASH_breakoutAll],\
                                            ['Duplicate and Constraint \n(first select source, then target objs)', rmm.duplicateToParents_constraint],\
                                            ['Bake Keys...', self.showBakeSimulationOptions],['Reconnect Transforms to Constraints', rmm.reconnectTransformToConstraints]], \
                                            label = 'MASH / Breakout / Baking', cols = 1, spacing= 2)
        
        unity_infoLabel = QLabel('best practice for unity export:\n- leave Maya units in meter\n- model in cm (1m = 100 units) \n- export in cm')
        
        #['setupGridForCm', rrt.rmh_setupGridForCm],['adjustCameraSettingsForCm', rrt.rmh_adjustCameraSettingsForCm],\
        optsContext = ['set paths', rrt.rmh_setGameExporterPath], ['set options', rrt.rmh_setGameExporterOptions]
        unityButtons = pw.createButtonList([['Open GameExporter', self.openGameExporter], ['Auto-Set GameExporter Options\n(right click for steps)', self.gameExporter_setAll, optsContext],\
                                            ['addUnityLightControl', rrt.rmh_addUnityLightControl], ['GameExport via light mult', rrt.rmh_doGameExportWithLightMult],['Goto AssetExportFolder', rrt.rmh_gotoAssetExportFolder],\
                                            ['Add Selection to exportSet', rrt.rmh_addToExportSet],['copyToUnityFolder', rrt.rmh_copyToUnityFolder],\
                                            ], \
                                            label = 'Unity Export', cols = 1, spacing= 2)
        
        
        caveButtons = pw.createButtonList([['Cave Simulator', rmhBW.showCavePreviewDialog]], \
                                            label = 'CAVE Tools', cols = 1, spacing= 2)
        
        
        bwFachButtons = pw.createButtonList([['shoot bullets (select straight curves)', rmhBW.BWFpf_shootBullet],['BW_scaleNonVisibleToZero', rmhBW.BW_scaleNonVisibleToZero]], \
                                            label = 'BW Fachpflege', cols = 1, spacing = 2)
        
        bwInfButtons = pw.createButtonList([['BWInf - create text', rmhBW.BWInf_textListToType], ['BWInf - splitObjects', rmhBW.BWInf_splitObjects],\
                                            ['BWInf - createMashFromObjects', rmhBW.BWInf_createMashFromObjects], ['BWInf - makeGyroConnections', rmhBW.BWInf_makeGyroConnections],\
                                            ['BWInf - setRandomValues', rmhBW.BWInf_gyro_setRandomValues],['BWInf - createConnection (NNetz)', rmhBW.BWInf_createConnection],\
                                            ['BWInf - createNeuralConnections (many2many)', rmhBW.BWInf_createNeuralConnections],['BWInf - createLineTransform_perCV', rmhBW.BWInf_createLineTransform_perCV],\
                                            ['BWInf - createSweepMeshes', rmhBW.BWInf_createSweepMeshes]], \
                                            label = 'BW Inf', cols = 1, spacing = 2)
        
        
        nukeButtons = pw.createButtonList([['exportNukeAssets_addToSet', rmm.rmh_exportNukeAssets_addToSet],['exportNukeAssets', rmm.rmh_exportNukeAssets_addToSet], \
                                            ['copyObjectPosToNuke (clipboard)', rmm.rmh_copyObjectPosToNuke]], \
                                            label = 'To Nuke', cols = 1, spacing = 2)
        
        afxButtons = pw.createButtonList([['rmh_exportWorldspaceKeyframesToAFX', rmm.rmh_exportWorldspaceKeyframesToAFX]], \
                                            label = 'To After Effects', cols = 1, spacing = 2)
        
        roentgenLayout = pw.createButtonList([['Bake Keys...', self.showBakeSimulationOptions],['Reconnect Transforms to Constraints', rmm.reconnectTransformToConstraints]], \
                                            label = 'Roentgen', cols = 1, spacing = 2)
        
        roboLayout = pw.createButtonList([['SETUP ALL (one click)', rmhRobotTools.rmhRobo_importAssetsAndSetupRendering], ['import robot', rmhRobotTools.rmhRobo_importRobot],\
                                            ['import environment', rmhRobotTools.rmhRobo_importEnvironment],['setup renderer', rmhRobotTools.rmhRobo_setupRendering],\
                                            ['import faceCap fbx and sound', rmhRobotTools.rmhRobo_importFbxAndSound],['connect faceCap Data', self.robo_connectToFaceCapData],\
                                            ['matchCurveShape', rmhRobotTools.matchCurveShape]], \
                                            label = 'OneMessage Robo', cols = 1, spacing = 2)
        
        summitLayout = pw.createButtonList([['createSweepMeshes', rmm.RMHSummit_createSweepMeshes],['combineMeshes_diff', rmm.rmh_combineMeshes_diff]], \
                                            label = 'Summit 23', cols = 2, spacing = 2)
        
        # exportSetButtons = pw.createButtonList([['create set', rrt.rmh_createExportSet],['add to set', rrt.rmh_addToExportSet]], \
        #                                     label = 'Export Set', cols = 2, spacing= 2)   
        
        realtimeLayout = pw.makeBoxLayout([glbButtons,mashButtons,unity_infoLabel,unityButtons,caveButtons,QWidget()],stretchArray = [0,0,0,0,0,1], alsWidget = True)
        
        # bundeswehrLayout = pw.makeBoxLayout([bwFachButtons,QWidget()],stretchArray = [0,1], alsWidget = True)
        # 
        # bencardLayout = pw.makeBoxLayout([nukeButtons,QWidget()],stretchArray = [0,1], alsWidget = True)
        
        projectsLayout = pw.makeBoxLayout([bwFachButtons,bwInfButtons, nukeButtons,afxButtons, roentgenLayout, roboLayout, summitLayout, QWidget()],stretchArray = [0,0,0,0,0,0,0,1], alsWidget = True)
        
        ############# mainTab
        self.mainTab = QTabWidget()
        
        self.mainTab.addTab(realtimeLayout,'Realtime')
        self.mainTab.addTab(projectsLayout,'Projects')
        
        # self.mainTab.addTab(bundeswehrLayout,'Bundeswehr')
        self.mainTab.addTab(VaillantTab(),'Vaillant')
        # self.mainTab.addTab(bencardLayout,'Bencard')
        
        ###### main
        
        sa = QScrollArea()
        sa.setWidget(self.mainTab)
        sa.setWidgetResizable (True)
        sa.setFrameStyle(QFrame.NoFrame)
        
        self.menu = QMenuBar()
        self.menuSetup()
        
        mainLayout = pw.makeBoxLayout([sa])
        mainLayout.setMenuBar(self.menu)
        
        self.setLayout(mainLayout)
        self.setWindowTitle('RmhTools')
        
        self.setGeometry(0,0, 400, 800)
    
    def menuSetup(self):
        self.generalMenu = self.menu.addMenu("Gnrl")
        gen_move = self.generalMenu.addMenu('test')
        gen_move.addAction(QAction(QIcon(),"hallo Nils", self, shortcut="",statusTip="", triggered=self.testProc))
        gen_move.addAction(QAction(QIcon(),"hallo Michael", self, shortcut="",statusTip="", triggered=self.testProc2))
    
    def exportToGLB(self):
        mel.eval('select -hi;toBabylon')
    
    def robo_connectToFaceCapData(self):
        reload(rmhRobotTools)
        rmhRobotTools.rmhRobo_connectToFaceCapData()
        
    def gameExporter_setAll(self):
        sceneName = mc.file( q = True, sn = True, shn = True).split('.')[0]
        if not sceneName:
            mc.confirmDialog(title='gameExporter_setAll',message='file needs to be saved first',button=['Ok'])
            return
        rrt.rmh_setGameExporterPath()
        rrt.rmh_setGameExporterOptions()
        
    def openGameExporter(self):
        currentUnit = mc.currentUnit(q = True, linear = True)
        if currentUnit != 'm' and not mc.optionVar( exists='openGameExporter_dontShowUnitWarning' ):
            res = mc.confirmDialog(title='openGameExporter',message='current unit is not m, you will have to set the asset scale in Unity',button=['Ok', 'Don\'t show again'])
            if res != 'Ok':
                mc.optionVar( iv=('openGameExporter_dontShowUnitWarning', 1))
        
        mel.eval('gameFbxExporter')
        
    def showBakeSimulationOptions(self):
        mel.eval('BakeSimulationOptions')
    def showMashOutliner(self):
        mel.eval('MASHOutliner;')
        
    def testProc(self):
        mc.confirmDialog(title='aha!',message='hallo Nils!',button= ['Ok...', 'Cancel'], defaultButton='OK...',cancelButton='Cancel', dismissString='Cancel')
        
    def testProc2(self):
        mc.confirmDialog(title='aha!',message='hallo Michael!',button= ['Ok...', 'Cancel'], defaultButton='OK...',cancelButton='Cancel', dismissString='Cancel')

    def createButtonList(self, butLabelsAndProcs = [[],[]], spacing = 0, margin = 0, label = 'Morph', cols = None):
        if not cols:
            buts = []
            for butLabel,proc in butLabelsAndProcs:
                but = pw.makeButton(butLabel,proc)
                buts.append(but)
                
            butLayout = pw.makeBoxLayout([QLabel(label)] + buts, spacing = spacing, margin = margin)
        else:
            gridLayout = QGridLayout()
            gridLayout.setMargin(0)
            gridLayout.setSpacing(spacing)
            
            count = 0
            for butLabel,proc in butLabelsAndProcs:
                row, col = int(count / float(cols)), count%cols
                # print row,col
                but = pw.makeButton(butLabel,proc)
                # buts.append(but)
                gridLayout.addWidget(but, row, col)
                count+=1
            butLayout = pw.makeBoxLayout([QLabel(label), gridLayout], spacing = spacing, margin = margin)
            
        return butLayout
    
    def showRedshiftBakingToolsDialog(self):
        import rmhRedshiftBakingTools as rs_bt
        reload(rs_bt)
        rs_bt.RS_showBakingToolsDialog()
 


def showRmhToolsDialog():
    def getMainWindow():
        global app
        app = QApplication.instance()
        
        ptr = apiUI.MQtUtil.mainWindow()
        win = wrapInstance(int(ptr), QWidget)
        
        return win
    mayaWin = getMainWindow()
    if mc.lsUI(type = 'dockControl') and hasattr(__main__, 'RmhTools') and __main__.RmhToolsUI in mc.lsUI(type = 'dockControl'):
        mc.deleteUI(__main__.RmhToolsUI)
    if hasattr(__main__, 'RmhToolsDialog'):
        try:
            __main__.RmhToolsDialog.close()
        except Exception:
            pass
        
    __main__.RmhToolsDialog = RmhTools(mayaWin)
    
    if (mc.dockControl('RmhTools', q=1, ex=1)):
        mc.deleteUI('RmhTools')
    __main__.RmhToolsDialog.show(dockable = True, area='left',  width=400, floating=False)
    __main__.RmhToolsUI = __main__.RmhToolsDialog
    