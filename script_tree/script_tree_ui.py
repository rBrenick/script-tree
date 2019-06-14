# General imports
import os
import stat
import json
import subprocess
import logging
import shutil
import time

# Qt Imports
try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from shiboken import wrapInstance

# Maya imports
import pymel.core as pm
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin, MayaQWidgetDockableMixin

"""
QT UTILS BEGIN
"""


def get_maya_window():
    from maya import OpenMayaUI as omui
    maya_main_window_ptr = omui.MQtUtil().mainWindow()
    maya_main_window = wrapInstance(long(maya_main_window_ptr), QWidget)
    return maya_main_window


def delete_window(object):
    for widget in QApplication.instance().topLevelWidgets():
        if "__class__" in dir(widget):
            if str(widget.__class__) == str(object.__class__):
                widget.deleteLater()
                widget.close()


"""
QT UTILS END
"""

# Global Vars
MAYA_FOLDER = os.path.dirname(os.path.dirname(os.path.dirname(pm.internalVar(upd=True))))
SCRIPT_TREE_FOLDER = os.path.join(MAYA_FOLDER, "ScriptTree")
SETTINGS_FILEPATH = os.path.join(SCRIPT_TREE_FOLDER, "ScriptTree.ini")

SCRIPT_BACKUP_FOLDER = os.path.join(SCRIPT_TREE_FOLDER, "ScriptTree_ScriptBackup")
TREE_BACKUP_FOLDER = os.path.join(SCRIPT_TREE_FOLDER, "ScriptTree_TreeBackup")

PROMPT_RELOAD = False


class ScriptTreeConstants:
    opVar_dockToScriptEditor = "ScriptTree_DockToScriptEditor"
    opVar_CreateOnScriptEditorStart = "ScriptTree_CreateOnScriptEditorStart"
    newTabDefaultCode = ["import pymel.core as pm"]
    default_folder = os.path.join(SCRIPT_TREE_FOLDER, "ScriptTree").replace("\\", "/")
    # default_folder = "M:/Art/Tools/Maya/Scripts"


stk = ScriptTreeConstants


class ScriptTreeWindow(QMainWindow):
    def __init__(self, parent=get_maya_window()):
        delete_window(object=self)
        super(ScriptTreeWindow, self).__init__(parent=parent)
        self.setWindowTitle("ScriptTree")

        self.tree_widgets = ScriptFileTreeWidgets()
        self.my_QMenu_bar = self.menuBar()

        self.setupUI()

    def setupUI(self):
        self.setCentralWidget(self.tree_widgets)

        file_menu = self.my_QMenu_bar.addMenu('File')
        self.create_action(name="New", command=new_tab, hotkey="Ctrl+N", menu=file_menu)
        self.create_action(name="Open", command=open_file, hotkey="Ctrl+O", menu=file_menu)
        self.create_action(name="Save", command=self.tree_widgets.save_selected, hotkey="Ctrl+S", menu=file_menu)
        self.create_action(name="Save As...", command=self.tree_widgets.save_as_selected, hotkey="Ctrl+Shift+S", menu=file_menu)
        self.create_action(name="Save Preferences", command=self.tree_widgets.save_settings, hotkey="Alt+Shift+S", menu=file_menu)
        self.create_action(name="Reload Tab", command=self.tree_widgets.reload_tab, hotkey="F5", menu=file_menu)
        self.create_action(name="Delete Current Tab", command=delete_current_tab, hotkey="Ctrl+W", menu=file_menu)
        self.create_action(name="Save Script Editor", command=save_script_editor, menu=file_menu)
        # self.create_action(name="Colorize Script Editor", command=colorizeScriptEditor, menu=file_menu)
        self.create_action(name="------------------", menu=file_menu)
        self.create_action(name="Backup Tree", command=backup_tree, menu=file_menu)
        file_menu.setTearOffEnabled(True)

        # edit menu
        edit_menu = self.my_QMenu_bar.addMenu('Edit')
        self.create_action(name="Clear Output", command=clear_script_output, hotkey="Alt+Shift+D", menu=edit_menu)
        self.create_action(name="Comment Selected Lines", command=toggle_comment_selected_lines, hotkey="Ctrl+/", menu=edit_menu)
        self.create_action(name="Insert pm.selected()[0]", command=insert_pm_selected, hotkey="Ctrl+Alt+S", menu=edit_menu)
        edit_menu.setTearOffEnabled(True)

        self.tree_widgets.load_settings()

    def create_action(self, name="Action", command=None, hotkey=None, menu=None):
        action = QAction(name, self)
        if command:
            action.triggered.connect(command)
        if hotkey:
            action.setShortcut(hotkey)
        menu.addAction(action)


