import re
import os
from sys import stdout

def write_with_encoding(s, encoding=None, errors='backslashreplace'):
	stdout.buffer.write(s.encode(encoding if encoding else stdout.encoding, errors=errors))

ptn_escape = re.compile(r'\033\[.*?m')

def declip(s):
	return ptn_escape.sub('', s)


def clean_row():
	w, _ = os.get_terminal_size()
	print('\r' + ' '*(w-1), end='\r', flush=True)


def rgb(r, g, b, bg='f'):
	return f'48;2;{r};{g};{b}' if bg in ['b', 'bg', 'background'] else f'38;2;{r};{g};{b}'

def color(name, k='f'):
	table = {
		'black': 0,
		'red': 1,
		'green': 2,
		'yellow': 3,
		'blue': 4,
		'magenta': 5,
		'cyan': 6,
		'white': 7
	}

	kind = {
		'f': 3,
		'b': 4,
		'fl': 9,
		'bl': 10
	}

	return f'{kind[k]}{table[name]}'


def reset_all():
	return ''

def reset_color():
	return '0'

def bold():
	return '1'

def dim():
	return '2'

def italic():
	return '3'

def underline():
	return '4'

def blink():
	return '5'

def inv():
	return '7'

def hide():
	return '8'

def strikeline():
	return '9'


if stdout.isatty():
	def mod(s, *cc): return f'\033[{";".join(cc)}m' + s + reset()

	def reset(): return '\033[m'

else:
	def mod(s, *_): return s

	def reset(): return ''



def move_cursor(n):
	if n<0:
		print(f'\033[{-n}A')
	elif n>0:
		print(f'\033[{n}B')

def selected(items, format=str, default=None):
	return [i for i, b in zip(items, select([format(i) for i in items], default)) if b]


def get_select_max_width():
	w, _ = os.get_terminal_size()
	return w-3

def select_all(selected):
	if all(selected):
		return [False for _ in selected]
	else:
		return [True for _ in selected]

def select_display_options(cursor, items, selected):
	max_width = get_select_max_width()
	print(mod("↑↓ to move, space to select, 'A' for all", color('yellow', 'fl')))
	for i, (item, s) in enumerate(zip(items, selected)):
		clean_row()
		option = ('>' if cursor==i else ' ') + ('[x]' if s else '[ ]') + ' ' + item
		if zen.display_length(option) > max_width:
			option = zen.trim(option, max_width) + '...'
		print(option + reset())


if not stdout.isatty():
	def select(items, default=None):
		return default if default else [True]*len(items)

elif os.name == 'nt':
	import msvcrt, sys
	from . import zen

	def query(q, end):
		sys.stdout.write(q)
		sys.stdout.flush()

		s = ''
		while True:
			c = msvcrt.getch().decode('ascii')
			s += c
			if c == end:
				break
		return s


	def select(items, default=None):
		n = len(items)
		selected = default if default else [False]*n
		cursor = 0
		while True:
			select_display_options(cursor, items, selected)

			ch = msvcrt.getch()
			# print(ch)

			if ch == b'\r':
				return selected

			if ch in (b'\x03', b'q'):
				sys.exit()

			elif ch == b'a':
				selected = select_all(selected)
			elif ch == b' ':
				selected[cursor] = not selected[cursor]

			elif ch == b'\xe0':
				ch = msvcrt.getch()
				if ch == b'H':
					cursor = (cursor-1) % n
				elif ch == b'P':
					cursor = (cursor+1) % n

			move_cursor(-n-2)

elif os.name == 'posix':
	import termios, sys
	from . import zen

	def query(q, end):
		fd = sys.stdout.fileno()

		old = termios.tcgetattr(fd)
		tc = termios.tcgetattr(fd)
		tc[3] &= ~(termios.ICANON | termios.ECHO)

		try:
			termios.tcsetattr(fd, termios.TCSANOW, tc)

			sys.stdout.write(q)
			sys.stdout.flush()

			s = ''
			while True:
				c = sys.stdin.read(1)
				s += c
				if c == end:
					break

		finally:
			termios.tcsetattr(fd, termios.TCSANOW, old)

		return s


	def select(items, default=None):
		fd = sys.stdout.fileno()

		old = termios.tcgetattr(fd)
		tc = termios.tcgetattr(fd)
		tc[3] &= ~(termios.ICANON | termios.ECHO)

		try:
			termios.tcsetattr(fd, termios.TCSANOW, tc)

			n = len(items)
			selected = default if default else [False]*n
			cursor = 0
			while True:
				select_display_options(cursor, items, selected)

				ch = sys.stdin.read(1)
				# print(ch)

				if ch == '\n':
					return selected

				if ch == 'q':
					sys.exit()

				elif ch == 'a':
					selected = select_all(selected)
				elif ch == ' ':
					selected[cursor] = not selected[cursor]

				elif ch == '\x1b':
					ch = sys.stdin.read(2)
					if ch == '[A':
						cursor = (cursor-1)%n
					elif ch == '[B':
						cursor = (cursor+1)%n

				move_cursor(-n-2)

		finally:
			termios.tcsetattr(fd, termios.TCSANOW, old)

else:
	raise ImportError('terminal working on unknown os.')
