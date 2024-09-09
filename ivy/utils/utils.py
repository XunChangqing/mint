from makeelf import elf
from makeelf import elfstruct

def make_obj(obj_name, sym_name, bs, section = '.data'):
  dataobj = elf.ELF(e_class=elfstruct.ELFCLASS64,
                    e_data=elfstruct.ELFDATA.ELFDATA2LSB,
                    e_type=elfstruct.ET.ET_REL,
                    e_machine=elfstruct.EM.EM_AARCH64)
  data_sec = dataobj._append_section(sec_name=f'.{section}',
                          sec_data=bs,
                          sec_addr=0,
                          sh_type=elfstruct.SHT.SHT_PROGBITS,
                          sh_flags=elfstruct.SHF.SHF_WRITE | elfstruct.SHF.SHF_ALLOC)
  dataobj.append_symbol(sym_name=sym_name,
                        sym_section=data_sec,
                        sym_offset=0,
                        sym_size=len(bs),
                        sym_binding=elf.STB.STB_GLOBAL,
                        sym_type=elf.STT.STT_OBJECT,
                        sym_visibility=elf.STV.STV_DEFAULT)
  with open(f'{obj_name}', 'wb') as f:
    f.write(bytes(elf))
