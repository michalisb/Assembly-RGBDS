'''
Main entry and init for the RGBDS plugin
'''

from .plugin import *
import sublime, sublime_plugin
import os, sys

if sys.version_info < (3, 3):
	raise RuntimeError('RGBDS Syntax works with Sublime Text 3 only')

def plugin_loaded():
	sublime.load_settings("Preferences.sublime-settings").add_on_change('color_scheme', ColorSchemeManager.adjustScheme)

	pp = sublime.packages_path()
	if not os.path.exists(pp+"/RGBDSThemes"):
		os.makedirs(pp+"/RGBDSThemes")

	ColorSchemeManager.adjustScheme()
	print('plugin loaded')


class GetDefinitionCommand(sublime_plugin.TextCommand):

	def is_visible(self, event):
		if not isAsm(self.view):
			return False

		pt = self.view.window_to_text((event['x'], event['y']))
		if self.view.classify(pt) & sublime.CLASS_EMPTY_LINE:
			return False
			
		pt_region = self.view.word(pt)
		region_word = self.view.substr(pt_region)
		print(region_word)

		return True

	def run(self, edit, event):
		print(event)


	def want_event(self):
		return True