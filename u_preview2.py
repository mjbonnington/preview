#!/usr/bin/python

# u_preview2.py
#
# Nuno Pereira <nuno.pereira@unit.tv>
# Mike Bonnington <mike.bonnington@unit.tv>
# (c) 2014-2019
#
# A generic UI for previewing animations, replaces Maya's playblast interface.
# TODO: Add Nuke/Houdini support.


import os
import re
import subprocess
import sys

from Qt import QtCore, QtGui, QtWidgets  # u_shared.Qt
import ui_template as UI

# Import custom modules
import appConnect
#import verbose
from u_vfx.u_publish.u_daily import dailyFromApp
from u_vfx.core import Launch


# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

cfg = {}

# Set window title and object names
cfg['WINDOW_TITLE'] = "u-preview"
cfg['WINDOW_OBJECT'] = "uPreviewUI"
cfg['VENDOR'] = "UNIT"

# Set the UI and the stylesheet
cfg['UI_FILE'] = "u_preview2.ui"
cfg['STYLESHEET'] = "u_preview2.qss"  # Set to None to use the parent app's stylesheet

# Other options
cfg['PREFS_FILE'] = os.path.join(os.environ['UHUB_USER_PREFS_LOCAL_PATH'], 'u_preview2.json')
cfg['STORE_WINDOW_GEOMETRY'] = True
cfg['DOCK_WITH_MAYA_UI'] = False
cfg['DOCK_WITH_NUKE_UI'] = False


# ----------------------------------------------------------------------------
# Main window class
# ----------------------------------------------------------------------------

