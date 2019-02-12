#!/usr/bin/python

# u_preview2_maya.py
#
# Nuno Pereira <nuno.pereira@unit.tv>
# Mike Bonnington <mike.bonnington@unit.tv>
# (c) 2014-2019
#
# Generate Maya playblasts for u-preview.


import maya.cmds as mc
import os
import time


# ----------------------------------------------------------------------------
# Main class
# ----------------------------------------------------------------------------

class Preview():

	def __init__(self, outputDir, outputFile, outputFormat, activeView, camera, 
				 res, frRange, offscreen, noSelect, guides, burnin, 
				 interruptible):
		self.playblastDir = outputDir
		self.outputFile = outputFile
		if outputFormat == "QuickTime":
			self.outputFormat = "qt"
			self.compression = "H.264"
			self.sound = self.getActiveAudioNode()
		elif outputFormat == "JPEG sequence":
			self.outputFormat = "image"
			self.compression = "jpg"
			self.sound = ""
		elif outputFormat == "TIFF sequence":
			self.outputFormat = "image"
			self.compression = "tif"
			self.sound = ""
		self.activeView = activeView
		self.camera = camera
		self.res = (int(res[0]), int(res[1]))
		self.frRange = (int(frRange[0]), int(frRange[1]))
		self.offscreen = offscreen
		self.noSelect = noSelect
		self.guides = guides
		self.burnin = burnin
		self.interruptible = interruptible


	def storeAttributes(self, obj, attrLs):
		""" Store the object's specified attribute values in a dictionary.
		"""
		storedAttrDic = {}
		for attr in attrLs:
			storedAttrDic[attr] = mc.getAttr('%s.%s' %(obj, attr))

		return storedAttrDic


	def retrieveAttributes(self, obj, storedAttrDic):
		""" Retrieve the stored attribute values in order to re-apply the
			settings.
		"""
		for attr, value in storedAttrDic.iteritems():
			try:
				mc.setAttr('%s.%s' %(obj, attr), value)
			except:
				mc.warning("Could not set attribute: %s.%s" %(obj, attr))


	def setAttributes(self, obj, attrLs, value):
		""" Set several attributes to the same value all at once.
		"""
		for attr in attrLs:
			try:
				mc.setAttr('%s.%s' %(obj, attr), value)
			except:
				mc.warning("Could not set attribute: %s.%s" %(obj, attr))


	# ------------------------------------------------------------------------
	# Burn-in / HUD

	def displayHUD(self, query=False, setValue=True):
		""" Show, hide or query the entire HUD.
		"""
		# currentPanel = mc.getPanel(withFocus=True)
		# panelType = mc.getPanel(typeOf=currentPanel)
		# if panelType == "modelPanel":
		# 	if query:
		# 		return mc.modelEditor(currentPanel, query=True, hud=True)
		# 	else:
		# 		mc.modelEditor(currentPanel, edit=True, hud=setValue)

		if query:
			return mc.modelEditor(self.activeView, query=True, hud=True)
		else:
			mc.modelEditor(self.activeView, edit=True, hud=setValue)


	def storeHUD(self):
		""" Store the current state of the HUD in a dictionary.
		"""
		hudLs = mc.headsUpDisplay(listHeadsUpDisplays=True)

		hudDic = {}
		for hud in hudLs:
			hudDic[hud] = mc.headsUpDisplay(hud, query=True, vis=True)

		return hudDic


	def showHUD(self, vis):
		""" Hide or show all HUD elements at once.
		"""
		hudLs = mc.headsUpDisplay(listHeadsUpDisplays=True)

		for hud in hudLs:
			mc.headsUpDisplay(hud, edit=True, vis=vis)


	def restoreHUD(self, hudDic):
		""" Restore the HUD from the state stored in the dictionary.
		"""
		hudLs = mc.headsUpDisplay(listHeadsUpDisplays=True)

		for hud, vis in hudDic.iteritems():
			mc.headsUpDisplay(hud, edit=True, vis=vis)


	# Header
	def hudHeader(self):
		return "UNIT"

	# Current project
	def hudJob(self):
		_job = os.environ['UHUB_JOB']  #JOB
		_shot = os.environ['UHUB_SHOTID']  #SHOT
		return '%s - %s' %(_job, _shot)

	# Maya scene name
	def hudScene(self):
		return os.path.split(mc.file(q=True, exn=True))[1]

	# Camera and lens info
	def hudCamera(self):
		#activeCamera = self.getActiveCamera(mc.getPanel(withFocus=True))
		activeCamera = self.camera
		cameraShape = [activeCamera]
		if mc.nodeType(activeCamera) != 'camera':
			cameraShape = mc.listRelatives(activeCamera, shapes=True)
		if mc.getAttr(cameraShape[0] + '.orthographic'):
			orthoWidth = mc.getAttr(cameraShape[0] + '.orthographicWidth')
			orthoWidth = round(orthoWidth, 2)
			camInfo = '%s (ortho %s)' %(activeCamera, orthoWidth)
		else:
			cameraLens = mc.getAttr(cameraShape[0] + '.focalLength')
			cameraLens = round(cameraLens, 2)
			camInfo = '%s (%s mm)' %(activeCamera, cameraLens)
		return camInfo

	# Date & time
	def hudTime(self):
		return time.strftime("%d/%m/%Y %H:%M")

	# Artist
	def hudArtist(self):
		return os.environ['USERNAME']  #IC_USERNAME

	# Current frame
	def hudFrame(self):
		return mc.currentTime(q=True)


	def showBurnin(self):
		""" Create custom elements and add them to the HUD.
			Names of all custom HUDs must begin with 'custom_hud'.
		"""
		# Hide all current HUD elements
		self.showHUD(0)

		# Delete pre-existing custom HUD elements
		self.hideBurnin()

		# Create custom HUD elements
		section = 0  # Top left
		mc.headsUpDisplay('custom_hud_job', 
		                  section=section, 
		                  block=mc.headsUpDisplay(nextFreeBlock=section), 
		                  blockSize='small', 
		                  command=lambda *args: self.hudJob(), 
		                  ev='playblasting', 
		                  dataFontSize='small')

		section = 3  # Top centre-right
		mc.headsUpDisplay('custom_hud_artist', 
		                  section=section, 
		                  block=mc.headsUpDisplay(nextFreeBlock=section), 
		                  blockSize='small', 
		                  command=lambda *args: self.hudArtist(), 
		                  ev='playblasting', 
		                  dataFontSize='small')

		section = 4  # Top right
		mc.headsUpDisplay('custom_hud_time', 
		                  section=section, 
		                  block=mc.headsUpDisplay(nextFreeBlock=section), 
		                  blockSize='small', 
		                  command=lambda *args: self.hudTime(), 
		                  ev='playblasting', 
		                  dataFontSize='small')

		section = 5  # Bottom left
		mc.headsUpDisplay('custom_hud_scene', 
		                  section=section, 
		                  block=mc.headsUpDisplay(nextFreeBlock=section), 
		                  blockSize='small', 
		                  #blockAlignment='right', 
		                  command=lambda *args: self.hudScene(), 
		                  ev='playblasting', 
		                  dataFontSize='small')

		section = 5  # Bottom left
		mc.headsUpDisplay('custom_hud_camera', 
		                  section=section, 
		                  block=mc.headsUpDisplay(nextFreeBlock=section), 
		                  blockSize='small', 
		                  #blockAlignment='right', 
		                  command=lambda *args: self.hudCamera(), 
		                  ev='playblasting', 
		                  dataFontSize='small')

		section = 8  # Bottom centre-right
		mc.headsUpDisplay('custom_hud_header', 
		                  section=section, 
		                  block=mc.headsUpDisplay(nextFreeBlock=section), 
		                  blockSize='small', 
		                  command=lambda *args: self.hudHeader(), 
		                  ev='playblasting', 
		                  dataFontSize='small')

		section = 9  # Bottom right
		mc.headsUpDisplay('custom_hud_frame', 
		                  section=section, 
		                  block=mc.headsUpDisplay(nextFreeBlock=section), 
		                  blockSize='small', 
		                  command=lambda *args: self.hudFrame(), 
		                  attachToRefresh = True, 
		                  dataFontSize='large')


	def hideBurnin(self):
		""" Remove the custom HUD elements.
		"""
		hudLs = mc.headsUpDisplay(listHeadsUpDisplays=True)

		for hud in hudLs:
			if hud.startswith('custom_hud'):
				if mc.headsUpDisplay(hud, exists=True):
					mc.headsUpDisplay(hud, remove=True)

	# End Burn-in / HUD
	# ------------------------------------------------------------------------


	def getActiveAudioNode(self):
		""" Gets active audio node from Maya's time slider control.
		"""
		import maya.mel as mel

		aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider')
		return mc.timeControl(aPlayBackSliderPython, q=True, sound=True)


	def playblast_(self):
		""" Sets playblast options and runs playblast.
		"""
		if not self.activeView:
			msg = "No active view selected. Please select a camera panel to playblast and try again."
			mc.warning(msg)
			return False, msg

		# Get current active panel camera
		try:
			activeCameraOrig = mc.modelPanel(self.activeView, cam=True, q=True)
		except:
			msg = "Panel '%s' not found. Please select a camera panel to playblast and try again." %self.activeView
			mc.warning(msg)
			return False, msg

		# Get active camera and shape
		activeCamera = self.camera
		if not activeCamera:
			msg = "Unable to generate playblast as no camera was specified."
			mc.warning(msg)
			return False, msg
		cameraShape = [activeCamera]
		if mc.nodeType(activeCamera) != 'camera':
			cameraShape = mc.listRelatives(activeCamera, shapes=True)

		# Disable undo
		mc.undoInfo(openChunk=True, chunkName='u_preview')
		# undoState = mc.undoInfo(q=True, state=True)
		# if undoState:
		# 	mc.undoInfo(state=False)

		# Look through camera if no active panel
		mc.lookThru(self.activeView, activeCamera)

		# Store current options
		displayOptions = self.storeAttributes(cameraShape[0], ['displayResolution', 'displayFieldChart', 'displaySafeAction', 'displaySafeTitle', 'displayFilmPivot', 'displayFilmOrigin', 'overscan', 'panZoomEnabled'])
		displayHUD = self.displayHUD(query=True)
		hudState = self.storeHUD()

		# Disable selection highlighting
		if self.noSelect:
			selectionHighlighting = mc.modelEditor(self.activeView, q=1, sel=1)
			mc.modelEditor(self.activeView, e=1, sel=False)

		# Display custom burn-in
		if self.burnin:
			self.displayHUD(setValue=True)
			self.showBurnin()
		else:
			self.displayHUD(setValue=False)

		# Display guides
		if self.guides:
			self.setAttributes(cameraShape[0], ['displayResolution', 'displaySafeAction', 'displaySafeTitle'], True)
		else:
			self.setAttributes(cameraShape[0], ['displayResolution', 'displayFieldChart', 'displaySafeAction', 'displaySafeTitle', 'displayFilmPivot', 'displayFilmOrigin'], False)

		# Set overscan value to 1.0 & disable 2D pan/zoom (unless render
		# pan/zoom is enabled)
		self.setAttributes(cameraShape[0], ['overscan'], 1.0)
		if mc.getAttr(cameraShape[0]+'.panZoomEnabled') and mc.getAttr(cameraShape[0]+'.renderPanZoom'):
			pass
		else:
			self.setAttributes(cameraShape[0], ['panZoomEnabled'], False)

		# Actually generate playblast!
		output = self.run_playblast()

		# Now reset things to their state prior to playblasting...
		# Hide custom burn-in
		if self.burnin:
			self.hideBurnin()

		# Restore selection highlighting
		if self.noSelect:
			mc.modelEditor(self.activeView, e=1, sel=selectionHighlighting)

		# Restore original settings
		self.retrieveAttributes(cameraShape[0], displayOptions)
		self.restoreHUD(hudState)
		self.displayHUD(setValue=displayHUD)

		# Restore camera panel
		mc.lookThru(self.activeView, activeCameraOrig)

		# Re-enable undo
		mc.undoInfo(closeChunk=True, chunkName='u_preview')
		# if undoState:
		# 	mc.undoInfo(state=True)

		# Return file output
		# print(output)
		if output:
			return "Completed", output
		# Return the output file path even if the playblast was interrupted.
		# In the playblast command's return value, Maya automatically adds the
		# extension for jpg, but not mov. We are replicating that behaviour
		# here.
		else:
			if self.interruptible:
				if self.outputFormat == 'image':
					output = os.path.join(self.playblastDir, '%s.#.%s' %(self.outputFile, self.compression))
				elif self.outputFormat == 'qt':
					output = os.path.join(self.playblastDir, self.outputFile)
				return "Interrupted", output
			else:  # Fail on interrupt
				return "Failed", "Playblast was interrupted."


	def run_playblast(self):
		""" Maya command to generate playblast.
		"""
		pb_args = {}
		pb_args['filename'] = '%s/%s' %(self.playblastDir, self.outputFile)
		pb_args['startTime'] = self.frRange[0]
		pb_args['endTime'] = self.frRange[1]
		pb_args['framePadding'] = 4
		pb_args['width'] = self.res[0]
		pb_args['height'] = self.res[1]
		pb_args['percent'] = 100
		pb_args['format'] = self.outputFormat
		pb_args['compression'] = self.compression
		if self.sound:
			pb_args['sound'] = self.sound
		pb_args['viewer'] = False
		pb_args['offScreen'] = self.offscreen
		pb_args['clearCache'] = True
		pb_args['showOrnaments'] = True
		pb_args['editorPanelName'] = self.activeView

		return mc.playblast(**pb_args)

# ----------------------------------------------------------------------------
# End of main class
# ----------------------------------------------------------------------------

