# -*- coding: utf-8 -*-
from os import environ
from google.protobuf.compiler import plugin_pb2
from protoc_gen_mavsdk.autogen_file import File
from protoc_gen_mavsdk.docs import Docs
from protoc_gen_mavsdk.pb_enum import Enum
from protoc_gen_mavsdk.methods import Method
from protoc_gen_mavsdk.pb_struct import Struct
from protoc_gen_mavsdk.utils import (get_template_env,
                                     has_result,
                                     is_server,
                                     name_parser_factory,
                                     type_info_factory)
from protoc_gen_mavsdk import mavsdk_options_pb2


class AutoGen(object):
    """ Autogenerator for the MAVSDK bindings """

    @staticmethod
    def generate_reactive(request):

        params = AutoGen.parse_parameter(request.parameter)

        if "output_file" in params:
            is_java = params["output_file"].endswith("java")
        else:
            is_java = params["file_ext"] == "java"

        # Load initialisms
        if "initialisms_file" in params:
            initialisms_path = params["initialisms_file"]
        else:
            initialisms_path = f"{params['template_path']}/initialisms"
        name_parser_factory.set_initialisms_path(initialisms_path)

        # Load type conversions
        if "conversions_file" in params:
            conversion_path = params["conversions_file"]
        else:
            conversion_path = f"{params['template_path']}/type_conversions"
        type_info_factory.set_conversion_path(conversion_path)

        template_env = get_template_env(params["template_path"], params["lstrip_blocks"], params["trim_blocks"])

        _codegen_response = plugin_pb2.CodeGeneratorResponse()

        for proto_file in request.proto_file:
            package = AutoGen.extract_package(proto_file, is_java)
            plugin_name, plugin_dir = AutoGen.extract_plugin_name_and_dir(
                proto_file.name, package, is_java)

            if package.startswith("google") or package == "mavsdk.options" or package.startswith("com.google") or package == "options.mavsdk":
                continue

            docs = Docs.collect_docs(proto_file.source_code_info)

            enums = Enum.collect_enums(plugin_name,
                                       package,
                                       proto_file.enum_type,
                                       template_env,
                                       docs)

            structs = Struct.collect_structs(plugin_name,
                                             package,
                                             proto_file.message_type,
                                             template_env,
                                             docs)

            requests = Struct.collect_requests(package,
                                               proto_file.message_type,
                                               docs)

            responses = Struct.collect_responses(package,
                                                 proto_file.message_type,
                                                 docs)

            methods = Method.collect_methods(plugin_name,
                                             package,
                                             is_server(plugin_name),
                                             docs,
                                             proto_file.service[0].method,
                                             structs,
                                             requests,
                                             responses,
                                             template_env)

            out_file = File(plugin_name,
                            package,
                            template_env,
                            params['template_file'],
                            docs,
                            enums,
                            structs,
                            methods,
                            has_result(structs),
                            is_server(plugin_name))

            # Fill response
            f = _codegen_response.file.add()
            if "output_file" in params:
                f.name = params["output_file"]
            else:
                f.name = f"{plugin_dir}/{plugin_name}.{params['file_ext']}"
            f.content = str(out_file)

        return _codegen_response

    @staticmethod
    def parse_parameter(parameter):
        raw_params = parameter.split(',')

        params_dict = {}
        for raw_param in raw_params:
            split_param = raw_param.split('=')
            if len(split_param) == 2:
                params_dict[split_param[0]] = split_param[1]

        if 'template_file' not in params_dict:
            params_dict["template_file"] = None

        if 'lstrip_blocks' not in params_dict:
            params_dict["lstrip_blocks"] = False

        if 'trim_blocks' not in params_dict:
            params_dict["trim_blocks"] = False

        if 'file_ext' not in params_dict and 'output_file' not in params_dict:
            raise Exception("'file_ext' option was not specified! See " +
                            "--[name]_out=file_ext=<value>,<other_options>:/path/to/output " +
                            "or --[name]_opt=file_ext=<value>,<other_options> in the protoc" +
                            "command line.")

        if 'template_path' not in params_dict:
            template_path = environ.get("TEMPLATE_PATH", "./")

            if template_path is not None:
                params_dict["template_path"] = template_path
            else:
                raise Exception("'template_path' option was not specified! See " +
                                "--[name]_out=template_path=<value>,<other_options>:/path/to/output " +
                                "or --[name]_opt=template_path=<value>,<other_options> in the protoc" +
                                "command line. Alternatively, you can set the TEMPLATE_PATH " +
                                "environment variable.")

        return params_dict

    @staticmethod
    def extract_package(proto_file, is_java):
        if is_java:
            try:
                return proto_file.options.java_package
            except AttributeError:
                return proto_file.package
        else:
            return proto_file.package

    @staticmethod
    def extract_plugin_name_and_dir(proto_file_name, package, is_java):
        """ The plugin name is the capitalized name of the proto file,
        without the extension. For instance, 'action.proto' becomes
        'Action'.

        The plugin directory is different between Java and other languages.
        - For Java, it is made from the package.
        - For other languages, it comes from the path to the proto file,
          e.g. 'action/action.proto' would become 'action/'. """
        proto_file_path_tree = proto_file_name.split('/')
        plugin_name = name_parser_factory.create(proto_file_path_tree[-1].split('.')[0]).upper_camel_case

        if is_java:
            plugin_dir = package.replace('.', '/')
        else:
            plugin_dir = "/".join(proto_file_path_tree[0:-1])

        return plugin_name, plugin_dir
