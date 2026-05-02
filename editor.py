import curses
import io
import traceback
from contextlib import redirect_stdout
TAB = "    "
editor_globals = {"__builtins__": __builtins__}
def main(stdscr):
    lines = [""]
    y_cursor = 0
    x_cursor = 0
    y_first_line_of_viewport = 0
    showing_output = False
    height_viewport, width_viewport = stdscr.getmaxyx()
    output_lines = []
    while True:
        stdscr.clear()
        if showing_output:
            for i in range(min(len(output_lines),height_viewport)):
                stdscr.addstr(height_viewport-i-1 , 0,output_lines[len(output_lines) - i-1][:width_viewport - 1])
        else:
            for i in range(height_viewport):
                y_line = y_first_line_of_viewport + i
                if y_line < len(lines):
                    stdscr.addstr(i, 0, lines[y_line][:width_viewport - 1])
            stdscr.move(y_cursor - y_first_line_of_viewport, x_cursor)
        stdscr.refresh()
        ch = stdscr.getch()
        if showing_output: # whatever character got after showing the output only results in a refresh
            showing_output = False
            continue
        if ch == curses.KEY_RESIZE:
            height_viewport, width_viewport = stdscr.getmaxyx()
            continue
        if ch == 24: # C-x
            break
        match ch:
            case curses.KEY_UP:
                if y_cursor > 0:
                    y_cursor -= 1
            case curses.KEY_DOWN:
                if y_cursor < len(lines) - 1:
                    y_cursor += 1
            case curses.KEY_LEFT:
                if x_cursor > 0:
                    x_cursor -= 1
                elif y_cursor > 0:
                    y_cursor -= 1
                    x_cursor = len(lines[y_cursor])
            case curses.KEY_RIGHT:
                if x_cursor < len(lines[y_cursor]):
                    x_cursor += 1
                elif y_cursor < len(lines) - 1:
                    y_cursor += 1
                    x_cursor = 0
            case 5: # C-e
                out_buf = io.StringIO()
                try:
                    with redirect_stdout(out_buf):
                        exec(compile("\n".join(lines), "<editor>", "exec"), editor_globals)
                    output_lines = out_buf.getvalue().rstrip().split("\n")
                except BaseException:
                    output_lines = traceback.format_exc().rstrip().split("\n")
                showing_output = True
            case curses.KEY_BACKSPACE | 127 | 8:
                if x_cursor > 0:
                    line = lines[y_cursor]
                    lines[y_cursor] = line[:x_cursor - 1] + line[x_cursor:]
                    x_cursor -= 1
                elif y_cursor > 0:
                    prev_len = len(lines[y_cursor - 1])
                    lines[y_cursor - 1] += lines.pop(y_cursor)
                    y_cursor -= 1
                    x_cursor = prev_len
            case curses.KEY_DC: # Delete
                line = lines[y_cursor]
                if x_cursor < len(line):
                    lines[y_cursor] = line[:x_cursor] + line[x_cursor + 1:]
                elif y_cursor < len(lines) - 1:
                    lines[y_cursor] += lines.pop(y_cursor + 1)
            case 10 | 13: # Enter
                line = lines[y_cursor]
                lines[y_cursor] = line[:x_cursor]
                lines.insert(y_cursor + 1, line[x_cursor:])
                y_cursor += 1
                x_cursor = 0
            case 9: # Tab
                line = lines[y_cursor]
                lines[y_cursor] = line[:x_cursor] + TAB + line[x_cursor:]
                x_cursor += len(TAB)
            case ch if 32 <= ch <= 126:
                line = lines[y_cursor]
                lines[y_cursor] = line[:x_cursor] + chr(ch) + line[x_cursor:]
                x_cursor += 1
        assert 0<=y_cursor <len(lines)
        assert 0<=x_cursor<=len(lines[y_cursor]), f"length_line: {len(lines[y_cursor])}, x_offset_cursor: {x_cursor}"
        if y_cursor < y_first_line_of_viewport:
            y_first_line_of_viewport = y_cursor
        if y_cursor > y_first_line_of_viewport + height_viewport - 1:
            y_first_line_of_viewport = y_cursor - height_viewport + 1
curses.wrapper(main)
