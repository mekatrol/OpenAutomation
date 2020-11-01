import os

from helpers.dictionary_helper import DictionaryHelper
from helpers.script_helper import ScriptHelper


class ModuleData:
    def __init__(self, payload):
        self.payload = payload


class ModuleInstance:
    def __init__(self, module, priority):
        self.module = module
        self.priority = priority


class ScriptManager:
    def __init__(self):
        self._modules = []

    def load_scripts(self, path, script_modules):
        # Make sure path ends with directory separator
        if not path.endswith("/"):
            path += "/"

        # Create script helper
        script_helper = ScriptHelper(path)

        # Load scripts
        for module_config in script_modules:
            # Wrap config in dictionary helper
            module_config = DictionaryHelper(module_config, "module")

            # Get required name
            name = module_config.get_str("name", False)

            # Get optional priority
            priority = module_config.get_int(
                "priority", True, default=1000, min_value=1)

            # Load the script, it must contain a class with the 'init' and 'tick' methods
            name, module = script_helper.load_class(
                name, None, ["init", "tick"])

            # Only add if matching script module found in file
            if name != None and module != None:
                module.init(module)
                self._modules.append(ModuleInstance(module, priority))

        self._modules.sort(key=self._get_module_priority)

    def tick(self):
        for module_instance in self._modules:
            module_instance.module.tick(
                module_instance.module, ModuleData("payload goes here"))

    def _get_module_priority(self, module):
        return module.priority
