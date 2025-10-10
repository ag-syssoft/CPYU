"""
Tiny‑RV16 (v1) — a didactic, RISC‑V‑flavored 16‑bit CPU simulator
=================================================================

This version is intentionally small and very readable for first‑semester students.
It implements the **v1 spec** we discussed:

- 32 registers `r0..r31` (16‑bit). **r0 is hard‑wired to 0** (writes ignored).
- Memory: **2^16 words** (65536), each **16‑bit**. Word‑addressed.
- Program Counter (PC) counts **instructions** (not bytes).
- Arithmetic wraps modulo 2^16.
- **Addressing in v1**: only *immediate* addresses for `LD`/`ST` (decimal or `0x...`).
  (Register‑indirect, indexed, stack, calls come later.)
- **I/O**: `IN rd` (read one line from stdin as decimal or 0xhex; strict range) and
  `OUT rs` (print signed decimal with sign, width 5, and hex `(0xhhhh)`).
- **CLI**: `python tiny_rv16.py program.asm [--single-step]`
  - `--single-step` prints a verbose trace of every executed instruction.
- **Assembler**: two‑pass; commas optional; case‑insensitive; labels supported for
  branch/jump *targets*. (For v1, `LD`/`ST` use numeric addresses only; see TODO.)

Open design choice (please confirm):
- For **LD/ST addresses**, we currently require **numeric** immediates only in v1.
  If you prefer `LD rd, mydata` where `mydata:` is a label that resolves to a
  numeric **address**, I can enable that (simple to add) — just say the word.

"""
from __future__ import annotations
import sys
import argparse
from dataclasses import dataclass
from typing import List, Tuple, Dict, Callable, Optional

# =====================
# Helpers
# =====================

U16_MASK = 0xFFFF
NUM_REGS = 32
MEM_SIZE = 1 << 16  # 65536 words


def u16(x: int) -> int:
    return x & U16_MASK


def to_signed16(x: int) -> int:
    x &= U16_MASK
    return x if x < 0x8000 else x - 0x10000


def parse_int_token(tok: str) -> int:
    """Parse a decimal or 0xhex integer with optional sign. Whitespace tolerant.
    Accepted examples: '123', '-5', '0x2a', '-0X000A'. Returns an int (may be negative).
    Raises ValueError on invalid format.
    """
    s = tok.strip()
    if not s:
        raise ValueError("empty number")
    neg = False
    if s[0] in "+-":
        neg = (s[0] == '-')
        s = s[1:].strip()
    base = 10
    if s.lower().startswith('0x'):
        base = 16
        s = s[2:]
    if not s:
        raise ValueError("missing digits")
    if base == 10:
        if not s.isdigit():
            raise ValueError(f"invalid decimal '{tok}'")
        val = int(s, 10)
    else:
        # hex digits only
        try:
            val = int(s, 16)
        except ValueError:
            raise ValueError(f"invalid hexadecimal '{tok}'")
    return -val if neg else val


# =====================
# CPU core
# =====================

@dataclass
class Instr:
    op: str
    args: Tuple


