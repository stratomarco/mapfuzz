// libFuzzer harness for llama.cpp's mmproj/CLIP loader (clip_init).
// Targets the CLIP-specific hparam parsing + arithmetic layered on top of GGUF,
// a surface not reached by the existing OSS-Fuzz llama.cpp targets (which fuzz
// the core LLM load/inference path, not the multimodal projector loader).
//
// clip_init takes a filename, so we write the fuzz input to a temp file and load
// it. We disable GPU and set no_alloc/warmup off-path so we exercise the LOADER
// (parsing untrusted hparams), not tensor compute.

#include "clip.h"

#include <cstdint>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <string>
#include <unistd.h>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    // Bound input size: mmproj headers are small; huge inputs just slow fuzzing.
    if (size == 0 || size > (1u << 20)) return 0;

    // Write the fuzz bytes to a temp file (clip_init loads from a path).
    char tmpl[] = "/tmp/fuzz_clip_XXXXXX";
    int fd = mkstemp(tmpl);
    if (fd < 0) return 0;
    ssize_t w = write(fd, data, size);
    close(fd);
    if (w != (ssize_t)size) { unlink(tmpl); return 0; }

    // Minimal params: no GPU, no warmup. We want the loader/parse path only.
    clip_context_params params;
    memset(&params, 0, sizeof(params));
    params.use_gpu = false;
    params.warmup  = false;
    params.no_alloc = true;   // avoid allocating compute buffers; parse only
    params.image_min_tokens = -1;
    params.image_max_tokens = -1;

    // clip_init may throw on malformed input (the loader uses exceptions);
    // catch so libFuzzer sees a clean rejection, not a crash, for handled cases.
    try {
        clip_init_result r = clip_init(tmpl, params);
        if (r.ctx_v)     clip_free(r.ctx_v);
        if (r.ctx_a)     clip_free(r.ctx_a);
        if (r.ctx_gen_a) clip_free(r.ctx_gen_a);
    } catch (const std::exception &) {
        // expected for malformed projector files
    } catch (...) {
        // any other C++ exception is a clean rejection for this harness
    }

    unlink(tmpl);
    return 0;
}
