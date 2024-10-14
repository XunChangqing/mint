`include "pattern.svh"

// function 

function denaliChiSizeT ToChiSize(bit [7:0] s);
  case (s)
    0: return DENALI_CHI_SIZE_UNSET;
    1: return DENALI_CHI_SIZE_BYTE;
    2: return DENALI_CHI_SIZE_HALFWORD;
    4: return DENALI_CHI_SIZE_WORD;
    8: return DENALI_CHI_SIZE_DOUBLEWORD;
    16: return DENALI_CHI_SIZE_QUARTERLINE;
    32: return DENALI_CHI_SIZE_HALFLINE;
    64: return DENALI_CHI_SIZE_FULLLINE;
    default: return DENALI_CHI_SIZE_UNSET;
  endcase
endfunction


class StressAppExecutor extends cdnChiUvmSequence;
  cdnChiUvmAgent agent;
  int id;

  function new(cdnChiUvmAgent agent);
    this.agent = agent;

    // avoid overflow, the default response queue depth is 8
    set_response_queue_depth(-1);
  endfunction

//   function void AddAddrInUse(bit [63:0] addr);
//     bit [63:0] aligned_addr = addr;
//     aligned_addr[5:0] = 0;
//     addr_board[aligned_addr] = 1;
//   endfunction : AddAddrInUse

//   function void FreeAddrInUse(bit [63:0] addr);
//     bit [63:0] aligned_addr = addr;
//     aligned_addr[5:0] = 0;
//     addr_board.delete(aligned_addr);
//   endfunction : FreeAddrInUse

//   task WaitAddrInUse(bit [63:0] addr);
//     bit [63:0] aligned_addr = addr;
//     aligned_addr[5:0] = 0;
//     `WAIT_WITH_WARNING(addr_board.exists(aligned_addr) == 0, wait_for_addr_board);
//   endtask

  // little endian
  // dl 数组按照地址序，从小到大
  // 返回 512 数据为该数组的 little endian 值
  function bit [511:0] ConcatClArr(bit [7:0] dl[]);
    bit [511:0] ret = 512'h0;
    for (int i = 64 - 1; i >= 0; i--) begin
      ret = (ret << 8);
      ret[7:0] = dl[i];
    end
    return ret;
  endfunction

  // little endian
  function void SplitCacheline(bit [511:0] cl, ref bit [7:0] ret[]);
    ret = new[64];
    for (int i = 0; i < 64; i++) begin
      ret[i] = cl[7:0];
      cl = (cl >> 8);
    end
  endfunction

  function bit CmpByteArr(bit [7:0] ev[], bit [7:0] dv[]);
    if (ev.size() != dv.size()) begin
      return 0;
    end

    for (int i = 0; i < ev.size(); i++) begin
      if (ev[i] != dv[i]) begin
        return 0;
      end
    end
    return 1;
  endfunction

  function string StrByteArr(bit [7:0] ev[]);
    string dv_str;
    for (int i = 0; i < ev.size(); i++) begin
      dv_str = {dv_str, $sformatf("%02x", ev[i])};
    end
    return dv_str;
  endfunction

  // no parallel actions will act on the same page

  task fill(bit [63:0] addr, int page_length, int pattern_idx);
  endtask

  task copy(bit [63:0] src_addr, bit[63:0] dst_addr, int page_length);
    reg [7:0] dut_value[];
    // ReadNotSharedDirty
    // ReadShared
    agent.inst.cacheRead(aligned_addr, state, dut_value, read_be, non_secure);
  endtask

  task invert_up(bit[63:0] addr, int page_length);
  endtask

  task invert_down(bit[63:0] addr, int page_length);
  endtask

  task invert(bit[63:0] addr, int page_length);
    invert_up(addr, page_length);
    invert_down(addr, page_length);
    invert_up(addr, page_length);
    invert_down(addr, page_length);
  endtask

  task check(bit[63:0] addr, int page_length, int pattern_idx);
  endtask

  task ReadRequest(denaliChiReqOpCodeT opcode, string name, bit [63:0] addr,
                   bit [7:0] expected_value[], bit need_unique = 0);
    denaliChiTransaction trans;
    denaliChiTransaction rsp_trans;
    uvm_sequence_item item;
    denaliChiCacheLineStateT state;

    reg [7:0] dut_value[];
    reg read_be[];
    reg [63:0] aligned_addr;
    reg non_secure = 0;

    bit issue_req = 0;

    aligned_addr = addr;
    aligned_addr[5:0] = 0;

    `uvm_info($sformatf("%s@%d", name, this.id), $sformatf(
              "addr: %x, expected value: %s", addr, StrByteArr(expected_value)), UVM_NONE);

    WaitAddrInUse(aligned_addr);
    `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
    // 要添加块地址，地址不同，但是同一个块的访问是冲突的
    AddAddrInUse(aligned_addr);

    agent.inst.cacheRead(aligned_addr, state, dut_value, read_be, non_secure);

    if (state == DENALI_CHI_CACHELINESTATE_Invalid) begin
      issue_req = 1;
    end
    else if((state == DENALI_CHI_CACHELINESTATE_SharedClean) || (state == DENALI_CHI_CACHELINESTATE_SharedDirty)) begin
      if (need_unique) begin
        issue_req = 1;
      end
    end
    else if(state == DENALI_CHI_CACHELINESTATE_UniqueCleanEmpty ||state ==  DENALI_CHI_CACHELINESTATE_UniqueDirtyPartial) begin
      issue_req = 1;
    end

    if (issue_req) begin
      `uvm_do_on_with(trans, agent.sequencer,
                      {
            trans.ReqOpCode == opcode;
            trans.Addr == aligned_addr;
            trans.Size == DENALI_CHI_SIZE_FULLLINE;
            trans.NonSecure == 0;
            // retry automatically
            trans.CancelOnRetryAck == 0;
            trans.MemAttr == 4'hd;
            trans.SnpAttr == 1;
            })
      get_response(item, trans.get_transaction_id());
      $cast(rsp_trans, item);
      dut_value = rsp_trans.Data;
    end

    if (!CmpByteArr(dut_value, expected_value)) begin
      `uvm_fatal($sformatf("%s@%d", name, this.id), $sformatf(
                 "addr: %x, expected value: %s, dut value: %s",
                 addr,
                 StrByteArr(
                     expected_value
                 ),
                 StrByteArr(
                     dut_value
                 )
                 ));
    end

    FreeAddrInUse(aligned_addr);
  endtask

  task ReadOnce(bit [63:0] addr, bit [7:0] value[]);
    ReadRequest(DENALI_CHI_REQOPCODE_ReadOnce, "ReadOnce", addr, value);
  endtask

  task ReadClean(bit [63:0] addr, bit [7:0] value[]);
    ReadRequest(DENALI_CHI_REQOPCODE_ReadClean, "ReadClean", addr, value);
  endtask

  task ReadShared(bit [63:0] addr, bit [7:0] value[]);
    ReadRequest(DENALI_CHI_REQOPCODE_ReadShared, "ReadShared", addr, value);
  endtask

  task ReadNotSharedDirty(bit [63:0] addr, bit [7:0] value[]);
    ReadRequest(DENALI_CHI_REQOPCODE_ReadNotSharedDirty, "ReadNotSharedDirty", addr, value);
  endtask

  task ReadUnique(bit [63:0] addr, bit [7:0] value[]);
    ReadRequest(DENALI_CHI_REQOPCODE_ReadUnique, "ReadUnique", addr, value, 1);
  endtask

  // task ReadPreferUnique(bit [63:0] addr, bit [511:0] value);
  //   ReadRequest(DENALI_CHI_REQOPCODE_ReadPreferUnique, "ReadPreferUnique", addr, value);
  // endtask

  task DatalessRequest(denaliChiReqOpCodeT opcode, string name, bit [63:0] addr);
    denaliChiTransaction trans;
    denaliChiTransaction rsp_trans;
    uvm_sequence_item item;
    denaliChiCacheLineStateT state;

    reg [7:0] cl_data_arr[];
    reg read_be[];
    reg [63:0] aligned_addr;
    reg non_secure = 0;
    bit issue_req = 1;

    aligned_addr = addr;
    aligned_addr[5:0] = 0;

    `uvm_info($sformatf("%s@%d", name, this.id), $sformatf("addr: %x", addr), UVM_NONE)

    WaitAddrInUse(aligned_addr);
    `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
    // 要添加块地址，地址不同，但是同一个块的访问是冲突的
    AddAddrInUse(aligned_addr);

    agent.inst.cacheRead(aligned_addr, state, cl_data_arr, read_be, non_secure);

    // if (opcode == DENALI_CHI_REQOPCODE_Evict) begin
    //   if (state == DENALI_CHI_CACHELINESTATE_Invalid) begin
    //     issue_req = 0;
    //   end

    //   if(state == DENALI_CHI_CACHELINESTATE_SharedDirty || state == DENALI_CHI_CACHELINESTATE_UniqueDirty) begin
    //     `uvm_fatal("", $sformatf("try to evict dirty cacheline, addr: %x", addr));
    //   end
    // end

    if(opcode == DENALI_CHI_REQOPCODE_MakeUnique || opcode == DENALI_CHI_REQOPCODE_CleanUnique) begin
      if(state == DENALI_CHI_CACHELINESTATE_UniqueClean || state == DENALI_CHI_CACHELINESTATE_UniqueDirty) begin
        issue_req = 0;
      end
    end

    if (opcode == DENALI_CHI_REQOPCODE_CleanInvalid || opcode == DENALI_CHI_REQOPCODE_CleanShared) begin
      // if(state == DENALI_CHI_CACHELINESTATE_UniqueClean || state == DENALI_CHI_CACHELINESTATE_UniqueDirty) begin
      //   issue_req = 0;
      // end
      // ensure to invalid
      SafeEvictUnlock(addr);
    end

    if (issue_req) begin
      `uvm_do_on_with(trans, agent.sequencer,
                      {
            trans.ReqOpCode == opcode;
            trans.Addr == aligned_addr;
            trans.Size == DENALI_CHI_SIZE_FULLLINE;
            trans.NonSecure == 0;
            // retry automatically
            trans.CancelOnRetryAck == 0;
            trans.MemAttr == 4'hd;
            trans.SnpAttr == 1;
            trans.Excl == 0;
            })
      get_response(item, trans.get_transaction_id());
    end

    FreeAddrInUse(aligned_addr);
  endtask

  // task CleanUnique(bit [63:0] addr);
  //   DatalessRequest(DENALI_CHI_REQOPCODE_CleanUnique, "CleanUnique", addr);
  // endtask

  // task MakeUnique(bit [63:0] addr, bit [7:0] value[]);
  //   denaliChiTransaction trans;
  //   denaliChiTransaction rsp_trans;
  //   uvm_sequence_item item;
  //   denaliChiCacheLineStateT state;

  //   reg be[];
  //   reg cacheline_be[];
  //   reg [63:0] aligned_addr;

  //   bit non_secure = 0;
  //   reg [7:0] read_data[];  //temp parameter but no use

  //   be = new[64];
  //   aligned_addr = addr;
  //   aligned_addr[5:0] = 0;

  //   `uvm_info($sformatf("MakeUnique@%d", this.id), $sformatf("addr: %x, value: %s", addr, StrByteArr(
  //                                                        value)), UVM_NONE)

  //   WaitAddrInUse(aligned_addr);
  //   `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
  //   // 要添加块地址，地址不同，但是同一个块的访问是冲突的
  //   AddAddrInUse(aligned_addr);

  //   agent.inst.cacheRead(aligned_addr, state, read_data, cacheline_be, non_secure);
  //   if((state == DENALI_CHI_CACHELINESTATE_Invalid)||
  //       (state == DENALI_CHI_CACHELINESTATE_SharedClean)||
  //       (state == DENALI_CHI_CACHELINESTATE_SharedDirty))begin

  //     `uvm_create_on(trans, agent.sequencer);

  //     trans.randomize() with {
  //       trans.ReqOpCode == DENALI_CHI_REQOPCODE_MakeUnique;
  //       trans.Addr == aligned_addr;
  //       trans.Size == DENALI_CHI_SIZE_FULLLINE;
  //       trans.NonSecure == 0;
  //       // retry automatically
  //       trans.CancelOnRetryAck == 0;
  //       trans.MemAttr == 4'hd;
  //     };

  //     `uvm_send(trans);
  //     get_response(item, trans.get_transaction_id());
  //     $cast(rsp_trans, item);
  //   end

  //   for (int i = 0; i < 64; i++) begin
  //     cacheline_be[i] = 1;
  //   end

  //   state = DENALI_CHI_CACHELINESTATE_UniqueDirty;
  //   agent.inst.cacheWrite(aligned_addr, state, value, cacheline_be, non_secure);

  //   FreeAddrInUse(aligned_addr);
  // endtask

  task Evict(bit [63:0] addr);
    DatalessRequest(DENALI_CHI_REQOPCODE_Evict, "Evict", addr);
  endtask

  task CleanShared(bit [63:0] addr);
    DatalessRequest(DENALI_CHI_REQOPCODE_CleanShared, "CleanShared", addr);
  endtask

  task CleanInvalid(bit [63:0] addr);
    DatalessRequest(DENALI_CHI_REQOPCODE_CleanInvalid, "CleanInvalid", addr);
  endtask

  task MakeInvalid(bit [63:0] addr);
    DatalessRequest(DENALI_CHI_REQOPCODE_MakeInvalid, "MakeInvalid", addr);
  endtask

  task WritebackRequest(denaliChiReqOpCodeT opcode, string name, bit [63:0] addr);
    denaliChiTransaction trans;
    denaliChiTransaction rsp_trans;
    uvm_sequence_item item;
    denaliChiCacheLineStateT state;

    reg [7:0] cl_data_arr[];
    reg read_be[];
    reg [63:0] aligned_addr;
    reg non_secure = 0;
    bit issue_req = 1;

    aligned_addr = addr;
    aligned_addr[5:0] = 0;

    `uvm_info($sformatf("%s@%d", name, this.id), $sformatf("addr: %x", addr), UVM_NONE);

    WaitAddrInUse(aligned_addr);
    `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
    // 要添加块地址，地址不同，但是同一个块的访问是冲突的
    AddAddrInUse(aligned_addr);


    agent.inst.cacheRead(aligned_addr, state, cl_data_arr, read_be, non_secure);

    if (opcode == DENALI_CHI_REQOPCODE_WriteCleanFull) begin
      if (state != DENALI_CHI_CACHELINESTATE_UniqueDirty && state != DENALI_CHI_CACHELINESTATE_SharedDirty) begin
        `uvm_info($sformatf("%s@%d", name, this.id), "no need to WriteCleanFull", UVM_NONE);
        issue_req = 0;
      end
    end

    // if (opcode == DENALI_CHI_REQOPCODE_Evict) begin
    //   if (state == DENALI_CHI_CACHELINESTATE_Invalid) begin
    //     issue_req = 0;
    //   end

    //   if(state == DENALI_CHI_CACHELINESTATE_SharedDirty || state == DENALI_CHI_CACHELINESTATE_UniqueDirty) begin
    //     `uvm_fatal("", $sformatf("try to evict dirty cacheline, addr: %x", addr))
    //   end
    // end

    if (issue_req) begin
      `uvm_do_on_with(trans, agent.sequencer,
                      {
            trans.ReqOpCode == opcode;
            trans.Addr == aligned_addr;
            trans.Size == DENALI_CHI_SIZE_FULLLINE;
            trans.NonSecure == 0;
            // retry automatically
            trans.CancelOnRetryAck == 0;
            trans.MemAttr == 4'hd;
            trans.SnpAttr == 1;
            })
      get_response(item, trans.get_transaction_id());
    end

    FreeAddrInUse(aligned_addr);
  endtask

  task WriteBackFull(bit [63:0] addr);
    WritebackRequest(DENALI_CHI_REQOPCODE_WriteBackFull, "WriteBackFull", addr);
  endtask

  task WriteCleanFull(bit [63:0] addr);
    WritebackRequest(DENALI_CHI_REQOPCODE_WriteCleanFull, "WriteCleanFull", addr);
  endtask

  task WriteEvictFull(bit [63:0] addr);
    WritebackRequest(DENALI_CHI_REQOPCODE_WriteEvictFull, "WriteEvictFull", addr);
  endtask

  task SafeEvictUnlock(bit [63:0] addr);
    denaliChiTransaction trans;
    denaliChiTransaction rsp_trans;
    uvm_sequence_item item;
    denaliChiCacheLineStateT state;

    reg [7:0] cl_data_arr[];
    reg read_be[];
    reg [63:0] aligned_addr;
    reg non_secure = 0;
    denaliChiReqOpCodeT opcode = DENALI_CHI_REQOPCODE_UNSET;
    bit use_write_evict = 0;
    bit [3:0] mem_attr = 4'hd;

    aligned_addr = addr;
    aligned_addr[5:0] = 0;

    `uvm_info($sformatf("SafeEvict@%d", this.id), $sformatf("addr: %x", addr), UVM_NONE);

    agent.inst.cacheRead(aligned_addr, state, cl_data_arr, read_be, non_secure);

    // dirty --> WriteBackFull
    if(state == DENALI_CHI_CACHELINESTATE_SharedDirty || state == DENALI_CHI_CACHELINESTATE_UniqueDirty) begin
      opcode = DENALI_CHI_REQOPCODE_WriteBackFull;
    end else if (state == DENALI_CHI_CACHELINESTATE_UniqueClean) begin
      opcode = DENALI_CHI_REQOPCODE_WriteEvictFull;
    end else if (state == DENALI_CHI_CACHELINESTATE_SharedClean) begin
      opcode   = DENALI_CHI_REQOPCODE_Evict;
      mem_attr = 4'b0101;
    end

    if (opcode != DENALI_CHI_REQOPCODE_UNSET) begin
      `uvm_do_on_with(trans, agent.sequencer,
                      {
            trans.ReqOpCode == opcode;
            trans.Addr == aligned_addr;
            trans.Size == DENALI_CHI_SIZE_FULLLINE;
            trans.NonSecure == 0;
            // retry automatically
            trans.CancelOnRetryAck == 0;
            trans.MemAttr == mem_attr;
            trans.SnpAttr == 1;
            })
      get_response(item, trans.get_transaction_id());
    end
  endtask

  task SafeEvict(bit [63:0] addr);
    bit [63:0] aligned_addr;
    aligned_addr = addr;
    aligned_addr[5:0] = 0;

    WaitAddrInUse(aligned_addr);
    `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
    // 要添加块地址，地址不同，但是同一个块的访问是冲突的
    AddAddrInUse(aligned_addr);

    SafeEvictUnlock(addr);

    FreeAddrInUse(aligned_addr);
  endtask


  // atomic opcode
  // 0 - ADD
  // 1 - CLR
  // 2 - EOR
  // 3 - SET
  // 4 - SMAX
  // 5 - SMIN
  // 6 - UMAX
  // 7 - UMIN

  // task AtomicLoad(bit [63:0] addr, bit [511:0] expected_value, bit[7:0] atomic_opcode, bit[7:0] offset, bit[7:0] size);
  //   denaliChiTransaction trans;
  //   denaliChiTransaction rsp_trans;
  //   uvm_sequence_item item;
  //   denaliChiCacheLineStateT state;

  //   bit [511:0] dut_value;
  //   reg [7:0] cl_data_arr[];
  //   reg read_be[];
  //   reg [63:0] aligned_addr;
  //   reg non_secure = 0;

  //   aligned_addr = addr;
  //   aligned_addr[5:0] = 0;

  //   `uvm_info($sformatf("%s@%d", name, this.id), $sformatf("addr: %x, expected value: %x", addr,
  //                                                          expected_value), UVM_NONE)

  //   WaitAddrInUse(aligned_addr);
  //   `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
  //   // 要添加块地址，地址不同，但是同一个块的访问是冲突的
  //   AddAddrInUse(aligned_addr);

  //   agent.inst.cacheRead(aligned_addr, state, cl_data_arr, read_be, non_secure);

  //   `uvm_do_on_with(trans, agent.sequencer,
  //                   {
  //           trans.ReqOpCode == DENALI_CHI_REQOPCODE_AtomicLoad_ADD;
  //           trans.Addr == aligned_addr;
  //           trans.Size == DENALI_CHI_SIZE_FULLLINE;
  //           trans.NonSecure == 0;
  //           // retry automatically
  //           trans.CancelOnRetryAck == 0;
  //           })
  //   get_response(item, trans.get_transaction_id());
  //   $cast(rsp_trans, item);
  //   cl_data_arr = rsp_trans.Data;

  //   dut_value   = ConcatClArr(cl_data_arr);

  //   if (dut_value != expected_value) begin
  //     `uvm_fatal($sformatf("%s@%d", name, this.id),
  //                $sformatf("addr: %x, expected value: %x, dut value: %x", addr, expected_value,
  //                          dut_value))
  //   end

  //   FreeAddrInUse(aligned_addr);
  // endtask

  task AtomicSwap(bit [63:0] addr, bit [7:0] init_value[], bit [7:0] swap_value[], bit [7:0] offset,
                  bit [7:0] size);
    denaliChiTransaction trans;
    denaliChiTransaction rsp_trans;
    uvm_sequence_item item;
    denaliChiCacheLineStateT state;

    bit [7:0] dut_value[];
    reg read_be[];
    reg [63:0] aligned_addr;
    reg non_secure = 0;
    denaliChiSizeT chi_size;
    string ops_name;

    chi_size = ToChiSize(size);

    aligned_addr = addr;
    aligned_addr[5:0] = 0;

    ops_name = $sformatf("AtomicSwap@%d", this.id);

    `uvm_info($sformatf("AtomicSwap@%d", this.id), $sformatf(
              "addr: %x, init value: %s, swap value: %s, offset: %d, size: %d",
              addr,
              StrByteArr(
                  init_value
              ),
              StrByteArr(
                  swap_value
              ),
              offset,
              size
              ), UVM_NONE);

    WaitAddrInUse(aligned_addr);
    `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
    // 要添加块地址，地址不同，但是同一个块的访问是冲突的
    AddAddrInUse(aligned_addr);

    state = agent.inst.getCacheLineState(addr);
    if (state != DENALI_CHI_CACHELINESTATE_Invalid) begin
      `uvm_info(ops_name, "cacheline is not invalid", UVM_NONE);
      SafeEvictUnlock(addr);
    end

    `uvm_create_on(trans, agent.sequencer);
    trans.randomize() with {trans.ReqOpCode == DENALI_CHI_REQOPCODE_AtomicSwap;
                            trans.Addr == (addr + offset);
                            trans.Size == chi_size;
                            trans.NonSecure == 0;
                            // retry automatically
                            trans.CancelOnRetryAck == 0;
                            trans.MemAttr == 4'hd;
                            trans.SnpAttr == 1;
                            };
    trans.Data = swap_value;
    `uvm_send(trans);

    get_response(item, trans.get_transaction_id());
    $cast(rsp_trans, item);
    dut_value = rsp_trans.ReturnData;

    if (dut_value.size() != size) begin
      `uvm_fatal($sformatf("AtomicSwap@%d", this.id), $sformatf(
                 "rsp data size: %d, expected size: %d", dut_value.size(), init_value.size()));
    end

    if (!CmpByteArr(init_value, dut_value)) begin
      `uvm_fatal($sformatf("AtomicSwap@%d", this.id), $sformatf(
                 "addr: %x, init value: %s, dut value: %s",
                 addr,
                 StrByteArr(
                     init_value
                 ),
                 StrByteArr(
                     dut_value
                 )
                 ));
    end

    FreeAddrInUse(aligned_addr);
  endtask

  task AtomicCompare(bit [63:0] addr, bit [7:0] init_value[], bit [7:0] cmp_value[],
                     bit [7:0] swap_value[], bit [7:0] offset, bit [7:0] size);
    denaliChiTransaction trans;
    denaliChiTransaction rsp_trans;
    uvm_sequence_item item;
    denaliChiCacheLineStateT state;

    bit [7:0] dut_value[];
    reg read_be[];
    reg [63:0] aligned_addr;
    reg non_secure = 0;
    denaliChiSizeT chi_size;
    int i;
    string ops_name;

    chi_size = ToChiSize(size * 2);

    aligned_addr = addr;
    aligned_addr[5:0] = 0;

    ops_name = $sformatf("AtomicCompare@%d", this.id);

    `uvm_info($sformatf("AtomicCompare@%d", this.id), $sformatf(
              "addr: %x, init value: %s, cmp value: %s, swap value: %s, offset: %d, size: %d",
              addr,
              StrByteArr(
                  init_value
              ),
              StrByteArr(
                  cmp_value
              ),
              StrByteArr(
                  swap_value
              ),
              offset,
              size
              ), UVM_NONE);

    WaitAddrInUse(aligned_addr);
    `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
    // 要添加块地址，地址不同，但是同一个块的访问是冲突的
    AddAddrInUse(aligned_addr);

    state = agent.inst.getCacheLineState(addr);
    if (state != DENALI_CHI_CACHELINESTATE_Invalid) begin
      `uvm_info(ops_name, "cacheline is not invalid", UVM_NONE);
      SafeEvictUnlock(addr);
    end

    `uvm_create_on(trans, agent.sequencer);
    trans.randomize() with {trans.ReqOpCode == DENALI_CHI_REQOPCODE_AtomicCompare;
                            trans.Addr == (addr + offset);
                            trans.Size == chi_size;
                            trans.NonSecure == 0;
                            // retry automatically
                            trans.CancelOnRetryAck == 0;
                            trans.MemAttr == 4'hd;
                            trans.SnpAttr == 1;
                            };

    if (trans.Data.size() != size * 2) begin
      `uvm_fatal($sformatf("AtomicSwap@%d", this.id), $sformatf(
                 "data size is incorrect: %d", trans.Data.size()));
    end

    // cmp 数据总是在前
    for (i = 0; i < size; i++) begin
      trans.Data[i] = cmp_value[i];
    end

    // swap 数据在后， vip会根据需要重新排序
    for (i = 0; i < size; i++) begin
      trans.Data[size+i] = swap_value[i];
    end


    `uvm_send(trans);

    get_response(item, trans.get_transaction_id());
    $cast(rsp_trans, item);
    dut_value = rsp_trans.ReturnData;

    if (dut_value.size() != size) begin
      `uvm_fatal($sformatf("AtomicSwap@%d", this.id), $sformatf(
                 "rsp data size: %d, expected size: %d", dut_value.size(), init_value.size()));
    end

    if (!CmpByteArr(init_value, dut_value)) begin
      `uvm_fatal($sformatf("AtomicSwap@%d", this.id), $sformatf(
                 "addr: %x, init value: %s, dut value: %s",
                 addr,
                 StrByteArr(
                     init_value
                 ),
                 StrByteArr(
                     dut_value
                 )
                 ));
    end

    FreeAddrInUse(aligned_addr);
  endtask

  task AtomicLoad(bit [63:0] addr, bit [7:0] init_value[], bit [7:0] txn_value[], bit [7:0] offset,
                  bit [7:0] size, denaliChiReqOpCodeT opcode);
    denaliChiTransaction trans;
    denaliChiTransaction rsp_trans;
    uvm_sequence_item item;
    denaliChiCacheLineStateT state;

    bit [7:0] dut_value[];
    reg read_be[];
    reg [63:0] aligned_addr;
    reg non_secure = 0;
    denaliChiSizeT chi_size;
    int i;
    string ops_name;

    chi_size = ToChiSize(size);

    aligned_addr = addr;
    aligned_addr[5:0] = 0;

    ops_name = $sformatf("AtomicLoad@%d", this.id);

    `uvm_info(ops_name, $sformatf(
              "addr: %x, init value: %s, txn value: %s, offset: %d, size: %d",
              addr,
              StrByteArr(
                  init_value
              ),
              StrByteArr(
                  txn_value
              ),
              offset,
              size
              ), UVM_NONE);

    WaitAddrInUse(aligned_addr);
    `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
    // 要添加块地址，地址不同，但是同一个块的访问是冲突的
    AddAddrInUse(aligned_addr);

    state = agent.inst.getCacheLineState(addr);
    if (state != DENALI_CHI_CACHELINESTATE_Invalid) begin
      `uvm_info(ops_name, "cacheline is not invalid", UVM_NONE);
      SafeEvictUnlock(addr);
    end

    `uvm_create_on(trans, agent.sequencer);
    trans.randomize() with {trans.ReqOpCode == opcode;
                            trans.Addr == (addr + offset);
                            trans.Size == chi_size;
                            trans.NonSecure == 0;
                            // retry automatically
                            trans.CancelOnRetryAck == 0;
                            trans.MemAttr == 4'hd;
                            trans.SnpAttr == 1;
                            trans.Endian == 0;
                            };

    if (trans.Data.size() != size) begin
      `uvm_fatal(ops_name, $sformatf("data size is incorrect: %d", trans.Data.size()));
    end

    for (i = 0; i < size; i++) begin
      trans.Data[i] = txn_value[i];
    end

    `uvm_send(trans);

    get_response(item, trans.get_transaction_id());
    $cast(rsp_trans, item);
    dut_value = rsp_trans.ReturnData;

    if (dut_value.size() != size) begin
      `uvm_fatal(ops_name, $sformatf(
                 "rsp data size: %d, expected size: %d", dut_value.size(), init_value.size()));
    end

    if (!CmpByteArr(init_value, dut_value)) begin
      `uvm_fatal(ops_name, $sformatf(
                 "addr: %x, init value: %s, dut value: %s",
                 addr,
                 StrByteArr(
                     init_value
                 ),
                 StrByteArr(
                     dut_value
                 )
                 ));
    end

    FreeAddrInUse(aligned_addr);
  endtask

  task AtomicStore(bit [63:0] addr, bit [7:0] txn_value[], bit [7:0] offset, bit [7:0] size,
                   denaliChiReqOpCodeT opcode);
    denaliChiTransaction trans;
    denaliChiTransaction rsp_trans;
    uvm_sequence_item item;
    denaliChiCacheLineStateT state;

    bit [7:0] dut_value[];
    reg read_be[];
    reg [63:0] aligned_addr;
    reg non_secure = 0;
    denaliChiSizeT chi_size;
    int i;
    string ops_name;

    chi_size = ToChiSize(size);

    aligned_addr = addr;
    aligned_addr[5:0] = 0;

    ops_name = $sformatf("AtomicStore@%d", this.id);

    `uvm_info(
        ops_name, $sformatf(
        "addr: %x, txn value: %s, offset: %d, size: %d", addr, StrByteArr(txn_value), offset, size),
        UVM_NONE);

    WaitAddrInUse(aligned_addr);
    `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
    // 要添加块地址，地址不同，但是同一个块的访问是冲突的
    AddAddrInUse(aligned_addr);

    state = agent.inst.getCacheLineState(addr);
    if (state != DENALI_CHI_CACHELINESTATE_Invalid) begin
      `uvm_info(ops_name, "cacheline is not invalid", UVM_NONE);
      SafeEvictUnlock(addr);
    end

    `uvm_create_on(trans, agent.sequencer);
    trans.randomize() with {trans.ReqOpCode == opcode;
                            trans.Addr == (addr + offset);
                            trans.Size == chi_size;
                            trans.NonSecure == 0;
                            // retry automatically
                            trans.CancelOnRetryAck == 0;
                            trans.MemAttr == 4'hd;
                            trans.SnpAttr == 1;
                            trans.Endian == 0;
                            };

    if (trans.Data.size() != size) begin
      `uvm_fatal(ops_name, $sformatf("data size is incorrect: %d", trans.Data.size()));
    end

    for (i = 0; i < size; i++) begin
      trans.Data[i] = txn_value[i];
    end

    `uvm_send(trans);

    get_response(item, trans.get_transaction_id());
    $cast(rsp_trans, item);

    FreeAddrInUse(aligned_addr);
  endtask

  task WriteUniqueFull(bit [63:0] addr, bit [7:0] value[]);
    denaliChiTransaction trans;
    denaliChiTransaction rsp_trans;
    uvm_sequence_item item;
    denaliChiCacheLineStateT state;

    reg [63:0] aligned_addr;
    string ops_name;

    aligned_addr = addr;
    aligned_addr[5:0] = 0;

    ops_name = $sformatf("WriteUniqueFull@%d", this.id);

    `uvm_info($sformatf("WriteUniqueFull@%d", this.id), $sformatf("addr: %x, value: %s", addr, StrByteArr(value)), UVM_NONE)

    WaitAddrInUse(aligned_addr);
    `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
    // 要添加块地址，地址不同，但是同一个块的访问是冲突的
    AddAddrInUse(aligned_addr);

    state = agent.inst.getCacheLineState(addr);
    if (state != DENALI_CHI_CACHELINESTATE_Invalid) begin
      `uvm_info(ops_name, "cacheline is not invalid", UVM_NONE);
      SafeEvictUnlock(addr);
    end

    `uvm_create_on(trans, agent.sequencer);
    trans.randomize() with {trans.ReqOpCode == DENALI_CHI_REQOPCODE_WriteUniqueFull;
                            trans.Addr == addr;
                            trans.Size == DENALI_CHI_SIZE_FULLLINE;
                            trans.NonSecure == 0;
                            // retry automatically
                            trans.CancelOnRetryAck == 0;
                            trans.MemAttr == 4'hd;
                            trans.SnpAttr == 1;
                            trans.Endian == 0;
                            };

    trans.Data = value;
    `uvm_send(trans);
    get_response(item, trans.get_transaction_id());
    $cast(rsp_trans, item);

    FreeAddrInUse(aligned_addr);
  endtask

  // ReadUnique/MakeUnique,
  // CleanUnique 后续通过 exclusive 操作覆盖
  task Modify(bit [63:0] addr, bit [7:0] value[]);
    //DENALI_CHI_REQOPCODE_ReadUnique
    denaliChiTransaction trans;
    denaliChiTransaction rsp_trans;
    uvm_sequence_item item;
    denaliChiCacheLineStateT state;

    reg be[];
    reg cacheline_be[];
    reg [63:0] aligned_addr;

    bit non_secure = 0;
    reg [7:0] read_data[];  //temp parameter but no use

    be = new[64];
    aligned_addr = addr;
    aligned_addr[5:0] = 0;

    `uvm_info($sformatf("Modify@%d", this.id), $sformatf("addr: %x, value: %s", addr, StrByteArr(
                                                         value)), UVM_NONE)

    WaitAddrInUse(aligned_addr);
    `uvm_info("", $sformatf("Wait for addr in use: %x, OK", aligned_addr), UVM_NONE);
    // 要添加块地址，地址不同，但是同一个块的访问是冲突的
    AddAddrInUse(aligned_addr);

    agent.inst.cacheRead(aligned_addr, state, read_data, cacheline_be, non_secure);
    if((state == DENALI_CHI_CACHELINESTATE_Invalid)||
        (state == DENALI_CHI_CACHELINESTATE_SharedClean)||
        (state == DENALI_CHI_CACHELINESTATE_SharedDirty))begin

      `uvm_create_on(trans, agent.sequencer);

      trans.randomize() with {
        trans.ReqOpCode == DENALI_CHI_REQOPCODE_ReadUnique || trans.ReqOpCode == DENALI_CHI_REQOPCODE_MakeUnique;
        trans.Addr == aligned_addr;
        trans.Size == DENALI_CHI_SIZE_FULLLINE;
        trans.NonSecure == 0;
        // retry automatically
        trans.CancelOnRetryAck == 0;
        trans.MemAttr == 4'hd;
        trans.SnpAttr == 1;
      };

      `uvm_send(trans);

      // `uvm_do_on_with(trans, agent.sequencer,
      //                 {
      //           trans.ReqOpCode == DENALI_CHI_REQOPCODE_ReadUnique;
      //           trans.Addr == aligned_addr;
      //           trans.Size == DENALI_CHI_SIZE_FULLLINE;
      //           trans.NonSecure == 0;
      //           trans.CancelOnRetryAck == 0;
      //           trans.MemAttr == DENALI_CHI_V8MEMATTR_MEMORY_WB_Alloc_Outer;
      //       })
      get_response(item, trans.get_transaction_id());
      $cast(rsp_trans, item);
    end

    for (int i = 0; i < 64; i++) begin
      cacheline_be[i] = 1;
    end

    state = DENALI_CHI_CACHELINESTATE_UniqueDirty;
    agent.inst.cacheWrite(aligned_addr, state, value, cacheline_be, non_secure);

    FreeAddrInUse(aligned_addr);
  endtask

  task CheckShared(bit [63:0] addr, bit dirty);
    denaliChiCacheLineStateT state;
    string ops_name;

    ops_name = $sformatf("CheckShared@%d", this.id);

    `uvm_info(ops_name, $sformatf("addr: %x, dirty: %d", addr, dirty), UVM_NONE);

    state = agent.inst.getCacheLineState(addr);
    if (state == DENALI_CHI_CACHELINESTATE_SharedClean) begin
      `uvm_info(ops_name, "cacheline is clean", UVM_NONE);
    end else if (!dirty && state == DENALI_CHI_CACHELINESTATE_SharedDirty) begin
      `uvm_info(ops_name, "cacheline is dirty", UVM_NONE);
    end
  endtask

endclass
