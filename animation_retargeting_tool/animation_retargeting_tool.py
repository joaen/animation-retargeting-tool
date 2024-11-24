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
from collections import OrderedDict
import os
import sys
import webbrowser
import maya.mel
import maya.cmds as cmds
from functools import partial
import maya.OpenMayaUI as omui

maya_version = int(cmds.about(version=True))

if maya_version < 2025:
    from shiboken2 import wrapInstance
    from PySide2 import QtCore, QtGui, QtWidgets
else:
    from shiboken6 import wrapInstance
    from PySide6 import QtCore, QtGui, QtWidgets


def maya_main_window():
    # Return the Maya main window as QMainWindow
    main_window = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window), QtWidgets.QWidget) # type: ignore


class RetargetingTool(QtWidgets.QDialog):
    '''
    Retargeting tool class
    ''' 
    WINDOW_TITLE = "Animation Retargeting Tool"
 
    def __init__(self):
        super(RetargetingTool, self).__init__(maya_main_window())
        
        self.script_job_ids = []
        self.connection_ui_widgets = []
        self.color_counter = 0
        self.maya_color_index = OrderedDict([(13, "red"), (18, "cyan"), (14, "lime"), (17, "yellow")])
        self.cached_connect_nodes = []
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(400, 300)
        self.create_ui_widgets()
        self.create_ui_layout()
        self.create_ui_connections()
        self.create_script_jobs()

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

    def create_script_jobs(self):
        self.script_job_ids.append(cmds.scriptJob(event=["SelectionChanged", partial(self.refresh_ui_list)]))
        self.script_job_ids.append(cmds.scriptJob(event=["NameChanged", partial(self.refresh_ui_list)]))

    def kill_script_jobs(self):
        for id in self.script_job_ids:
            if cmds.scriptJob(exists=id):
                cmds.scriptJob(kill=id)
            else:
                pass
 
    def refresh_ui_list(self):
        self.clear_list()
 
        connect_nodes_in_scene = RetargetingTool.get_connect_nodes()
        self.cached_connect_nodes = connect_nodes_in_scene
        for node in connect_nodes_in_scene:
            connection_ui_item = ListItemWidget(parent_instance=self, connection_node=node)
            self.connection_layout.addWidget(connection_ui_item)
            self.connection_ui_widgets.append(connection_ui_item)
 
    def clear_list(self):
        self.connection_ui_widgets = []
 
        while self.connection_layout.count() > 0:
            connection_ui_item = self.connection_layout.takeAt(0)
            if connection_ui_item.widget():
                connection_ui_item.widget().deleteLater() 
 
    def showEvent(self, event):
        self.refresh_ui_list()
 
    def closeEvent(self, event):
        self.kill_script_jobs()
        self.clear_list()

    def create_connection_node(self):
        try:
            selected_joint = cmds.ls(selection=True)[0]
            selected_ctrl = cmds.ls(selection=True)[1]
        except:
            return cmds.warning("No selections!")

        if self.snap_checkbox.isChecked() == True:
            cmds.matchTransform(selected_ctrl, selected_joint, pos=True)
        else:
            pass
        
        if self.rot_checkbox.isChecked() == True and self.pos_checkbox.isChecked() == False:
            suffix = "_ROT"
    
        elif self.pos_checkbox.isChecked() == True and self.rot_checkbox.isChecked() == False:
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
        if self.rot_checkbox.isChecked() == True and self.pos_checkbox.isChecked() == True:
            cmds.parentConstraint(locator, selected_ctrl, maintainOffset=True)
    
        elif self.rot_checkbox.isChecked() == True and self.pos_checkbox.isChecked() == False:
            cmds.orientConstraint(locator, selected_ctrl, maintainOffset=True)
    
        elif self.pos_checkbox.isChecked() == True and self.rot_checkbox.isChecked() == False:
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

        if self.snap_checkbox.isChecked() == True:
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
    
        joint_parent = cmds.listRelatives(selected_joint, parent=True)[0]
        cmds.parent(tran_locator, joint_parent)
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
        cmds.setAttr(locator+".overrideColor", list(self.maya_color_index.keys())[self.color_counter])
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
        cmds.setAttr(sphere+".overrideColor", list(self.maya_color_index.keys())[self.color_counter])
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
            progress_dialog = QtWidgets.QProgressDialog("Baking animation", None, 0, -1, self)
            progress_dialog.setWindowFlags(progress_dialog.windowFlags() ^ QtCore.Qt.WindowCloseButtonHint)
            progress_dialog.setWindowFlags(progress_dialog.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
            progress_dialog.setWindowTitle("Progress...")
            progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
            progress_dialog.show()
            QtCore.QCoreApplication.processEvents()
            # Bake animation
            self.bake_animation()
            progress_dialog.close()
        if confirm == "No":
            pass
        self.refresh_ui_list()

    def help_dialog(self):        
        confirm = cmds.confirmDialog(
                        title="How to use",
                        message="To create a connection simply select the driver and then the driven and click 'Create connection'. For IK hands and IK feet controllers you can use 'Create IK Connection' for more complex retargeting. \n \nAs an example: if you want to transfer animation from a skeleton to a rig, first select the animated joint and then select the controller before you create a connection.",
                        button=["How to use the retargeting tool (Youtube)", "How to use the batch exporter (Youtube)", "Cancel"],
                        defaultButton="Cancel",
                        cancelButton="Cancel",
                        dismissString="Cancel")

        if confirm == "How to use the retargeting tool (Youtube)":  
            webbrowser.open_new("https://youtu.be/x2-agPVfinc")
        elif confirm == "How to use the batch exporter (Youtube)":
            webbrowser.open_new("https://youtu.be/KOURUtN36ko")

    def open_batch_window(self):
        try:
            self.settings_window.close()
            self.settings_window.deleteLater()
        except:
            pass
        self.settings_window = BatchExport()
        self.settings_window.show()

    @classmethod
    def bake_animation(cls):
        if len(cls.get_connected_ctrls()) == 0:
            cmds.warning("No connections found in scene!")
        if len(cls.get_connected_ctrls()) != 0:
            time_min = cmds.playbackOptions(query=True, min=True)
            time_max = cmds.playbackOptions(query=True, max=True)

            # Bake the animation
            cmds.refresh(suspend=True)
            cmds.bakeResults(cls.get_connected_ctrls(), t=(time_min, time_max), sb=1, at=["rx","ry","rz","tx","ty","tz"], hi="none")
            cmds.refresh(suspend=False)

            # Delete the connect nodes
            for node in cls.get_connect_nodes():
                try:
                    cmds.delete(node)
                except:
                    pass
            
            # Remove the message attribute from the controllers
            for ctrl in cls.get_connected_ctrls():
                try:
                    cmds.deleteAttr(ctrl, attribute="ConnectedCtrl")
                except:
                    pass

    @classmethod
    def get_connect_nodes(cls):
        connect_nodes_in_scene = []
        for i in cmds.ls():
            if cmds.attributeQuery("ConnectNode", node=i, exists=True) == True:
                connect_nodes_in_scene.append(i)
            else:
                pass
        return connect_nodes_in_scene

    @classmethod
    def get_connected_ctrls(cls):
        connected_ctrls_in_scene = []
        for i in cmds.ls():
            if cmds.attributeQuery("ConnectedCtrl", node=i, exists=True) == True:
                connected_ctrls_in_scene.append(i)
            else:
                pass
        return connected_ctrls_in_scene


class ListItemWidget(QtWidgets.QWidget):
    '''
    UI list item class.
    When a new List Item is created it gets added to the connection_list_widget in the RetargetingTool class.
    '''
    def __init__(self, connection_node, parent_instance):
        super(ListItemWidget, self).__init__()
        self.connection_node = connection_node
        self.main = parent_instance
 
        self.setFixedHeight(26)
        self.create_ui_widgets()
        self.create_ui_layout()
        self.create_ui_connections()

        # If there is already connection nodes in the scene update the color counter
        try:
            current_override = cmds.getAttr(self.connection_node+".overrideColor")
            self.main.color_counter = self.main.maya_color_index.keys().index(current_override)
        except:
            pass
 
    def create_ui_widgets(self):
        self.color_button = QtWidgets.QPushButton()
        self.color_button.setFixedSize(20, 20)
        self.color_button.setStyleSheet("background-color:" + self.get_current_color())
 
        self.sel_button = QtWidgets.QPushButton()
        self.sel_button.setStyleSheet("background-color: #707070")
        self.sel_button.setText("Select")
        self.sel_button.setFixedWidth(80)
 
        self.del_button = QtWidgets.QPushButton()
        self.del_button.setStyleSheet("background-color: #707070")
        self.del_button.setText("Delete")
        self.del_button.setFixedWidth(80)

        self.transform_name_label = QtWidgets.QLabel(self.connection_node)
        self.transform_name_label.setAlignment(QtCore.Qt.AlignCenter)

        self.transform_name_label.setStyleSheet("color: darkgray")
        for selected in cmds.ls(selection=True):
            if selected == self.connection_node:
                self.transform_name_label.setStyleSheet("color: white")
 
    def create_ui_layout(self):
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 20, 0)
        main_layout.addWidget(self.color_button)
        main_layout.addWidget(self.transform_name_label)
        main_layout.addWidget(self.sel_button)
        main_layout.addWidget(self.del_button)
 
    def create_ui_connections(self):
        self.sel_button.clicked.connect(self.select_connection_node)
        self.del_button.clicked.connect(self.delete_connection_node)
        self.color_button.clicked.connect(self.set_color)
 
    def select_connection_node(self):
        cmds.select(self.connection_node) 
        for widget in self.main.connection_ui_widgets:
            widget.transform_name_label.setStyleSheet("color: darkgray")
        self.transform_name_label.setStyleSheet("color: white")

    def delete_connection_node(self):
        try:
            for attr in cmds.listConnections(self.connection_node, destination=True):
                if cmds.attributeQuery("ConnectedCtrl", node=attr, exists=True):
                    cmds.deleteAttr(attr, at="ConnectedCtrl")
        except:
            pass

        cmds.delete(self.connection_node)
        self.main.refresh_ui_list()
 
    def set_color(self):
        # Set the color on the connection node and button
        connection_nodes = self.main.cached_connect_nodes
        color = list(self.main.maya_color_index.keys())

        if self.main.color_counter < 3:
            self.main.color_counter += 1
        else:
            self.main.color_counter = 0

        for node in connection_nodes:
            cmds.setAttr(node+".overrideEnabled", 1)
            cmds.setAttr(node+".overrideColor", color[self.main.color_counter])

        for widget in self.main.connection_ui_widgets:
            widget.color_button.setStyleSheet("background-color:"+self.get_current_color())
 
    def get_current_color(self):
        current_color_index = cmds.getAttr(self.connection_node+".overrideColor")
        color_name = self.main.maya_color_index.get(current_color_index, "grey")
        return color_name