class CPU:
    def __init__(self):
        self.reg: List[int] = [0] * NUM_REGS
        self.mem: List[int] = [0] * MEM_SIZE
        self.pc: int = 0  # instruction index
        self.prog: List[Instr] = []
        self.labels: Dict[str, int] = {}
        self.single_step: bool = False
        self.on_out: Optional[Callable[[str], None]] = None  # for tests

    # -------- Memory --------
    def mread(self, addr: int) -> int:
        if not (0 <= addr < MEM_SIZE):
            raise RuntimeError(f"Memory read OOB at address {addr}")
        return self.mem[addr]

    def mwrite(self, addr: int, val: int):
        if not (0 <= addr < MEM_SIZE):
            raise RuntimeError(f"Memory write OOB at address {addr}")
        self.mem[addr] = u16(val)

    # -------- Execution --------
    def _set_reg(self, rd: int, val: int):
        if rd == 0:
            return  # r0 is hard-wired to 0
        self.reg[rd] = u16(val)

    def _trace(self, old_pc: int, instr: Instr, before_regs: Tuple[int, ...]):
        if not self.single_step:
            return
        # Build a simple trace: PC, op/args, and changed registers
        changed = []
        for i, (b, a) in enumerate(zip(before_regs, self.reg)):
            if b != a:
                changed.append(f"r{i}={a:04x}")
        args_txt = ', '.join(map(str, instr.args))
        print(f"PC={old_pc:05d}  {instr.op} {args_txt:20s}  | " + ' '.join(changed))

    def step(self) -> bool:
        if self.pc < 0 or self.pc >= len(self.prog):
            return False
        instr = self.prog[self.pc]
        old_pc = self.pc
        self.pc += 1
        before = tuple(self.reg)

        op = instr.op
        a = instr.args

        if op == 'ADD':
            rd, rs1, rs2 = a
            self._set_reg(rd, self.reg[rs1] + self.reg[rs2])
        elif op == 'ADDI':
            rd, rs1, imm = a
            self._set_reg(rd, self.reg[rs1] + imm)
        elif op == 'SUB':
            rd, rs1, rs2 = a
            self._set_reg(rd, self.reg[rs1] - self.reg[rs2])
        elif op == 'AND':
            rd, rs1, rs2 = a
            self._set_reg(rd, self.reg[rs1] & self.reg[rs2])
        elif op == 'OR':
            rd, rs1, rs2 = a
            self._set_reg(rd, self.reg[rs1] | self.reg[rs2])
        elif op == 'XOR':
            rd, rs1, rs2 = a
            self._set_reg(rd, self.reg[rs1] ^ self.reg[rs2])
        elif op == 'LD':
            rd, addr = a
            self._set_reg(rd, self.mread(addr))
        elif op == 'ST':
            rs, addr = a
            self.mwrite(addr, self.reg[rs])
        elif op == 'BEQ':
            rs1, rs2, target = a
            if self.reg[rs1] == self.reg[rs2]:
                self.pc = target
        elif op == 'BNE':
            rs1, rs2, target = a
            if self.reg[rs1] != self.reg[rs2]:
                self.pc = target
        elif op == 'JMP':
            (target,) = a
            self.pc = target
        elif op == 'IN':
            (rd,) = a
            line = sys.stdin.readline()
            if line == '':
                raise RuntimeError("IN: EOF on stdin")
            try:
                val = parse_int_token(line)
            except ValueError as e:
                raise RuntimeError(f"IN: invalid input — {e}")
            # Strict range: decimal/hex outside [-32768, 65535] aborts
            if val < -32768 or val > 65535:
                raise RuntimeError(f"IN: value {val} out of range [-32768, 65535]")
            self._set_reg(rd, val)
        elif op == 'OUT':
            (rs,) = a
            signed = to_signed16(self.reg[rs])
            text = f"{signed:+06d} (0x{self.reg[rs]:04x})"  # +ddddd width 6 includes sign; we want width 5: pad manually
            # Ensure exactly +ddddd with width 5 (excluding sign) as requested
            absval = abs(signed)
            text = f"{('+' if signed>=0 else '-')}{absval:05d} (0x{self.reg[rs]:04x})"
            if self.on_out:
                self.on_out(text + "\n")
            else:
                print(text)
        elif op == 'HALT':
            return False
        else:
            raise RuntimeError(f"Unknown op {op}")

        self._trace(old_pc, instr, before)
        return True

    def run(self, max_steps: int = 1_000_000):
        steps = 0
        while steps < max_steps and self.step():
            steps += 1
        return steps


# =====================
# Assembler
# =====================

class AsmError(Exception):
    pass


