## 1. 环境所需工具

1. cmake (>=3.30.0)  
2. python (>=3.10.0)
3. gcc 交叉工具链

## 2. poetry安装
`poetry`是一个专注于Python项目依赖管理的工具，它提供了一种简洁而强大的方式来定义项目依赖、创建虚拟环境、构建和发布Python包  

* 由于内网无法联网，需要配置pip.conf来配置本地源（外网使用可跳过此步）
```
  $ vim ~/.config/pip/pip.conf
```
```
  [global]
  trusted-host=10.10.10.111
  index-url=http://10.10.10.111:3141/ivy/pub/+simple/
```
* 创建虚环境
```
  $ python -m venv poetry_venv
```
* 激活虚环境
```
  $ source poetry_venv/bin/activate
```
* 下载poetry
```
  $ pip install poetry
```
* poetry用法  
  poetry可以根据项目目录内的pyproject.toml文件中的依赖列表来安装依赖,直接在pyproject.toml所在目录下poetry install。
  有两种方式来调用poetry：  
  1. 直接使用poetry venv中的poetry的全路径来使用
  2. 将poetry的路径放到`PATH`环境变量中(推荐)
```
  export PATH=~/poetry_venv/bin:$PATH 
```
  
## 3. 安装
### 配置pyproject.toml
poetry使用pyproject.toml来定义项目的配置和依赖信息，通过pyproject.toml，用户可以指定`项目依赖`、`Python版本`、`项目元数据`等信息。   

* 如果是在内网使用的的话，需要在pyproject.toml配置：
```
[tool.poetry.source]
name = "ivy_pub"
url = "http://10.10.10.111:3141/ivy/pub/+simple/"
priority = "primary"
```
* 如果是在外网使用的话，就不能使用上面的源，建议使用清华的源
```
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
```

### 安装工具所需依赖
* 为mint建立独立虚环境
```bash
  $ python -m venv mint_venv
  $ source mint_venv/bin/activate
```
* 安装自身及所需依赖到虚环境中
```bash
  $ cd <path/to/mint>
  $ poetry install
``` 

## 4. aarch64_moesi使用
在mint/aarch64_moesi目录下包含3个文件：`aarch64_moesi.py`、`main.c`、`CMakeLists.txt`  
`aarch64_moesi.py`基于purslane来生成测试激励  
### qemu
* qemu设备树文件的使用可以用qemu的dumpdtb来生成,通过dtc来将dtb转换成dts
```
$ ./qemu-system-aarch64 -M virt,secure=true,virtualization=true,dumpdtb=qemu.dtb -cpu cortex-a76 -smp cpus=2 -m size=2048M -kernel aarch64-moesi.uimage -nographic
$ dtc -I dtb -O dts qemu.dtb > qemu.dts
```
* qemu使用
```
  $ cd mint/aarch64_moesi
  $ ivy build --dt qemu.dts --tc ../toolchains/aarch64-none-linux-gnu.cmake --ic ../ivy_cfg/emu.py
  $ cmake --preset debug
  $ cmake --build --preset debug
  $ cd <qemu path>
  $ cd build
  $ ./qemu-system-aarch64 -M virt,secure=true,virtualization=true -cpu cortex-a76 -smp cpus=2 -m size=2048M -kernel /../aarch64_moesi/build/debug/aarch64-moesi.uimage -nographic
```
--ic 是指定生成激励时需要的配置，emu.py适用于硬仿和qemu

### 软仿
* 软仿的设备树需要自己编写，这里提供一个简单的设备树描述文件
```
/dts-v1/;

/ {
	#size-cells = <0x02>;
	#address-cells = <0x02>;
	compatible = "linux,dummy-virt";

	
	memory@00 {
		reg = <0x100 0x00000000 0xf 0xffffffff>;
		device_type = "memory";
	};

	psci {
		compatible = "arm,psci-1.0", "arm,psci-0.2", "arm,psci";
		method = "smc";
		cpu_suspend = <0xc4000001>;
		cpu_off = <0x84000002>;
		cpu_on = <0xc4000003>;
		sys_poweroff = <0x84000008>;
		sys_reset = <0x84000009>;
	};
	
	cpus {
		#size-cells = <0x00>;
		#address-cells = <0x01>;

		cpu@0{
			compatible = "arm,armv8";
			reg = <0>;
			device_type = "cpu";
			enable-method = "psci";
		};

		cpu@1 {
			compatible = "arm,armv8";
			reg = <0x100>;
			device_type = "cpu";
			enable-method = "psci";
		};
	};

	dummy_uart@28001000{
		compatible = "ft,sim";
		reg = <0x0 0x28001000 0x0 0x1000>;
		clock-frequency = <50000000>;
	};

};
```  
* 软仿使用
```
  $ cd mint/aarch64_moesi
  $ ivy build --dt sim.dts --tc ../toolchains/aarch64-none-linux-gnu.cmake --ic ../ivy_cfg/sim.py
  $ cmake --preset debug
  $ cmake --build --preset debug
  $ cd build/debug
  $ cp aarch64_mosei 软仿环境路径
```  
--ic 是指定生成激励时需要的配置，sim.py适用于硬仿和qemu

## 5. chi_moesi使用
在mint/chi_moesi的目录有:chi_moesi.py，调用py文件就可以生成sv文件
```
  $ cd mint/chi_moesi
  $ python chi_moesi.py --uvm_executor_name CdnChiExecutor --num_executors --uvm_output chi_test_case.sv --uvm_repeat_times=20 -S 13
```
 --uvm_executor_name executor 指定输出uvm源码中使用executor的类型名  
 --num_executors n 指定executors的数量  
 --uvm_output xx.sv 指定uvm输出文件  
 --uvm_repeat_times n 指定aciton重复次数  
 -S n 指定随机种子

