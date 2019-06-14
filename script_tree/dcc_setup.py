
def startup():
    from maya import cmds
    if cmds.optionVar(q="ScriptTree_CreateOnScriptEditorStart"):
        # put script tree startup stuff here
        pass
        
        # cmds.evalDeferred("import script_tree.script_tree_ui; script_tree.script_tree_ui.startup()")
    
