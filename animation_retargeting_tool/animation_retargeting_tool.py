'''
Name: animation_retargeting_tool

Description: Transfer animation data between rigs or transfer raw mocap from a skeleton to a custom rig.
 
Author: Joar Engberg 2021

Installation:
Add animation_retargeting_tool.py to your Maya scripts folder (Username\Documents\maya\scripts).
To start the tool within Maya, run these this lines of code from the Maya script editor or add them to a shelf button:

import animation_retargeting_tool
animation_retargeting_tool.start()
 
'''
import sys
from unittest import skip
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om2
from shiboken2 import wrapInstance
from PySide2 import QtCore, QtGui, QtWidgets
import os
import maya.mel


def maya_main_window():
    # Return the Maya main window as QMainWindow
    main_window = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window), QtWidgets.QWidget) # type: ignore


class RetargetingTool(QtWidgets.QDialog):
    '''
    The RetargetWindow_UI is the main UI window.
    When a new ListItem_UI is created it gets added to the RetargetWindow_UI
    ''' 
    WINDOW_TITLE = "Animation Retargeting Tool"
 
    def __init__(self):
        super(RetargetingTool, self).__init__(maya_main_window())
        
        self.connection_list = []
        self.counter = 0
        self.maya_color_list = [13, 18, 14, 17]
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(400, 300)
        self.create_ui_widgets()
        self.create_ui_layout()
        self.create_ui_connections()

        if cmds.about(macOS=True):
            self.setWindowFlags(QtCore.Qt.Tool)
 
    def create_ui_widgets(self):
        self.refresh_button = QtWidgets.QPushButton(QtGui.QIcon(":refresh.png"), "")
        self.simple_conn_button = QtWidgets.QPushButton("Create Connection")
        self.ik_conn_button = QtWidgets.QPushButton("Create IK Connection")
        self.bake_button = QtWidgets.QPushButton("Bake Animation")
        self.bake_button.setStyleSheet("background-color: lightgreen; color: black")
        self.batch_bake_button = QtWidgets.QPushButton("Batch Bake And Export ...")

        self.help_button = QtWidgets.QPushButton("?")
        self.help_button.setFixedWidth(25)
 
        self.rot_checkbox = QtWidgets.QCheckBox("Rotation")
        self.pos_checkbox = QtWidgets.QCheckBox("Translation")
        self.mo_checkbox = QtWidgets.QCheckBox("Maintain Offset")
        self.snap_checkbox = QtWidgets.QCheckBox("Align To Position")
 
    def create_ui_layout(self):
        horizontal_layout_1 = QtWidgets.QHBoxLayout()
        horizontal_layout_1.addWidget(self.pos_checkbox)
        horizontal_layout_1.addWidget(self.rot_checkbox)
        horizontal_layout_1.addWidget(self.snap_checkbox)
        horizontal_layout_1.addStretch()
        horizontal_layout_1.addWidget(self.help_button)
        horizontal_layout_2 = QtWidgets.QHBoxLayout()
        horizontal_layout_2.addWidget(self.simple_conn_button)
        horizontal_layout_2.addWidget(self.ik_conn_button)

        horizontal_layout_3 = QtWidgets.QHBoxLayout()
        horizontal_layout_3.addWidget(self.batch_bake_button)
        horizontal_layout_3.addWidget(self.bake_button)
 
        connection_list_widget = QtWidgets.QWidget()
 
        self.connection_layout = QtWidgets.QVBoxLayout(connection_list_widget)
        self.connection_layout.setContentsMargins(2, 2, 2, 2)
        self.connection_layout.setSpacing(3)
        self.connection_layout.setAlignment(QtCore.Qt.AlignTop)
 
        list_scroll_area = QtWidgets.QScrollArea()
        list_scroll_area.setWidgetResizable(True)
        list_scroll_area.setWidget(connection_list_widget)

        separator_line = QtWidgets.QFrame(parent=None)
        separator_line.setFrameShape(QtWidgets.QFrame.HLine)
        separator_line.setFrameShadow(QtWidgets.QFrame.Sunken)
 
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(list_scroll_area)
        main_layout.addLayout(horizontal_layout_1)
        main_layout.addLayout(horizontal_layout_2)
        main_layout.addWidget(separator_line)
        main_layout.addLayout(horizontal_layout_3)
 
    def create_ui_connections(self):
        self.simple_conn_button.clicked.connect(self.create_connection_node)
        self.ik_conn_button.clicked.connect(self.create_ik_connection_node)
        self.refresh_button.clicked.connect(self.refresh_ui_list)
        self.bake_button.clicked.connect(self.bake_animation_confirm)
        self.batch_bake_button.clicked.connect(self.open_batch_window)
        self.help_button.clicked.connect(self.help_dialog)

        self.rot_checkbox.setChecked(True)
        self.pos_checkbox.setChecked(True)
        self.snap_checkbox.setChecked(True)
 
    @classmethod
    def get_connect_nodes(self):
        connect_nodes_in_scene = []
        for i in cmds.ls():
            if cmds.attributeQuery("ConnectNode", node=i, exists=True) == True:
                connect_nodes_in_scene.append(i)
            else:
                pass
        return connect_nodes_in_scene

    @classmethod
    def get_connected_ctrls(self):
        connected_ctrls_in_scene = []
        for i in cmds.ls():
            if cmds.attributeQuery("ConnectedCtrl", node=i, exists=True) == True:
                connected_ctrls_in_scene.append(i)
            else:
                pass
        return connected_ctrls_in_scene
 
    def refresh_ui_list(self):
        self.clear_list()
 
        connect_nodes_in_scene = self.get_connect_nodes()
        for conn in connect_nodes_in_scene:
            connection_ui_item = ListItem_UI(conn)
 
            self.connection_layout.addWidget(connection_ui_item)
            self.connection_list.append(connection_ui_item)
 
    def clear_list(self):
        self.connection_list = []
 
        while self.connection_layout.count() > 0:
            connection_ui_item = self.connection_layout.takeAt(0)
            if connection_ui_item.widget():
                connection_ui_item.widget().deleteLater() 
 
    def get_snap_checkbox(self):
        if self.snap_checkbox.isChecked() == True:
            return True
        else:
            return False

    def get_mo_checkbox(self):
        if self.mo_checkbox.isChecked() == True:
            return True
        else:
            return False
 
    def get_rot_checkbox(self):
        if self.rot_checkbox.isChecked() == True:
            return True
        else:
            return False
    
    def get_pos_checkbox(self):
        if self.pos_checkbox.isChecked() == True:
            return True
        else:
            return False
 
    def showEvent(self, event):
        self.refresh_ui_list()
 
    def closeEvent(self, event):
        self.clear_list()

    def create_connection_node(self):
        try:
            selected_joint = cmds.ls(selection=True)[0]
            selected_ctrl = cmds.ls(selection=True)[1]
        except:
            return cmds.warning("No selections!")

        if retarget_tool_ui.get_snap_checkbox() == True:
            cmds.matchTransform(selected_ctrl, selected_joint, pos=True)
        else:
            pass
        
        if retarget_tool_ui.get_rot_checkbox() == True and retarget_tool_ui.get_pos_checkbox() == False:
            suffix = "_ROT"
    
        elif retarget_tool_ui.get_pos_checkbox() == True and retarget_tool_ui.get_rot_checkbox() == False:
            suffix = "_TRAN"
        
        else:
            suffix = "_TRAN_ROT"

        locator = self.create_ctrl_sphere(selected_joint+suffix)
        
        # Add message attr
        cmds.addAttr(locator, longName="ConnectNode", attributeType="message")
        cmds.addAttr(selected_ctrl, longName="ConnectedCtrl", attributeType="message")
        cmds.connectAttr(locator+".ConnectNode",selected_ctrl+".ConnectedCtrl")

        cmds.parent(locator, selected_joint)
        cmds.xform(locator, rotation=(0, 0, 0))
        cmds.xform(locator, translation=(0, 0, 0))
 
        # Select the type of constraint based on the ui checkboxes
        if retarget_tool_ui.get_rot_checkbox() == True and retarget_tool_ui.get_pos_checkbox() == True:
            cmds.parentConstraint(locator, selected_ctrl, maintainOffset=True)
    
        elif retarget_tool_ui.get_rot_checkbox() == True and retarget_tool_ui.get_pos_checkbox() == False:
            cmds.orientConstraint(locator, selected_ctrl, maintainOffset=True)
    
        elif retarget_tool_ui.get_pos_checkbox() == True and retarget_tool_ui.get_rot_checkbox() == False:
            cmds.pointConstraint(locator, selected_ctrl, maintainOffset=True)
        else:
            cmds.warning("Select translation and/or rotation!")
            cmds.delete(locator)
            cmds.deleteAttr(selected_ctrl, at="ConnectedCtrl")

        self.refresh_ui_list()
 
    def create_ik_connection_node(self):
        try:
            selected_joint = cmds.ls(selection=True)[0]
            selected_ctrl = cmds.ls(selection=True)[1]
        except:
            return cmds.warning("No selections!")

        self.rot_checkbox.setChecked(True)
        self.pos_checkbox.setChecked(True)

        if retarget_tool_ui.get_snap_checkbox() == True:
            cmds.matchTransform(selected_ctrl, selected_joint, pos=True)
        else:
            pass
        
        tran_locator = self.create_ctrl_sphere(selected_joint+"_TRAN")

        cmds.parent(tran_locator, selected_joint)
        cmds.xform(tran_locator, rotation=(0, 0, 0))
        cmds.xform(tran_locator, translation=(0, 0, 0))

        rot_locator = self.create_ctrl_locator(selected_joint+"_ROT")

        # Add message attributes and connect them
        cmds.addAttr(tran_locator, longName="ConnectNode", attributeType="message")
        cmds.addAttr(rot_locator, longName="ConnectNode", attributeType="message")
        cmds.addAttr(selected_ctrl, longName="ConnectedCtrl", attributeType="message")
        cmds.connectAttr(tran_locator+".ConnectNode",selected_ctrl+".ConnectedCtrl")

        cmds.parent(rot_locator, tran_locator)
        cmds.xform(rot_locator, rotation=(0, 0, 0))
        cmds.xform(rot_locator, translation=(0, 0, 0))
    
        jointParent = cmds.listRelatives(selected_joint, parent=True)[0]
        cmds.parent(tran_locator, jointParent)
        cmds.makeIdentity(tran_locator, apply=True, translate=True)
    
        cmds.orientConstraint(selected_joint, tran_locator, maintainOffset=False)
        cmds.parentConstraint(rot_locator, selected_ctrl, maintainOffset=True)

        # Lock and hide attributes
        cmds.setAttr(rot_locator+".tx", lock=True, keyable=False)
        cmds.setAttr(rot_locator+".ty", lock=True, keyable=False)
        cmds.setAttr(rot_locator+".tz", lock=True, keyable=False)
        cmds.setAttr(tran_locator+".rx", lock=True, keyable=False)
        cmds.setAttr(tran_locator+".ry", lock=True, keyable=False)
        cmds.setAttr(tran_locator+".rz", lock=True, keyable=False)

        self.refresh_ui_list()

    def scale_ctrl_shape(self, controller, size):
        cmds.select(self.get_cvs(controller), replace=True)
        cmds.scale(size, size, size) 
        cmds.select(clear=True)

    def get_cvs(self, object):
        children = cmds.listRelatives(object, type="shape", children=True)
        ctrl_vertices = []
        for c in children:
            spans = int(cmds.getAttr(c+".spans")) + 1
            vertices = "{shape}.cv[0:{count}]".format(shape=c, count=spans)
            ctrl_vertices.append(vertices)
        return ctrl_vertices

    def create_ctrl_locator(self, ctrl_shape_name):
        curves = []
        curves.append(cmds.curve(degree=1, p=[(0, 0, 1), (0, 0, -1)], k=[0,1]))
        curves.append(cmds.curve(degree=1, p=[(1, 0, 0), (-1, 0, 0)], k=[0,1]))
        curves.append(cmds.curve(degree=1, p=[(0, 1, 0), (0, -1, 0)], k=[0,1]))

        locator = self.combine_shapes(curves, ctrl_shape_name)
        cmds.setAttr(locator+".overrideEnabled", 1)
        cmds.setAttr(locator+".overrideColor", self.maya_color_list[self.counter])
        return locator

    def create_ctrl_sphere(self, ctrl_shape_name):
        circles = []
        for n in range(0, 5):
            circles.append(cmds.circle(normal=(0,0,0), center=(0,0,0))[0])

        cmds.rotate(0, 45, 0, circles[0])
        cmds.rotate(0, -45, 0, circles[1])
        cmds.rotate(0, -90, 0, circles[2])
        cmds.rotate(90, 0, 0, circles[3])
        sphere = self.combine_shapes(circles, ctrl_shape_name)
        cmds.setAttr(sphere+".overrideEnabled", 1)
        cmds.setAttr(sphere+".overrideColor", self.maya_color_list[self.counter])
        self.scale_ctrl_shape(sphere, 0.5)
        return sphere

    def combine_shapes(self, shapes, ctrl_shape_name):
        shape_nodes = cmds.listRelatives(shapes, shapes=True)
        output_node = cmds.group(empty=True, name=ctrl_shape_name)
        cmds.makeIdentity(shapes, apply=True, translate=True, rotate=True, scale=True)
        cmds.parent(shape_nodes, output_node, shape=True, relative=True)
        cmds.delete(shape_nodes, constructionHistory=True)
        cmds.delete(shapes)
        return output_node

    def bake_animation_confirm(self):
        confirm = cmds.confirmDialog(title="Confirm", message="Baking the animation will delete all the connection nodes. Do you wish to proceed?", button=["Yes","No"], defaultButton="Yes", cancelButton="No")
        if confirm == "Yes":
            self.bake_animation()
        if confirm == "No":
            pass
        self.refresh_ui_list()

    @classmethod
    def bake_animation(self):

        if len(self.get_connected_ctrls()) == 0:
            cmds.warning("No connections found in scene!")
        if len(self.get_connected_ctrls()) != 0:
            time_min = cmds.playbackOptions(query=True, min=True)
            time_max = cmds.playbackOptions(query=True, max=True)

            # Bake the animation
            cmds.refresh(suspend=True)
            cmds.bakeResults(self.get_connected_ctrls(), t=(time_min, time_max), sb=1, at=["rx","ry","rz","tx","ty","tz"], hi="none")
            cmds.refresh(suspend=False)

            # Delete the connect nodes
            for node in self.get_connect_nodes():
                try:
                    cmds.delete(node)
                except:
                    pass
            
            # Remove the message attribute from the controllers
            for ctrl in self.get_connected_ctrls():
                try:
                    cmds.deleteAttr(ctrl, attribute="ConnectedCtrl")
                except:
                    pass

    def help_dialog(self):
        dialog = cmds.confirmDialog(title="Instructions", message="To create a connection simply select the driver and then the driven and click 'Create connection'. For IK hands and IK feet controllers you can use 'Create IK Connection' for more complex retargeting. \n \nAs an example: if you want to transfer animation from a skeleton to a rig, first select the animated joint and then select the controller before you create a connection.", button=["Ok"], defaultButton="Ok", cancelButton="Ok")
        return dialog

    def open_batch_window(self):
        try:
            self.settings_window.close()
            self.settings_window.deleteLater()
        except:
            pass
        self.settings_window = BatchExport()
        self.settings_window.show()


