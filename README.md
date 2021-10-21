# Animation Retargeting Tool for Maya

A tool for transfer animation data between rigs or transfer raw mocap from a skeleton to a custom rig.

## Installation:
1. Add ***animation_retargeting_tool.py*** to your Maya scripts folder (Username\Documents\maya\scripts).
2. To start the tool within Maya, run these these lines of code from the Maya script editor or add them to a shelf button:

```python
import animation_retargeting_tool
animation_retargeting_tool.start()
```

## How to save rig connections:
1. Make sure that you have a rig and skeleton with connections.
2. Save the scene as a ma. file. This file will store all the connection nodes.

## How to load rig connections:
1. Open the ma. file where you saved your connections.
2. Click refresh to load the connection nodes into the list.

## How to load a new animation clip to the connected rig:
1. Open the ma. file where you saved your connections.
1. In the top menu of Maya click 'File' > 'Import...' and select a fbx. with animation or mocap.
2. The animation will be loaded on the skeleton without affecting the rig connections.

![](https://github.com/joaen/animation_retargeting_tool/blob/main/images/load_fbx.gif)

## Known bugs:
* The bake animation command is a bit slow.
* ~~The script is not compatible with Maya 2022 at the moment.~~
