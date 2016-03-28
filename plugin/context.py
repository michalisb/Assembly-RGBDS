'''
Manages the file contexts
'''

from .misc import isAsm
from time import time
import sublime, sublime_plugin
import os, re


class Context:

	def __init__(self, view):
		self.includes = dict()
		self.aliases = []
		self.exported_labels = []
		self.labels = []
		self.macros = []
		self.symbols = dict()
		self.view = view
		self.mtime = 0
		self.view_id = view.id()
		self.file_path = view.file_name()


	def getViewId(self):
		return self.view_id


	def getFilePath(self):
		return self.file_path


	def setFilePath(self, path):
		self.file_path = path


	def getSymbols(self, files):
		if self.file_path in files:
			return {"labels": [], "aliases": [], "macros": []}
		files.add(self.file_path)

		labels = self.labels
		aliases = self.aliases
		macros = self.macros

		for ctx in self.includes.values():
			ctx_sym = ctx.getSymbols(files)
			labels = labels + ctx_sym["labels"]
			aliases = aliases + ctx_sym["aliases"]
			macros = macros + ctx_sym["macros"]

		symbols = {"labels": labels, "aliases": aliases, "macros": macros}
		return symbols


	def __getIncludePaths(self):
		# add the current directory in the paths
		paths = [os.path.dirname(self.getFilePath())]

		# check if additional paths are available in the project settings
		if self.view and self.view.window():
			project_path = self.view.window().project_file_name()
			if project_path:
				project_path = os.path.dirname(project_path)
				project_data = self.view.window().project_data()

				# check that project data has settings and include_paths is contained
				if "settings" in project_data and "include_paths" in project_data["settings"]:
					for p in project_data["settings"]["include_paths"]:
						additional_path = os.path.realpath(os.path.join(project_path, p))

						# validate that path exists
						if os.path.isdir(additional_path):
							paths.append(additional_path)
		return paths


	def scanIncludes(self):
		if self.view is None or self.getFilePath() is None:
			return

		include_paths = self.__getIncludePaths()

		scope = "string.quoted.include"
		include_files = [self.view.substr(r) for r in self.view.find_by_selector(scope)]
		for file_name in include_files:

			if file_name in self.includes:
				self.includes[file_name].reCheckLatest()
				continue

			# look for file in include paths and get the first
			for p in include_paths:
				full_path = os.path.realpath(os.path.join(p, file_name))

				# check that the file actualy exists
				if os.path.isfile(full_path):
					# is the file already opened?
					newView = sublime.active_window().find_open_file(full_path)
					if newView is None:
						ctx = ContextManager.instance().addScanRequest(full_path)
						self.includes[full_path] = ctx
					else:
						ctx = ContextManager.instance().addView(newView)
						self.includes[full_path] = ctx
					break


	def reCheckLatest(self):
		if os.path.getmtime(self.getFilePath()) > self.mtime:
			if self.view is None:
				# context is stale, re-open the file
				ctx = ContextManager.instance().addScanRequest(full_path)
			else:
				self.scanSymbols()
				

	def scanSymbols(self):
		if self.view is None:
			return

		self.mtime = time()	# update modified time
		self.scanIncludes()
		
		# grab the rest of the symbols defined in the view
		self.exported_labels = [self.view.substr(r) for r in self.view.find_by_selector("rgbds.label.exported")]

		self.macros = []
		for r in self.view.find_by_selector("rgbds.label.macro"):
			symbol = self.view.substr(r)
			self.symbols[symbol] = r
			self.macros.append(symbol)

		self.aliases = []
		for r in self.view.find_by_selector("rgbds.alias"):
			symbol = self.view.substr(r)
			self.symbols[symbol] = r
			self.aliases.append(symbol)
		
		self.labels = []
		for r in self.view.find_by_selector("rgbds.label.global"):
			symbol = self.view.substr(r)
			self.symbols[symbol] = r
			end_r = sublime.Region(r.end(), r.end() + 2)

			# check if the label is an exported one
			if self.view.substr(end_r) == "::":
				self.exported_labels.append(symbol)
			else:
				self.labels.append(symbol)



class ContextManager(sublime_plugin.EventListener):
	_instance = None

	def __init__(self):
		ContextManager._instance = self
		self.contexts = dict()
		self.scanRequests = set()
			

	@staticmethod
	def instance():
		return ContextManager._instance


	def getContextFromView(self, view):
		if view.file_name() is None:
			for ctx in self.contexts.values():
				if view.id() == ctx.getViewId():
					return ctx
		else:
			if view.file_name() in self.contexts:
				return self.contexts[view.file_name()]
		return None


	def addView(self, view):
		ctx = self.getContextFromView(view)
		if ctx is None and isAsm(view):
			ctx = Context(view)

			# We don't want to perform a scan until is loaded
			if not view.is_loading():
				ctx.scanSymbols()

			# add the context based on filename or id, if view not on disk
			if view.file_name():
				self.contexts[view.file_name()] = ctx
			else:
				self.contexts[view.id()] = ctx

		if ctx and ctx.view is None:
			ctx.view = view
		return ctx


	def addScanRequest(self, path):
		self.scanRequests.add(path)
		view = sublime.active_window().open_file(path)
		ctx = self.addView(view)
		return ctx


	def getActiveContexts(self):
		return self.contexts


	def getExportedLabels(self):
		exported = []
		for c in self.contexts.values():
			exported = exported + c.exported_labels
		return exported

		
	def on_activated(self, view):
		if not isAsm(view):
			return

		ctx = self.getContextFromView(view)
		if ctx is None:
			ctx = self.addView(view)

			def activateAsync():
				view.run_command('syntax_highlight')

			if view.file_name() not in self.scanRequests:
				sublime.set_timeout(activateAsync, 100)


	def on_activated_async(self, view):
		if not isAsm(view):
			return

		ctx = self.getContextFromView(view)
		if ctx is None:
			ctx = self.addView(view)

		view.run_command('syntax_highlight')


	def on_modified_async(self, view):
		if not isAsm(view):
			return

		view.run_command('syntax_highlight')


	def on_load_async(self, view):
		if not isAsm(view):
			return
			
		ctx = self.getContextFromView(view)
		if ctx is None:
			ctx = self.addView(view)

		if view.file_name() in self.scanRequests:
			self.scanRequests.remove(view.file_name())

			ctx.scanSymbols()

			# we don't want that view attached anymore, close it
			view.set_scratch(True)
			group_index, view_index = view.window().get_view_index(view)
			view.window().run_command("close_by_index", { "group": group_index, "index": view_index})


	def on_pre_close(self, view):
		if not isAsm(view):
			return

		# if we have a context for that view, mark it as stale
		# by removing the reference to the view - no further ops possible
		ctx = self.getContextFromView(view)
		if ctx:
			ctx.view = None


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