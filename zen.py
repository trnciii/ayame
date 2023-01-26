import unicodedata as uc
from .terminal import declip, ptn_escape

def ret_to_width(r):
	return 1 + int(r in 'FW')

def char_to_width(c):
	return 1 + int(uc.east_asian_width(c) in 'FW')


def display_length(s):
	return sum(map(ret_to_width, map(uc.east_asian_width, declip(s))))


def ljust(s, w):
	return s + ' '*max(0, w-display_length(s))

def rjust(s, w):
	return ' '*max(0, w-display_length(s)) + s


def trim(s, w):
	default = (len(s), 0)
	spans = (m.span() for m in ptn_escape.finditer(s))

	i = 0
	l = 0
	b, e = next(spans, default)
	while i < len(s) and l < w:
		if b <= i:
			i = e
			b, e = next(spans, default)
		else:
			l += char_to_width(s[i])
			i += 1
	return s[:i-1 if l>w else i]
