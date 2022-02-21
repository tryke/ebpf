from binaryninja.architecture import *
from binaryninja.binaryview import *
import struct
import enum

class BPFOpClass(enum.IntEnum):
    LD = 0
    LDX = 1
    ST = 2
    STX = 3
    ALU = 4
    JMP = 5
    UNUSED = 6
    ALU64 = 7

class ALUOps(enum.IntEnum):
        ADD = 0
        SUB = 1
        MUL = 2
        DIV = 3
        OR = 4
        AND = 5
        LSH = 6
        RSH = 7
        NEG = 8
        MOD = 9
        XOR = 0xa
        MOV = 0xb
        ARSH = 0xc
        END = 0xd

# TODO: Is this a LLVM doc bug?? Sources disagree.
class ALUSrc(enum.IntEnum):
    K = 0
    X = 1

class LdStSizeMods(enum.IntEnum):
    WORD = 0
    HALFWORD = 1
    BYTE = 2
    DWORD = 3

class LdStModes(enum.IntEnum):
    IMM = 0
    ABS = 1
    IND = 2
    MEM = 3
    XADD = 6

# TODO: better way to organize this? reused across LD/ST
def size_mod_string(size):
    sizes = {
        LdStSizeMods.WORD: "W",
        LdStSizeMods.HALFWORD: "H",
        LdStSizeMods.BYTE: "B",
        LdStSizeMods.DWORD: "DW"
    }
    return sizes[size]

def mem_mode_string(mode):
    if (mode == LdStModes.ABS):
        return "ABS"
    elif (mode == LdStModes.IND):
        return "IND"
    return ""

class eBPFInstruction(object):
    def __init__(self, data, addr):
        (self.opcode, dstsrc, self.offset, self.imm) = struct.unpack("<BBhl", data[:8])
        self.dst = dstsrc & 0x0f
        self.src = (dstsrc & 0xf0) >> 4
        self.opclass = self.opcode & 0x07
        self.addr = addr
        self.length = 8 # always assume 8-byte instruction

    @staticmethod
    def decode(data, addr):
        classes = {
            BPFOpClass.LD:      LDInstruction,
            BPFOpClass.LDX:     LDXInstruction,
            BPFOpClass.ST:      STInstruction,
            BPFOpClass.STX:     STXInstruction,
            BPFOpClass.ALU:     ALUInstruction,
            BPFOpClass.ALU64:   ALU64Instruction,
            BPFOpClass.JMP:     JMPInstruction,
            BPFOpClass.UNUSED:  UnusedInstruction
        }
        opclass = int(data[0]) & 0x07
        return classes[opclass](data, addr)

    def get_info(self, result):
        return

    def get_text(self):
        return

    def get_instruction_low_level_il(self, data:bytes, addr:int, il:'lowlevelil.LowLevelILFunction') -> Optional[int]:
        return None

class LDInstruction(eBPFInstruction):
    def __init__(self, data, addr):
        super().__init__(data, addr)
        self.size = (self.opcode & 0x18) >> 3
        self.mode = (self.opcode & 0xe0) >> 5

    def get_text(self):
        mnem = "LD%s%s" % (mem_mode_string(self.mode), size_mod_string(self.size))
        dst = "r%d" % self.dst
        src = "r%d" % self.src
        imm = "#%x" % self.imm

        tokens = [
            InstructionTextToken(InstructionTextTokenType.InstructionToken, mnem),
            InstructionTextToken(InstructionTextTokenType.TextToken, " ")
        ]

        if (self.mode == LdStModes.ABS or self.mode == LdStModes.IND):
            tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, src))
            tokens.append(InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "))

        tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, dst))
        tokens.append(InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "))
        tokens.append(InstructionTextToken(InstructionTextTokenType.IntegerToken, imm, self.imm))

        return tokens

class LDXInstruction(eBPFInstruction):
    def __init__(self, data, addr):
        super().__init__(data, addr)
        self.size = (self.opcode & 0x18) >> 3
        self.mode = (self.opcode & 0xe0) >> 5

    def get_text(self):
        mnem = "LDX%s%s" % (size_mod_string(self.size), mem_mode_string(self.mode))
        dst = "r%d" % self.dst
        src = "r%d" % self.src
        offset = "$%x" % abs(self.offset)
        if self.offset >= 0:
            sign = "+"
        else:
            sign = "-"

        return [
            InstructionTextToken(InstructionTextTokenType.InstructionToken, mnem),
            InstructionTextToken(InstructionTextTokenType.TextToken, " "),
            InstructionTextToken(InstructionTextTokenType.RegisterToken, dst),
            InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "),
            InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, "["),
            InstructionTextToken(InstructionTextTokenType.RegisterToken, src),
            InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, sign),
            # XXX: Why does this next line crash binja if I use IntegerToken or PossibleAddressToken?
            InstructionTextToken(InstructionTextTokenType.TextToken, offset),
            InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, "]")
        ]

