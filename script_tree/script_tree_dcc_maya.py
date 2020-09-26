import logging
import os

import pymel.core as pm


def open_script(script_path):
    """
    This is pretty much a duplicate of scriptEditorPanel.mel - global proc loadFileInNewTab(),
    but that function doesn't accept a path argument so we need to rebuild the logic

    :param script_path:
    :return:
    """
    if pm.mel.selectExecuterTabByName(script_path):  # tab exists, switch to it
        reload_selected_tab()
        return

    script_ext = os.path.splitext(script_path)[-1].lower()

    # create tab
    if script_ext == ".py":
        pm.mel.buildNewExecuterTab(-1, "Python", "python", 0)
    elif script_ext == ".mel":
        pm.mel.buildNewExecuterTab(-1, "MEL", "mel", 0)

    tabs = pm.melGlobals["$gCommandExecuterTabs"]
    tabs_layout = pm.tabLayout(tabs, q=True, ca=True)

    # Select newly created tab
    tabs_len = pm.tabLayout(tabs, q=True, numberOfChildren=True)
    pm.tabLayout(tabs, e=True, selectTabIndex=tabs_len)
    tab = tabs_layout[-1]

    # add script contents
    cmd_exec = pm.formLayout(tab, q=True, ca=True)[0]
    pm.cmdScrollFieldExecuter(cmd_exec, e=True, loadFile=script_path)

    # print(pm.cmdScrollFieldExecuter(cmd_exec, q=True, filename=True))

    # rename tab
    pm.mel.eval('renameCurrentExecuterTab("{}", 0);'.format(script_path))

    # hookup signals
    hookup_tab_signals(cmd_exec)


def create_new_tab(default_script_content=""):
    """
    Create Tab and fill with content of default_script_content

    :param default_script_content:
    :return:
    """
    pm.mel.buildNewExecuterTab(-1, "Python", "python", 0)

    tabs = pm.melGlobals["$gCommandExecuterTabs"]
    tabs_layout = pm.tabLayout(tabs, q=True, ca=True)

    tabs_len = pm.tabLayout(tabs, q=True, numberOfChildren=True)
    pm.tabLayout(tabs, e=True, selectTabIndex=tabs_len)  # select newly created tab

    tab = tabs_layout[-1]
    cmd_exec = pm.formLayout(tab, q=True, ca=True)[0]

    pm.cmdScrollFieldExecuter(cmd_exec, e=True, text=default_script_content)


def get_selected_script_path():
    cmd_exec = get_selected_cmd_executer()
    return pm.cmdScrollFieldExecuter(cmd_exec, q=True, filename=True)


def save_selected_tab(script_path=None):
    if script_path is None:
        script_path = get_selected_script_path()

    cmd_exec = get_selected_cmd_executer()

    pm.cmdScrollFieldExecuter(cmd_exec, edit=True, saveFile=script_path)

    pm.mel.eval('renameCurrentExecuterTab("{}", 0);'.format(script_path))
    hookup_tab_signals(cmd_exec)

    logging.info("Saved: {}".format(script_path))


def reload_selected_tab():
    cmd_exec = get_selected_cmd_executer()
    script_path = pm.cmdScrollFieldExecuter(cmd_exec, q=True, filename=True)
    pm.cmdScrollFieldExecuter(cmd_exec, e=True, loadFile=script_path)


def delete_selected_tab():
    pm.mel.eval("removeCurrentExecuterTab;")


def insert_pm_selected():
    cmd_exec = get_selected_cmd_executer()
    pm.cmdScrollFieldExecuter(cmd_exec, edit=True, insertText="pm.selected()[0]")


def toggle_comment_selected_lines():
    cmd_exec = get_selected_cmd_executer()
    selected_text = pm.cmdScrollFieldExecuter(cmd_exec, q=True, selectedText=True)

    comment_lines = "#" not in selected_text.split("\n")[0]

    new_text_lines = []
    for line in selected_text.split("\n"):
        if comment_lines:
            new_line = "# {}".format(line)
        else:
            new_line = line.replace("# ", "")

        new_text_lines.append(new_line)

    new_text = "\n".join(new_text_lines)
    pm.cmdScrollFieldExecuter(cmd_exec, e=True, insertText=new_text)


def get_selected_script_text():
    cmd_exec = get_selected_cmd_executer()
    return pm.cmdScrollFieldExecuter(cmd_exec, q=True, selectedText=True)


def clear_script_output():
    pm.scriptEditorInfo(clearHistory=True)


def save_script_editor():
    pm.mel.syncExecuterBackupFiles()
    logging.info("Script Editor Saved")


def get_selected_cmd_executer():
    tab_layout = pm.ui.TabLayout(pm.melGlobals["$gCommandExecuterTabs"])
    return pm.formLayout(tab_layout.getSelectTab(), q=True, ca=True)[0]


def hookup_tab_signals(cmd_exec):
    pm.cmdScrollFieldExecuter(cmd_exec, e=True,
                              modificationChangedCommand=lambda x: pm.mel.executerTabModificationChanged(x))
    pm.cmdScrollFieldExecuter(cmd_exec, e=True, fileChangedCommand=lambda x: pm.mel.executerTabFileChanged(x))


def open_search_dialog():
    pm.mel.createSearchAndReplaceWindow()
    # Just creating the window isn't properly bringing it too focus, so I add this line to make sure it shows
    pm.showWindow("commandSearchAndReplaceWnd")


def eval_deferred(*args, **kwargs):
    pm.evalDeferred(*args, **kwargs)


def add_to_repeat_commands(exec_command):
    pm.repeatLast(ac=exec_command)