class ListItem_UI(QtWidgets.QWidget):
    '''
    UI item.
    When a new List Item is created it gets added to the RetargetWindow_UI
    '''
    def __init__(self, shape_name, parent=None):
        super(ListItem_UI, self).__init__(parent)
        self.shape_name = shape_name
 
        self.setFixedHeight(26)
        self.create_ui_widgets()
        self.create_ui_layout()
        self.create_ui_connections()
 
    def create_ui_widgets(self):
        self.color_button = QtWidgets.QPushButton()
        self.color_button.setFixedSize(20, 20)
        self.color_button.setStyleSheet("background-color:" + self.get_color())
 
        self.sel_button = QtWidgets.QPushButton()
        self.sel_button.setStyleSheet("background-color: #707070")
        self.sel_button.setText("Select")
 
        self.del_button = QtWidgets.QPushButton()
        self.del_button.setStyleSheet("background-color: #707070")
        self.del_button.setText("Delete")
 
        self.transform_name_label = QtWidgets.QLabel(self.shape_name)
        self.transform_name_label.setFixedWidth(280)
        self.transform_name_label.setAlignment(QtCore.Qt.AlignCenter)
 
    def create_ui_layout(self):
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 0, 0)
        main_layout.addWidget(self.color_button)
        main_layout.addWidget(self.transform_name_label)
        main_layout.addWidget(self.sel_button)
        main_layout.addWidget(self.del_button)
        main_layout.addStretch()
 
    def create_ui_connections(self):
        self.sel_button.clicked.connect(self.select_connection_node)
        self.del_button.clicked.connect(self.delete_connection_node)
        self.color_button.clicked.connect(self.set_color)
 
    def select_connection_node(self):
        cmds.select(self.shape_name)  

    def delete_connection_node(self):
        try:
            for attr in cmds.listConnections(self.shape_name, destination=True):
                if cmds.attributeQuery("ConnectedCtrl", node=attr, exists=True):
                    cmds.deleteAttr(attr, at="ConnectedCtrl")
        except:
            pass

        cmds.delete(self.shape_name)
        retarget_tool_ui.refresh_ui_list()
 
    def set_color(self):
        # Get the connection nodes, their ui element and the Maya override color list
        connection_node = retarget_tool_ui.get_connect_nodes()
        color = retarget_tool_ui.maya_color_list
        ui_items = retarget_tool_ui.connection_list

        if retarget_tool_ui.counter < 3:
            retarget_tool_ui.counter += 1
        else:
            retarget_tool_ui.counter = 0

        # Set the color on the connection node shape and button
        for con in connection_node:
            cmds.setAttr(con+".overrideEnabled", 1)
            cmds.setAttr(con+".overrideColor", color[retarget_tool_ui.counter])

        for i in ui_items:
            i.color_button.setStyleSheet("background-color:"+self.get_color())
 
    def get_color(self):
        # Set the color of the button based on the color of the connection shape
        ctrl = self.shape_name
        current_color = cmds.getAttr(ctrl+".overrideColor")
        colors_dict = {"13":"red", "18":"cyan", "14":"green", "17":"yellow"}
        color = colors_dict.get(str(current_color), "grey")
        return color

