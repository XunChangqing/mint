import os
import tempfile
import tarfile
import flask
import argparse
import subprocess
from pathlib import Path
from flask import Flask
from flask import request
# from ivy.http.asset import Asset
# from contextlib import chdir (require python >= 3.11)
from contextlib import contextmanager

@contextmanager
def chdir(path):
  old_path = os.getcwd()
  os.chdir(path)
  try:
    yield
  finally:
    os.chdir(old_path)

app = Flask(__name__)

# @app.route("/")
# def RootRedirect():
#     return app.redirect('static/index.html')

# soc scenarios
# def SocAppParamParse(req_json: dict)->(int, str, str, str):
#   seed = req_json['seed']
#   dt = req_json['device_tree']
#   rt_cfg = req_json['rt_cfg']
#   scen_cfg_dict = req_json['scen_cfg']
#   return seed, dt, rt_cfg, scen_cfg_dict

MINT_HOME = Path(os.path.abspath(__file__)).parent.parent
print('mint home: ', MINT_HOME)
# IVY_DIR = Path('/home/xuncq/stiwork/ivy/cmake')
IVY_DIR = os.getenv('IVY_DIR')
if not IVY_DIR:
  raise "please set env IVY_DIR"

# 裸机激励接收 4 组参数
# 1. seed
# 2. 设备树
# 3. ivy cfg json 文件
# 4. 激励配置，将 json 的每个 key：value 组合转换为 cmake 的 -D 项，激励本身只支持通过 cmake 变量定义可配置参数，c 激励可以通过 configure file 机制使用
def ivy_app_build(name, req_json):
  if 'seed' in req_json:
    seed = req_json['seed']
  else:
    seed = 0
  dt = req_json['device_tree']
  ivy_cfg = request.json['rt_cfg']
  scen_cfg = request.json['scen_cfg']

  # 提取所有 scen cfg 的 kv 组合

  with tempfile.TemporaryDirectory(prefix="ivy_app_") as tmpdirname:
    with chdir(tmpdirname):
      # 建立 dt 文件
      with open('device_tree.dts', 'w') as f:
        f.write(dt)
      # 建立 rt cfg 文件
      with open('ivy_cfg.json', 'w') as f:
        f.write(str(ivy_cfg))

      # 执行 cmake 命令
      cmake_cmd = f'cmake --toolchain {MINT_HOME}/toolchains/aarch64-generic-gnu.cmake -Divy_DIR={IVY_DIR} -Ddevice_tree=device_tree.dts -Divy_cfg=ivy_cfg.json '
      for k,v in scen_cfg.items():
        cmake_cmd += f' -D{k}={v} '
      cmake_cmd += f' {MINT_HOME}/{name}'

      print('cmake cmd: ', cmake_cmd)
      subprocess.run(cmake_cmd , shell=True)
      subprocess.run('make mkimage', shell=True)
      
      # 执行 make 命令进行 build
      # 打包文件并返回
      with tarfile.open("ret.tar", 'w') as tar:
        if os.path.exists('pregen_mermaid.md'):
          tar.add('pregen_mermaid.md')
        tar.add(f'{name}')
        tar.add(f'{name}.uimage')
      return flask.send_file(os.path.join(tmpdirname, 'ret.tar'))

@app.route('/api/stimulus/soc/scenario/bringup', methods=['POST'])
def soc_bringup():
  return ivy_app_build('bringup', request.json)

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--port', default=8080, help="port", type=int)
  args = parser.parse_args()
  app.run(debug=True, host='0.0.0.0', port = args.port)
