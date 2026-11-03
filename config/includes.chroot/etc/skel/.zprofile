# Start the terminal-first graphical session only on the live console.
if [[ -o interactive && -z "${DISPLAY:-}" && "${DEVOS_NO_AUTO_X:-0}" != 1 ]]; then
	if [[ "$(tty 2>/dev/null)" == /dev/tty2 ]]; then
		startx
	fi
fi
