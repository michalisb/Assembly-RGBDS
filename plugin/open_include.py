import sublime, sublime_plugin
import os, sys
from .misc import isAsm

class OpenIncludeFileCommand(sublime_plugin.TextCommand):

	def want_event(self):
		return True


	def __getIncludePaths(self):
		''' Get all paths that we should search for the file'''

		paths = [os.path.dirname(self.view.file_name())]

		# check if additional paths are available in the project settings
		if self.view.window():
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


	def is_visible(self, event):
		'''
		Performs a quick context search, if the command should be visible
		based on the scope of the text we right clicked on
		'''

		self.file_path = None

		if not isAsm(self.view) or self.view.file_name() is None:
			return False

		# get point from vector coordinates of the event
		pt = self.view.window_to_text((event['x'], event['y']))
		# extract scope
		scope_name = self.view.scope_name(pt)

		# Option is visible only for include scope
		if 'string.quoted.include' not in scope_name:
			return False

		# get full include path by extracting the region and name from point
		# this depends on our syntax definition scope for 'string.quoted.include'
		include_region = self.view.extract_scope(pt)
		self.file_path = self.view.substr(include_region)		
		return True


	def run(self, edit, event):
		if self.file_path is None:
			return

		include_paths = self.__getIncludePaths()
		for p in include_paths:
			full_path = os.path.realpath(os.path.join(p, self.file_path))

			# check that the file actualy exists
			if os.path.isfile(full_path):
				newView = sublime.active_window().find_open_file(full_path)
				if newView is None:
					sublime.active_window().open_file(full_path)
				else:
					self.view.window().focus_view(newView)
				break