class ScriptTreeDockableWindow(MayaQWidgetDockableMixin, ScriptTreeWindow):
    def __init__(self, name="ScriptTree", *args, **kwargs):
        delete_window(object=self)

        super(ScriptTreeDockableWindow, self).__init__()
        # Destroy this widget when closed.  Otherwise it will stay around
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName(name)
        self.setWindowTitle(name)

        self.show(dockable=True)


class ScriptFileTreeWidgets(QWidget):
    def __init__(self, parent=None):
        super(ScriptFileTreeWidgets, self).__init__(parent)
        self.scripts = []

        self.fileWatcher = QFileSystemWatcher()
        if PROMPT_RELOAD:
            self.fileWatcher.fileChanged.connect(self.script_updated)

        self.network_tree = None
        # self.localTree = None
        self.splitterHeight = 0

        self.setObjectName('ScriptFileTreeWidget')

        self.setup_ui()
        self.load_settings()

        self.read_current_tabs()

    def setup_ui(self):

        self.network_tree = ScriptTreeWidget(FileTreeSettings.kNetworkFolder, parent=self)
        # self.localTree = ScriptTreeWidget(FileTreeSettings.kLocalFolder, parent=self)

        # Add to main layout
        self.main_layout = QVBoxLayout()
        # self.mainLayout.addWidget(saveButton)

        # Add File trees to a splitter
        # self.split = QSplitter()
        # self.split.setOrientation(Qt.Vertical)
        # self.split.addWidget(self.networkTree)
        self.main_layout.addWidget(self.network_tree)
        # self.split.addWidget(self.localTree)
        # self.split.splitterMoved.connect(self.setSplitterHeight)

        if PROMPT_RELOAD:
            self.connect_current_tab_check()

        # self.mainLayout.addWidget(self.split)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.main_layout)

    def load_settings(self):
        settings = FileTreeSettings()

        # Set folders on file trees
        self.network_tree.load_settings()
        # self.localTree.loadSettings()

        # Restore Splitter Height from settings
        # storedSplitterHeight = settings.data.get(FileTreeSettings.kSplitter, {}).get(FileTreeSettings.kSplitterHeight, 1000)
        # self.split.moveSplitter(storedSplitterHeight, 1)

    def save_settings(self):
        self.network_tree.save_settings()
        # self.localTree.saveSettings()
        # self.saveSplitterSettings()
        logging.info("Preferences Saved")

    def save_splitter_settings(self):
        settings = FileTreeSettings()
        settings.data[FileTreeSettings.kSplitter][FileTreeSettings.kSplitterHeight] = self.splitterHeight
        settings.save()

    def set_splitter_height(self, *args):
        self.splitterHeight = args[0]

    def read_current_tabs(self):
        script_editor_window = get_script_editor_window()
        if not script_editor_window:
            return

        self.scripts = []
        settings = FileTreeSettings()
        tab_file_paths = settings.data.get(FileTreeSettings.kTabPaths, {})

        mel_tabs_layout = pm.melGlobals["$gCommandExecuterTabs"]
        tab_layout = pm.ui.TabLayout(mel_tabs_layout)

        tabs_child_array = tab_layout.getChildArray()
        tab_names = pm.tabLayout(mel_tabs_layout, q=True, tabLabel=True)

        for tab, tabName in zip(tabs_child_array, tab_names):
            script_tab = ScriptTab(tab=tab)
            self.scripts.append(script_tab)

            # Get saved info
            tab_file_path = tab_file_paths.get(tabName)

            if tab_file_path:
                script_tab.set_file_info(tab_file_path)
                if tab_file_path not in self.fileWatcher.files():
                    self.fileWatcher.addPath(tab_file_path)

    def script_updated(self, *file_paths):
        script_tabs = self.scripts

        for path in file_paths:
            for scriptTab in script_tabs:
                if scriptTab.selected and scriptTab.filePath == path:
                    script_tabs.pop(script_tabs.index(scriptTab))
                    scriptTab.prompt_reload()

        self.read_current_tabs()

    @staticmethod
    def disconnect_current_tab_check():
        """
        used for Prompt Reload
        :return:
        """
        mel_tabs_layout = pm.melGlobals["$gCommandExecuterTabs"]
        tab_layout = pm.ui.TabLayout(mel_tabs_layout)
        tab_layout.changeCommand(do_nothing)

    def connect_current_tab_check(self):
        mel_tabs_layout = pm.melGlobals["$gCommandExecuterTabs"]
        tab_layout = pm.ui.TabLayout(mel_tabs_layout)
        tab_layout.changeCommand(self.check_current_tab_updated)

    def check_current_tab_updated(self, *args):
        if not PROMPT_RELOAD:
            return

        self.read_current_tabs()
        sel_tab = get_selected_tab()

        if not sel_tab or not sel_tab.filePath:
            return

        tab_content = sel_tab.textArea.toPlainText()
        with open(sel_tab.filePath, "r") as f:
            file_contents = f.read()

        if tab_content != file_contents:
            sel_tab.prompt_reload()

    def save_selected(self):
        self.disconnect_current_tab_check()
        tab = get_selected_tab()
        if tab.filePath:
            self.fileWatcher.removePath(tab.filePath)

        tab.save()

        if tab.filePath:
            self.fileWatcher.addPath(tab.filePath)
            self.connect_current_tab_check()

    def save_as_selected(self):
        self.disconnect_current_tab_check()
        tab = get_selected_tab()
        if tab.filePath:
            self.fileWatcher.removePath(tab.filePath)

        tab.save(prompt_file=True)

        if tab.filePath:
            self.fileWatcher.addPath(tab.filePath)
        self.connect_current_tab_check()

    def reload_tab(self):
        self.load_settings()
        tab = get_selected_tab()
        tab.reload()