class PreviewUI(QtWidgets.QMainWindow, UI.TemplateUI):
	""" u-preview UI.
	"""
	def __init__(self, parent=None):
		super(PreviewUI, self).__init__(parent)
		self.parent = parent

		#self.setupUI(**cfg)
		self.setupUI(window_object=cfg['WINDOW_OBJECT'], 
		             window_title=cfg['WINDOW_TITLE'], 
		             ui_file=cfg['UI_FILE'], 
		             stylesheet=cfg['STYLESHEET'], 
		             prefs_file=cfg['PREFS_FILE'], 
		             store_window_geometry=cfg['STORE_WINDOW_GEOMETRY'])

		self.conformFormLayoutLabels(self.ui.centralwidget)

		# Set window flags
		self.setWindowFlags(QtCore.Qt.Tool)

		# Set other Qt attributes
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

		# Connect signals & slots
		self.ui.name_lineEdit.textChanged.connect(self.checkFilename)
		#self.ui.nameUpdate_toolButton.clicked.connect(self.updateFilename)
		self.ui.format_comboBox.currentIndexChanged.connect(self.setCreateDaily)
		self.ui.camera_radioButton.toggled.connect(self.updateCameras)
		self.ui.resolution_comboBox.currentIndexChanged.connect(self.updateResGrp)
		self.ui.x_spinBox.valueChanged.connect(self.storeRes)
		self.ui.y_spinBox.valueChanged.connect(self.storeRes)
		self.ui.range_comboBox.currentIndexChanged.connect(self.updateRangeGrp)
		self.ui.start_spinBox.valueChanged.connect(self.storeRangeStart)
		self.ui.end_spinBox.valueChanged.connect(self.storeRangeEnd)
		self.ui.preview_pushButton.clicked.connect(self.preview)

		# Context menus
		self.addContextMenu(self.ui.nameUpdate_toolButton, "Reset to default", self.updateFilename)
		self.addContextMenu(self.ui.nameUpdate_toolButton, "Insert scene name token <Scene>", lambda: self.insertFilenameToken("<Scene>"))
		self.addContextMenu(self.ui.nameUpdate_toolButton, "Insert camera name token <Camera>", lambda: self.insertFilenameToken("<Camera>"))

		# Set SVG icons
		#self.ui.nameUpdate_toolButton.setIcon(self.setSVGIcon('configure'))

		# Set input validators
		alphanumeric_validator = QtGui.QRegExpValidator(QtCore.QRegExp(r'[\w<>]+'), self.ui.name_lineEdit) #r'[\w\.-]+'
		self.ui.name_lineEdit.setValidator(alphanumeric_validator)


	def display(self):
		""" Initialise UI and set options to stored values if possible.
		"""
		self.returnValue = False

		self.initSettings()

		self.show()
		self.raise_()

		return self.returnValue


	def initSettings(self):
		""" Initialise settings.
		"""
		self.activeView = self.xd.getValue('preview', 'activeview') #None
		# self.ui.activeView_lineEdit.hide()
		self.ui.message_plainTextEdit.hide()
		self.setFixedHeight(self.minimumSizeHint().height())

		if not self.ui.name_lineEdit.text():
			self.updateFilename()
		# self.updateCameras()
		self.updateResGrp()
		self.updateRangeGrp()
		self.checkFilename()


	def updateFilename(self):
		""" Update filename field.
		"""
		# Add camera token only if multiple renderable cameras found
		if len(appConnect.getCameras(renderableOnly=True)) > 1:
			filename = "<Scene>_<Camera>"
		else:
			filename = "<Scene>"
		self.ui.name_lineEdit.setText(filename)


	def insertFilenameToken(self, token):
		""" Insert token into filename field.
		"""
		self.ui.name_lineEdit.insert(token)


	def setCreateDaily(self):
		""" Disable dailies creation if format is set to QuickTime movie.
		"""
		if self.sender().currentText() == "QuickTime":
			#self.createDailyTemp = self.createDaily
			self.ui.createDaily_checkBox.setCheckState(QtCore.Qt.Unchecked)
			self.ui.createDaily_checkBox.setEnabled(False)
		else:
			self.ui.createDaily_checkBox.setEnabled(True)


	def updateCameras(self):
		""" Update active view and camera combo box.
		"""
		activeView = appConnect.getActiveView()
		if activeView:  # Only update active view if it has a camera attached
			self.activeView = activeView
			self.storeValue('preview', 'activeview', self.activeView)
			#verbose.print_("Active view set to %s" %self.activeView)
			print("Active view set to %s" %self.activeView)
			# self.ui.activeView_lineEdit.setText(activeView)
		else:
			#verbose.warning("Using active view %s" %self.activeView)
			print("Using active view %s" %self.activeView)

		self.populateComboBox(self.ui.camera_comboBox, appConnect.getCameras())


	def updateResGrp(self):
		""" Update resolution group UI based on combo box selection.
		"""
		# Stop the other widgets from emitting signals
		self.ui.x_spinBox.blockSignals(True)
		self.ui.y_spinBox.blockSignals(True)

		# Store current values
		res = self.ui.x_spinBox.value(), self.ui.y_spinBox.value()
		resMode = self.ui.resolution_comboBox.currentText()

		# Set resolution appropriately
		if resMode == "Custom":
			self.ui.x_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
			self.ui.y_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
			self.ui.x_spinBox.setEnabled(True) #setReadOnly(False)
			self.ui.y_spinBox.setEnabled(True) #setReadOnly(False)
			self.ui.resSep_label.setEnabled(True)

			# Read values from user settings
			value = self.xd.getValue('preview', 'customresolution')
			if value is not None:
				try:
					res = value.split('x')
					res = int(res[0]), int(res[1])
				except:
					res = value
		else:
			self.ui.x_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
			self.ui.y_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
			self.ui.x_spinBox.setEnabled(False) #setReadOnly(True)
			self.ui.y_spinBox.setEnabled(False) #setReadOnly(True)
			self.ui.resSep_label.setEnabled(False)

			if resMode == "Shot default":
				res = int(os.environ['UHUB_RESOLUTIONX']), int(os.environ['UHUB_RESOLUTIONY'])
			elif resMode == "Proxy":
				try:
					proxy_scale = float(os.environ['UHUB_PROXY_SCALE'])
				except:
					proxy_scale = 0.5
				resX = float(os.environ['UHUB_RESOLUTIONX']) * proxy_scale
				resY = float(os.environ['UHUB_RESOLUTIONY']) * proxy_scale
				res = int(resX), int(resY)
				#res = int(os.environ['PROXY_RESOLUTIONX']), int(os.environ['PROXY_RESOLUTIONY'])
			elif resMode == "Render settings":
				res = appConnect.getResolution()
			else:
				resOrig = appConnect.getResolution()
				resMult = float(self.ui.resolution_comboBox.currentText().replace('%', '')) / 100.0
				res = int((float(resOrig[0])*resMult)), int((float(resOrig[1])*resMult))

		# Update widgets
		self.ui.x_spinBox.setValue(res[0])
		self.ui.y_spinBox.setValue(res[1])

		# Re-enable signals
		self.ui.x_spinBox.blockSignals(False)
		self.ui.y_spinBox.blockSignals(False)


	def updateRangeGrp(self):
		""" Update frame range group UI based on combo box selection.
		"""
		# Stop the other widgets from emitting signals
		self.ui.start_spinBox.blockSignals(True)
		self.ui.end_spinBox.blockSignals(True)

		# Store current values
		frRange = self.ui.start_spinBox.value(), self.ui.end_spinBox.value()
		rangeMode = self.ui.range_comboBox.currentText()

		# Set frame range appropriately
		if rangeMode == "Custom":
			self.ui.start_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
			self.ui.end_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
			self.ui.start_spinBox.setEnabled(True) #setReadOnly(False)
			self.ui.end_spinBox.setEnabled(True) #setReadOnly(False)
			self.ui.rangeSep_label.setEnabled(True)

			# Read values from user settings
			value = self.xd.getValue('preview', 'customframerange')
			if value is not None:
				try:
					frRange = value.split('-')
					frRange = int(frRange[0]), int(frRange[1])
				except:
					frRange = value
		else:
			self.ui.start_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
			self.ui.end_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
			self.ui.start_spinBox.setEnabled(False) #setReadOnly(True)
			self.ui.end_spinBox.setEnabled(False) #setReadOnly(True)
			self.ui.rangeSep_label.setEnabled(False)
			self.ui.start_spinBox.setMaximum(9999)
			self.ui.end_spinBox.setMinimum(0)

			if rangeMode == "Shot default":
				frRange = int(os.environ['UHUB_STARTFRAME']), int(os.environ['UHUB_ENDFRAME'])
			elif rangeMode == "Timeline":
				frRange = appConnect.getFrameRange()
			elif rangeMode == "Current frame only":
				frame = appConnect.getCurrentFrame()
				frRange = frame, frame

		# Update widgets
		self.ui.start_spinBox.setValue(frRange[0])
		self.ui.end_spinBox.setValue(frRange[1])

		# Re-enable signals
		self.ui.start_spinBox.blockSignals(False)
		self.ui.end_spinBox.blockSignals(False)


	# @QtCore.Slot()
	def checkFilename(self):
		""" Check custom output filename and adjust UI appropriately.
		"""
		filename = self.ui.name_lineEdit.text()
		camera = self.getCurrentCamera()

		# Replace tokens and remove invalid characters...
		#filename = filename.replace('<Scene>', self.sanitize(appConnect.getScene(), pattern=r"[^\w]", replace="_"))
		filename = filename.replace('<Scene>', appConnect.getScene())
		filename = filename.replace('<Camera>', camera)

		#if filename and filename == self.sanitize(filename): # and camera:
		if filename:
			#verbose.print_("Filename preview: '%s'" %filename)
			print("Filename preview: '%s'" %filename)
			self.ui.preview_pushButton.setEnabled(True)
			self.ui.message_plainTextEdit.hide()
			self.setFixedHeight(self.minimumSizeHint().height())
			return filename
		else:
			msg = "Invalid output name."
			#verbose.warning(msg)
			self.ui.preview_pushButton.setEnabled(False)
			self.ui.message_plainTextEdit.setPlainText(msg)
			self.ui.message_plainTextEdit.show()
			self.setFixedHeight(self.minimumSizeHint().height())
			return False


	# @QtCore.Slot()
	def storeRes(self):
		""" Store custom resolution in user prefs.
		"""
		#res = "%dx%d" %(self.ui.x_spinBox.value(), self.ui.y_spinBox.value())
		res = [self.ui.x_spinBox.value(), self.ui.y_spinBox.value()]
		self.storeValue('preview', 'customresolution', res)


	# @QtCore.Slot()
	def storeRangeStart(self):
		""" Store custom frame range in user prefs.
		"""
		rangeStart = self.ui.start_spinBox.value()
		rangeEnd = self.ui.end_spinBox.value()

		# Stop the other widgets from emitting signals
		self.ui.end_spinBox.blockSignals(True)

		# Update widgets
		self.ui.end_spinBox.setMinimum(rangeStart)
		if rangeStart >= rangeEnd:
			self.ui.end_spinBox.setValue(rangeStart)

		# Re-enable signals
		self.ui.end_spinBox.blockSignals(False)

		#frRange = "%d-%d" %(self.ui.start_spinBox.value(), self.ui.end_spinBox.value())
		frRange = [self.ui.start_spinBox.value(), self.ui.end_spinBox.value()]
		self.storeValue('preview', 'customframerange', frRange)


	# @QtCore.Slot()
	def storeRangeEnd(self):
		""" Store custom frame range in user prefs.
		"""
		rangeStart = self.ui.start_spinBox.value()
		rangeEnd = self.ui.end_spinBox.value()
		#frRange = "%d-%d" %(self.ui.start_spinBox.value(), self.ui.end_spinBox.value())
		frRange = [self.ui.start_spinBox.value(), self.ui.end_spinBox.value()]
		self.storeValue('preview', 'customframerange', frRange)


	def getCurrentCamera(self):
		""" Get the current camera to playblast from.
		"""
		self.updateCameras()
		if self.ui.camera_radioButton.isChecked():
			return self.ui.camera_comboBox.currentText()
		else:
			#print(self.activeView)
			return appConnect.getActiveCamera(self.activeView)


	def getOpts(self):
		""" Get UI options before generating playblast.
		"""
		try:
			# Get file name output string
			self.fileInput = self.checkFilename() #self.ui.name_lineEdit.text()

			# Get file format
			self.format = self.ui.format_comboBox.currentText()

			# Get camera
			# self.updateCameras()
			# self.activeView = self.ui.activeView_lineEdit.text()
			self.camera = self.getCurrentCamera()

			# Get frame range and resolution
			self.updateRangeGrp()
			self.res = self.ui.x_spinBox.value(), self.ui.y_spinBox.value()
			self.frRange = self.ui.start_spinBox.value(), self.ui.end_spinBox.value()

			# Get option values from checkboxes
			self.offscreen = self.getCheckBoxValue(self.ui.offscreen_checkBox)
			self.noSelect = self.getCheckBoxValue(self.ui.noSelection_checkBox)
			self.guides = self.getCheckBoxValue(self.ui.guides_checkBox)
			self.burnin = self.getCheckBoxValue(self.ui.burnin_checkBox)
			self.viewer = self.getCheckBoxValue(self.ui.launchViewer_checkBox)
			self.createDaily = self.getCheckBoxValue(self.ui.createDaily_checkBox)
			self.interruptible = True
			# self.interruptible = self.getCheckBoxValue(self.ui.interruptible_checkBox)

			return True

		except:
			return False


	def preview(self, showUI=True):
		""" Get options, pass information to appConnect and save options once
			appConnect is done.
		"""
		if self.getOpts():
			# Minimise window if rendering offscreen
			if not self.offscreen and showUI:
				self.showMinimized()

			previewSetup = appConnect.AppConnect(fileInput=self.fileInput, 
			                                     format=self.format, 
			                                     activeView=self.activeView, 
			                                     camera=self.camera, 
			                                     res=self.res, 
			                                     frRange=self.frRange, 
			                                     offscreen=self.offscreen, 
			                                     noSelect=self.noSelect, 
			                                     guides=self.guides, 
			                                     burnin=self.burnin, 
			                                     interruptible=self.interruptible)
			previewOutput = previewSetup.appPreview()
			if previewOutput[0] == "Completed":  # Playblast completed without interruption
				# print(previewOutput[1])
				outputFilePath = previewOutput[1]
				if self.viewer:
					self.launchViewer(outputFilePath)
				if self.createDaily:
					self.makeDaily(outputFilePath)
				self.ui.message_plainTextEdit.hide()
				self.setFixedHeight(self.minimumSizeHint().height())
			elif previewOutput[0] == "Interrupted":  # Playblast interrupted
				# print(previewOutput[1])
				outputFilePath = previewOutput[1]
				if self.viewer:
					self.launchViewer(outputFilePath)
				self.ui.message_plainTextEdit.hide()
				self.setFixedHeight(self.minimumSizeHint().height())
			else:  # Playblast failed
				self.ui.message_plainTextEdit.setPlainText(previewOutput[1])
				self.ui.message_plainTextEdit.show()
				self.setFixedHeight(self.minimumSizeHint().height())

			# Restore window
			if not self.offscreen and showUI:
				self.showNormal()

		self.save()  # Save settings


	def launchViewer(self, outputFilePath):
		""" Launch viewer.
		"""
		if self.format == "QuickTime":
			outputFilePath += ".mov"

		Launch.djvView(outputFilePath)


	def makeDaily(self, outputFilePath):
		""" Create daily from playblast.
		"""
		if self.format == "QuickTime":
			print("Warning: Cannot create dailies from QuickTime movies.")
			return False
		else:
			# Quick hack to replace frame number padding with first frame
			outputFilePath = outputFilePath.replace(
				"####", 
				os.environ['UHUB_STARTFRAME'])
			dailyFromApp.makeDaily(
				app=os.environ['UHUB_UPREVIEW_APPCONNECT'], 
				outputFile=outputFilePath, 
				sourceFile=appConnect.getScene(fullPath=True))
			return True


	def sanitize(instr, pattern=r'\W', replace=''):
		""" Sanitizes characters in string. Default removes all non-
			alphanumeric characters.
		"""
		return re.sub(pattern, replace, instr)


	def closeEvent(self, event):
		""" Event handler for when window is closed.
		"""
		self.save()  # Save settings
		self.storeWindow()  # Store window geometry

