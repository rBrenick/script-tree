def main(*args, **kwargs):
    from . import script_tree_ui_new
    return script_tree_ui_new.main(*args, **kwargs)


def reload_module():
    import sys
    if sys.version_info[0] >= 3:
        from importlib import reload
    else:
        from imp import reload

    from . import ui_utils
    from . import script_tree_utils
    from . import script_tree_dcc_maya
    from . import script_tree_ui_new

    # Remove all shortcuts from the cache so we can reload and let them go
    for shortcut in script_tree_utils.GlobalCache.shortcuts:
        shortcut.setEnabled(0)
        del shortcut

    reload(ui_utils)
    reload(script_tree_utils)
    reload(script_tree_dcc_maya)
    reload(script_tree_ui_new)
