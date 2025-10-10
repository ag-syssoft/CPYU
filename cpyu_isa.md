# CPYU-V16 Instruction Set Architecture (v1)
**Compact Python University Virtual 16-bit Architecture**

Designed for educational use in architecture and operating-system courses at Universität Trier.

---

## Overview
- **Word size:** 16 bit  
- **Registers:** 32 general-purpose registers (`r0` – `r31`), 16 bit each  
  - `r0` is **hard-wired to 0** and ignores writes  
- **Memory:** 64 Ki × 16-bit words (word-addressed)  
- **Address space:** 0 – 65535  
- **Program counter (PC):** word index into program memory  
- **Immediate range:** –32768 … 65535 (masked to 16 bit unsigned)  
- **Endianness:** not applicable (Python list model)  
- **Architecture model:** Harvard (separate code / data memory)

---

## 1. Arithmetic and Logic Instructions

| Mnemonic | Operands | Description | Operation |
|-----------|-----------|--------------|------------|
| `ADD rd, rs1, rs2` | 3 regs | Add two registers | `rd ← (rs1 + rs2) mod 2¹⁶` |
| `ADDI rd, rs1, imm` | 2 regs + imm | Add immediate | `rd ← (rs1 + imm) mod 2¹⁶` |
| `SUB rd, rs1, rs2` | 3 regs | Subtract | `rd ← (rs1 – rs2) mod 2¹⁶` |
| `AND rd, rs1, rs2` | 3 regs | Bitwise AND | `rd ← rs1 & rs2` |
| `OR  rd, rs1, rs2` | 3 regs | Bitwise OR | `rd ← rs1 \| rs2` |
| `XOR rd, rs1, rs2` | 3 regs | Bitwise XOR | `rd ← rs1 ⊕ rs2` |

Notes:
- All results are **masked to 16 bits** (`0xFFFF` wrap-around).
- Writing to `r0` has **no effect**.

---

## 2. Memory Access Instructions

| Mnemonic | Operands | Description | Operation |
|-----------|-----------|--------------|------------|
| `LD rd, addr` | reg + absolute addr | Load 16-bit word from memory | `rd ← MEM[addr]` |
| `ST rs, addr` | reg + absolute addr | Store 16-bit word to memory | `MEM[addr] ← rs` |

Notes:
- `addr` is a **literal numeric address** (hex or decimal).  
  Label-based data addresses will be introduced in v2.  
- Out-of-range accesses raise a runtime error.

---

## 3. Control-Flow Instructions

| Mnemonic | Operands | Description | Behavior |
|-----------|-----------|-------------|-----------|
| `BEQ rs1, rs2, target` | 2 regs + label/imm | Branch if equal | if `rs1 == rs2` → `PC ← target` |
| `BNE rs1, rs2, target` | 2 regs + label/imm | Branch if not equal | if `rs1 != rs2` → `PC ← target` |
| `JMP target` | label/imm | Unconditional jump | `PC ← target` |
| `HALT` | — | Stop execution | Terminates simulation |

Notes:
- Branch and jump targets refer to **instruction indices** (labels resolved by assembler).  
- After a taken branch, no instruction delay slot exists.

---

## 4. Input / Output Instructions

| Mnemonic | Operands | Description | Operation |
|-----------|-----------|-------------|------------|
| `IN rd` | 1 reg | Read integer from stdin | Parses decimal or `0x` hex into 16 bit value |
| `OUT rs` | 1 reg | Write integer to stdout | Prints signed + unsigned form, e.g. `+00123 (0x007b)` |

Notes:
- `IN` accepts values –32768 … 65535; outside range → runtime error.  
- `OUT` shows both signed and hex values for clarity.  
- In test mode, output may be captured via `on_out` callback.

---

## 5. Pseudo-Instructions

| Pseudo | Expansion | Meaning |
|---------|------------|----------|
| `LI rd, imm` | `ADDI rd, r0, imm` | Load immediate (since `r0 = 0`) |
| `MOV rd, rs` | `ADD rd, rs, r0` | Copy register |

---

## 6. Program Structure Elements

| Syntax | Meaning |
|---------|----------|
| `label:` | Defines a symbolic address for branch/jump targets |
| `; comment` or `# comment` | Comment to end of line |
| Operands may be comma- or space-separated. |
| Numbers may be **decimal** (`42`) or **hexadecimal** (`0x2A`). |

---

## 7. Example Programs

### 7.1 Sum of N Inputs
```asm
; Reads N numbers and prints their sum
IN  r1          ; N
LI  r2, 0       ; sum = 0
LI  r3, 0       ; i = 0
loop:
  IN   r4
  ADD  r2, r2, r4
  ADDI r3, r3, 1
  BNE  r3, r1, loop
OUT r2
HALT
```

### 7.2 Memory Load and Store Test
```asm
LI  r1, 0x003C
ST  r1, 0x0020
LD  r2, 0x0020
OUT r2
HALT
```

## 8. Exception Behavior

The simulator enforces strict runtime checks to help students detect programming errors early.

| Condition | Error Message | Description |
|------------|----------------|-------------|
| Invalid opcode | `Unknown op ...` | The assembler or simulator encountered an unknown instruction mnemonic. |
| Memory access out of bounds | `Memory read/write OOB at address ...` | An instruction attempted to read or write outside the 64 Ki memory range. |
| Invalid or malformed input | `IN: invalid input` | The value read from standard input was not a valid integer (decimal or hex). |
| Input value out of range | `IN: value ... out of range [-32768, 65535]` | Entered number exceeded the representable 16-bit range. |

The simulator stops immediately when a runtime error occurs.

---

## 9. Design Notes

- **Arithmetic:** All operations are performed on 16-bit unsigned integers with automatic wrap-around (`mod 2¹⁶`).  
- **Signed interpretation:** The helper `to_signed16()` provides a two’s-complement view of register values for display purposes.  
- **No status flags:** There is no carry, zero, or sign flag; conditional branches rely solely on register comparisons.  
- **Register 0:** Hard-wired constant 0; writes are ignored.  
- **Harvard organization:** Code (`prog`) and data (`mem`) memories are conceptually separate, emphasizing clarity of control vs. data flow.  
- **Single-cycle conceptual model:** Each instruction executes atomically in one interpreter step, with optional trace mode (`--single-step`) showing changes to registers.  
- **Pedagogical goal:** The ISA is intentionally minimal and transparent, enabling students to reason about each instruction’s precise effect before moving to pipelined or microcoded versions in later iterations.

---

*CPYU-V16 v1 — Universität Trier, 2025.*