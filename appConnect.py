#!/usr/bin/python

# appConnect.py
#
# Nuno Pereira <nuno.pereira@unit.tv>
# Mike Bonnington <mike.bonnington@unit.tv>
# (c) 2014-2019
#
# App-specific functions for u-preview.


import os


# Detect environment and import approprate modules
try:
	import maya.cmds as mc
	#os.environ['UHUB_UPREVIEW_APPCONNECT'] = 'maya'
except ImportError:
	pass

try:
	import hou
	#os.environ['UHUB_UPREVIEW_APPCONNECT'] = 'houdini'
except ImportError:
	pass

try:
	import nuke
	import nukescripts
	#os.environ['UHUB_UPREVIEW_APPCONNECT'] = 'nuke'
except ImportError:
	pass


# ----------------------------------------------------------------------------
# Main class
# ----------------------------------------------------------------------------

#class connect(object):
class AppConnect(object):
	""" Connects u-preview to the relevant application and passes args to its
		internal preview API.
	"""
	def __init__(self, fileInput, format, activeView, camera, res, frRange, offscreen, noSelect, guides, burnin, interruptible):
	#def __init__(self, **kwargs):
		self.fileInput = fileInput
		self.outputFile = os.path.split(self.fileInput)[1]
		self.format = format
		self.activeView = activeView
		self.camera = camera
		self.hres = int(res[0])
		self.vres = int(res[1])
		self.frRange = frRange
		try:
			self.range = (int(self.frRange[0]), int(self.frRange[1]))
		except ValueError:
			pass
		self.offscreen = offscreen
		self.noSelect = noSelect
		self.guides = guides
		self.burnin = burnin
		self.interruptible = interruptible


	def appPreview(self):
		""" Detect environment & begin preview.
		"""
		#if os.environ['IC_ENV'] == 'MAYA':
		if os.environ['UHUB_UPREVIEW_APPCONNECT'] == 'maya':
			self.outputDir = os.path.join(os.environ['UHUB_MAYA_UPREVIEW_PATH'], self.fileInput)
			import u_preview2_maya
			previewSetup = u_preview2_maya.Preview(self.outputDir, 
			                                       self.outputFile, 
			                                       self.format, 
			                                       self.activeView, 
			                                       self.camera, 
			                                       (self.hres, self.vres), 
			                                       self.frRange, 
			                                       self.offscreen, 
			                                       self.noSelect, 
			                                       self.guides, 
			                                       self.burnin, 
			                                       self.interruptible)
			return previewSetup.playblast_()

# ----------------------------------------------------------------------------
# End of main class
# ----------------------------------------------------------------------------


def getScene(fullPath=False):
	""" Returns name of scene/script/project file.
		fullPath : returns full path to scene file.
	"""
	#if os.environ['IC_ENV'] == 'MAYA':
	if os.environ['UHUB_UPREVIEW_APPCONNECT'] == 'maya':
		scene = mc.file(q=True, sceneName=True)

		if fullPath:
			return scene
		else:
			sceneName = os.path.splitext(os.path.basename(scene))[0]

			if sceneName:
				return sceneName
			else:
				return "untitled"


def getCameras(renderableOnly=False):
	""" Returns list of cameras in the scene. Renderable cameras will be
		listed first.
	"""
	camera_list = []

	#if os.environ['IC_ENV'] == 'MAYA':
	if os.environ['UHUB_UPREVIEW_APPCONNECT'] == 'maya':
		# noSelectText = ""
		# camera_list = [noSelectText, ]
		#camera_list = []
		# cameras = mc.ls(cameras=True)
		persp_cameras = mc.listCameras(perspective=True)
		ortho_cameras = mc.listCameras(orthographic=True)
		cameras = persp_cameras+ortho_cameras
		for camera in cameras:
			if mc.getAttr(camera+'.renderable'):
				camera_list.insert(0, camera)
			elif renderableOnly == False:
				camera_list.append(camera)

	return camera_list


def getActiveCamera(panel):
	""" Returns camera for the specified panel.
	"""
	#if os.environ['IC_ENV'] == 'MAYA':
	if os.environ['UHUB_UPREVIEW_APPCONNECT'] == 'maya':
		try:
			camera = mc.modelPanel(panel, cam=True, q=True)
		except:
			camera = ""

		return camera


def getActiveView():
	""" Returns currently active panel. If panel has no camera attached,
		return False.
	"""
	#if os.environ['IC_ENV'] == 'MAYA':
	if os.environ['UHUB_UPREVIEW_APPCONNECT'] == 'maya':
		panel = mc.getPanel(withFocus=True)
		camera = getActiveCamera(panel)

		if camera is not "":
			return panel
		else:
			return False


def getResolution():
	""" Returns the current resolution of scene/script/project file as a
		tuple (integer, integer).
	"""
	#if os.environ['IC_ENV'] == 'MAYA':
	if os.environ['UHUB_UPREVIEW_APPCONNECT'] == 'maya':
		width = mc.getAttr("defaultResolution.w")
		height = mc.getAttr("defaultResolution.h")

		return width, height


def getFrameRange():
	""" Returns the frame range of scene/script/project file as a tuple
		(integer, integer).
	"""
	#if os.environ['IC_ENV'] == 'MAYA':
	if os.environ['UHUB_UPREVIEW_APPCONNECT'] == 'maya':
		start = int(mc.playbackOptions(min=True, q=True))
		end = int(mc.playbackOptions(max=True, q=True))

		return start, end


def getCurrentFrame():
	""" Returns the current frame of scene/script/project file as an integer.
	"""
	#if os.environ['IC_ENV'] == 'MAYA':
	if os.environ['UHUB_UPREVIEW_APPCONNECT'] == 'maya':
		frame = int(mc.currentTime(q=True))

		return frame

