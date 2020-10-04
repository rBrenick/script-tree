import logging
import os

def open_script(script_path):
    """
    This is pretty much a duplicate of scriptEditorPanel.mel - global proc loadFileInNewTab(),
    but that function doesn't accept a path argument so we need to rebuild the logic

    :param script_path:
    :return:
    """
    pass


def create_new_tab(default_script_content=""):
    """
    Create Tab and fill with content of default_script_content

    :param default_script_content:
    :return:
    """
    pass

def get_selected_script_path():
    cmd_exec = get_selected_cmd_executer()
    return


def save_selected_tab(script_path=None):
    if script_path is None:
        script_path = get_selected_script_path()

    pass

def reload_selected_tab():
    cmd_exec = get_selected_cmd_executer()
    pass

def delete_selected_tab():
    pass

def insert_pm_selected():
    cmd_exec = get_selected_cmd_executer()
    pass

def toggle_comment_selected_lines():
    cmd_exec = get_selected_cmd_executer()
    pass

def get_selected_script_text():
    cmd_exec = get_selected_cmd_executer()
    pass

def clear_script_output():
    pass

def save_script_editor():
    pass

def get_selected_cmd_executer():
    pass

def hookup_tab_signals(cmd_exec):
    pass

def open_search_dialog():
    pass

def eval_deferred(*args, **kwargs):
    pass

def add_to_repeat_commands(exec_command):
    pass
