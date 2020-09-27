# Standard
import os
import sys
import functools

if sys.version_info[0] >= 3:
    long = int

# Not even going to pretend to have Maya 2016 support
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

UI_FILES_FOLDER = os.path.dirname(__file__)
ICON_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")
"""
QT UTILS BEGIN
"""


def get_app_window():
    top_window = None
    try:
        from maya import OpenMayaUI as omui
        maya_main_window_ptr = omui.MQtUtil().mainWindow()
        top_window = wrapInstance(long(maya_main_window_ptr), QtWidgets.QMainWindow)
    except ImportError as e:
        pass
    return top_window


def delete_window(object_to_delete):
    qApp = QtWidgets.QApplication.instance()
    if not qApp:
        return

    for widget in qApp.topLevelWidgets():
        if "__class__" in dir(widget):
            if str(widget.__class__) == str(object_to_delete.__class__):
                widget.deleteLater()
                widget.close()


def load_ui_file(ui_file_name):
    ui_file_path = os.path.join(UI_FILES_FOLDER, ui_file_name)  # get full path
    if not os.path.exists(ui_file_path):
        sys.stdout.write("UI FILE NOT FOUND: {}\n".format(ui_file_path))
        return None

    ui_file = QtCore.QFile(ui_file_path)
    ui_file.open(QtCore.QFile.ReadOnly)
    loader = QtUiTools.QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()
    return window


def create_qicon(icon_path):
    icon_path = icon_path.replace("\\", "/")
    if "/" not in icon_path:
        icon_path = os.path.join(ICON_FOLDER, icon_path + ".png")  # find in icons folder if not full path
        if not os.path.exists(icon_path):
            return

    return QtGui.QIcon(icon_path)


class BaseWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=get_app_window(), ui_file_name=None):
        delete_window(self)
        super(BaseWindow, self).__init__(parent)

        self.ui = None
        if ui_file_name:
            self.load_ui(ui_file_name)

        self.set_tool_icon("TOOL_NAME_icon")

        self.show()

    def set_tool_icon(self, icon_name):
        icon = create_qicon(icon_name)
        if icon:
            self.setWindowIcon(icon)

    def load_ui(self, ui_file_name):
        self.ui = load_ui_file(ui_file_name)
        self.setGeometry(self.ui.rect())
        self.setWindowTitle(self.ui.property("windowTitle"))
        self.setCentralWidget(self.ui)

        parent_window = self.parent()
        if not parent_window:
            return

        dcc_window_center = parent_window.mapToGlobal(parent_window.rect().center())
        window_offset_x = dcc_window_center.x() - self.geometry().width() / 2
        window_offset_y = dcc_window_center.y() - self.geometry().height() / 2
        self.move(window_offset_x, window_offset_y)  # move to dcc screen center


"""
QT UTILS END
"""

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya import OpenMayaUI as omui
from PySide2 import QtWidgets
from maya import cmds


class WindowHandler(object):
    pass


wh = WindowHandler()


class DockableWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    docking_object_name = "DockableWidget"

    def __init__(self, parent=None):
        super(DockableWidget, self).__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setObjectName(self.docking_object_name)  # this one is important
        self.setWindowTitle('Custom Maya Mixin Workspace Control')


def create_dockable_widget(widget_class,
                           restore=False, restore_script="create_dockable_widget(restore=True)",
                           force_refresh=False
                           ):
    if force_refresh:
        if widget_class.docking_object_name in wh.__dict__.keys():
            wh.__dict__.pop(widget_class.docking_object_name)

        workspace_control_name = widget_class.docking_object_name + "WorkspaceControl"
        if cmds.workspaceControl(workspace_control_name, q=True, exists=True):
            cmds.workspaceControl(workspace_control_name, e=True, close=True)
            cmds.deleteUI(workspace_control_name, control=True)

    if restore:
        # Grab the created workspace control with the following.
        restored_control = omui.MQtUtil.getCurrentParent()

    widget_instance = wh.__dict__.get(widget_class.docking_object_name)

    if widget_instance is None:
        # Create a custom mixin widget for the first time
        widget_instance = widget_class()  # type: DockableWidget
        wh.__dict__[widget_class.docking_object_name] = widget_instance

    if restore:
        # Add custom mixin widget to the workspace control
        mixin_ptr = omui.MQtUtil.findControl(widget_class.docking_object_name)
        omui.MQtUtil.addWidgetToMayaLayout(long(mixin_ptr), long(restored_control))
    else:
        # Create a workspace control for the mixin widget by passing all the needed parameters.
        # See workspaceControl command documentation for all available flags.
        widget_instance.show(dockable=True, height=600, width=480, uiScript=restore_script)

    return widget_instance


def build_menu_from_action_list(actions, menu=None, is_sub_menu=False):
    if not menu:
        menu = QtWidgets.QMenu()

    for action in actions:
        if action == "-":
            menu.addSeparator()
            continue

        for action_title, action_command in action.items():
            if action_title == "RADIO_SETTING":
                # Create RadioButtons for QSettings object
                settings_obj = action_command.get("settings")  # type: QtCore.QSettings
                settings_key = action_command.get("settings_key")  # type: str
                choices = action_command.get("choices")  # type: list
                default_choice = action_command.get("default")  # type: str
                on_trigger_command = action_command.get("on_trigger_command")  # function to trigger after setting value

                # Has choice been defined in settings?
                item_to_check = settings_obj.value(settings_key)

                # If not, read from default option argument
                if not item_to_check:
                    item_to_check = default_choice

                grp = QtWidgets.QActionGroup(menu)
                for choice_key in choices:
                    action = QtWidgets.QAction(choice_key, menu)
                    action.setCheckable(True)

                    if choice_key == item_to_check:
                        action.setChecked(True)

                    action.triggered.connect(functools.partial(set_settings_value,
                                                               settings_obj,
                                                               settings_key,
                                                               choice_key,
                                                               on_trigger_command))
                    menu.addAction(action)
                    grp.addAction(action)

                grp.setExclusive(True)
                continue

            if isinstance(action_command, list):
                sub_menu = menu.addMenu(action_title)
                build_menu_from_action_list(action_command, menu=sub_menu, is_sub_menu=True)
                continue

            atn = menu.addAction(action_title)
            atn.triggered.connect(action_command)

    if not is_sub_menu:
        cursor = QtGui.QCursor()
        menu.exec_(cursor.pos())

    return menu


def set_settings_value(settings_obj, key, value, post_set_command):
    settings_obj.setValue(key, value)
    post_set_command()
