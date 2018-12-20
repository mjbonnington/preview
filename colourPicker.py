#!/usr/bin/python

# Colour Picker
# v0.1
#
# Mike Bonnington <mjbonnington@gmail.com>
# (c) 2017-2018
#
# Maya Colour picker dialog.


import maya.cmds as mc


class ColourPicker():

	def __init__(self):
		self.winTitle = "Colour Picker"
		self.winName = "ColourPicker"


	def UI(self, index=None):
		""" Create UI.
		"""
		if index is None:
			self.index = mc.displayColor('headsUpDisplayLabels', q=1) + 1
			# mc.displayColor('headsUpDisplayValues', query=True)
		else:
			self.index = index

		# Check if UI window already exists
		if mc.window(self.winName, exists=True):
			mc.deleteUI(self.winName)

		# Create window
		mc.window(self.winName, title=self.winTitle, sizeable=True, menuBar=True, menuBarVisible=True)

		# Create menu bar
		# mc.menu(label="Edit", tearOff=False)
		# mc.menuItem(label="Reset Settings", command="")
		# mc.menu(label="Help", tearOff=False)
		# mc.menuItem(label="About...", command=lambda *args: self.aboutUI())

		# Create controls
		#setUITemplate -pushTemplate mjbToolsTemplate;
		mc.columnLayout("windowRoot")
		self.colourPickerUI("indexColourRollout", "windowRoot")

		mc.separator(height=8, style="none")
		mc.rowLayout(numberOfColumns=2)
		mc.button(width=198, height=28, label="Apply", command=lambda *args: self.applyColourAndClose())
		mc.button(width=198, height=28, label="Close", command=lambda *args: mc.deleteUI(self.winName))
		#setUITemplate -popTemplate;

		mc.showWindow(self.winName)
		return self.index


	def colourPickerUI(self, name, parent, collapse=False):
		"""
		"""
		mc.frameLayout(width=400, collapsable=True, cl=collapse, borderStyle="etchedIn", label="Index")
		mc.columnLayout(name)

		mc.separator(height=4, style="none")
		columns = 16; rows = 2
		cellWidth = 25; cellHeight = 25
		# mc.palettePort(dimensions=(columns, rows), 
		#                width=cellWidth*columns, 
		#                height=cellHeight*rows)
		# mc.colorSliderGrp("colour", label="Colour: ", rgb=(0, 0, 0))
		mc.colorIndexSliderGrp("colour", label="Colour: ", 
		                       min=2, max=32, value=self.index, 
		                       forceDragRefresh=True, 
		                       changeCommand=lambda *args: self.applyColour())
		mc.setParent(name)

		mc.separator(height=8, style="none")
		mc.setParent(parent)


	def applyColour(self):
		""" Return selected colour.
		"""
		self.index = mc.colorIndexSliderGrp("colour", q=1, value=True) - 1
		print(self.index)
		mc.displayColor('headsUpDisplayLabels', self.index, dormant=True)
		mc.displayColor('headsUpDisplayValues', self.index, dormant=True)


	def applyColourAndClose(self):
		""" Return selected colour.
		"""
		self.applyColour()
		mc.deleteUI(self.winName)


	# def setColour(self, obj):
	# 	""" Set object colour.
	# 	"""
	# 	# Get options
	# 	col = mc.colorSliderGrp("colour", q=1, rgb=True)
	# 	setOutlinerColour = mc.checkBox("setOutliner", q=1, value=True)

	# 	mc.setAttr(obj+".useObjectColor", 2)  # RGB
	# 	mc.setAttr(obj+".objectColorR", col[0])
	# 	mc.setAttr(obj+".objectColorG", col[1])
	# 	mc.setAttr(obj+".objectColorB", col[2])

	# 	mc.setAttr(obj+".wireColorR", col[0])
	# 	mc.setAttr(obj+".wireColorG", col[1])
	# 	mc.setAttr(obj+".wireColorB", col[2])

	# 	if setOutlinerColour:
	# 		mc.setAttr(obj+".useOutlinerColor", 1)
	# 		mc.setAttr(obj+".outlinerColor", col[0], col[1], col[2])