# ----------------------------------------------------------------------------
# End of main window class
# ============================================================================
# Run functions - MOVE TO TEMPLATE MODULE?
# ----------------------------------------------------------------------------

def run_maya(showUI=True):
	""" Run in Maya.
	"""
	os.environ['UHUB_UPREVIEW_APPCONNECT'] = 'maya'  # Temporary fudge

	UI._maya_delete_ui(cfg['WINDOW_OBJECT'], cfg['WINDOW_TITLE'])  # Delete any already existing UI
	previewApp = PreviewUI(parent=UI._maya_main_window())

	if showUI:  # Show the UI
		previewApp.display()
	else:  # Run playblast without displaying the UI
		previewApp.initSettings()
		previewApp.preview(showUI=showUI)
		# previewApp.hide()

	# if not cfg['DOCK_WITH_MAYA_UI']:
	# 	previewApp.display(**kwargs)  # Show the UI
	# elif cfg['DOCK_WITH_MAYA_UI']:
	# 	allowed_areas = ['right', 'left']
	# 	mc.dockControl(cfg['WINDOW_TITLE'], label=cfg['WINDOW_TITLE'], area='left', 
	# 	               content=cfg['WINDOW_OBJECT'], allowedArea=allowed_areas)


# def run_nuke(**kwargs):
# 	""" Run in Nuke. NOT YET IMPLEMENTED

