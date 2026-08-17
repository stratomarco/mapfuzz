# GGUF seed corpus

seed_minimal.gguf is a hand-made minimal valid GGUF. To enrich (better cold
start), add varied valid GGUF files generated on a machine with the `gguf` Python
package: different metadata types (int/float/string/array KVs), 0/1/multiple
tensors, various dtypes and dimension counts. Each seed should LOAD cleanly
(verify with the built fuzz_gguf on the seed before adding). Keep seeds tiny.
