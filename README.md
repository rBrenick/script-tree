# ScriptTree
Maya Qt file tree view of scripts

![script tree in action in maya](https://raw.githubusercontent.com/rBrenick/ScriptTree/master/docs/example_image.PNG)


# Install options

<pre>
Run install_maya_mod.bat (will create a .mod file in your maya/modules folder)
Restart Maya
</pre>

Alternatively

<pre>
import sys
sys.path.append(r"LOCAL_FOLDER\ScriptTree\src\scripts")
</pre>


# Start the tool
<pre>

import ScriptTree.ScriptTree
ScriptTree.ScriptTree.set_dock_to_script_editor(True)  # Use this if you want to dock it directly to the script editor
ScriptTree.ScriptTree.main()

</pre>

