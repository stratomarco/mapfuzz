#!/usr/bin/env python3
# Generate a minimal VALID gguf seed for the GGUFReader fuzzer corpus.
# Requires gguf-py on PYTHONPATH (llama.cpp/gguf-py).
import os
import gguf

def main(out="corpus/seed.gguf"):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    w = gguf.GGUFWriter(out, "llama")
    w.add_uint32("answer", 42)
    w.add_string("name", "seed")
    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.close()
    print("seed written:", os.path.getsize(out), "bytes")

if __name__ == "__main__":
    main()