class BatchExport(QtWidgets.QDialog):

    WINDOW_TITLE = "Batch Exporter"

    def __init__(self):
        super(BatchExport, self).__init__(maya_main_window())
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(400, 300)
        self.animation_clip_paths = []
        self.output_folder = ""
        
        if cmds.about(macOS=True):
            self.setWindowFlags(QtCore.Qt.Tool)

        self.create_ui()
        self.create_connections()

    def create_ui(self):
        self.file_list_widget = QtWidgets.QListWidget()
        self.delete_selected_button = QtWidgets.QPushButton("Remove Selected")
        self.delete_selected_button.setFixedHeight(24)
        self.load_anim_button = QtWidgets.QPushButton("Load Animations")
        self.load_anim_button.setFixedHeight(24)
        self.export_button = QtWidgets.QPushButton("Batch Export Animations")
        self.export_button.setStyleSheet("background-color: lightgreen; color: black")
        self.connection_file_line = QtWidgets.QLineEdit()
        self.connection_filepath_button = QtWidgets.QPushButton()
        self.connection_filepath_button.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.connection_filepath_button.setFixedSize(24, 24)

        output_filepath_button = QtWidgets.QPushButton()
        output_filepath_button.setIcon(QtGui.QIcon(":fileOpen.png"))

        self.file_type_combo = QtWidgets.QComboBox()
        self.file_type_combo.addItems([".ma", ".fbx"])

        horizontal_layout_1 = QtWidgets.QHBoxLayout()
        horizontal_layout_1.addWidget(QtWidgets.QLabel("Connection Rig File:"))
        horizontal_layout_1.addWidget(self.connection_file_line)
        horizontal_layout_1.addWidget(self.connection_filepath_button)

        horizontal_layout_2 = QtWidgets.QHBoxLayout()
        horizontal_layout_2.addWidget(self.load_anim_button)
        horizontal_layout_2.addWidget(self.delete_selected_button)

        horizontal_layout_3 = QtWidgets.QHBoxLayout()
        horizontal_layout_3.addWidget(QtWidgets.QLabel("Output File Type:"))
        horizontal_layout_3.addWidget(self.file_type_combo)
        horizontal_layout_3.addWidget(self.export_button)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.file_list_widget)
        main_layout.addLayout(horizontal_layout_2)
        main_layout.addLayout(horizontal_layout_1)
        main_layout.addLayout(horizontal_layout_3)


    def create_connections(self):
        self.connection_filepath_button.clicked.connect(self.connection_filepath_dialog)
        self.load_anim_button.clicked.connect(self.animation_filepath_dialog)
        self.export_button.clicked.connect(self.batch_action)

    def connection_filepath_dialog(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Select Connection Rig File", "", "Maya ACSII (*.ma);;All files (*.*)")
        if file_path[0]:
            self.connection_file_line.setText(file_path[0])

    def output_filepath_dialog(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select export folder path", "")
        if folder_path:
            self.output_folder = folder_path

    def animation_filepath_dialog(self):
        file_paths = QtWidgets.QFileDialog.getOpenFileNames(self, "Select Animation Clips", "", "Maya ACSII (*.ma);;FBX (*.fbx);;All files (*.*)")
        file_path_list = file_paths[0]
        self.animation_clip_paths = []
        if file_path_list[0]:
            for i in file_path_list:
                self.file_list_widget.addItem(i)
                self.animation_clip_paths.append(i)

            # self.file_list_widget.item(0).setTextColor(QtGui.QColor("red"))

    def batch_action(self):
        self.output_filepath_dialog()
        self.bake_export()

    def bake_export(self):
        # connection_file = self.connection_file_line.text()
        # animation_clip_paths = self.animation_clip_paths
        # anim_files = [f for f in os.listdir(anim_path) if os.path.isfile(os.path.join(anim_path, f)) and str(os.path.join(anim_path, f)).endswith(".fbx")]
        # output_folder = ""

        for i, path in enumerate(self.animation_clip_paths):
            # Import connection file and animation clip
            cmds.file(new=True, force=True) 
            cmds.file(self.connection_file_line.text(), open=True)
            maya.mel.eval('FBXImportMode -v "exmerge";')
            maya.mel.eval('FBXImport -file "{}";'.format(path))
            
            # Bake animation
            RetargetingTool.bake_animation()
            
            # Export animation
            # cmds.select("human:rig", replace=True)
            
            output_path = self.output_folder + "/" + os.path.basename(path)
            if self.file_type_combo.currentText == ".fbx":
                # pm.mel.eval('FBXLoadExportPresetFile -f "' + mt_common_utils.sanitize(self.fbx_export_preset_file) + '"')
                maya.mel.eval('FBXExport -f "{}" -s'.format(output_path))
            if self.file_type_combo.currentText == ".ma":
                pass

            if os.path.exists(output_path):
                self.file_list_widget.item(i).setTextColor(QtGui.QColor("green"))
            else:
                self.file_list_widget.item(i).setTextColor(QtGui.QColor("red"))


def start():
    global retarget_tool_ui
    try:
        retarget_tool_ui.close()
        retarget_tool_ui.deleteLater()
    except:
        pass
    retarget_tool_ui = RetargetingTool()
    retarget_tool_ui.show()

if __name__ == "__main__":
    start()