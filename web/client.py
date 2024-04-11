import os
import tempfile
import tarfile
import requests
import shutil
from contextlib import contextmanager

@contextmanager
def chdir(path):
  old_path = os.getcwd()
  os.chdir(path)
  try:
    yield
  finally:
    os.chdir(old_path)

qemu_device_tree = """
/dts-v1/;

/ {
	interrupt-parent = <0x8002>;
	model = "linux,dummy-virt";
	#size-cells = <0x02>;
	#address-cells = <0x02>;
	compatible = "linux,dummy-virt";

	memory@40000000 {
		reg = <0x00 0x40000000 0x00 0x80000000>;
		device_type = "memory";
	};

	platform-bus@c000000 {
		interrupt-parent = <0x8002>;
		ranges = <0x00 0x00 0xc000000 0x2000000>;
		#address-cells = <0x01>;
		#size-cells = <0x01>;
		compatible = "qemu,platform\0simple-bus";
	};

	fw-cfg@9020000 {
		dma-coherent;
		reg = <0x00 0x9020000 0x00 0x18>;
		compatible = "qemu,fw-cfg-mmio";
	};

	virtio_mmio@a000000 {
		dma-coherent;
		interrupts = <0x00 0x10 0x01>;
		reg = <0x00 0xa000000 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a000200 {
		dma-coherent;
		interrupts = <0x00 0x11 0x01>;
		reg = <0x00 0xa000200 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a000400 {
		dma-coherent;
		interrupts = <0x00 0x12 0x01>;
		reg = <0x00 0xa000400 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a000600 {
		dma-coherent;
		interrupts = <0x00 0x13 0x01>;
		reg = <0x00 0xa000600 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a000800 {
		dma-coherent;
		interrupts = <0x00 0x14 0x01>;
		reg = <0x00 0xa000800 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a000a00 {
		dma-coherent;
		interrupts = <0x00 0x15 0x01>;
		reg = <0x00 0xa000a00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a000c00 {
		dma-coherent;
		interrupts = <0x00 0x16 0x01>;
		reg = <0x00 0xa000c00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a000e00 {
		dma-coherent;
		interrupts = <0x00 0x17 0x01>;
		reg = <0x00 0xa000e00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a001000 {
		dma-coherent;
		interrupts = <0x00 0x18 0x01>;
		reg = <0x00 0xa001000 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a001200 {
		dma-coherent;
		interrupts = <0x00 0x19 0x01>;
		reg = <0x00 0xa001200 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a001400 {
		dma-coherent;
		interrupts = <0x00 0x1a 0x01>;
		reg = <0x00 0xa001400 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a001600 {
		dma-coherent;
		interrupts = <0x00 0x1b 0x01>;
		reg = <0x00 0xa001600 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a001800 {
		dma-coherent;
		interrupts = <0x00 0x1c 0x01>;
		reg = <0x00 0xa001800 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a001a00 {
		dma-coherent;
		interrupts = <0x00 0x1d 0x01>;
		reg = <0x00 0xa001a00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a001c00 {
		dma-coherent;
		interrupts = <0x00 0x1e 0x01>;
		reg = <0x00 0xa001c00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a001e00 {
		dma-coherent;
		interrupts = <0x00 0x1f 0x01>;
		reg = <0x00 0xa001e00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a002000 {
		dma-coherent;
		interrupts = <0x00 0x20 0x01>;
		reg = <0x00 0xa002000 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a002200 {
		dma-coherent;
		interrupts = <0x00 0x21 0x01>;
		reg = <0x00 0xa002200 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a002400 {
		dma-coherent;
		interrupts = <0x00 0x22 0x01>;
		reg = <0x00 0xa002400 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a002600 {
		dma-coherent;
		interrupts = <0x00 0x23 0x01>;
		reg = <0x00 0xa002600 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a002800 {
		dma-coherent;
		interrupts = <0x00 0x24 0x01>;
		reg = <0x00 0xa002800 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a002a00 {
		dma-coherent;
		interrupts = <0x00 0x25 0x01>;
		reg = <0x00 0xa002a00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a002c00 {
		dma-coherent;
		interrupts = <0x00 0x26 0x01>;
		reg = <0x00 0xa002c00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a002e00 {
		dma-coherent;
		interrupts = <0x00 0x27 0x01>;
		reg = <0x00 0xa002e00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a003000 {
		dma-coherent;
		interrupts = <0x00 0x28 0x01>;
		reg = <0x00 0xa003000 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a003200 {
		dma-coherent;
		interrupts = <0x00 0x29 0x01>;
		reg = <0x00 0xa003200 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a003400 {
		dma-coherent;
		interrupts = <0x00 0x2a 0x01>;
		reg = <0x00 0xa003400 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a003600 {
		dma-coherent;
		interrupts = <0x00 0x2b 0x01>;
		reg = <0x00 0xa003600 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a003800 {
		dma-coherent;
		interrupts = <0x00 0x2c 0x01>;
		reg = <0x00 0xa003800 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a003a00 {
		dma-coherent;
		interrupts = <0x00 0x2d 0x01>;
		reg = <0x00 0xa003a00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a003c00 {
		dma-coherent;
		interrupts = <0x00 0x2e 0x01>;
		reg = <0x00 0xa003c00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	virtio_mmio@a003e00 {
		dma-coherent;
		interrupts = <0x00 0x2f 0x01>;
		reg = <0x00 0xa003e00 0x00 0x200>;
		compatible = "virtio,mmio";
	};

	gpio-restart {
		secure-status = "okay";
		status = "disabled";
		gpios = <0x8005 0x01 0x00>;
		compatible = "gpio-restart";
	};

	gpio-poweroff {
		secure-status = "okay";
		status = "disabled";
		gpios = <0x8005 0x00 0x00>;
		compatible = "gpio-poweroff";
	};

	pl061@90b0000 {
		secure-status = "okay";
		status = "disabled";
		phandle = <0x8005>;
		clock-names = "apb_pclk";
		clocks = <0x8000>;
		interrupts = <0x00 0x00 0x04>;
		gpio-controller;
		#gpio-cells = <0x02>;
		compatible = "arm,pl061\0arm,primecell";
		reg = <0x00 0x90b0000 0x00 0x1000>;
	};

	gpio-keys {
		compatible = "gpio-keys";

		poweroff {
			gpios = <0x8004 0x03 0x00>;
			linux,code = <0x74>;
			label = "GPIO Key Poweroff";
		};
	};

	pl061@9030000 {
		phandle = <0x8004>;
		clock-names = "apb_pclk";
		clocks = <0x8000>;
		interrupts = <0x00 0x07 0x04>;
		gpio-controller;
		#gpio-cells = <0x02>;
		compatible = "arm,pl061\0arm,primecell";
		reg = <0x00 0x9030000 0x00 0x1000>;
	};

	pcie@10000000 {
		interrupt-map-mask = <0x1800 0x00 0x00 0x07>;
		interrupt-map = <0x00 0x00 0x00 0x01 0x8002 0x00 0x00 0x00 0x03 0x04 0x00 0x00 0x00 0x02 0x8002 0x00 0x00 0x00 0x04 0x04 0x00 0x00 0x00 0x03 0x8002 0x00 0x00 0x00 0x05 0x04 0x00 0x00 0x00 0x04 0x8002 0x00 0x00 0x00 0x06 0x04 0x800 0x00 0x00 0x01 0x8002 0x00 0x00 0x00 0x04 0x04 0x800 0x00 0x00 0x02 0x8002 0x00 0x00 0x00 0x05 0x04 0x800 0x00 0x00 0x03 0x8002 0x00 0x00 0x00 0x06 0x04 0x800 0x00 0x00 0x04 0x8002 0x00 0x00 0x00 0x03 0x04 0x1000 0x00 0x00 0x01 0x8002 0x00 0x00 0x00 0x05 0x04 0x1000 0x00 0x00 0x02 0x8002 0x00 0x00 0x00 0x06 0x04 0x1000 0x00 0x00 0x03 0x8002 0x00 0x00 0x00 0x03 0x04 0x1000 0x00 0x00 0x04 0x8002 0x00 0x00 0x00 0x04 0x04 0x1800 0x00 0x00 0x01 0x8002 0x00 0x00 0x00 0x06 0x04 0x1800 0x00 0x00 0x02 0x8002 0x00 0x00 0x00 0x03 0x04 0x1800 0x00 0x00 0x03 0x8002 0x00 0x00 0x00 0x04 0x04 0x1800 0x00 0x00 0x04 0x8002 0x00 0x00 0x00 0x05 0x04>;
		#interrupt-cells = <0x01>;
		ranges = <0x1000000 0x00 0x00 0x00 0x3eff0000 0x00 0x10000 0x2000000 0x00 0x10000000 0x00 0x10000000 0x00 0x2eff0000 0x3000000 0x80 0x00 0x80 0x00 0x80 0x00>;
		reg = <0x40 0x10000000 0x00 0x10000000>;
		msi-map = <0x00 0x8003 0x00 0x10000>;
		dma-coherent;
		bus-range = <0x00 0xff>;
		linux,pci-domain = <0x00>;
		#size-cells = <0x02>;
		#address-cells = <0x03>;
		device_type = "pci";
		compatible = "pci-host-ecam-generic";
	};

	pl031@9010000 {
		clock-names = "apb_pclk";
		clocks = <0x8000>;
		interrupts = <0x00 0x02 0x04>;
		reg = <0x00 0x9010000 0x00 0x1000>;
		compatible = "arm,pl031\0arm,primecell";
	};

	pl011@9040000 {
		secure-status = "okay";
		status = "disabled";
		clock-names = "uartclk\0apb_pclk";
		clocks = <0x8000 0x8000>;
		interrupts = <0x00 0x08 0x04>;
		reg = <0x00 0x9040000 0x00 0x1000>;
		compatible = "arm,pl011\0arm,primecell";
	};

	secram@e000000 {
		secure-status = "okay";
		status = "disabled";
		reg = <0x00 0xe000000 0x00 0x1000000>;
		device_type = "memory";
	};

	pl011@9000000 {
		clock-names = "uartclk\0apb_pclk";
		clocks = <0x8000 0x8000>;
		interrupts = <0x00 0x01 0x04>;
		reg = <0x00 0x9000000 0x00 0x1000>;
		compatible = "arm,pl011\0arm,primecell";
	};

	pmu {
		interrupts = <0x01 0x07 0x104>;
		compatible = "arm,armv8-pmuv3";
	};

	intc@8000000 {
		phandle = <0x8002>;
		interrupts = <0x01 0x09 0x04>;
		reg = <0x00 0x8000000 0x00 0x10000 0x00 0x8010000 0x00 0x10000 0x00 0x8030000 0x00 0x10000 0x00 0x8040000 0x00 0x10000>;
		compatible = "arm,cortex-a15-gic";
		ranges;
		#size-cells = <0x02>;
		#address-cells = <0x02>;
		interrupt-controller;
		#interrupt-cells = <0x03>;

		v2m@8020000 {
			phandle = <0x8003>;
			reg = <0x00 0x8020000 0x00 0x1000>;
			msi-controller;
			compatible = "arm,gic-v2m-frame";
		};
	};

	flash@4000000 {
		bank-width = <0x04>;
		reg = <0x00 0x4000000 0x00 0x4000000>;
		compatible = "cfi-flash";
	};

	secflash@0 {
		secure-status = "okay";
		status = "disabled";
		bank-width = <0x04>;
		reg = <0x00 0x00 0x00 0x4000000>;
		compatible = "cfi-flash";
	};

	cpus {
		#size-cells = <0x00>;
		#address-cells = <0x01>;

		cpu-map {

			socket0 {

				cluster0 {

					core0 {
						cpu = <0x8001>;
					};
				};
			};
		};

		cpu@0 {
			phandle = <0x8001>;
			reg = <0x00>;
			compatible = "arm,cortex-a76";
			device_type = "cpu";
		};
	};

	timer {
		interrupts = <0x01 0x0d 0x104 0x01 0x0e 0x104 0x01 0x0b 0x104 0x01 0x0a 0x104>;
		always-on;
		compatible = "arm,armv8-timer\0arm,armv7-timer";
	};

	apb-pclk {
		phandle = <0x8000>;
		clock-output-names = "clk24mhz";
		clock-frequency = <0x16e3600>;
		#clock-cells = <0x00>;
		compatible = "fixed-clock";
	};

	secure-chosen {
		stdout-path = "/pl011@9040000";
		rng-seed = <0xde65937e 0x5826ced0 0x8e730e67 0xfb11c4ff 0xe9e08c1b 0xd66995d6 0x8eca3a7 0x3d10a1>;
		kaslr-seed = <0xd67378d6 0xda3b48eb>;
	};

	chosen {
		stdout-path = "/pl011@9000000";
		rng-seed = <0x92e435e0 0xd3c19fd8 0xd79a576 0x4e44a25b 0xebaabe90 0xe6445abc 0x578380bc 0x24b93ad8>;
		kaslr-seed = <0x8e5abddd 0xbb87a99b>;
	};
};
"""