class ScriptTreeWidget(QWidget):
    def __init__(self, name, parent=None):
        super(ScriptTreeWidget, self).__init__(parent)

        self.folder = None
        self.name = name
        self.ui_parent = parent

        self.setup_ui()

    def setup_ui(self):

        self.folder_path = QLineEdit()
        self.folder_path.textChanged.connect(self.line_edit_set_folder)

        self.search_bar = QLineEdit()
        self.search_bar.textChanged.connect(self.filter_results)
        self.search_bar.setPlaceholderText("search")

        self.default_filter = ["*.py", "*.mel"]

        set_folder_btn = QPushButton("...")
        set_folder_btn.clicked.connect(self.button_set_folder)

        self.model = QFileSystemModel()
        self.model.setRootPath(self.folder)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.AllEntries)
        self.model.setNameFilters(self.default_filter)
        self.model.setNameFilterDisables(0)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(self.folder))
        self.tree_view.doubleClicked.connect(self.add_script)

        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.context_menu_file_system)

        # self.treeView.setColumnWidth(0, 300)
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)
        self.tree_view.setHeaderHidden(True)

        # Add to main layout
        self.main_layout = QVBoxLayout()
        file_line_layout = QHBoxLayout()
        file_line_layout.addWidget(self.folder_path)
        file_line_layout.addWidget(set_folder_btn)

        self.main_layout.addLayout(file_line_layout)
        self.main_layout.addWidget(self.search_bar)
        self.main_layout.addWidget(self.tree_view)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.main_layout)

    def context_menu_file_system(self, position):
        actions = list()
        actions.append({"Run Script": self.run_script})
        actions.append({"Show in Explorer": self.open_path_in_explorer})
        actions.append({"Open Backup Folder": self.open_backup_folder})

        menu = self.build_context_menu(actions)
        menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def build_context_menu(self, actions):
        menu = QMenu(self)
        for action in actions:
            if action == "SEPERATOR":
                menu.addSeparator()
            else:
                for text, method in action.items():
                    action = QAction(self)
                    action.setText(text)
                    action.triggered.connect(method)
                    menu.addAction(action)

        return menu

    def get_current_selected_file_path(self):
        index = self.tree_view.currentIndex()
        file_path = self.model.filePath(index)
        return file_path

    def open_path_in_explorer(self, file_path=None):
        if not file_path:
            file_path = self.get_current_selected_file_path()

        if os.path.isdir(file_path):
            file_path += "/"

        file_path = file_path.replace("/", "\\")

        try:
            if os.path.isdir(file_path):
                subprocess.Popen(r'explorer %s' % file_path)
            else:
                subprocess.Popen(r'explorer /select,%s' % file_path)
        except StandardError:
            pm.warning("Attempt to Open path in explorer failed")

    def open_backup_folder(self):
        self.open_path_in_explorer(SCRIPT_BACKUP_FOLDER)

    def run_script(self, file_path=None):
        if not file_path:
            file_path = self.get_current_selected_file_path()

        file_path = file_path.replace("\\", "/")
        if file_path.endswith(".py"):
            cmd = "execfile('{}', globals())".format(file_path)
            exec_command = 'python("{}")'.format(cmd)
            execfile(file_path, globals())

        elif file_path.endswith(".mel"):
            pm.warning("TODO: add Mel support")
            exec_command = ""

        logging.info("Executed: {}".format(file_path))
        pm.repeatLast(ac=exec_command)

    # Settings
    def load_settings(self):
        settings = FileTreeSettings()
        folder = settings.data.get(FileTreeSettings.kFolders, {}).get(self.name)
        if folder:
            self.set_folder(folder)

    def save_settings(self):
        settings = FileTreeSettings()
        settings.data[FileTreeSettings.kFolders][self.name] = self.folder
        settings.save()

    # Filter Files
    def filter_results(self, *args):
        filter_text = args[0]
        if not filter_text:
            self.model.setNameFilters(self.default_filter)
            self.tree_view.collapseAll()
        else:
            filters = []
            for filter_string in filter_text.split(","):
                filter_string = filter_string.replace(" ", "")
                filters += ["*" + filter_string + "*.py"]
                filters += ["*" + filter_string + "*.mel"]
            self.tree_view.expandAll()
            self.model.setNameFilters(filters)

    # Folder
    def line_edit_set_folder(self, folder):
        self.set_folder(folder)

    def button_set_folder(self):
        folder_query = pm.fileDialog2(fileMode=2, dialogStyle=1, startingDirectory=self.folder)
        if folder_query:
            folder = folder_query[0]
            self.set_folder(folder)

    def set_folder(self, folder=None):
        if folder == stk.default_folder:
            try:
                os.makedirs(folder)
            except WindowsError, e:
                pass

        if not os.path.exists(folder):
            return

        folder = folder.replace("\\", "/")

        self.folder = folder
        self.model.setRootPath(self.folder)
        self.tree_view.setRootIndex(self.model.index(self.folder))
        self.folder_path.setText(folder)

        self.save_settings()

    # Add Tab
    def add_script(self, index):
        if not get_script_editor_window():
            pm.warning("Script Editor has to be active to create a ScriptTab for this file")
            return

        self.ui_parent.disconnect_current_tab_check()

        path = self.get_file_path(index)
        script_tab = add_script_to_editor(path)
        if script_tab:
            add_script_tab_to_settings(script_tab)

        self.ui_parent.connect_current_tab_check()

    def get_file_path(self, index):
        file_path = self.model.filePath(index)
        file_path = file_path.replace("\\", "/")
        return file_path


