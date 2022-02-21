from binaryninja.architecture import *
from binaryninja.binaryview import *
from .eBPFInstruction import eBPFInstruction

class eBPFArch(Architecture):
    name = 'eBPF'
    address_size = 8
    instr_alignment = 8
    max_instr_length = 8

    regs = {"r%d" % n : RegisterInfo('r%d' % n, 8) for n in range(0,11)}
    stack_pointer = "r10"

    def get_instruction_info(self, data, addr):
        instruction = eBPFInstruction.decode(data, addr)
        result = InstructionInfo()
        instruction.get_info(result)
        result.length = instruction.length
        return result

    def get_instruction_text(self, data, addr):
        instruction = eBPFInstruction.decode(data, addr)
        tokens = instruction.get_text()
        return tokens, instruction.length

    def get_instruction_low_level_il(self, data:bytes, addr:int, il:'lowlevelil.LowLevelILFunction') -> Optional[int]:
        instruction = eBPFInstruction.decode(data, addr)
        return instruction.get_instruction_low_level_il(data, addr, il)