# def GetSocHelloworld():
#   try:
#     req = {'seed': 10, 'device_tree' : qemu_device_tree, 'rt_cfg': {}, 'scen_cfg': {}}
#     rsp = requests.post('http://localhost:8080/api/stimulus/soc/scenario/helloworld', json = req)
#     rsp.raise_for_status()
#     with open('helloworld.tar', 'wb') as f:
#       f.write(rsp.content)
    
#     # 自动解压
#     # with tempfile.TemporaryDirectory(prefix="soc_helloworld_") as tmpdirname:
#     #     tmptar = os.path.join(tmpdirname, 'ret.tar')
#     #     with open(tmptar, 'wb') as f:
#     #       f.write(r.content)
        
#     #     result_dir = "helloworld"
#     #     shutil.rmtree(result_dir, ignore_errors=True)
#     #     os.makedirs(result_dir)
#     #     with tarfile.open(tmptar) as tar, chdir(result_dir):
#     #       tar.extractall()
#   except Exception as e:
#     print(e)

def GetSocBringup():
  try:
    req = {'seed': 10, 'device_tree' : qemu_device_tree, 'rt_cfg': {}, 'scen_cfg': {'name':1}}
    rsp = requests.post('http://localhost:8080/api/stimulus/soc/scenario/bringup', json = req)
    rsp.raise_for_status()
    with open('bringup.tar', 'wb') as f:
      f.write(rsp.content)
          
  except Exception as e:
      print(e)

if __name__ == '__main__':
#   GetSocHelloworld()
  GetSocBringup()