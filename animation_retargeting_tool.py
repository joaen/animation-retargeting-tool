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
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.api.OpenMaya as om2
from shiboken2 import wrapInstance
from PySide2 import QtCore
from PySide2 import QtWidgets


def maya_main_window():
    # Return the Maya main window as QMainWindow
    main_window = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window), QtWidgets.QWidget)


class RetargetWindow_UI(QtWidgets.QDialog):
    '''
    The RetargetWindow_UI is the main UI window.
    When a new ListItem_UI is created it gets added to the RetargetWindow_UI
    ''' 
    WINDOW_TITLE = "Animation Retargeting Tool"
 
    def __init__(self):
        super(RetargetWindow_UI, self).__init__(maya_main_window())
        
        self.connection_list = []
        self.counter = 0
        self.maya_color_list = [13, 18, 14, 17]
 
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.resize(380, 300)
 
        self.create_ui_widgets()
        self.create_ui_layout()
        self.create_ui_connections()
 
    def create_ui_widgets(self):
        self.refresh_button = QtWidgets.QPushButton("Refresh List")
        self.simple_conn_button = QtWidgets.QPushButton("Create Connection")
        self.ik_conn_button = QtWidgets.QPushButton("Create IK Connection")
        self.bake_button = QtWidgets.QPushButton("Bake Animation")

        self.help_button = QtWidgets.QPushButton("?")
        self.help_button.setFixedWidth(25)
 
        self.rot_checkbox = QtWidgets.QCheckBox("Rot")
        self.pos_checkbox = QtWidgets.QCheckBox("Trans")
        self.mo_checkbox = QtWidgets.QCheckBox("Maintain Offset")
        self.snap_checkbox = QtWidgets.QCheckBox("Align To Position")
 
    def create_ui_layout(self):
        upper_row_buttons = QtWidgets.QHBoxLayout()
        upper_row_buttons.addWidget(self.simple_conn_button)
        upper_row_buttons.addWidget(self.ik_conn_button)
        upper_row_buttons.addWidget(self.pos_checkbox)
        upper_row_buttons.addWidget(self.rot_checkbox)
        upper_row_buttons.addWidget(self.snap_checkbox)
        upper_row_buttons.addWidget(self.help_button)
        upper_row_buttons.addStretch()

        lower_row_buttons = QtWidgets.QHBoxLayout()
        lower_row_buttons.addWidget(self.refresh_button)
        lower_row_buttons.addWidget(self.bake_button)
 
        connection_list_widget = QtWidgets.QWidget()
 
        self.connection_layout = QtWidgets.QVBoxLayout(connection_list_widget)
        self.connection_layout.setContentsMargins(2, 2, 2, 2)
        self.connection_layout.setSpacing(3)
        self.connection_layout.setAlignment(QtCore.Qt.AlignTop)
 
        list_scroll_area = QtWidgets.QScrollArea()
        list_scroll_area.setWidgetResizable(True)
        list_scroll_area.setWidget(connection_list_widget)
 
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(list_scroll_area)
        main_layout.addLayout(upper_row_buttons)
        main_layout.addLayout(lower_row_buttons)
 
    def create_ui_connections(self):
        self.simple_conn_button.clicked.connect(self.create_connection_node)
        self.ik_conn_button.clicked.connect(self.create_ik_connection_node)
        self.refresh_button.clicked.connect(self.refresh_ui_list)
        self.bake_button.clicked.connect(self.bake_animation)
        self.help_button.clicked.connect(self.help_dialog)

        self.rot_checkbox.setChecked(True)
        self.pos_checkbox.setChecked(True)
        self.snap_checkbox.setChecked(True)
 
    def get_connect_nodes(self):
        connect_nodes_in_scene = []
        for i in cmds.ls():
            if cmds.attributeQuery("ConnectNode", node=i, exists=True) == True:
                connect_nodes_in_scene.append(i)
            else:
                pass
        return connect_nodes_in_scene

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
            selected_joint = cmds.ls(sl=True)[0]
            selected_ctrl = cmds.ls(sl=True)[1]
        except:
            return cmds.warning("No selections!")

        if retarget_tool_ui.get_snap_checkbox() == True:
            self.align_a_to_b(selected_ctrl, selected_joint)
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
        cmds.addAttr(locator, ln="ConnectNode", attributeType="message")
        cmds.addAttr(selected_ctrl, ln="ConnectedCtrl", attributeType="message")
        cmds.connectAttr(locator+".ConnectNode",selected_ctrl+".ConnectedCtrl")

        cmds.parent(locator, selected_joint)
        cmds.xform(locator, ro=(0, 0, 0))
        cmds.xform(locator, t=(0, 0, 0))
 
        # Select the type of constraint based on the ui checkboxes
        if retarget_tool_ui.get_rot_checkbox() == True and retarget_tool_ui.get_pos_checkbox() == True:
            cmds.parentConstraint(locator, selected_ctrl, w=1, mo=True)
    
        elif retarget_tool_ui.get_rot_checkbox() == True and retarget_tool_ui.get_pos_checkbox() == False:
            cmds.orientConstraint(locator, selected_ctrl, w=1, mo=True)
    
        elif retarget_tool_ui.get_pos_checkbox() == True and retarget_tool_ui.get_rot_checkbox() == False:
            cmds.pointConstraint(locator, selected_ctrl, w=1, mo=True)
        else:
            cmds.warning("Select translation and/or rotation!")
            cmds.delete(locator)
            cmds.deleteAttr(selected_ctrl, at="ConnectedCtrl")

        self.refresh_ui_list()
 
    def create_ik_connection_node(self):
        try:
            selected_joint = cmds.ls(sl=True)[0]
            selected_ctrl = cmds.ls(sl=True)[1]
        except:
            return cmds.warning("No selections!")

        self.rot_checkbox.setChecked(True)
        self.pos_checkbox.setChecked(True)

        if retarget_tool_ui.get_snap_checkbox() == True:
            self.align_a_to_b(selected_ctrl, selected_joint)
        else:
            pass
        
        tran_locator = self.create_ctrl_sphere(selected_joint+"_TRAN")

        cmds.parent(tran_locator, selected_joint)
        cmds.xform(tran_locator, ro=(0, 0, 0))
        cmds.xform(tran_locator, t=(0, 0, 0))

        rot_locator = self.create_ctrl_locator(selected_joint+"_ROT")

        # Add message attributes and connect them
        cmds.addAttr(tran_locator, ln="ConnectNode", attributeType="message")
        cmds.addAttr(rot_locator, ln="ConnectNode", attributeType="message")
        cmds.addAttr(selected_ctrl, ln="ConnectedCtrl", attributeType="message")
        cmds.connectAttr(tran_locator+".ConnectNode",selected_ctrl+".ConnectedCtrl")

        cmds.parent(rot_locator, tran_locator)
        cmds.xform(rot_locator, ro=(0, 0, 0))
        cmds.xform(rot_locator, t=(0, 0, 0))
    
        jointParent = cmds.listRelatives(selected_joint, parent=True)[0]
        cmds.parent(tran_locator, jointParent)
        cmds.makeIdentity(tran_locator, apply=True, translate=True)
    
        cmds.orientConstraint(selected_joint, tran_locator, w=1, mo=False)
        cmds.parentConstraint(rot_locator, selected_ctrl, w=1, mo=True)

        # Lock and hide attributes
        cmds.setAttr(rot_locator+".tx", lock=True, keyable=False)
        cmds.setAttr(rot_locator+".ty", lock=True, keyable=False)
        cmds.setAttr(rot_locator+".tz", lock=True, keyable=False)
        cmds.setAttr(tran_locator+".rx", lock=True, keyable=False)
        cmds.setAttr(tran_locator+".ry", lock=True, keyable=False)
        cmds.setAttr(tran_locator+".rz", lock=True, keyable=False)

        self.refresh_ui_list()

    def align_a_to_b(self, a, b):
        # Align point A to point B using the delta between the points
        b_pos = cmds.xform(b, q=True, worldSpace=True, rotatePivot=True)
        b_vec = om2.MVector(b_pos)
        a_pos = cmds.xform(a, q=True, rotatePivot=True)
        a_vec = om2.MVector(a_pos)

        new_pos = b_vec - a_vec

        cmds.xform(a, absolute=True, worldSpace=True, translation=new_pos)

    def create_ctrl_locator(self, ctrl_shape_name):
        ctrl = cmds.spaceLocator(name=ctrl_shape_name)[0]
        cmds.setAttr(ctrl+".overrideEnabled", 1)
        cmds.setAttr(ctrl+".overrideColor", self.maya_color_list[self.counter])
        cmds.setAttr(ctrl+".localScaleX", 1)
        cmds.setAttr(ctrl+".localScaleY", 1)
        cmds.setAttr(ctrl+".localScaleZ", 1)
        return ctrl

    def create_ctrl_sphere(self, ctrl_shape_name):
        ctrl = cmds.sphere(name=ctrl_shape_name)[0]
        cmds.setAttr(ctrl+".overrideEnabled", 1)
        cmds.setAttr(ctrl+".overrideColor", self.maya_color_list[self.counter])
        cmds.setAttr(ctrl+".overrideShading", False)
        cmds.setAttr(ctrl+".scaleX", 0.5)
        cmds.setAttr(ctrl+".scaleY", 0.5)
        cmds.setAttr(ctrl+".scaleZ", 0.5)
        return ctrl

    def bake_animation(self):
        confirm = cmds.confirmDialog(title="Confirm", message="Baking the animation will delete all the connection nodes. Do you wish to proceed?", button=["Yes","No"], defaultButton="Yes", cancelButton="No")

        if confirm == "Yes" and len(self.get_connected_ctrls()) == 0:
            cmds.warning("No connections found in scene!")

        if confirm == "Yes" and len(self.get_connected_ctrls()) != 0:
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
                    cmds.deleteAttr(ctrl, at="ConnectedCtrl")
                except:
                    pass
            
            self.refresh_ui_list()

        if confirm == "No":
            pass

    def help_dialog(self):
        dialog = cmds.confirmDialog(title="Instructions", message="To create a connection simply select the driver and then the driven and click 'Create connection'. For IK hands and IK feet controllers you can use 'Create IK Connection' for more complex retargeting. \n \nAs an example: if you want to transfer animation from a skeleton to a rig, first select the animated joint and then select the controller before you create a connection.", button=["Ok"], defaultButton="Ok", cancelButton="Ok")
        return dialog


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
        connection_shapes = retarget_tool_ui.get_connect_nodes()
        color = retarget_tool_ui.maya_color_list
        ui_items = retarget_tool_ui.connection_list

        if retarget_tool_ui.counter < 3:
            retarget_tool_ui.counter += 1
        else:
            retarget_tool_ui.counter = 0

        # Set the color on the connection node shape and button
        for c in connection_shapes:
            cmds.setAttr(c+".overrideEnabled", 1)
            cmds.setAttr(c+".overrideColor", color[retarget_tool_ui.counter])

        for i in ui_items:
            i.color_button.setStyleSheet("background-color:"+self.get_color())
 
    def get_color(self):
        # Set the color of the button based on the color of the connection shape
        ctrl = self.shape_name
        current_color = cmds.getAttr(ctrl+".overrideColor")
 
        if current_color == 13:
            return "red"
        elif current_color == 18:
            return "cyan"
        elif current_color == 14:
            return "green"
        elif current_color == 17:
            return "yellow"
        else:
            return "grey"


def start():
    global retarget_tool_ui
    try:
        retarget_tool_ui.close()
        retarget_tool_ui.deleteLater()
    except:
        pass
    retarget_tool_ui = RetargetWindow_UI()
    retarget_tool_ui.show()

if __name__ == "__main__":
    start()