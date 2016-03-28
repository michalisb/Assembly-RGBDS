'''
Main entry and init for the RGBDS plugin
'''

from .plugin import *
import sublime
import os, sys

if sys.version_info < (3, 3):
	raise RuntimeError('RGBDS Syntax works with Sublime Text 3 only')

def plugin_loaded():
	sublime.load_settings("Preferences.sublime-settings").add_on_change('color_scheme', ColorSchemeManager.adjustScheme)

	pp = sublime.packages_path()
	if not os.path.exists(pp+"/RGBDSThemes"):
		os.makedirs(pp+"/RGBDSThemes")

	ColorSchemeManager.adjustScheme()

