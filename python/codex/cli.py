import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from codex.record import record

import click


@click.group(
    options_metavar="<options>",
    subcommand_metavar="<command>",
    context_settings=dict(help_option_names=["-h", "--help"]),
    epilog='Type "codex <command> -h" for more help.',
)
def main():
    pass


@click.argument("script_name")
@click.command(options_metavar="<options>")
def run(script_name: str):
    """
    Run the given Python script, and record its entire execution.
    
    The recorded execution tree (which includes copies of all intermediate
    values) can then be displayed and explored in the Codex GUI.
    """
    record()
    import_file(script_name)


def import_file(path: str):
    """
    Imports a Python module from any local filesystem path. Temporarily alters
    sys.path to allow the imported module to import other modules in the same
    directory.
    
    Modified from https://github.com/raymondbutcher/pretf/blob/master/pretf/pretf/util.py#L190
    """
    module_path = Path(path).resolve().expanduser()
    module_dir = module_path.parent
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
        added_to_sys_path = True
    else:
        added_to_sys_path = False
    try:
        module_name = module_path.stem
        spec = spec_from_file_location(module_name, str(module_path))
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if added_to_sys_path:
            sys.path.remove(module_dir)


main: click.Group
main.add_command(run)