class ScriptTab(object):
    def __init__(self, tab=None, file_path=None):

        self.tab = None
        self.index = None
        self.textArea = None
        self.label = None

        self.__selected = False

        self.filePath = None
        self.extension = None
        self.fileName = None

        self.isDirty = False

        if tab:
            self.tab = tab
            self.get_tab_info()

        if file_path:
            self.set_file_info(file_path)

    @property
    def selected(self):
        self.__selected = False

        selected_tab = pm.mel.getCurrentExecuterControl()
        cmd_exec = pm.formLayout(self.tab, q=True, ca=True)[0]

        if selected_tab == cmd_exec:
            self.__selected = True

        return self.__selected

    def set_file_info(self, file_path):
        self.filePath = file_path
        self.extension = os.path.splitext(file_path)[-1]
        self.fileName = os.path.basename(self.filePath).replace(self.extension, "")

    def create_tab(self):
        """
        Creates a new script tab from the filepath
        
        :return: 
        """
        if not os.path.exists(self.filePath):
            return

        if not get_script_editor_window():
            pm.warning("Script Editor has to be opened to create a ScriptTab for this file")
            return

        # If tab already exists, switch to it
        self.tab = get_script_tab_by_name(self.fileName)

        if self.tab:
            select_tab_by_name(self.fileName)

        if not self.tab:
            # Build tab
            fileType = "python"
            if os.path.splitext(self.filePath)[-1][1:].lower() == "mel":
                fileType = "mel"

            pm.mel.buildNewExecuterTab(-1, self.fileName, fileType, 0)

            # Get tab settings
            tabs = pm.melGlobals["$gCommandExecuterTabs"]
            tabs_layout = pm.tabLayout(tabs, q=True, ca=True)
            self.tab = tabs_layout[-1]

            # Select Created Tab
            tabs_len = pm.tabLayout(tabs, q=True, numberOfChildren=True)
            pm.tabLayout(tabs, e=True, selectTabIndex=tabs_len)

        # Indent this if you want to fill tab content from file only if it didn't exist
        cmd_exec = pm.formLayout(self.tab, q=True, ca=True)[0]
        with open(self.filePath, "r") as f:
            file_contents = f.read()
        pm.cmdScrollFieldExecuter(cmd_exec, e=True, text=file_contents)

        self.get_tab_info()

    def create_new_tab(self):
        pm.mel.buildNewExecuterTab(-1, "Python", "python", 0)

        tabs = pm.melGlobals["$gCommandExecuterTabs"]
        tabs_layout = pm.tabLayout(tabs, q=True, ca=True)
        self.tab = tabs_layout[-1]

        tabs_len = pm.tabLayout(tabs, q=True, numberOfChildren=True)
        pm.tabLayout(tabs, e=True, selectTabIndex=tabs_len)

        cmd_exec = pm.formLayout(self.tab, q=True, ca=True)[0]

        default_code = "\n".join(stk.newTabDefaultCode)

        pm.cmdScrollFieldExecuter(cmd_exec, e=True, text=default_code)

    def get_tab_info(self):
        """
        Gets the tab info from the Qt elements of the script editor
        
        :return: 
        """
        if not self.tab:
            return

        reporter = self.tab
        py_reporter = pm.ui.CmdScrollFieldExecuter(reporter)
        reporter_qt = py_reporter.asQtObject()

        # I am kind of ashamed of the following, but findChildren was being weird
        for child in reporter_qt.children():
            for qtChild in child.children():
                if "QTextDocument" in str(qtChild):
                    self.textArea = qtChild

                for qtChild2 in qtChild.children():
                    if "QTextDocument" in str(qtChild2):
                        self.textArea = qtChild2

        tab_layout = pm.ui.TabLayout(pm.melGlobals["$gCommandExecuterTabs"])
        tab_name = self.tab.split("|")[-1]
        self.index = tab_layout.getChildArray().index(tab_name)
        self.label = tab_layout.getTabLabel()[self.index]

        """
        # This will just save constantly on text change. 
        # Use this if you want your Hardrive to die an early, glorious, death
         
        self.textArea.contentsChanged.connect(self.markDirty)
        """

    def mark_dirty(self, value=True):
        self.isDirty = value

    def prompt_reload(self):
        if not self.filePath:
            return

        if prompt_reload_file(self.filePath):
            self.reload()

    def reload(self):
        """
        Reloads the tab contents from disk
        
        :return: 
        """
        if not self.filePath:
            return

        if os.path.exists(self.filePath):
            with open(self.filePath, "r") as f:
                file_contents = f.read()

            tabs_layout_children = pm.formLayout(self.tab, q=True, ca=True)
            tab = tabs_layout_children[0]

            pm.cmdScrollFieldExecuter(tab, e=True, text=file_contents)
            logging.info("Tab Reloaded: {}".format(self.fileName))

    def get_new_file_path(self):
        """
        Gives the user the ability to specify a filepath for this scriptTab
        
        :return: 
        """
        settings = FileTreeSettings()
        script_folder = settings.data.get(FileTreeSettings.kFolders, {}).get(FileTreeSettings.kNetworkFolder, None)

        dialog_params = dict()
        dialog_params["fileMode"] = 0
        dialog_params["fileFilter"] = "Python and MEL(*.py *.mel)"
        dialog_params["dialogStyle"] = 1
        if script_folder:
            dialog_params["startingDirectory"] = script_folder

        file_query = pm.fileDialog2(**dialog_params)
        if not file_query:
            return

        target_file_path = file_query[0]

        if os.path.basename(target_file_path).lower() == "python.py":
            logging.error("You can not create a file called 'Python' as that will interfere with the normal tabs")
            return

        self.set_file_info(target_file_path)

    def save(self, prompt_file=False, log_save_message=True):
        """
        Does all the checks on whether it's a valid path and whether it can access the script data
        
        :param prompt_file:
        :param log_save_message:
        :return: 
        """
        rename_tab = False
        if not self.filePath or prompt_file:
            self.get_new_file_path()
            rename_tab = True

        try:
            script = self.textArea.toPlainText()
        except StandardError, e:
            script = None

        if script and self.filePath and prompt_is_writable(self.filePath):
            self.create_backup_file()
            return self.save_file(rename_tab=rename_tab, log_save_message=log_save_message)

        return False

    def save_file(self, rename_tab=True, log_save_message=True):
        """
        Saves the script content to the filepath
        
        :param rename_tab:
        :param log_save_message:
        :return: 
        """
        script = self.textArea.toPlainText()

        with open(self.filePath, "w+") as f:
            f.write(script)

        if rename_tab:
            pm.mel.eval(
                'tabLayout -e -tabLabelIndex {} {} $gCommandExecuterTabs;'.format(self.index + 1, self.fileName))
            melCmd = '$gCommandExecuterName[{}] = "{}";'.format(self.index, self.fileName)
            pm.mel.eval(melCmd)

        if log_save_message:
            logging.info("SAVED: {}".format(self.filePath))

        add_script_tab_to_settings(self)
        pm.mel.syncExecuterTabState()

        return True

    def create_backup_file(self):
        """
        Copies the current file to the users local backup folder 
        
        :return: 
        """
        if not os.path.exists(self.filePath):
            return
        try:
            unique_time = str(int(time.time()))
            backup_file_name = self.fileName + "_BACKUP_{}".format(unique_time) + self.extension
            backup_file_path = os.path.join(SCRIPT_BACKUP_FOLDER, self.fileName, backup_file_name)
            if not os.path.exists(os.path.dirname(backup_file_path)):
                os.makedirs(os.path.dirname(backup_file_path))

            shutil.copy2(self.filePath, backup_file_path)
        except StandardError, e:
            logging.error(e)


