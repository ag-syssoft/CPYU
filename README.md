# CPYU-V16 — Compact Python University Virtual 16-bit Architecture

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Educational-green.svg)]()

An educational CPU simulator and assembler designed for first-semester computer architecture courses at Universität Trier. CPYU-V16 implements a minimal 16-bit RISC architecture with Harvard memory model, making it ideal for teaching fundamental concepts in computer organization.

## Features

- **16-bit word-addressed architecture** with 32 general-purpose registers
- **Harvard architecture model** with separate program and data memory
- **64 Ki × 16-bit word memory** (65,536 words)
- **Two-pass assembler** with label support
- **Real-time debugging** with single-step execution
- **Comprehensive error handling** for educational feedback
- **Built-in self-test suite** for validation

## Architecture Overview

### Core Specifications
- **Registers**: 32 general-purpose registers (`r0`-`r31`)
  - `r0` is hard-wired to zero (writes ignored)
- **Memory**: 64K words of 16-bit memory (word-addressed 0-65535)
- **Immediate Values**: Range from -32768 to 65535 (masked to 16-bit)
- **Arithmetic**: All operations wrap around at 16 bits (mod 2¹⁶)

### Instruction Set
- **Arithmetic & Logic**: `ADD`, `ADDI`, `SUB`, `AND`, `OR`, `XOR`
- **Memory Access**: `LD`, `ST` (absolute addressing)
- **Control Flow**: `BEQ`, `BNE`, `JMP`, `HALT`
- **I/O**: `IN` (stdin), `OUT` (formatted stdout)
- **Pseudo-instructions**: `LI` (load immediate), `MOV` (register copy)

## Quick Start

### Prerequisites
- Python 3.7 or higher
- No additional dependencies required

### Installation
```bash
git clone <repository-url>
cd cpyu
```

### Running Programs
```bash
# Run an assembly program
python cpyu.py sumup_n.cpyu

# Run with single-step debugging
python cpyu.py --single-step sumup_n.cpyu

# Run built-in self-tests
python cpyu.py --selftest
```

## Usage Examples

### Basic Arithmetic Program
```assembly
; Simple addition example
LI   r1, 10        ; Load immediate 10 into r1
LI   r2, 20        ; Load immediate 20 into r2
ADD  r3, r1, r2    ; r3 = r1 + r2
OUT  r3            ; Print result: +00030 (0x001e)
HALT
```

### Input/Output Program
```assembly
; Read a number and double it
IN   r1            ; Read integer from stdin
ADD  r2, r1, r1    ; r2 = r1 + r1 (double)
OUT  r2            ; Print doubled value
HALT
```

### Memory Operations
```assembly
; Store and load from memory
LI   r1, 0x00FF    ; Load value
ST   r1, 100       ; Store at memory address 100
LD   r2, 100       ; Load from memory address 100
OUT  r2            ; Print loaded value
HALT
```

## Assembly Language Syntax

### Basic Syntax
- **Comments**: Lines starting with `;` or `#`
- **Labels**: Identifiers followed by `:` (used for branches/jumps)
- **Instructions**: Mnemonic followed by operands
- **Operands**: Separated by commas or spaces

### Number Formats
- **Decimal**: `42`, `-15`
- **Hexadecimal**: `0x2A`, `-0x000F`

### Register Syntax
- Registers: `r0` through `r31` (case-insensitive)
- `r0` always contains zero

## Command Line Options

```bash
python cpyu.py [options] <assembly_file>

Options:
  --single-step     Enable single-step debugging mode
  --selftest        Run comprehensive self-tests
  -h, --help        Show help message
```

## Debugging Features

### Single-Step Mode
Use `--single-step` to trace execution:
```bash
python cpyu.py --single-step sumup_n.cpyu
```

Output shows:
```
PC=00001  LI r1, 1              | r1=0001
PC=00002  LI r3, 0              | r3=0000
PC=00003  ADD r3, r3, r1        | r3=0001
...
```

### Error Handling
The simulator provides detailed error messages for:
- **Memory errors**: Out-of-bounds access
- **Input errors**: Invalid or out-of-range values
- **Assembly errors**: Invalid syntax, unknown opcodes
- **Runtime errors**: Execution problems

## File Structure

```
cpyu/
├── cpyu.py           # Main simulator and assembler
├── cpyu_isa.md       # Complete instruction set documentation
├── sumup_n.cpyu      # Example program (sum of 1 to N)
├── README.md         # This file
└── WARP.md          # Development guidelines
```

## Testing

Run the comprehensive self-test suite:
```bash
python cpyu.py --selftest
```

Tests cover:
- Arithmetic operations and overflow handling
- Memory load/store operations
- Control flow (branches, jumps)
- I/O operations
- Error conditions

## Educational Use

CPYU-V16 is designed specifically for computer architecture education:

- **Minimal complexity** allows focus on fundamental concepts
- **Clear instruction semantics** with predictable behavior
- **Debugging support** helps students understand execution flow
- **Comprehensive error checking** provides immediate feedback
- **Harvard model** clearly separates code and data

## Architecture Details

For complete instruction set documentation and architectural specifications, see [`cpyu_isa.md`](cpyu_isa.md).

Key architectural features:
- Word-addressed memory (not byte-addressed)
- No pipeline or cache complexity
- Single-cycle instruction execution model
- Explicit register-to-register operations
- Immediate values handled consistently across instructions

## Contributing

This is an educational project developed at Universität Trier. For development guidelines and project structure information, see [`WARP.md`](WARP.md).

## License

Educational use license. Developed for computer architecture courses at Universität Trier.

---

*CPYU-V16 v1 — Universität Trier, 2025*