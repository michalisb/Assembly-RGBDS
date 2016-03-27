'''
Misc helper functions
'''

def isAsm(view):
	if view is None:
		return False

	try:
		location = view.sel()[0].begin()
	except IndexError:
		return False
	return view.match_selector(location, 'source.rgbds') != 0


def getScopeList(scope_line):
	scopes = scope_line.split(' ')
	for i, s in enumerate(scopes):
		scopes[i] = s.replace(',', '')
	return scopes


def getForegroundColorForScope(definitions, scope):
	color = "#ffffff"
	while True:
		for rule in definitions:
			if "scope" in rule and "settings" in rule and "foreground" in rule['settings']:
				rule_scope = getScopeList(rule['scope'])
				if scope in rule_scope :
					color = rule['settings']['foreground']
					return color

		p = scope.find('.')
		if p is -1:
			break
		scope = scope[:p]

	return color
