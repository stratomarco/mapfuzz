# Restricted-unpickler structure-aware mutation notes

The input is a pickle opcode stream. Random byte mutation produces many
invalid streams that the unpickler rejects immediately, so most of the budget
is wasted before reaching the interesting handlers. A structure-aware approach
generates valid-ish opcode sequences and mutates the fields that drive the
dangerous handlers.

## Opcode-VM model

A pickle stream is a program for a stack machine: opcodes push, pop, build
containers, and (in full pickle) call functions. The restricted unpickler
reimplements a subset with an allowlist. The stack and the mark stack are the
core state. Bugs cluster where a handler indexes the stack without checking it
is non-empty or well-typed.

## High-value handlers and their untrusted inputs

- REDUCE: pops `args`, peeks `func` (must be allowlisted), then `func(*args)`.
  The allowlist gates the function; `args` are fully attacker-controlled. Target
  the rebuild/storage functions with malformed shapes, sizes, strides, offsets,
  dtypes. This is the path to the C++ backend.
- BUILD: `inst.set_(*state)` for Tensor, `__setstate__(state)` for Parameter,
  dict update for OrderedDict, with attacker-controlled `state`. Target
  malformed state tuples and wrong-arity `set_` arguments.
- SETITEM / SETITEMS: guarded to dict / OrderedDict / Counter, then
  `stack[-1][k] = v`. Target the guard boundaries and the key/value types.
- APPEND / APPENDS: guarded to list (and allowlisted list subclasses). Target
  the subclass boundary.
- MARK / stack manipulation and the persistent-id path: target sequences that
  leave the stack in unexpected depths so a later handler underflows.

## Mutation targets

- Opcode sequences that reach a handler with an empty or short stack (underflow).
- REDUCE argument tuples with wrong arity, extreme integers, negative sizes,
  mismatched declared-vs-actual counts (the storage-size-mismatch class).
- BUILD state tuples of wrong shape for `set_` / `__setstate__`.
- Deeply nested containers (recursion / stack depth).
- Large declared collection sizes (allocation).

## Approach

1. A generator that emits valid restricted-unpickler programs (choosing
   allowlisted globals, building small tensors/state_dicts) and mutates one
   field class per input while keeping the stream loadable up to the mutation
   point. This reaches the handlers reliably.
2. Seed-based byte/opcode mutation from the extracted `data.pkl` seeds, keeping
   the stream mostly valid.

Start with option 1 focused on REDUCE argument fuzzing for the allowlisted
storage/rebuild functions, since that is the documented path to the tensor
backend and the class of the most recent CVE.