def assemble(src: str) -> Tuple[List[Instr], Dict[str, int]]:
    lines = src.splitlines()

    def clean(line: str) -> str:
        # remove comments ';' or '#'
        for sep in (';', '#'):
            i = line.find(sep)
            if i != -1:
                line = line[:i]
        return line.strip()

    def is_reg(tok: str) -> bool:
        t = tok.strip().lower()
        return t.startswith('r') and t[1:].isdigit() and (0 <= int(t[1:]) < NUM_REGS)

    def reg_idx(tok: str, ln: int) -> int:
        if not is_reg(tok):
            raise AsmError(f"Line {ln}: expected register r0..r31, got '{tok}'")
        return int(tok.strip().lower()[1:])

    def parse_imm(tok: str, ln: int) -> int:
        try:
            val = parse_int_token(tok)
        except ValueError as e:
            raise AsmError(f"Line {ln}: invalid immediate — {e}")
        if val < -32768 or val > 65535:
            raise AsmError(f"Line {ln}: immediate {val} out of range [-32768, 65535]")
        return u16(val)

    # Pass 1: collect labels (instruction indices)
    labels: Dict[str, int] = {}
    pc = 0
    cleaned = []
    for ln, raw in enumerate(lines, start=1):
        line = clean(raw)
        cleaned.append((ln, line))
        if not line:
            continue
        if line.endswith(':'):
            label = line[:-1].strip()
            if not label or ' ' in label or '\t' in label:
                raise AsmError(f"Line {ln}: invalid label '{label}'")
            if label in labels:
                raise AsmError(f"Line {ln}: duplicate label '{label}'")
            labels[label] = pc
        else:
            pc += 1

    # Pass 2: parse instructions
    prog: List[Instr] = []

    def toks_for(line: str) -> List[str]:
        # commas optional → normalize to spaces, split on whitespace
        return [t for t in line.replace(',', ' ').split()]

    def label_or_imm(tok: str, ln: int) -> int:
        # For v1, allow labels ONLY for branch/jump targets; addresses for LD/ST are numeric only
        if tok in labels:
            return labels[tok]
        return parse_imm(tok, ln)

    for ln, line in cleaned:
        if not line or line.endswith(':'):
            continue
        parts = toks_for(line)
        op = parts[0].upper()
        args = parts[1:]

        def need_n(n: int):
            if len(args) != n:
                raise AsmError(f"Line {ln}: '{op}' expects {n} operand(s), got {len(args)}")

        # Pseudos first
        if op == 'LI':
            need_n(2)
            rd = reg_idx(args[0], ln)
            imm = parse_imm(args[1], ln)
            prog.append(Instr('ADDI', (rd, 0, imm)))
            continue
        if op == 'MOV':
            need_n(2)
            rd = reg_idx(args[0], ln)
            rs = reg_idx(args[1], ln)
            prog.append(Instr('ADD', (rd, rs, 0)))
            continue

        if op in ('ADD', 'SUB', 'AND', 'OR', 'XOR'):
            need_n(3)
            rd = reg_idx(args[0], ln)
            rs1 = reg_idx(args[1], ln)
            rs2 = reg_idx(args[2], ln)
            prog.append(Instr(op, (rd, rs1, rs2)))
        elif op == 'ADDI':
            need_n(3)
            rd = reg_idx(args[0], ln)
            rs1 = reg_idx(args[1], ln)
            imm = parse_imm(args[2], ln)
            prog.append(Instr('ADDI', (rd, rs1, imm)))
        elif op == 'LD':
            need_n(2)
            rd = reg_idx(args[0], ln)
            # v1: numeric address only (no labels for data yet); allow hex/dec
            addr = parse_imm(args[1], ln)
            prog.append(Instr('LD', (rd, addr)))
        elif op == 'ST':
            need_n(2)
            rs = reg_idx(args[0], ln)
            addr = parse_imm(args[1], ln)
            prog.append(Instr('ST', (rs, addr)))
        elif op in ('BEQ', 'BNE'):
            need_n(3)
            rs1 = reg_idx(args[0], ln)
            rs2 = reg_idx(args[1], ln)
            tgt = label_or_imm(args[2], ln)
            prog.append(Instr(op, (rs1, rs2, tgt)))
        elif op == 'JMP':
            need_n(1)
            tgt = label_or_imm(args[0], ln)
            prog.append(Instr('JMP', (tgt,)))
        elif op == 'IN':
            need_n(1)
            rd = reg_idx(args[0], ln)
            prog.append(Instr('IN', (rd,)))
        elif op == 'OUT':
            need_n(1)
            rs = reg_idx(args[0], ln)
            prog.append(Instr('OUT', (rs,)))
        elif op == 'HALT':
            need_n(0)
            prog.append(Instr('HALT', tuple()))
        else:
            raise AsmError(f"Line {ln}: unknown mnemonic '{op}'")

    return prog, labels


