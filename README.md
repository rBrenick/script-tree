# ScriptTree
A Qt FileTreeView of Maya scripts.

![script tree in action in maya](https://raw.githubusercontent.com/rBrenick/ScriptTree/master/docs/example_image.PNG)

The poor mans <a href="http://zurbrigg.com/charcoal-editor-2">Charcoal Editor.</a>
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

If you work in a studio / with multiple people, I would recommend pointing the folder at a network path so it's easier to access scripts from any machine.

Special Thanks to Niels Vaes for adding some convenience stuff to this tool, and throwing me some good feature ideas.
