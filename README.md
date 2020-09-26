# ScriptTree
A Qt FileTreeView of Maya scripts.

![script tree in action in maya](https://raw.githubusercontent.com/rBrenick/ScriptTree/master/docs/example_image.PNG)

The poor mans <a href="http://zurbrigg.com/charcoal-editor-2">Charcoal Editor.</a>
# Update

2020-09-26 - Rewrote the tool from scratch.
New features:
- Switch between Run Script and Edit Script on double click
- Search all scripts for specific string
- Better integration to maya's docking procedures
- Re-open recently closed tabs with "Ctrl+Shift+T"

# Install options

<pre>
Run installer.bat (will create a .mod file in your maya/modules folder)
Restart Maya
</pre>

Alternatively

<pre>
import sys
sys.path.append(r"UNZIP_FOLDER\script-tree")
</pre>


# Start the tool
<pre>

import script_tree
script_tree.main()

</pre>

If you work in a studio / with multiple people, I would recommend pointing the folder at a network path so it's easier to access scripts from any machine.

Special Thanks to Niels Vaes for adding some convenience stuff to this tool, and throwing me some good feature ideas.
