# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is **CPYU-V16** (Compact Python University Virtual 16-bit Architecture), an educational CPU simulator and assembler designed for first-semester computer architecture courses at Universität Trier.

### Core Architecture
- **16-bit word-addressed architecture** with 32 general-purpose registers (r0-r31)
- **Harvard architecture** model with separate program and data memory
- **r0 is hard-wired to zero** and ignores all writes
- **64 Ki × 16-bit word memory** (65536 words, word-addressed 0-65535)
- **Immediate values** range from -32768 to 65535 (masked to 16-bit unsigned)
- **All arithmetic operations** wrap around at 16 bits (mod 2¹⁶)

### Key Components
1. **CPU class** (`CPU`): The main simulator engine with registers, memory, and execution logic
2. **Assembler** (`assemble()` function): Two-pass assembler that converts assembly source to instruction objects
3. **Instruction representation** (`Instr` dataclass): Decoded instructions with operation and arguments
4. **CLI runner** (`main()`, `run_file()`): Command-line interface for running assembly programs

## Common Development Commands

### Running Programs
```bash
# Run an assembly program
python cpyu.py program.cpyu

# Run with single-step debugging (shows register changes for each instruction)
python cpyu.py --single-step program.cpyu

# Run the built-in self-tests
python cpyu.py --selftest
```

### Testing and Validation
```bash
# Run comprehensive self-tests (includes arithmetic, memory, I/O, and error handling)
python cpyu.py --selftest

# Test with the included example program
python cpyu.py sumup_n.cpyu
```

## Instruction Set Architecture

The ISA is documented in detail in `cpyu_isa.md`. Key instruction categories:

### Arithmetic & Logic
- `ADD`, `ADDI`, `SUB`, `AND`, `OR`, `XOR`
- All operations use 16-bit wrap-around arithmetic

### Memory Access
- `LD rd, addr` - Load from absolute memory address
- `ST rs, addr` - Store to absolute memory address  
- Currently uses numeric addresses only (no label-based data addressing)

### Control Flow
- `BEQ`, `BNE` - Conditional branches comparing two registers
- `JMP` - Unconditional jump
- `HALT` - Stop execution
- Branch/jump targets can use labels or immediate values

### I/O
- `IN rd` - Read integer from stdin (supports decimal and 0x hex format)
- `OUT rs` - Print register value in both signed and hex format (e.g., "+00123 (0x007b)")

### Pseudo-instructions
- `LI rd, imm` → `ADDI rd, r0, imm` (load immediate)
- `MOV rd, rs` → `ADD rd, rs, r0` (copy register)

## Assembly Language Syntax

### Program Structure
```assembly
; Comments start with ; or #
label:          ; Labels end with colon, used for branch targets
    INSTRUCTION operands    ; Instructions with operands
    INSTRUCTION             ; Instructions without operands (like HALT)
```

### Operand Formats
- **Registers**: `r0` through `r31` (case-insensitive)
- **Immediates**: Decimal (`42`) or hexadecimal (`0x2A`, `-0x000A`)
- **Addresses**: Numeric only for LD/ST (hex or decimal)
- **Branch targets**: Labels or immediate instruction indices
- **Operand separators**: Commas and spaces are both accepted and interchangeable

## Error Handling and Debugging

### Runtime Error Categories
1. **Memory errors**: Out-of-bounds access to the 64K word memory space
2. **Input errors**: Invalid or out-of-range values for IN instruction (-32768 to 65535)
3. **Assembly errors**: Invalid syntax, unknown opcodes, duplicate labels
4. **Unknown instruction errors**: Unrecognized mnemonics

### Debug Features
- Use `--single-step` flag to trace execution with register change display
- Built-in self-test suite validates core functionality
- All runtime errors include descriptive messages with context

## Code Organization

### Main Module Structure (`cpyu.py`)
1. **Helper functions** (lines 20-70): Bit manipulation, number parsing utilities
2. **CPU core** (lines 75-218): CPU class with execution engine
3. **Assembler** (lines 224-370): Two-pass assembler implementation  
4. **CLI interface** (lines 375-413): Argument parsing and file execution
5. **Self-tests** (lines 420-512): Comprehensive regression tests

### Key Implementation Details
- **Two-pass assembly**: Pass 1 collects labels, Pass 2 generates instructions
- **Harvard model**: Program stored in `cpu.prog` list, data in `cpu.mem` array
- **Instruction execution**: Single `step()` method handles all opcodes with dispatch pattern
- **16-bit arithmetic**: All values masked with `U16_MASK = 0xFFFF` for hardware simulation
- **Register 0 protection**: `_set_reg()` method ignores writes to r0

## Development Patterns

### Adding New Instructions
1. Add opcode handling in `CPU.step()` method (around line 140)
2. Add assembly parsing in `assemble()` function (around line 320)
3. Update ISA documentation in `cpyu_isa.md`
4. Add test cases to `_selftest()` function

### Memory Model
- Word-addressed: All addresses refer to 16-bit words, not bytes
- No alignment requirements (each word is independently addressable)
- Memory bounds checking on all accesses with descriptive error messages

### I/O Model
- Synchronous terminal I/O using Python's stdin/stdout
- IN instruction blocks until input is received
- OUT instruction formats values consistently for educational clarity
- Test harness supports output capture via `cpu.on_out` callback