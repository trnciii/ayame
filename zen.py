import unicodedata as uc
from .terminal import declip

def to_width(r):
	return 1 + int(r in 'FW')

def display_length(s):
	return sum(map(to_width, map(uc.east_asian_width, declip(s))))


def ljust(s, w):
	return s + ' '*max(0, w-display_length(s))

def rjust(s, w):
	return ' '*max(0, w-display_length(s)) + s
