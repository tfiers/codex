import html
import re
import sys
import webbrowser
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class TracedLine:
    linenr: int
    event: str
    source_code: str
    locals_diff: Dict[str, Any]
    arg: Any

    def __repr__(self):
        return (
            f"{self.event: >6} {self.linenr: <4} "
            + f"{self.source_code.rstrip(): <40} "
            + ", ".join(
                f"{name}: {value}" for name, value in self.locals_diff.items()
            )
        )


def process(raw_traced_lines: List[TracedLine]):
    traced_lines = raw_traced_lines.copy()
    # Shift back `locals_diff`s of "line" events to display next to the previous line.
    for i in range(1, len(traced_lines)):
        prev_line = traced_lines[i - 1]
        current_line = traced_lines[i]
        if current_line.event == "line" and prev_line.event == "line":
            prev_line.locals_diff = current_line.locals_diff.copy()
            current_line.locals_diff = {}

    # Remove redundant "line" events -- namely "line" events with no changed
    # variables and the same source code as a preceding or following line.
    # I.e. they don't add any information.
    i = 1
    while i < len(traced_lines) - 1:
        prev_line = traced_lines[i - 1]
        current_line = traced_lines[i]
        next_line = traced_lines[i + 1]
        if (
            current_line.event == "line"
            and not current_line.locals_diff
            and (
                current_line.source_code == prev_line.source_code
                or current_line.source_code == next_line.source_code
            )
        ):
            traced_lines.remove(current_line)
        i += 1

    # Add return value to variables list, for display.
    for line in traced_lines:
        if line.event == "return":
            line.locals_diff["return"] = line.arg

    # Remove duplicate first line (it's there both as a "call" and a "line").
    traced_lines.pop(0)

    return traced_lines


HTML_FILENAME = "index.html"
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>Codex &ndash; Code Execution GUI</title>
</head>
<body>
    <pre>{}</pre>
</body>
</html>
"""


class Codex:
    def __init__(self):
        self.raw_traced_lines: List[TracedLine] = []

    def record(self, new_line: TracedLine):
        self.raw_traced_lines.append(new_line)

    def __repr__(self):
        processed_lines = process(self.raw_traced_lines)
        return "\n".join(map(str, processed_lines))

    def save_as_html(self):
        my_html = HTML_TEMPLATE.format(html.escape(str(self)))
        with open(HTML_FILENAME, "w") as fh:
            fh.write(my_html)
        return HTML_FILENAME


# We need a to wrap the trace function in a class, because it needs to be able
# to return a reference to itself.
class Tracer:
    def __init__(self):
        self.source_codes = {}
        self.codex = Codex()
        self.last_locals = {}

    def trace(self, frame, event, arg):
        frame_code = frame.f_code
        filename = frame_code.co_filename
        if "my_data_analysis.py" in filename:
            if filename in self.source_codes:
                source_code = self.source_codes[filename]
            else:
                with open(filename) as fh:
                    source_code = fh.readlines()
                self.source_codes[filename] = source_code

            linenr = frame.f_lineno
            current_locals: Dict[str, str] = {
                name: Tracer.to_string(value)
                for name, value in frame.f_locals.items()
            }
            locals_diff = {}
            for name, current_value in current_locals.items():
                if name.startswith("__"):
                    continue
                # If we have a new variable, or if its value has changed..
                if name not in self.last_locals or current_value != (
                    last_value := self.last_locals[name]
                ):
                    # ..record the variable
                    locals_diff[name] = current_value

            # Python uses 1-based indexing for source code lines (just like
            # code editors do). Hence the -1 to extract the correct line from
            # the source code file.
            self.codex.record(
                TracedLine(
                    linenr, event, source_code[linenr - 1], locals_diff, arg
                )
            )

            self.last_locals = current_locals.copy()

        return self.trace

    def to_string(value: Any) -> str:
        string = str(value)
        if match := re.match(
            "^<(?P<object_description>.*) at 0x[A-Z0-9]{16}>$", string
        ):
            string = f"<{match.group('object_description')}>"
        return string


@contextmanager
def record():
    tracer = Tracer()
    sys.settrace(tracer.trace)
    yield
    webbrowser.open(tracer.codex.save_as_html())
