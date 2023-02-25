""" Details see below in class definition.
"""
import glob
import os
import re

from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginOpenvino(NuitkaPluginBase):
    plugin_name = "mediapipe"
    plugin_desc = "Required for mediapipe"
    reason = "Dynamic import compilation needed"

    def __init__(self):
        pass

    def getImplicitImports(self, module):
        full_name = module.getFullName()
        if full_name == "mediapipe":
            yield "mediapipe.python"

    def considerDataFiles(self, module):
        full_name = module.getFullName()
        if full_name == "mediapipe":
            module_folder = module.getCompileTimeDirectory()
            extensions = ["binarypb", "tflite", "txt"]
            # data_re = re.compile(r"^.*\.(?!py.*$)[^.]+$")
            # for base, _, files in os.walk(os.path.join(module_folder, modules_path)):
            #    for filename in files:
            #        if data_re.match(filename):
            #            source = os.path.join(base, filename)
            #            rel_path = os.path.relpath(source, module_folder)
            #            dest = os.path.join(full_name, rel_path)
            #            yield self.makeIncludedDataFile(
            #                source_path=source,
            #                dest_path=dest,
            #                reason="package data for mediapipe"
            #                )
            for extension in extensions:
                pattern = os.path.join("modules", "**", f"*.{extension}")
                pwd = os.getcwd()
                os.chdir(module_folder)
                for path in glob.glob(pattern):
                    yield self.makeIncludedDataFile(
                        source_path=os.path.join(module_folder, path),
                        dest_path=os.path.join(full_name, path),
                        reason=self.reason
                    )
                os.chdir(pwd)
