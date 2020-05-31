import sys
import dis
from pprint import pprint


def print_instr(instr: dis.Instruction):
    info = (
        instr.starts_line if instr.starts_line is not None else "  ",
        instr.opname,
        instr.argrepr,
        "(jump target)" if instr.is_jump_target else "",
    )
    return " ".join(map(str, info))


...
# We need a to wrap the trace function in a class, because it needs to be able
# to return a reference to itself.
class Tracer:
    def trace(self, frame, event, arg):
        code = frame.f_code
        filename = code.co_filename
        if "my_data_analysis.py" in filename:
            local_vars = [
                f"{name}={frame.f_locals[name]}"
                for name in code.co_names + code.co_varnames
                if name in frame.f_locals
            ]
            varlist = ", ".join(local_vars)
            line_info = (
                event,
                # code.co_firstlineno,
                frame.f_lineno,
                f"({varlist})",
            )
            print("")
            print(*line_info)
            # pprint(list(map(print_instr, dis.get_instructions(code))))
        return self.trace


def start_recording():
    sys.settrace(Tracer().trace)