class FileTreeSettings(object):
    kTabPaths = "Tabs"
    kSplitter = "Splitter"
    kSplitterHeight = "height"

    kFolders = "Folders"
    kLocalFolder = "LocalScriptFolder"
    kNetworkFolder = "NetworkScriptFolder"
    kDefaultFolder = stk.default_folder

    def __init__(self):
        self.data = {}
        self.load()

    def load(self):
        settings = {FileTreeSettings.kFolders: {FileTreeSettings.kNetworkFolder: FileTreeSettings.kDefaultFolder},
                    FileTreeSettings.kTabPaths: {},
                    FileTreeSettings.kSplitter: {}}

        if os.path.exists(SETTINGS_FILEPATH):
            with open(SETTINGS_FILEPATH, "r") as f:
                settings_str = f.read()
                stored_settings = json.loads(settings_str)

            settings = dict(settings, **stored_settings)

        self.data = settings

    def save(self):
        with open(SETTINGS_FILEPATH, "w+") as f:
            f.write(json.dumps(self.data, indent=4))


def prompt_reload_file(file_path):
    do_reload = False

    file_name = os.path.basename(file_path)
    btn_reload_files = "Load File"
    btn_cancel = "Keep Tab"

    confirm_params = dict()
    confirm_params["title"] = "Load From File"
    confirm_params["message"] = "Tab contents does not match {}".format(file_name)
    confirm_params["messageAlign"] = "center"
    confirm_params["button"] = [btn_reload_files, btn_cancel]
    confirm_params["defaultButton"] = btn_reload_files
    confirm_params["cancelButton"] = btn_cancel
    confirm_params["dismissString"] = btn_cancel

    con_return = pm.confirmDialog(**confirm_params)

    if con_return == btn_reload_files:
        do_reload = True

    return do_reload


