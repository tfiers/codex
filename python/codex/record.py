import re
import sys
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


class Codex:
    def __init__(self):
        self.traced_lines: List[TracedLine] = []

    def record(self, new_line: TracedLine):
        if len(self.traced_lines) > 0:
            # Present changed variables at end of previous line.
            prev_line = self.traced_lines[-1]
            if prev_line.event == "line":
                if new_line.event == "line":
                    prev_line.locals_diff = new_line.locals_diff.copy()
                elif prev_line.source_code == new_line.source_code and (
                    not prev_line.locals_diff or not new_line.locals_diff
                ):
                    self.traced_lines.remove(prev_line)
                else:
                    # New line is a call or a return, with different source
                    # code as previous line
                    prev_line.locals_diff = {}
        if new_line.event == "return":
            new_line.locals_diff = {"return": new_line.arg}
        if not (new_line.linenr == 1 and new_line.event == "call"):
            self.traced_lines.append(new_line)

    def __repr__(self):
        return "\n".join(map(str, self.traced_lines))


def to_string(value: Any) -> str:
    string = str(value)
    if match := re.match(
        "^<(?P<object_description>.*) at 0x[A-Z0-9]{16}>$", string
    ):
        string = f"<{match.group('object_description')}>"
    return string


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
                name: to_string(value) for name, value in frame.f_locals.items()
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


@contextmanager
def record():
    tracer = Tracer()
    sys.settrace(tracer.trace)
    yield
    print(tracer.codex)
