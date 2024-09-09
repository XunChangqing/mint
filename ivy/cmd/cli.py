import argparse
from pathlib import Path

NEW_CMAKE_PRJ = """
cmake_minimum_required(VERSION 3.27)

project(
  {name}
  VERSION 0.1.0
  DESCRIPTION "{name} based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

# set(device_tree "/path/to/file.dts")

add_ivy_executable({name})
# add source files
# target_sources({name} PRIVATE main.c)
"""

def new(args: argparse.Namespace):
  with open('CMakeLists.txt', 'w') as f:
    f.write(NEW_CMAKE_PRJ.format(name=args.name))

NEW_CMAKE_PRESETS = """
{{
  "version": 6,
    "cmakeMinimumRequired": {{
    "major": 3,
    "minor": 27,
    "patch": 0
  }},
  "configurePresets": [
    {{
      "name": "default",
      "displayName": "Default Config",
      "description": "Default build",
      "binaryDir": "${{sourceDir}}/build/default",
      "cacheVariables": {{
        "ivy_DIR": {{
          "type": "STRING",
          "value": "{ivy_dir}/__crel__/cmake"
        }},
        "device_tree": {{
          "type": "STRING",
          "value": "{dts_file}"
        }},
        "ivy_cfg": {{
          "type": "STRING",
          "value": "{ivy_cfg_file}"
        }}
      }},
      "toolchainFile": "{tc_file}"
    }},
    {{
      "name": "debug",
      "inherits": "default",
      "binaryDir": "${{sourceDir}}/build/debug",
      "cacheVariables": {{
        "CMAKE_BUILD_TYPE": "Debug"
      }}
    }},
    {{
      "name": "release",
      "binaryDir": "${{sourceDir}}/build/release",
      "inherits": "default",
      "cacheVariables": {{
        "CMAKE_BUILD_TYPE": "Release"
      }}
    }}
  ],
  "buildPresets": [
    {{
      "name": "default",
      "configurePreset": "default"
    }},
    {{
      "name": "debug",
      "configurePreset": "debug"
    }},
    {{
      "name": "release",
      "configurePreset": "release"
    }}
  ]
}}
"""

def build(args: argparse.Namespace):
  dts_path = Path(args.device_tree)
  if not dts_path.exists():
    raise f'dts{args.device_tree} does not exist'
  dts_path = dts_path.absolute().resolve()

  tc_path = Path(args.toolchain)
  if not tc_path.exists():
    raise f'tc{args.toolchain} does not exist'
  tc_path = tc_path.absolute().resolve()

  ivy_cfg_path = Path(args.ivy_cfg)
  if not ivy_cfg_path.exists():
    raise f'ic{args.ivy_cfg} does not exist'
  ivy_cfg_path = ivy_cfg_path.absolute().resolve()

  with open("CMakeUserPresets.json", 'w') as f:
    f.write(NEW_CMAKE_PRESETS.format(ivy_dir=Path(__file__).parent.parent, dts_file=dts_path, tc_file=tc_path, ivy_cfg_file=ivy_cfg_path))
  print('please DO NOT track the CMakeUserPresets.json generated in your version control system')
  print('take GIT for example, you should add the CMakeUserPresets.json to the .gitignore')
  print('to configure and build with DEBUG')
  print("cmake --preset debug")
  print("cmake --build --preset debug")
  print('to configure and build with Release')
  print("cmake --preset release")
  print("cmake --build --preset release")

  # subprocess.run(objcopy_cmd, shell=True)

def Main():
  global_parser = argparse.ArgumentParser(prog='ivy')
  
  subparsers = global_parser.add_subparsers(
      title="subcommands", help="sub-commands"
  )

  new_parser = subparsers.add_parser('new', help = 'create a new ivy application in current directory')
  new_parser.set_defaults(func=new)
  new_parser.add_argument('name', help='name of the application')

  # new_parser.add_argument()

  build_parser = subparsers.add_parser('build', help = 'build the ivy application in current directory')
  build_parser.set_defaults(func=build)
  build_parser.add_argument('--device-tree', '--dt', help='path to the device tree file', required=True)
  build_parser.add_argument('--toolchain', '--tc', help='path to the toolchain file', required=True)
  build_parser.add_argument('--ivy-cfg', '--ic', help='path to the ivy cfg file', required=True)

  # # build_parser.add_argument()

  # arg_template = {
  #     "dest": "operands",
  #     "type": float,
  #     "nargs": 2,
  #     "metavar": "OPERAND",
  #     "help": "a numeric value",
  # }

  # add_parser = subparsers.add_parser("add", help="add two numbers a and b")
  # add_parser.add_argument(**arg_template)
  # add_parser.set_defaults(func=add)

  # sub_parser = subparsers.add_parser("sub", help="subtract two numbers a and b")
  # sub_parser.add_argument(**arg_template)
  # sub_parser.set_defaults(func=sub)

  # mul_parser = subparsers.add_parser("mul", help="multiply two numbers a and b")
  # mul_parser.add_argument(**arg_template)
  # mul_parser.set_defaults(func=mul)

  # div_parser = subparsers.add_parser("div", help="divide two numbers a and b")
  # div_parser.add_argument(**arg_template)
  # div_parser.set_defaults(func=div)

  args = global_parser.parse_args()

  if hasattr(args, 'func'):
    args.func(args)

if __name__ == '__main__':
  Main()