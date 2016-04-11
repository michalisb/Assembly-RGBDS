from .misc import isAsm
from .context import ContextManager
import sublime, sublime_plugin
import re


class SyntaxHighlightCommand(sublime_plugin.TextCommand):	
	
	def is_enabled(self):
		return isAsm(self.view)


	def getRegionsFromSymbols(self, symbols):
		regions = []
		for s in symbols:
			pattern = '\\b%s\\b' % s
			if s[0] == '.' or s[-1] == "@":
				pattern = re.escape(s)	# local labels regex needs a bit of love
			for r in self.view.find_all(pattern):
				word_scope = self.view.scope_name(r.begin()).strip()
				if "rgbds.label" not in word_scope and "comment" not in word_scope:
					regions.append(r)
		return regions


	def run(self, edit):
		self.view.erase_regions('labels')
		self.view.erase_regions('aliases')
		self.view.erase_regions('macros')
		ctx = ContextManager.instance().getContextFromView(self.view)
		if ctx:
			files = set()
			ctx_sym = ctx.getSymbols(files)
			labels = ContextManager.instance().getExportedLabels() + ctx_sym["labels"]

			scopes = "rgbds.label.local"
			for r in self.view.find_by_selector(scopes):
				local_label = self.view.substr(r)
				if local_label not in labels:
					labels.append(local_label)		

			label_regions = self.getRegionsFromSymbols(labels)
			aliases_regions = self.getRegionsFromSymbols(ctx_sym["aliases"])
			macros_regions = self.getRegionsFromSymbols(ctx_sym["macros"])
			
		
			if len(label_regions):
				self.view.add_regions("labels", label_regions, "rgbdsLabel", '', sublime.DRAW_NO_OUTLINE)
			if len(aliases_regions):
				self.view.add_regions("aliases", aliases_regions, "rgbdsAlias", '', sublime.DRAW_NO_OUTLINE)
			if len(macros_regions):
				self.view.add_regions("macros", macros_regions, "rgbdsMacro", '', sublime.DRAW_NO_OUTLINE)