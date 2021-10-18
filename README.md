# Animation Retargeting Tool for Maya

 A tool for transferring animation data and mocap from a skeleton to a custom rig in Autodesk Maya.

Installation:
1. Add ***animation_retargeting_tool.py*** to your Maya scripts folder (Username\Documents\maya\scripts).
2. To start the tool within Maya, run these these lines of code from the Maya script editor or add them to a shelf button:

```python
import animation_retargeting_tool
animation_retargeting_tool.start()
```

Known bugs:
* The bake animation is a tad bit slow. Might have to replace the BakeResults command with something more robust.

![Image of tool](https://github.com/joaen/animation_retargeting_tool/blob/main/images/thumbnail.png?raw=true)
