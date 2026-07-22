#!/usr/bin/env -S uv run --script

from modules.instances import Instance, SwayInstance, PySideInstance
from modules.states_parsing import LiveState, ScriptArguments, init_parse

def get_instance(i: ScriptArguments.DisplayType) -> Instance:
    return {
        ScriptArguments.DisplayType.PYSIDE: PySideInstance,
        ScriptArguments.DisplayType.SWAYBG: SwayInstance,
    }[i]()

def main():
    exec_state = init_parse()
    instance = get_instance(exec_state.Arguments.display)

    live_state = LiveState(Exec=exec_state, Instance=instance)
    
    print(live_state.next())
    exit(instance.exec())

if __name__ == "__main__":
    main()
