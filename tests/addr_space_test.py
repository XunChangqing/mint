import unittest
import logging
import random

from purslane import addr_space
from purslane.addr_space import AddrSpace, ShadowMemory

logger = logging.getLogger()

class TestAddrSpace(unittest.TestCase):
    def test_addr_space(self):
        addr_space = AddrSpace()
        addr_space.Add(0x40000000, 0x40080000-0x40000000)
        addr_space.Add(0x44080000, 0xc0000000-0x44080000)

        for ti in range(32):
            logger.info(f'test addr space iter {ti}')
            cls = []
            for i in range(64):
                addr = addr_space.AllocRandom(64, 64)
                # logger.info(f'alloc {addr:#x}')
                # for fr in addr_space.FreeRegions():
                #     logger.info(f'fr {fr.base:#x}, {fr.size:#x}, {fr.base+fr.size:#x}')
                self.assertEqual(addr%64, 0)
                cls.append(addr)
            
            logger.info('free')
            for cl in cls:
                addr_space.Free(cl, 64)
                # logger.info(f'free {cl:#x}')
                # for fr in addr_space.FreeRegions():
                #     logger.info(f'fr {fr.base:#x}, {fr.size:#x}, {fr.base+fr.size:#x}')

            frs = list(addr_space.FreeRegions())
            self.assertEqual(len(frs), 2)
            self.assertEqual(frs[0].base, 0x40000000)
            self.assertEqual(frs[0].size, (0x40080000 - 0x40000000))
            self.assertEqual(frs[1].base, 0x44080000)
            self.assertEqual(frs[1].size, (0xc0000000 - 0x44080000))


class TestShadowMemory(unittest.TestCase):
    def test_rw(self):
        sm = ShadowMemory()

        v = 0x1234567890abcdef

        vb = v.to_bytes(8, 'little')
        # print(vb.hex())

        sm.WriteBytes(0, v.to_bytes(8, 'little'))
        v0 = sm.ReadBytes(0, 8)
        # print(f'v0 {v0.hex()}')
        v0int = int.from_bytes(v0, 'little')
        self.assertEqual(v, v0int)

        sm.WriteBytes(addr_space.MEMORY_BLOCK_SIZE-4, vb)
        v1 = sm.ReadBytes(addr_space.MEMORY_BLOCK_SIZE-4, 8)
        # print(f'v1 {v1.hex()}')
        v1int = int.from_bytes(v1, 'little')
        self.assertEqual(v, v1int)


if __name__ == '__main__':
    random.seed(0)
    logging.basicConfig(level=logging.INFO)
    unittest.main()