# =====================
# CLI & runner
# =====================

def run_file(filename: str, single_step: bool) -> int:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            src = f.read()
    except OSError as e:
        print(f"Error: cannot read '{filename}': {e}", file=sys.stderr)
        return 1

    try:
        prog, _ = assemble(src)
    except AsmError as e:
        print(f"Assembly error: {e}", file=sys.stderr)
        return 2

    cpu = CPU()
    cpu.prog = prog
    cpu.single_step = single_step

    try:
        cpu.run()
    except RuntimeError as e:
        print(f"Runtime error: {e}", file=sys.stderr)
        return 3
    return 0


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Tiny‑RV16 (v1) CPU simulator")
    ap.add_argument('program', help='assembly source file')
    ap.add_argument('--single-step', action='store_true', dest='single_step',
                    help='verbose trace of every executed instruction')
    args = ap.parse_args(argv)
    return run_file(args.program, args.single_step)


# =====================
# Self‑tests (minimal; deterministic)
# Run via: python tiny_rv16.py --selftest
# =====================

def _selftest() -> int:
    # 1) Wraparound test
    src = """
        LI r1, 65530
        ADDI r1, r1, 10
        OUT r1
        HALT
    """
    cpu = CPU()
    prog, _ = assemble(src)
    cpu.prog = prog
    outs: List[str] = []
    cpu.on_out = outs.append
    cpu.run()
    assert outs and outs[-1].strip() == "+00004 (0x0004)", outs

    # 2) Store/Load
    src = """
        LI r1, 0x003C
        ST r1, 0x0020
        LD r2, 0x0020
        OUT r2
        HALT
    """
    cpu = CPU()
    prog, _ = assemble(src)
    cpu.prog = prog
    outs = []
    cpu.on_out = outs.append
    cpu.run()
    assert outs[-1].strip() == "+00060 (0x003c)", outs

    # 3) Branch sanity
    src = """
        LI r1, 7
        LI r2, 7
        BNE r1, r2, wrong
        LI r3, 0x002A
        JMP done
    wrong:
        LI r3, 0x0000
    done:
        OUT r3
        HALT
    """
    cpu = CPU(); prog, _ = assemble(src); cpu.prog = prog
    outs = []; cpu.on_out = outs.append; cpu.run()
    assert outs[-1].strip() == "+00042 (0x002a)", outs

    # 4) IN/OUT format tests — feed lines manually
    from io import StringIO
    src = """
        IN r1
        OUT r1
        IN r2
        OUT r2
        IN r3
        OUT r3
        HALT
    """
    stdin_backup = sys.stdin
    try:
        sys.stdin = StringIO("123\n0xFFFE\n-0x000A\n")
        cpu = CPU(); prog, _ = assemble(src); cpu.prog = prog
        outs = []; cpu.on_out = outs.append; cpu.run()
        want = ["+00123 (0x007b)", "-00002 (0xfffe)", "-00010 (0xfff6)"]
        got = [o.strip() for o in outs]
        assert got == want, got
    finally:
        sys.stdin = stdin_backup

    # 5) Bad IN (out of range) → runtime error
    from io import StringIO as _S
    src = """
        IN r1
        HALT
    """
    cpu = CPU(); prog, _ = assemble(src); cpu.prog = prog
    sys.stdin = _S("70000\n")
    try:
        try:
            cpu.run()
            raise AssertionError("Expected runtime error for out-of-range IN")
        except RuntimeError as e:
            assert "out of range" in str(e)
    finally:
        sys.stdin = stdin_backup

    return 0


if __name__ == '__main__':
    # Support a lightweight self-test trigger to validate behavior without separate files
    if len(sys.argv) == 2 and sys.argv[1] == '--selftest':
        code = _selftest()
        print('[selftest] OK')
        sys.exit(code)
    sys.exit(main(sys.argv[1:]))
