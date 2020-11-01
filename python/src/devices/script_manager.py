import glob
import os

from helpers.script_helper import ScriptHelper


class ModuleData:
    def __init__(self, payload):
        self.payload = payload


class ScriptManager:
    def __init__(self):
        self._modules = []

    def load_scripts(self, path):
        # Make sure path ends with directory separator
        if not path.endswith("/"):
            path += "/"

        # Get python scripts
        script_names = glob.glob(path + "*.py")

        # Create script helper
        script_helper = ScriptHelper(path)

        # Load scripts
        for script_name in script_names:
            name, module = script_helper.load_class(script_name, None, [ "init", "tick" ])

            # Only add if matching script module found in file
            if name != None and module != None:
                module.init(module)
                self._modules.append(module)

    def reset(self):
        return

    def tick(self):
        for module in self._modules:
            module.tick(module, ModuleData("payload goes here"))
