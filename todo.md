## 激励
* 裸机软仿
  * cache coherency，针对单个 cacheline 连续操作
    * 完善 dc 部分
    * 丰富 load 和 store 指令覆盖范围
    * 增加 dma load 和 store 实现部分
* 裸机仿真器
  * memory order 激励, litmus
  * cache coherency，大块数据，而不是只有一个 cacheline，可以测试到连续存储访问压力下，cache coherency 是否能保持正确
  * qspinlock