class STInstruction(eBPFInstruction):
    def __init__(self, data, addr):
        super().__init__(data, addr)
        self.size = (self.opcode & 0x18) >> 3
        self.mode = (self.opcode & 0xe0) >> 5

    def get_text(self):
        mnem = "ST%s" % size_mod_string(self.size)
        dst = "r%d" % self.dst
        offset = "$%x" % abs(self.offset)
        imm = "#%x" % self.imm
        if self.offset >= 0:
            sign = "+"
        else:
            sign = "-"

        return [
            InstructionTextToken(InstructionTextTokenType.InstructionToken, mnem),
            InstructionTextToken(InstructionTextTokenType.TextToken, " "),
            InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, "["),
            InstructionTextToken(InstructionTextTokenType.RegisterToken, dst),
            InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, sign),
            # XXX: Why does this next line crash binja if I use IntegerToken or PossibleAddressToken?
            InstructionTextToken(InstructionTextTokenType.TextToken, offset),
            InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, "]"),
            InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "),
            InstructionTextToken(InstructionTextTokenType.IntegerToken, imm, self.imm)
        ]

class STXInstruction(eBPFInstruction):
    def __init__(self, data, addr):
        super().__init__(data, addr)
        self.size = (self.opcode & 0x18) >> 3
        self.mode = (self.opcode & 0xe0) >> 5

    def get_text(self):
        mnem = "STX%s%s" % (size_mod_string(self.size), mem_mode_string(self.mode))
        dst = "r%d" % self.dst
        src = "r%d" % self.src
        offset = "$%x" % abs(self.offset)
        if self.offset >= 0:
            sign = "+"
        else:
            sign = "-"

        return [
            InstructionTextToken(InstructionTextTokenType.InstructionToken, mnem),
            InstructionTextToken(InstructionTextTokenType.TextToken, " "),
            InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, "["),
            InstructionTextToken(InstructionTextTokenType.RegisterToken, dst),
            InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, sign),
            # XXX: Why does this next line crash binja if I use IntegerToken or PossibleAddressToken?
            InstructionTextToken(InstructionTextTokenType.TextToken, offset),
            InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, "]"),
            InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "),
            InstructionTextToken(InstructionTextTokenType.RegisterToken, src)
        ]

class ALUInstruction(eBPFInstruction):
    def __init__(self, data, addr):
        super().__init__(data, addr)
        self.op = (self.opcode & 0xf0) >> 4
        self.srctype = (self.opcode & 0x08) >> 3

    def get_text(self):
        mnems = {
            ALUOps.SUB: "SUB",
            ALUOps.ADD: "ADD",
            ALUOps.MUL: "MUL",
            ALUOps.DIV: "DIV",
            ALUOps.OR: "OR",
            ALUOps.AND: "AND",
            ALUOps.LSH: "LSH",
            ALUOps.RSH: "RSH",
            ALUOps.NEG: "NEG",
            ALUOps.MOD: "MOD",
            ALUOps.XOR: "XOR",
            ALUOps.MOV: "MOV",
            ALUOps.ARSH: "ARSH",
            ALUOps.END: "END",
        }
        return [InstructionTextToken(InstructionTextTokenType.TextToken, mnems[self.op])]

