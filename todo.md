# 具体激励
* pci 设备枚举，bus id 配置，bar 配置
* mlmo 直接输出 asm，并且插入随机代码噪声
* stressapp sv 实现
* c_stressapp 不同的 copy 方法, dma_copy
  * 考虑一个动态 c_stressapp
* pcie pio, dma 存储序测试激励

* 3000v dma
* zni dma
* thirdparty dma

# 方法学
* purslane 几个不同任务的合并执行
* 类似 riscv 的指令级别随机生成, 如果能够 model based 最好，以便相同激励在不同指令集之间移植
  * 定向指令序列和随机指令序列的mixing，如何保证随机指令序列不会干扰定向指令序列
    * 随机噪声的明确目标，增加覆盖的目标，处理核流水线、存储系统场景
  * 子程序生成
  * 类似 threadmill 的 filler 产生噪音
  * 类似 threadmill 的 irritator 在超线程处理核上增加多线程压力
* 建立 tm 中几个测试激励

threadmill 中可以通过 concurrent 将激励分成多个 phase，无法支持灵活的场景级建模