def prompt_is_writable(file_path):
    if not os.path.exists(file_path):
        return True

    write_access = os.access(file_path, os.W_OK)

    if not write_access:

        file_name = os.path.basename(file_path)
        btn_make_write = "Make Writeable"
        btn_cancel = "Cancel"

        confirm_params = dict()
        confirm_params["title"] = "File Not Writable"
        confirm_params["message"] = "{} is not writable".format(file_name)
        confirm_params["messageAlign"] = "center"
        confirm_params["button"] = [btn_make_write, btn_cancel]
        confirm_params["defaultButton"] = btn_make_write
        confirm_params["cancelButton"] = btn_cancel
        confirm_params["dismissString"] = btn_cancel

        con_return = pm.confirmDialog(**confirm_params)

        if con_return == btn_make_write:
            os.chmod(file_path, stat.S_IWRITE)
            write_access = os.access(file_path, os.W_OK)
            if not write_access:
                pm.warning("Unable to make file writeable: {}".format(file_path))

    return write_access


def get_script_tab_by_name(name):
    mel_tabs = pm.melGlobals["$gCommandExecuterTabs"]
    tabs = pm.tabLayout(mel_tabs, q=True, ca=True)
    tab_names = pm.tabLayout(mel_tabs, q=True, tabLabel=True)

    if name in tab_names:
        tab_index = tab_names.index(name)
        tab = pm.ui.FormLayout(tabs[tab_index])
        return tab

    return None