# 		Note:
# 			If you want the UI to always stay on top, replace:
# 			`previewApp.ui.setWindowFlags(QtCore.Qt.Tool)`
# 			with:
# 			`previewApp.ui.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)`

# 			If you want the UI to be modal:
# 			`previewApp.ui.setWindowModality(QtCore.Qt.WindowModal)`
# 	"""
# 	UI._nuke_delete_ui(cfg['WINDOW_OBJECT'], cfg['WINDOW_TITLE'])  # Delete any already existing UI

# 	if not cfg['DOCK_WITH_NUKE_UI']:
# 		previewApp = PreviewUI(parent=UI._nuke_main_window())
# 		previewApp.setWindowFlags(QtCore.Qt.Tool)
# 		previewApp.display(**kwargs)  # Show the UI
# 	elif cfg['DOCK_WITH_NUKE_UI']:
# 		prefix = ''
# 		basename = os.path.basename(__file__)
# 		module_name = basename[: basename.rfind('.')]
# 		if __name__ == module_name:
# 			prefix = module_name + '.'
# 		panel = nukescripts.panels.registerWidgetAsPanel(
# 			widget=prefix + cfg['WINDOW_TITLE'],  # module_name.Class_name
# 			name=cfg['WINDOW_TITLE'],
# 			id='uk.co.thefoundry.' + cfg['WINDOW_TITLE'],
# 			create=True)
# 		pane = nuke.getPaneFor('Properties.1')
# 		panel.addToPane(pane)
# 		previewApp = panel.customKnob.getObject().widget
# 		UI._nuke_set_zero_margins(previewApp)


# # Detect environment and run application
# if os.environ['IC_ENV'] == 'STANDALONE':
# 	verbose.print_(%cfg['WINDOW_TITLE'])
# elif os.environ['IC_ENV'] == 'MAYA':
# 	import maya.cmds as mc
# 	verbose.print_("%s for Maya" %cfg['WINDOW_TITLE'])
# 	# run_maya()
# elif os.environ['IC_ENV'] == 'NUKE':
# 	import nuke
# 	import nukescripts
# 	verbose.print_("%s for Nuke" %cfg['WINDOW_TITLE'])
# 	# run_nuke()
# # elif __name__ == '__main__':
# # 	run_standalone()