class ALU64Instruction(eBPFInstruction):
    def __init__(self, data, addr):
        super().__init__(data, addr)
        self.op = (self.opcode & 0xf0) >> 4
        self.srctype = (self.opcode & 0x08) >> 3

    def get_text(self):
        mnems = {
            ALUOps.SUB: "SUB",
            ALUOps.ADD: "ADD",
            ALUOps.MUL: "MUL",
            ALUOps.DIV: "DIV",
            ALUOps.OR: "OR",
            ALUOps.AND: "AND",
            ALUOps.LSH: "LSH",
            ALUOps.RSH: "RSH",
            ALUOps.NEG: "NEG",
            ALUOps.MOD: "MOD",
            ALUOps.XOR: "XOR",
            ALUOps.MOV: "MOV",
            ALUOps.ARSH: "ARSH",
            ALUOps.END: "END",
        }
        mnem = InstructionTextToken(InstructionTextTokenType.InstructionToken, mnems[self.op])
        space = InstructionTextToken(InstructionTextTokenType.TextToken, " ")
        dstname = InstructionTextToken(InstructionTextTokenType.RegisterToken, ("r%d" % self.dst))
        sep = InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", ")
        if (self.srctype == ALUSrc.K):
            srcname = InstructionTextToken(InstructionTextTokenType.IntegerToken, ("#%x" % self.imm), self.imm)
        else:
            srcname = InstructionTextToken(InstructionTextTokenType.RegisterToken, ("r%d" % self.src))

        return [mnem, space, dstname, sep, srcname]

class JMPInstruction(eBPFInstruction):
    class Ops(enum.IntEnum):
        JA = 0
        JEQ = 1
        JGT = 2
        JGE = 3
        JSET = 4
        JNE = 5
        JSGT = 6
        JSGE = 7
        CALL = 8
        EXIT = 9
    
    def __init__(self, data, addr):
        super().__init__(data, addr)
        self.op = (self.opcode & 0xf0) >> 4
        self.srctype = (self.opcode & 0x08) >> 3

        if self.op == JMPInstruction.Ops.CALL:
            self.target = (self.imm * 8) + self.addr + self.length
        else:
            self.target = (self.offset * 8) + self.addr + self.length

    def get_info(self, result):
        # TODO clean up magic numbers
        if self.op == JMPInstruction.Ops.CALL:
            result.add_branch(BranchType.CallDestination, self.target)
        elif self.op == JMPInstruction.Ops.EXIT:
            result.add_branch(BranchType.FunctionReturn)
        elif self.op == JMPInstruction.Ops.JA:
            result.add_branch(BranchType.UnconditionalBranch, self.target)
        else:
            result.add_branch(BranchType.TrueBranch, self.target)
            result.add_branch(BranchType.FalseBranch, self.addr+8)

    def get_text(self):
        mnems = {
            JMPInstruction.Ops.JA: "JA",
            JMPInstruction.Ops.JEQ: "JEQ",
            JMPInstruction.Ops.JGT: "JGT",
            JMPInstruction.Ops.JGE: "JGE",
            JMPInstruction.Ops.JSET: "JSET",
            JMPInstruction.Ops.JNE: "JNE",
            JMPInstruction.Ops.JSGT: "JSGT",
            JMPInstruction.Ops.JSGE: "JSGE",
            JMPInstruction.Ops.CALL: "CALL",
            JMPInstruction.Ops.EXIT: "EXIT",
        }

        mnem = mnems[self.op]
        tokens = [InstructionTextToken(InstructionTextTokenType.InstructionToken, mnem)]
        tokens.append(InstructionTextToken(InstructionTextTokenType.TextToken, " "))

        if ((self.op == JMPInstruction.Ops.CALL and self.srctype == ALUSrc.K) or
             self.op == JMPInstruction.Ops.JA):
            target = "$%x" % self.target
            tokens.append(InstructionTextToken(InstructionTextTokenType.PossibleAddressToken, target, self.target))
        elif (self.op == JMPInstruction.Ops.CALL and self.srctype == ALUSrc.X):
            target = "r%10" % self.imm
            tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, target))
        elif self.op != JMPInstruction.Ops.EXIT:
            dst = "r%d" % self.dst
            tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, dst))
            tokens.append(InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "))

            if self.srctype == ALUSrc.K:
                src = "#%x" % self.imm
                tokens.append(InstructionTextToken(InstructionTextTokenType.IntegerToken, src, self.imm))
            else:
                src = "r%d" % self.src
                tokens.append(InstructionTextToken(InstructionTextTokenType.RegisterToken, src))

            tokens.append(InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, ", "))
            target = "$%x" % self.target
            tokens.append(InstructionTextToken(InstructionTextTokenType.PossibleAddressToken, target, self.target))

        return tokens


class UnusedInstruction(eBPFInstruction):
    def __init__(self, data, addr):
        super().__init__(data, addr)

    def get_text(self):
        return [InstructionTextToken(InstructionTextTokenType.TextToken, "UNUSED")]