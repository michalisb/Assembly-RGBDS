'''
Manages the color scheme in sublime, by making a copy of the active one with 
the extra scopes needed by our syntax manager
'''

from .misc import getScopeList, getForegroundColorForScope
import sublime, sublime_plugin
import re, plistlib



class ColorSchemeManager(sublime_plugin.ApplicationCommand):
	modification_running = False

	@staticmethod
	def adjustScheme():		
		scheme = sublime.load_settings("Preferences.sublime-settings").get('color_scheme')
		if ColorSchemeManager.modification_running:
			return
		if "Packages/RGBDSThemes" in scheme:
			return
		ColorSchemeManager.modification_running = True
		try:
			cs = plistlib.readPlistFromBytes(sublime.load_binary_resource(scheme))

			tokenclr = "#000000"
			for rule in cs['settings']:
				# print(rule)
				if "scope" not in rule and "name" not in rule:
					bgc = rule['settings']['background']
					r = int(bgc[1:3], 16)
					g = int(bgc[3:5], 16)
					b = int(bgc[5:7], 16)
					if b > 0:
						b = b-1
					elif g > 0:
						g = g-1
					elif r > 0:
						r = r-1
					else:
						rule['settings']['background'] = "#000001"
					tokenclr = "#%02x%02x%02x" % (r, g, b)
					break

			labelfgc = getForegroundColorForScope(cs['settings'], 'entity.name.function')
			aliasfgc = getForegroundColorForScope(cs['settings'], 'variable.other.constant')
			macrofgc = getForegroundColorForScope(cs['settings'], 'keyword.control.directive')

			print('tokenclr = {0}, foregroundC = {1}'.format(tokenclr, labelfgc))
			cs['name'] = cs['name'] + " (RGBDS)"

			cs['settings'].append(dict(
				scope="rgbdsLabel",
				settings=dict(
					foreground=labelfgc,
					background=tokenclr)
				)
			)
			cs['settings'].append(dict(
				scope="rgbdsAlias",
				settings=dict(
					foreground=aliasfgc,
					background=tokenclr)
				)
			)
			cs['settings'].append(dict(
				scope="rgbdsMacro",
				settings=dict(
					foreground=macrofgc,
					background=tokenclr)
				)
			)

			newname = "/RGBDSThemes/(RGBDS) %s.tmTheme" % re.search("/([^/]+).tmTheme$", scheme).group(1)
			plistlib.writePlist(cs,"%s%s" % (sublime.packages_path(), newname))

			sublime.load_settings("Preferences.sublime-settings").set("original_color_scheme", scheme)
			sublime.load_settings("Preferences.sublime-settings").set("color_scheme","Packages%s" % newname)
			sublime.save_settings("Preferences.sublime-settings")

		except Exception as e:
			#sublime.error_message("Colorcoder was not able to parse the colorscheme\nCheck the console for the actual error message.")
			#sublime.active_window().run_command("show_panel", {"panel": "console", "toggle": True})
			print(e)
		finally:
			ColorSchemeManager.modification_running = False
