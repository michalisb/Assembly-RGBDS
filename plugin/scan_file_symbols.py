'''
Sublime command to open a file with the path provided and scan for symbols
'''

import sublime, sublime_plugin
from .context import ContextManager


class ScanFileSymbolsCommand(sublime_plugin.TextCommand):

	def is_enabled(self):
		return True

	def run(self, edit, args):
		path = args
		
		with open(path, "r") as file:
			file_text = file.read()

			# create a popup which is a un-attached view in the end
			view = sublime.active_window().create_output_panel(path)
			view.set_read_only(False)

			# clear any pre-existing data
			region = sublime.Region(0, view.size())
			view.erase(edit, region)

			# add file contents and set RGBDS syntax
			view.insert(edit, 0, file_text)
			view.set_syntax_file('Packages/Assembly RGBDS/Assembly RGBDS.sublime-syntax')
			view.set_read_only(True)

			# assign to the context created and scan the file
			ctx = ContextManager.instance().getContextForPath(path)
			ctx.view = view
			ctx.scanSymbols()
			ctx.view = None

			# we don't need the view any more
			view.set_scratch(True)
			view.close()
			view = None