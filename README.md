# Animation Retargeting Tool for Maya

A tool for transferring animation data between rigs or transfer raw mocap from a skeleton to a custom rig. (The script is compatible with Autodesk: Maya 2017 or later.)

## Installation:
1. Place ***animation_retargeting_tool.py*** and ***userSetup.mel*** in (Username/Documents/maya/version/scripts)
2. The next time you start Maya you will find "Animation Retargeting Tool" on the menu bar at the top.

## How to use:

* To create a connection select the joint with animation data and then select the controller it should drive and click 'Create Connection'.
* 'Create IK Connection' will create a separate rotation and translation controller which will help transfer the transform values from the joint to the rig controller more accurately.
* When you have created a connection for all the essential controllers of the rig you can click 'Bake Animation' to bake the animation from the skeleton to the rig and delete the connections.

## How to save rig connections:
1. Make sure that you have a rig and skeleton with connections.
2. Save the scene as a ma. file. This file will store all the connection nodes.

## How to load rig connections:
1. Open the ma. file where you saved your connections.
2. Click refresh to load the connection nodes into the list.

## How to load a new animation clip to the connected rig:
1. Open the ma. file where you saved your connections.
2. In the top menu of Maya click 'File' > 'Import...' and select a fbx. with animation or mocap.
3. Select FBX file type and to the right, scroll to the bottom and choose 'Update animation' under 'File content'.
4. The animation will be loaded on the skeleton without affecting the rig connections.

![](https://github.com/joaen/animation_retargeting_tool/blob/main/images/dino.gif)
