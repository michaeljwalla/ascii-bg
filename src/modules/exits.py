import sys
from typing import Any, Callable


def P_ERR(s): print(s, file=sys.stderr, flush=True)
def P_OUT(s): print(s, file=sys.stdout, flush=True)

def run_or_exit(f:Callable[..., Any], other: Any=None, err:str|None=None):
    try:
        x = f()
        if issubclass(type(x), Exception):
            raise x
        return x
    except Exception:
        if err:
            P_ERR(err)
            exit(1)
    return other
