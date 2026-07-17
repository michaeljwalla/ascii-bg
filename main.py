from dataclasses import dataclass
from enum import Enum
import shlex
import sys
from typing import Any, Callable, override
from PySide6 import QtCore
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow
import subprocess
from pathlib import Path
import json

HELP_OUTPUT = '''Usage: asciibg [args-for-script] [file-or-directory] -- [args-to-pass]
            args-for-script:
                --cache <m>   - cache images immediately
                    Lazy, Preload
                --dims <WxH>   - max dimension to scale to
                --mode <m>  - options when selecting from directory
                    static, cycle, random
                --speed <s> - speed, in seconds, to change on
                
            file-or-directory:
                select from one file, or choose randomly from dir
            
            args-to-pass:
                any arguments to pass into ascii-image-convert'''

def P_ERR(s): print(s, file=sys.stderr)
def P_OUT(s): print(s, file=sys.stdout)

def run(f:Callable[..., Any], other: Any=None, err:str|None=None):
    try:
        x = f()
        if issubclass(type(x), Exception):
            raise x
        return x
    except Exception as e:
        if err:
            P_ERR(err)
            exit(1)
    return other

class ScriptArguments:
    class ArgType(Enum):
        # @staticmethod
        # def fromString(s: str):
        #     try:
        #         return ScriptArguments.ArgType(s)
        #     except Exception as e:
        #         return None
        NEVER = ""
        CACHE = "--cache"
        DIMS = "--dims"
        MODE = "--mode"
        SPEED = "--speed"


    class ModeType(Enum):
        STATIC = 0
        CYCLE = 1
        RANDOM = 2
    class CacheType(Enum):
        LAZY = 0,
        NOW = 1
    mode: ModeType = ModeType.STATIC
    cache: CacheType = CacheType.LAZY
    width: int = 0
    height: int = 0
    speed: float = 0

    def __str__(self):
        return f"--mode {self.mode.name.lower()} --cache {self.cache.name.lower()} --dims {self.width}x{self.height} --speed {self.speed:.3f}"
    def __setArg(self, arg: ScriptArguments.ArgType, args: list[str]) -> list[str]:
        AT = ScriptArguments.ArgType
        if arg == AT.DIMS:
            dims = run(lambda: tuple(int(i) for i in args[0].split("x")), err="usage: --dims WxH")
            w, h = dims
            run(lambda: w > 0 and h > 0 and ValueError(), err="width/height must be positive")
            self.width, self.height = w, h
            return args[1:]
        elif arg == AT.MODE:
            self.mode = run(
                lambda: self.ModeType[args[0].upper()],
                err=f"usage: --dims {"|".join([i.name for i in self.ModeType])}"
            )
            return args[1:]
        elif arg == AT.CACHE:
            self.cache = run(
                lambda: self.CacheType[args[0].upper()],
                err=f"usage: --dims {"|".join([i.name for i in self.ModeType])}"
            )
            return args[1:]
        elif arg == AT.SPEED:
            s = run(lambda: float(args[0]), err="usage: --speed <s>")
            run(lambda: s < 0 and ValueError(), err="speed must be non-negative")
            self.speed = s
            return args[1:]

        run(Exception, err=f"Invalid: self.__setArg({arg}, {args})")
        return []

    def set(self, args: list[str]) -> ScriptArguments:
        while len(args):
            next = args[0].strip()
            if not next:
                arg = args[1:]
                continue
            elif not next.startswith("--"):
                run(Exception, err=HELP_OUTPUT)
            arg = run(lambda: self.ArgType[next[2:].upper()], err=f"Unknown argument: {next}\n{HELP_OUTPUT}")
            args = self.__setArg(arg, args[1:])
        return self
    def __init__(self, args:list[str]=[]):
        self.set(args)    
            
@dataclass
class ExecState:
    CachePath: Path
    Files: list[Path]
    Arguments: ScriptArguments
    PassArgs: list[str]
    
    def __str__(self):
        return f"Cache: {str(self.CachePath)} \
        \nFiles: {[str(i.name) for i in self.Files]} \
        \nArguments: \"{self.Arguments}\" \
        \nPassed Arguments: {self.PassArgs}"


def init_parse() -> ExecState:
    #grab settings
    with open(Path(__file__).resolve().parent / "settings.json", "r") as f:
        data = json.load(f)
        CACHE_PATH:str = run(lambda: data["cache-path"], "Missing 'cache-path' in settings.json")
        FILETYPES:set[str] = run(lambda: set("."+i for i in data["accepted-filetypes"]), other=set(), err="Missing 'accepted-filetypes' in settings.json")
        ARGUMENTS:list[str] = run(lambda: data["default-args"], other=[])
        #sanity check
        run(lambda: isinstance(CACHE_PATH, str) or Exception(), err="cache-path expects a string path")
        run(lambda: isinstance(FILETYPES, set) or Exception(), err="accepted-filetypes expects a list of inputs")
        run(lambda: isinstance(ARGUMENTS, list) or Exception(), err="default-args expects a list of inputs")
    
    #commandline helpers & input checking

    def is_valid_name(s: str) -> bool:
        s = s.lower()
        return any( s.endswith(i.lower()) for i in FILETYPES )
    
    def arg_split(args: list[str]) -> tuple[list[str], Path, list[str]]:
        if not args:
            return [], Path(":\0:invalid"), []
        try:                # [locals] [path] -- [others]
            splitter = args.index("--") - 1
            run(lambda: splitter < 0 and ValueError(), err=HELP_OUTPUT)
            return args[:splitter], Path(args[splitter]).expanduser().resolve(), args[splitter+2:]
        except ValueError:  # [locals] [path]
            return args[:-1], Path(args[-1]).expanduser(), []
    
    run(lambda: len(sys.argv) <= 1 and Exception(), err=HELP_OUTPUT)

    # input parameters
    local_args, path_arg, pass_args = arg_split(shlex.split(sys.argv[1]))
    final_args = ScriptArguments(ARGUMENTS).set(local_args)
    files = []

    run(lambda: path_arg.exists() or Exception(), f"{path_arg}: No such file or directory")
    
    if path_arg.is_dir():
        files = [
            i for i in path_arg.iterdir()
            if
                i.is_file()
                and is_valid_name( i.name )
        ]
    elif is_valid_name(path_arg.name):
        files = [path_arg]

    
    run(lambda: len(files) or Exception(), err=f"{path_arg}: No suitable file(s) found.")

    # check for existing at cached location
    cache = run(Path(CACHE_PATH).expanduser().resolve, f"Couldn't generate cache at {CACHE_PATH}")
    run(lambda: Path.mkdir(cache, parents=True, exist_ok=True), f"Couldn't generate cache at {CACHE_PATH}")

    return ExecState(
        CachePath   = cache.resolve(),
        Files       = files,
        Arguments   = final_args,
        PassArgs    = pass_args
    )


def main():
    app_state = init_parse()
    print(app_state)

if __name__ == "__main__":
    main()

exit()
app = QApplication(sys.argv)
app.setStyleSheet('''* {
                  background-color: black;
                  color: white;
}''')

window = QMainWindow()

label = QLabel("Hello, Wayland!")
label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
label.setFont(QFont("Monospace", 14))

window.setCentralWidget(label)
window.resize(400, 200)
window.show()
sys.exit(app.exec())
