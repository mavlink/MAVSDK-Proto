# -*- coding: utf-8 -*-
from protoc_gen_mavsdk.utils import name_parser_factory


class File(object):
    """ Represents the generated file """

    def __init__(
            self,
            plugin_name,
            package,
            template_env,
            template_file,
            docs,
            enums,
            structs,
            methods,
            has_result,
            is_server):
        self._package = name_parser_factory.create(package)
        self._plugin_name = name_parser_factory.create(plugin_name)
        self._class_description = docs['class'].strip()
        self._enums = enums
        self._structs = structs
        self._methods = methods
        self._has_result = has_result
        self._is_server = is_server

        if template_file is None:
            self._template = template_env.get_template("file.j2")
        else:
            self._template = template_env.get_template(template_file)

    def __repr__(self):
        return self._template.render(package=self._package,
                                     plugin_name=self._plugin_name,
                                     class_description=self._class_description,
                                     enums=self._enums.values(),
                                     structs=self._structs.values(),
                                     methods=self._methods.values(),
                                     has_result=self._has_result,
                                     is_server=self._is_server)
