仍然是一个锁配合counter进行测试的激励，但是有一些特点
1. 不同处理核可能访问不同的锁
2. 部分处理核不进行锁操作，只读取锁数据进行干扰
3. 多种加锁方法随机，目前包括基于 exclusive acquire-release 语义的实现，和 exclusive + dmb 的实现

NOTE
如果不适用 pair 方式进行加锁，则对于同一个 lock 可以使用不同的方式进行加锁，因为都是写1，并且 little endian，都是写入最低地址的方式

TODO
增加基于带 acquire-release 语义的原子操作的实现
