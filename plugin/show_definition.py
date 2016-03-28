import sublime, sublime_plugin
import os, sys
from .misc import isAsm
from .context import ContextManager



class ShowDefinitionCommand(sublime_plugin.TextCommand):

	def want_event(self):
		# we want the mouse coordinates to find the word underneath
		return True


	def findSymbolInContexts(self, symbol):
		''' Go through all our view contexts and search for the symbol '''

		for ctx in ContextManager.instance().getActiveContexts().values():
			if symbol in ctx.symbols:	
				return (ctx.getFilePath(), ctx.symbols[symbol])
		return None


	def findLocalLabelInView(self, symbol_region):
		''' Try to expand the region so that it includes a local label (including macro ones) '''

		# check if there is a punctuation at the start
		if self.view.classify(symbol_region.begin()) & sublime.CLASS_PUNCTUATION_END:
			# cool, there is a punctuation expand selection with custom logic
			new_region = self.view.expand_by_class(symbol_region, 
				sublime.CLASS_WORD_START | sublime.CLASS_WORD_END,
				"()[]:, ")
			region_word = self.view.substr(new_region).strip()

			# we could also use self.view.indexed_symbols() here instead of the scopes

			# get the global label point closest to this local one
			closest_global = 0
			for r in self.view.find_by_selector("rgbds.label.global"):
				if r.end() < symbol_region.begin():
					closest_global = r.end()

			# now get all local labels and stop at the one after the global point
			for r in self.view.find_by_selector("rgbds.label.local"):
				if self.view.substr(r) == region_word and r.begin() > closest_global:
					return (self.view.file_name(), r)
		return None


	def showSymbol(self, view, region):
		# focus view
		sublime.active_window().focus_view(view)
		# clear selection(s) and set it at symbol
		view.sel().clear()
		view.sel().add(region)
		# center view to focused region
		view.show_at_center(region)
					

	def is_visible(self, event):
		if not isAsm(self.view):
			return False

		pt = self.view.window_to_text((event['x'], event['y']))
		if self.view.classify(pt) & sublime.CLASS_EMPTY_LINE:
			return False
			
		# with our captures pt get the text (word) at the mouse point
		pt_region = self.view.word(pt)
		region_word = self.view.substr(pt_region)

		self.symbol_details = self.findSymbolInContexts(region_word)

		if not self.symbol_details:
			# found no symbol with that name, search for local label
			self.symbol_details = self.findLocalLabelInView(pt_region)
			if not self.symbol_details:
				return False

		return True


	def run(self, edit, event):
		if self.symbol_details:
			view_path = self.symbol_details[0]
			focus_region = self.symbol_details[1]
			# collapse the region to a single point, the region start
			focus_region = sublime.Region(focus_region.begin(), focus_region.begin())

			# get the view with this path
			view = sublime.active_window().find_open_file(view_path)
			if view:
				self.showSymbol(view, focus_region)
			else:
				# weird issue, but unless we open the file with 'ENCODED_POSITION' it won't scroll afterwards
				# https://github.com/SublimeTextIssues/Core/issues/538
				view = sublime.active_window().open_file("%s:%d:%d" % (view_path, 1, 0), sublime.ENCODED_POSITION)

				def viewLoadedTimeout():
					# we can run methods only on loaded views
					if not view.is_loading():
						self.showSymbol(view, focus_region)
					else:
						sublime.set_timeout(viewLoadedTimeout, 100)
				
				# open is asynchronous, wait for a bit and then try to focus
				sublime.set_timeout(viewLoadedTimeout, 100)