def select_tab_by_name(name):
    mel_tabs = pm.melGlobals["$gCommandExecuterTabs"]
    tabs = pm.tabLayout(mel_tabs, q=True, ca=True)
    tab_names = pm.tabLayout(mel_tabs, q=True, tabLabel=True)

    if name in tab_names:
        tab_index = tab_names.index(name)
        tab = pm.ui.FormLayout(tabs[tab_index])
        pm.tabLayout(mel_tabs, e=True, selectTabIndex=tab_index + 1)

        return tab

    return None


def get_selected_tab():
    tab_layout = pm.ui.TabLayout(pm.melGlobals["$gCommandExecuterTabs"])
    selected_tab_layout = pm.ui.FormLayout(tab_layout.getSelectTab())

    sel_tab = ScriptTab(tab=selected_tab_layout)
    tab_file_paths = FileTreeSettings().data.get(FileTreeSettings.kTabPaths, {})
    tab_file_path = tab_file_paths.get(sel_tab.label)
    if tab_file_path:
        sel_tab.set_file_info(tab_file_path)

    return sel_tab


def add_script_to_editor(file_path):
    ext = os.path.splitext(file_path)[-1]
    if ext != ".py" and ext != ".mel":
        return None

    script_tab = ScriptTab(file_path=file_path)
    script_tab.create_tab()
    return script_tab


def add_script_tab_to_settings(script_tab):
    file_name = script_tab.fileName
    settings = FileTreeSettings()
    settings.data[FileTreeSettings.kTabPaths][file_name] = script_tab.filePath
    settings.save()


def new_tab():
    script_tab = ScriptTab()
    script_tab.create_new_tab()
    script_tab = add_script_to_editor("somefilename.py")
    if script_tab:
        add_script_tab_to_settings(script_tab)


def open_file():
    file_query = pm.fileDialog2(fileMode=4, fileFilter="*.py", dialogStyle=1)
    if not file_query:
        return

    path = file_query[0]

    script_tab = add_script_to_editor(path)
    if script_tab:
        add_script_tab_to_settings(script_tab)


def clear_script_output():
    pm.scriptEditorInfo(clearHistory=True)


def save_script_editor():
    pm.mel.syncExecuterBackupFiles()
    logging.info("Script Editor Saved")


def toggle_comment_selected_lines():
    tab = get_selected_tab()
    tabs_layout_children = pm.formLayout(tab.tab, q=True, ca=True)
    text_tab = tabs_layout_children[0]
    selected_text = pm.cmdScrollFieldExecuter(text_tab, q=True, selectedText=True)

    comment_lines = "#" not in selected_text.split("\n")[0]

    new_text_lines = []
    for line in selected_text.split("\n"):
        if comment_lines:
            newLine = "# {}".format(line)
        else:
            newLine = line.replace("# ", "")

        new_text_lines.append(newLine)

    new_text = "\n".join(new_text_lines)
    pm.cmdScrollFieldExecuter(text_tab, e=True, insertText=new_text)


