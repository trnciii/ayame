import unicodedata as uc

def display_length(s):
	return sum( map(lambda x:int(x in 'FW')+1, map(uc.east_asian_width, s)) )

def ljust(s, w):
	return s + ' '*max(0, w-display_length(s))

def rjust(s, w):
	return ' '*max(0, w-display_length(s)) + s
