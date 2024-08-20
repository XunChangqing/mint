class MinSeq extends uvm_sequence;

  `uvm_object_utils(MinSeq)
  `uvm_declare_p_sequencer(cdnChiUvmUserVirtualSequencer)
  CdnChiExecutor core[2];
  TestCase test_case;

  function new(string name = "wrCheckSeq");
    super.new(name);
`ifdef UVM_VERSION
    set_response_queue_error_report_enabled(0);
`else
    set_response_queue_error_report_disabled(1);
`endif
  endfunction

  virtual task pre_body();
`ifdef UVM_POST_VERSION_1_1
    var uvm_phase starting_phase = get_starting_phase();
`endif

    if (starting_phase != null) begin
      starting_phase.raise_objection(this, "seq not finished");
    end
    #1000;
  endtask

  virtual task post_body();
`ifdef UVM_POST_VERSION_1_1
    var uvm_phase starting_phase = get_starting_phase();
`endif

    if (starting_phase != null) begin
      starting_phase.drop_objection(this);
    end
  endtask


  virtual task body();
    #1000;
    //
    core[0] = new(p_sequencer.pEnv.Rn0);
    core[0].id = 0;
    core[1] = new(p_sequencer.pEnv.Rn1);
    core[1].id = 1;

    test_case = new(core);
    test_case.Run();

    #1000;
  endtask
endclass