def insert_pm_selected():
    tab = get_selected_tab()
    tabs_layout_children = pm.formLayout(tab.tab, q=True, ca=True)
    text_tab = tabs_layout_children[0]
    pm.cmdScrollFieldExecuter(text_tab, edit=True, insertText="pm.selected()[0]")


def backup_tree():
    settings = FileTreeSettings()
    script_folder = settings.data.get(FileTreeSettings.kFolders, {}).get(FileTreeSettings.kNetworkFolder, None)

    unique_time = str(int(time.time()))
    backup_directory_name = "ScriptTree_BACKUP_{}".format(unique_time)
    backup_directory_path = os.path.join(TREE_BACKUP_FOLDER, backup_directory_name)

    copy_directory(script_folder, backup_directory_path)

    logging.info("ScriptTree Network Folder Saved: {}".format(backup_directory_path))


def copy_directory(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)

        if "fb_pbr_preview" not in s:
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)


def print_arguments(*args):
    print("Args", args)


def do_nothing(*args):
    pass


def delete_current_tab():
    pm.mel.eval("removeCurrentExecuterTab;")


########################################################################################
# Launch methods
########################################################################################


def delete_workspace_control(control):
    try:  # This is here for pre-2017 maya versions
        if pm.workspaceControl(control, q=True, exists=True):
            scriptTreeWidth = pm.workspaceControl(control, q=True, width=True)
            pm.workspaceControl(control, e=True, close=True)
            pm.deleteUI(control, control=True)

            script_editor_win = get_script_editor_window()
            script_editor_win.setWidth(script_editor_win.getWidth() - scriptTreeWidth)

    except StandardError, e:
        pass


def get_script_editor_window():
    possible_windows = [win.window() for win in pm.lsUI(type="cmdScrollFieldReporter") if
                       "scriptEditorPanel1Window" in win.window()]
    if possible_windows:
        return possible_windows[0]
    return None


def set_dock_to_script_editor(state=True):
    pm.optionVar[stk.opVar_dockToScriptEditor] = state


def main(*args):
    """
    This is the ugliest function in the tool

    Lots of stuff to work around the maya docking procedures

    :param args:
    :return:
    """

    name = "ScriptTree"
    workspace_name = name + "WorkspaceControl"
    default_width = 355

    docking_enabled = pm.optionVar.get(stk.opVar_dockToScriptEditor, False)
    create_on_script_editor_startup = pm.optionVar.get(stk.opVar_CreateOnScriptEditorStart, False)

    window_exists = get_script_editor_window()
    if docking_enabled and not window_exists:
        pm.mel.ScriptEditor()

    delete_workspace_control(workspace_name)

    dockable_widget = ScriptTreeDockableWindow(name=name)

    if docking_enabled:

        script_editor_window = get_script_editor_window().asQtObject()
        before_dock_height = script_editor_window.height()

        if not pm.workspaceControl(workspace_name, query=True, exists=True):
            pm.workspaceControl(workspace_name, initialWidth=355)

        # Dock it to the script editor
        pm.workspaceControl(workspace_name, edit=True, dockToControl=["scriptEditorPanel1Window", "left"])

        try:
            workspace_qt_object = pm.ui.PyUI(workspace_name).asQtObject()
            object_splitter = workspace_qt_object.findChildren(QSplitter)[0]

            after_dock_width = script_editor_window.width()
            new_size = (after_dock_width + default_width - 90, before_dock_height)  # not sure why -90 but okay
            script_editor_window.resize(*new_size)

            object_splitter.moveSplitter(default_width, 1)
            object_splitter.setHandleWidth(10)

        except StandardError, e:
            logging.info("ScriptTree - Setting Width Error: {}".format(e))

    else:
        pm.workspaceControl(workspace_name, edit=True, floating=True)

    if create_on_script_editor_startup:
        # TODO set option to start with every script editor
        # pm.mel.eval("""global proc ScriptEditor(){if (`scriptedPanel -q -exists scriptEditorPanel1`) { scriptedPanel -e -tor scriptEditorPanel1; showWindow scriptEditorPanel1Window; selectCurrentExecuterControl; }else { CommandWindow; }; python("import atcore.atmaya.menu as mayaMenu;mayaMenu.runMenuCommand('main()', 'atextensions.dice.maya.ScriptTree.ScriptTree', 'python')");};""")
        pass

    return dockable_widget


if __name__ == "__main__":
    ui = main()
