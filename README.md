# ScriptTree
Maya Qt file tree view of scripts

![script tree in action in maya](https://raw.githubusercontent.com/rBrenick/ScriptTree/master/docs/example_image.PNG)


# Install options

Run install_maya_mod.bat (will create a .mod file in your maya/modules folder)
Restart Maya


Alternatively

<pre>
import sys
sys.path.append(r"YOUR_GIT_FOLDER\ScriptTree\src\scripts")
</pre>


# Execute the command
<pre>
import ScriptTree.ScriptTree
ScriptTree.ScriptTree.main()
</pre>