class BatchExport(QtWidgets.QDialog):
    '''
    Batch exporter class
    ''' 
    WINDOW_TITLE = "Batch Exporter"

    def __init__(self):
        super(BatchExport, self).__init__(maya_main_window())
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(400, 250)
        self.animation_clip_paths = []
        self.output_folder = ""
        
        if cmds.about(macOS=True):
            self.setWindowFlags(QtCore.Qt.Tool)

        self.create_ui()
        self.create_connections()

    def create_ui(self):
        self.file_list_widget = QtWidgets.QListWidget()
        self.remove_selected_button = QtWidgets.QPushButton("Remove Selected")
        self.remove_selected_button.setFixedHeight(24)
        self.load_anim_button = QtWidgets.QPushButton("Load Animations")
        self.load_anim_button.setFixedHeight(24)
        self.export_button = QtWidgets.QPushButton("Batch Export Animations")
        self.export_button.setStyleSheet("background-color: lightgreen; color: black")
        self.connection_file_line = QtWidgets.QLineEdit()
        self.connection_file_line.setToolTip("Enter the file path to the connection rig file. A file which contains a rig with connections.")
        self.connection_filepath_button = QtWidgets.QPushButton()
        self.connection_filepath_button.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.connection_filepath_button.setFixedSize(24, 24)

        self.export_selected_label = QtWidgets.QLabel("Export Selected (Optional):")
        self.export_selected_line = QtWidgets.QLineEdit()
        self.export_selected_line.setToolTip("Enter the name(s) of the nodes that should be exported. Leave blank to export all.")
        self.export_selected_button = QtWidgets.QPushButton()
        self.export_selected_button.setIcon(QtGui.QIcon(":addClip.png"))
        self.export_selected_button.setFixedSize(24, 24)

        self.output_filepath_button = QtWidgets.QPushButton()
        self.output_filepath_button.setIcon(QtGui.QIcon(":fileOpen.png"))

        self.file_type_combo = QtWidgets.QComboBox()
        self.file_type_combo.addItems([".fbx", ".ma"])

        horizontal_layout_1 = QtWidgets.QHBoxLayout()
        horizontal_layout_1.addWidget(QtWidgets.QLabel("Connection Rig File:"))
        horizontal_layout_1.addWidget(self.connection_file_line)
        horizontal_layout_1.addWidget(self.connection_filepath_button)

        horizontal_layout_2 = QtWidgets.QHBoxLayout()
        horizontal_layout_2.addWidget(self.load_anim_button)
        horizontal_layout_2.addWidget(self.remove_selected_button)

        horizontal_layout_3 = QtWidgets.QHBoxLayout()
        horizontal_layout_3.addWidget(QtWidgets.QLabel("Output File Type:"))
        horizontal_layout_3.addWidget(self.file_type_combo)
        horizontal_layout_3.addWidget(self.export_button)

        horizontal_layout_4 = QtWidgets.QHBoxLayout()
        horizontal_layout_4.addWidget(self.export_selected_label)
        horizontal_layout_4.addWidget(self.export_selected_line)
        horizontal_layout_4.addWidget(self.export_selected_button)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.file_list_widget)
        main_layout.addLayout(horizontal_layout_2)
        main_layout.addLayout(horizontal_layout_1)
        main_layout.addLayout(horizontal_layout_4)
        main_layout.addLayout(horizontal_layout_3)

    def create_connections(self):
        self.connection_filepath_button.clicked.connect(self.connection_filepath_dialog)
        self.load_anim_button.clicked.connect(self.animation_filepath_dialog)
        self.export_button.clicked.connect(self.batch_action)
        self.export_selected_button.clicked.connect(self.add_selected_action)
        self.remove_selected_button.clicked.connect(self.remove_selected_item)

    def connection_filepath_dialog(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Select Connection Rig File", "", "Maya ACSII (*.ma);;All files (*.*)")
        if file_path[0]:
            self.connection_file_line.setText(file_path[0])

    def output_filepath_dialog(self):
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select export folder path", "")
        if folder_path:
            self.output_folder = folder_path
            return True
        else:
            return False

    def animation_filepath_dialog(self):
        file_paths = QtWidgets.QFileDialog.getOpenFileNames(self, "Select Animation Clips", "", "FBX (*.fbx);;All files (*.*)")
        file_path_list = file_paths[0]

        if file_path_list[0]:
            for i in file_path_list:
                self.file_list_widget.addItem(i)
        
        for i in range(0, self.file_list_widget.count()):
            self.file_list_widget.item(i).setTextColor(QtGui.QColor("white"))

    def add_selected_action(self):
        selection = cmds.ls(selection=True)
        if len(selection) > 1:
            text_string = "["
            for i in selection:
                text_string += '"{}", '.format(i)
            text_string = text_string[:-2]
            text_string += "]"
        elif selection[0]:
            text_string = "{}".format(selection[0])
        else:
            pass

        self.export_selected_line.setText(text_string)

    def remove_selected_item(self):
        try:
            selected_items = self.file_list_widget.selectedItems()
            for item in selected_items:
                self.file_list_widget.takeItem(self.file_list_widget.row(item))
        except:
            pass

    def batch_action(self):
        if self.connection_file_line.text() == "":
            cmds.warning("Connection file textfield is empty. Add a connection rig file to be able to export. This file should contain the rig and connections to a skeleton.")
        elif self.file_list_widget.count() == 0:
            cmds.warning("Animation clip list is empty. Add animation clips to the list to be able to export!")
        else:
            confirm_dialog = self.output_filepath_dialog()
            if confirm_dialog == True:
                self.bake_export()         
            else:
                pass

    def bake_export(self):
        self.animation_clip_paths = []
        for i in range(self.file_list_widget.count()):
            self.animation_clip_paths.append(self.file_list_widget.item(i).text())

        number_of_operations = len(self.animation_clip_paths) * 3
        current_operation = 0
        progress_dialog = QtWidgets.QProgressDialog("Preparing", "Cancel", 0, number_of_operations, self)
        progress_dialog.setWindowFlags(progress_dialog.windowFlags() ^ QtCore.Qt.WindowCloseButtonHint)
        progress_dialog.setWindowFlags(progress_dialog.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        progress_dialog.setValue(0)
        progress_dialog.setWindowTitle("Progress...")
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.show()
        QtCore.QCoreApplication.processEvents()
        export_result = []

        for i, path in enumerate(self.animation_clip_paths):
            # Import connection file and animation clip
            progress_dialog.setLabelText("Baking and exporting {} of {}".format(i + 1, len(self.animation_clip_paths)))
            self.file_list_widget.item(i).setTextColor(QtGui.QColor("yellow"))
            cmds.file(new=True, force=True)
            cmds.file(self.connection_file_line.text(), open=True)
            maya.mel.eval('FBXImportMode -v "exmerge";')
            maya.mel.eval('FBXImport -file "{}";'.format(path))
            current_operation += 1
            progress_dialog.setValue(current_operation) 

            # Bake animation
            RetargetingTool.bake_animation()
            current_operation += 1
            progress_dialog.setValue(current_operation) 

            # Export animation            
            output_path = self.output_folder + "/" + os.path.splitext(os.path.basename(path))[0]
            if self.file_type_combo.currentText() == ".fbx":
                output_path += ".fbx"
                cmds.file(rename=output_path)
                if self.export_selected_line.text() != "":
                    cmds.select(self.export_selected_line.text(), replace=True)
                    maya.mel.eval('FBXExport -f "{}" -s'.format(output_path))
                else:
                    maya.mel.eval('FBXExport -f "{}"'.format(output_path))
            elif self.file_type_combo.currentText() == ".ma":
                output_path += ".ma"
                cmds.file(rename=output_path)
                if self.export_selected_line.text() != "":
                    cmds.select(self.export_selected_line.text(), replace=True)
                    cmds.file(exportSelected=True, type="mayaAscii")
                else:
                    cmds.file(exportAll=True, type="mayaAscii")
            
            current_operation += 1
            progress_dialog.setValue(current_operation)        

            if os.path.exists(output_path):
                self.file_list_widget.item(i).setTextColor(QtGui.QColor("lime"))
                export_result.append("Sucessfully exported: "+output_path)

            else:
                self.file_list_widget.item(i).setTextColor(QtGui.QColor("red"))
                export_result.append("Failed exporting: "+output_path)
        
        print("------")
        for i in export_result:
            print(i)
        print("------")

        progress_dialog.setValue(number_of_operations)
        progress_dialog.close()


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