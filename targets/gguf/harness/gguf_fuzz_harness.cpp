// GGUF parser fuzz harness.
//
// Target: ggml/llama.cpp GGUF loader, entry point gguf_init_from_buffer.
// API verified against ggml/include/gguf.h at llama.cpp commit
// 432d7ffe2c3b4e539f3d0d4ae0a4893090a018d6 (see targets/gguf/README.md).
//
// Design notes:
//   - Uses gguf_init_from_buffer (in-memory) rather than gguf_init_from_file so
//     the fuzzer never touches the filesystem per input.
//   - no_alloc = true: parses metadata and tensor descriptors without allocating
//     tensor data. This reaches the alignment, offset, enum, and size-computation
//     paths (the classes behind the 2026-05-15 advisory) while keeping each run
//     fast and memory-bounded.
//   - Every value accessor is gated on the type reported by the loader, so the
//     harness itself never invokes a type-mismatched accessor. A harness bug is
//     not a target finding.
//   - Assertion-triggered aborts (GGML_ASSERT) reachable through accessors are a
//     distinct triage category from memory-safety findings; see the target README.

#include <cstddef>
#include <cstdint>

#include "ggml.h"
#include "gguf.h"

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    struct gguf_init_params params;
    params.no_alloc = true;
    params.ctx      = nullptr;

    struct gguf_context *ctx =
        gguf_init_from_buffer(static_cast<const void *>(data), size, params);
    if (ctx == nullptr) {
        return 0;
    }

    // Metadata read path.
    const int64_t n_kv = gguf_get_n_kv(ctx);
    for (int64_t i = 0; i < n_kv; ++i) {
        (void) gguf_get_key(ctx, i);

        const enum gguf_type kt = gguf_get_kv_type(ctx, i);
        switch (kt) {
            case GGUF_TYPE_UINT8:   (void) gguf_get_val_u8(ctx, i);   break;
            case GGUF_TYPE_INT8:    (void) gguf_get_val_i8(ctx, i);   break;
            case GGUF_TYPE_UINT16:  (void) gguf_get_val_u16(ctx, i);  break;
            case GGUF_TYPE_INT16:   (void) gguf_get_val_i16(ctx, i);  break;
            case GGUF_TYPE_UINT32:  (void) gguf_get_val_u32(ctx, i);  break;
            case GGUF_TYPE_INT32:   (void) gguf_get_val_i32(ctx, i);  break;
            case GGUF_TYPE_FLOAT32: (void) gguf_get_val_f32(ctx, i);  break;
            case GGUF_TYPE_UINT64:  (void) gguf_get_val_u64(ctx, i);  break;
            case GGUF_TYPE_INT64:   (void) gguf_get_val_i64(ctx, i);  break;
            case GGUF_TYPE_FLOAT64: (void) gguf_get_val_f64(ctx, i);  break;
            case GGUF_TYPE_BOOL:    (void) gguf_get_val_bool(ctx, i); break;
            case GGUF_TYPE_STRING:  (void) gguf_get_val_str(ctx, i);  break;
            case GGUF_TYPE_ARRAY: {
                const enum gguf_type at = gguf_get_arr_type(ctx, i);
                const size_t n = gguf_get_arr_n(ctx, i);
                if (at == GGUF_TYPE_STRING) {
                    for (size_t j = 0; j < n; ++j) {
                        (void) gguf_get_arr_str(ctx, i, j);
                    }
                } else {
                    (void) gguf_get_arr_data(ctx, i);
                }
                break;
            }
            default:
                // Out-of-range or COUNT sentinel: do not call a value accessor.
                break;
        }
    }

    // Tensor descriptor read path: reaches per-tensor size computation
    // (the block-size division class) without allocating tensor data.
    const int64_t n_tensors = gguf_get_n_tensors(ctx);
    for (int64_t t = 0; t < n_tensors; ++t) {
        (void) gguf_get_tensor_name(ctx, t);
        (void) gguf_get_tensor_type(ctx, t);
        (void) gguf_get_tensor_offset(ctx, t);
        (void) gguf_get_tensor_size(ctx, t);
        (void) gguf_get_tensor_ne(ctx, t);
    }

    gguf_free(ctx);
    return 0;
}
