'''
Manages the color scheme in sublime, by making a copy of the active one with 
the extra scopes needed by our syntax manager
This is a workaround, to define colours for the symbols we specify through view.add_regions

https://github.com/SublimeTextIssues/Core/issues/817
'''

from .misc import getScopeList, getForegroundColorForScope
from time import time
import sublime, sublime_plugin
import re, plistlib


class ColorSchemeManager(sublime_plugin.ApplicationCommand):
	modification_last_run = 0

	@staticmethod
	def adjustScheme():		
		scheme = sublime.load_settings("Preferences.sublime-settings").get('color_scheme')
		time_now = time()

		# if already using an RGBDS modified theme, do nothing
		if "Packages/RGBDSThemes" in scheme:
			return

		# other plugins use the same workaround for their custom scopes
		# pay nice by unsubscribing from the 'color_scheme' event and waiting a couple of seconds
		if ColorSchemeManager.modification_last_run + 2 > time_now:
			return

		sublime.load_settings("Preferences.sublime-settings").clear_on_change('color_scheme')
		ColorSchemeManager.modification_last_run = time_now
		try:
			cs = plistlib.readPlistFromBytes(sublime.load_binary_resource(scheme))

			# this workaround for custom scopes-regions, works by using the a different background colour
			# than the one in the theme, but we don't actually want it to differ - just different enough
			# so that the workaround works
			backgroundColour = "#000000"
			for rule in cs['settings']:
				if "scope" not in rule and "name" not in rule:
					colour = re.sub('^#(.)(.)(.)$', r'#\1\1\2\2\3\3', rule['settings']['background'])
					colour_value = int(colour[1:], base=16)
					if colour_value < 0xffffff:
						colour_value += 1
					else:
						colour_value -= 1
					backgroundColour = "#{:06x}".format(colour_value)
					break


			cs['name'] = cs['name'] + " (RGBDS)"

			# add a scope for labels, it should use the functions color
			labelfgc = getForegroundColorForScope(cs['settings'], 'entity.name.function')
			cs['settings'].append(dict(
				scope="rgbdsLabel",
				settings=dict(
					foreground=labelfgc,
					background=backgroundColour)
				)
			)

			# add a scope for aliases/equates, it should use the variable/constant color
			aliasfgc = getForegroundColorForScope(cs['settings'], 'variable.other.constant')
			cs['settings'].append(dict(
				scope="rgbdsAlias",
				settings=dict(
					foreground=aliasfgc,
					background=backgroundColour)
				)
			)

			# and lastly one for macros
			macrofgc = getForegroundColorForScope(cs['settings'], 'keyword.control.directive')
			cs['settings'].append(dict(
				scope="rgbdsMacro",
				settings=dict(
					foreground=macrofgc,
					background=backgroundColour)
				)
			)

			newname = "/RGBDSThemes/(RGBDS) %s.tmTheme" % re.search("/([^/]+).tmTheme$", scheme).group(1)
			plistlib.writePlist(cs,"%s%s" % (sublime.packages_path(), newname))

			sublime.load_settings("Preferences.sublime-settings").set("original_color_scheme", scheme)
			sublime.load_settings("Preferences.sublime-settings").set("color_scheme","Packages%s" % newname)
			sublime.save_settings("Preferences.sublime-settings")

		except Exception as e:
			print(e)
		finally:
			sublime.load_settings("Preferences.sublime-settings").add_on_change('color_scheme', ColorSchemeManager.adjustScheme)
