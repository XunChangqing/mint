import unittest
from ivy_dev.soc import xmb
from ivy_dev.soc import const

class TestXmbMethods(unittest.TestCase):
    def test(self):
        mb = xmb.MemBlock()
        mb.AddNode(0, 1024, 0)
        mb.AddNode(2048, 1024, 1)
        addr = mb.AllocNid(512, 1024, 1)
        self.assertEqual(addr, 2048)
        addr = mb.AllocNid(512, 1024, 0)
        self.assertEqual(addr, 0)
    
    def test_virt(self):
        mb = xmb.MemBlock()
        mem_base = 0x40000000
        mem_size = 0x80000000
        mb.AddNode(mem_base, mem_size, 0)
        max_text_size = 64*const.SIZE_MB
        page_size = 64*const.SIZE_KB
        ret = mb.AllocRange(max_text_size, page_size,
                      mem_base+64*const.SIZE_KB, mem_base+64*const.SIZE_KB+max_text_size)
        self.assertEqual(ret, mem_base+64*const.SIZE_KB)

if __name__ == '__main__':
    unittest.main()
