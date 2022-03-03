# eBPF Archictecture Plugin for Binary Ninja
Author: Ryan Jordan (@tryke)
Version: 0.1

## Introduction

This is a Binary Ninja plugin to add support for the eBPF architecture.
eBPF is designed to attach small, user-supplied programs to the Linux kernel.
It has also seen adoption as a portable bytecode format for other
applications, e.g. smart contracts.

## What Works

- Disassembly: Press the 'P' hotkey to create a procedure at the cursor
- Little-endian mode

## Next Priorities

- ELF support
- Low-Level IL lifting
