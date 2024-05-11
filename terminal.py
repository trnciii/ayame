import re
import os
from sys import stdout

def write_with_encoding(s, encoding=None, errors='backslashreplace', file=stdout):
	file.buffer.write(s.encode(encoding if encoding else file.encoding, errors=errors))

ptn_escape = re.compile(r'\033\[.*?m')

def declip(s):
	return ptn_escape.sub('', s)


def clean_row():
	print('\033[2K', end='\r')

def clean_rows(n):
	print('\033[1F'.join('\033[2K' for _ in range(n)), end='')

def clean_screen():
	print('\033[2J\033[H', end='')

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
		print(f'\033[{-n}A', end='')
	elif n>0:
		print(f'\033[{n}B', end='')

def selected(pager, page=1, to_string=str, default=None):
	if isinstance(pager, list):
		if isinstance(default, list):
			default = {1:default}
		return [i for i, b in select(SinglePager(pager), 1, to_string, default) if b]
	return [i for i, b in select(pager, page, to_string, default) if b]


def get_select_max_width():
	w, _ = os.get_terminal_size()
	return w-3

def select_all(selection):
	if all(selection):
		return [False for _ in selection]
	else:
		return [True for _ in selection]

def select_display_options(cursor, li, to_string, current_page, max_page):
	max_width = get_select_max_width()
	nav = f" 👈{current_page: {len(str(max_page))}}/{max_page}☛ | 👇👆 (Move) | space (Select) | 'A' to all"
	print(mod(nav, color('yellow', 'fl')))
	for i, (item, s) in enumerate(li.to_list()):
		option = ('>' if cursor==i else ' ') + ('[x]' if s else '[ ]') + ' ' + to_string(item)
		if zen.display_length(option) > max_width:
			option = zen.trim(option, max_width) + '...'
		print(option + reset())
	return li.count + (len(nav)//max_width + 1)

class SelectionList:
	def __init__(self, items):
		self.items = items
		self.count = len(items)
		self.selection = [False]*self.count

	def to_list(self):
		return list(zip(self.items, self.selection))

class SinglePager:
	def __init__(self, items):
		self._list = SelectionList(items)

	def flip(self, _):
		return self._list

	def max_page(self):
		return 1


def fill(lines, max_height):
	w, _ = os.get_terminal_size()
	clean_rows(max_height)
	true_height = 0
	for line in lines:
		true_height += zen.display_height(line)
		diff = true_height - max_height
		if diff < 0:
			print(line)
		elif diff == 0:
			print(line, end='', flush=True)
			break
		else:
			print(zen.trim(line, diff*w), end='', flush=True)
			break

def extend_to_range(itr, lines, begin, height, preview):
	while len(lines) - begin < height:
		try:
			lines.append(next(itr))
			preview(lines[begin:], height)
		except StopIteration:
			return True
	return False

def append_eof(lines, eof, end):
	yield from lines
	if end:
		yield eof()


if not stdout.isatty():
	def select(pager, page, to_string=str, default=None):
		return default if default else [(i, True) for i, _ in pager.flip(page).to_list()]

	def scroll(itr, eof=lambda:'[EOF]'):
		write_with_encoding('\n'.join(itr))

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


	def select(pager, page, to_string=str, default=None):
		pages = {}
		cursor = 0
		while True:
			if not page in pages.keys():
				pages[page] = pager.flip(page)
				max_page = pager.max_page()
				if default and default.get(page, None):
					pages[page].selection = default[page]
			li = pages[page]
			cursor = cursor % li.count

			height = select_display_options(cursor, li, to_string, page, max_page)

			ch = msvcrt.getch()
			# print(ch)

			if ch == b'\r':
				return sum((v.to_list() for _, v in sorted(pages.items())), [])

			if ch in (b'\x03', b'q'):
				sys.exit()

			elif ch == b'a':
				li.selection = select_all(li.selection)
			elif ch == b' ':
				li.selection[cursor] = not li.selection[cursor]

			elif ch == b'\xe0':
				ch = msvcrt.getch()
				if ch == b'H':
					cursor -= 1
				elif ch == b'P':
					cursor += 1
				elif ch == b'I':
					cursor = 0
				elif ch == b'Q':
					cursor = li.count -1
				elif ch == b'M' and page < max_page:
					page += 1
				elif ch == b'K' and page > 1:
					page -= 1

			clean_rows(height+1)

	def scroll(itr, eof=lambda:'[EOF]'):
		_, height = os.get_terminal_size()
		print('\n'*(height-1), end='')
		lines = []
		begin = 0
		while True:
			_, height = os.get_terminal_size()
			end = extend_to_range(itr, lines, begin, height, fill)

			if end and len(lines) < height and sum(map(zen.display_height, lines)) < height:
				return # fill is already called in extend_to_range

			fill(append_eof(lines[begin:], eof, end), height)

			ch = msvcrt.getch()
			if ch == b'q' or ch == b'\x03':
				print()
				return
			elif ch == b'\xe0':
				ch = msvcrt.getch()
				# print(ch)
				if ch == b'H' and begin > 0:
					begin -= 1
				elif ch == b'P' and not (end and begin > len(lines)-2):
					begin += 1
				elif ch == b'I':
					begin = max(0, begin - height)
				elif ch == b'Q':
					if (not end) or begin+height < len(lines):
						begin += height
				elif ch == b'G':
					begin = 0
				elif ch == b'O':
					begin = len(lines)-height//2


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


	def select(pager, page, to_string=str, default=None):
		fd = sys.stdout.fileno()

		old = termios.tcgetattr(fd)
		tc = termios.tcgetattr(fd)
		tc[3] &= ~(termios.ICANON | termios.ECHO)

		try:
			termios.tcsetattr(fd, termios.TCSANOW, tc)

			pages = {}
			cursor = 0
			while True:
				if not page in pages.keys():
					pages[page] = pager.flip(page)
					max_page = pager.max_page()
					if default and default.get(page, None):
						pages[page].selection = default[page]
				li = pages[page]
				cursor = cursor % li.count

				height = select_display_options(cursor, li, to_string, page, max_page)

				ch = sys.stdin.read(1)
				# print(ch)

				if ch == '\n':
					return sum((v.to_list() for _, v in sorted(pages.items())), [])

				if ch == 'q':
					sys.exit()

				elif ch == 'a':
					li.selection = select_all(li.selection)
				elif ch == ' ':
					li.selection[cursor] = not li.selection[cursor]

				elif ch == '\x1b':
					ch = sys.stdin.read(2)
					if ch == '[A':
						cursor -= 1
					elif ch == '[B':
						cursor += 1
					elif ch == '[H':
						cursor = 0
					elif ch == '[F':
						cursor = li.count - 1
					elif ch == '[C' and page < max_page:
						page += 1
					elif ch == '[D' and page > 1:
						page -= 1

				clean_rows(height+1)

		finally:
			termios.tcsetattr(fd, termios.TCSANOW, old)

	def scroll(itr, eof=lambda:'[EOF]'):
		fd = sys.stdout.fileno()

		old = termios.tcgetattr(fd)
		tc = termios.tcgetattr(fd)
		tc[3] &= ~(termios.ICANON | termios.ECHO)

		try:
			termios.tcsetattr(fd, termios.TCSANOW, tc)

			_, height = os.get_terminal_size()
			print('\n'*(height-1),end='')
			lines = []
			begin = 0
			while True:
				_, height = os.get_terminal_size()
				end = extend_to_range(itr, lines, begin, height, fill)

				if end and len(lines) < height and sum(map(zen.display_height, lines)) < height:
					return # fill is already called in extend_to_range

				fill(append_eof(lines[begin:], eof, end), height)

				ch = sys.stdin.read(1)
				if ch == 'q':
					return
				elif ch == '\x1b':
					ch = sys.stdin.read(2)
					# print(ch)
					if ch == '[A' and begin > 0:
						begin -= 1
					elif ch == '[B' and not (end and begin > len(lines)-2):
						begin += 1
					elif ch == '[5':
						begin = max(0, begin - height)
					elif ch == '[6':
						if (not end) or begin+height < len(lines):
							begin += height
					elif ch == '[H':
						begin = 0
					elif ch == '[F':
						begin = len(lines) - height//2

		finally:
			print()
			termios.tcsetattr(fd, termios.TCSANOW, old)

else:
	raise ImportError('terminal working on unknown os.')
