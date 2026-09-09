#include "clip.h"
#include "ggml.h"
#include "gguf.h"

#include <algorithm>
#include <cstdio>
#include <filesystem>
#include <limits>

namespace {

struct progress_state {
    size_t callbacks = 0;
    size_t data_events = 0;
    float last = 0.0f;
};

bool record_progress(float progress, void * opaque) {
    auto * state = static_cast<progress_state *>(opaque);
    ++state->callbacks;
    if (progress > state->last) {
        ++state->data_events;
        state->last = progress;
    }
    return true;
}

void free_result(clip_init_result & result) {
    if (result.ctx_v) {
        clip_free(result.ctx_v);
    }
    if (result.ctx_a) {
        clip_free(result.ctx_a);
    }
    if (result.ctx_gen_a) {
        clip_free(result.ctx_gen_a);
    }
}

} // namespace

int main(int argc, char ** argv) {
    if (argc != 2) {
        std::fprintf(stderr, "usage: %s MODEL.gguf\n", argv[0]);
        return 2;
    }

    const uintmax_t file_size = std::filesystem::file_size(argv[1]);
    ggml_context * meta = nullptr;
    gguf_init_params inspect_params = {
        /*.no_alloc =*/ true,
        /*.ctx      =*/ &meta,
    };
    gguf_context * gguf = gguf_init_from_file(argv[1], inspect_params);
    if (!gguf || !meta) {
        std::printf("MILESTONE metadata_rejected file_bytes=%ju\n", file_size);
        if (gguf) {
            gguf_free(gguf);
        }
        if (meta) {
            ggml_free(meta);
        }
        return 3;
    }

    const int64_t n_tensors = gguf_get_n_tensors(gguf);
    uintmax_t declared_end = gguf_get_data_offset(gguf);
    size_t declared_bytes = 0;
    for (int64_t i = 0; i < n_tensors; ++i) {
        const char * name = gguf_get_tensor_name(gguf, i);
        ggml_tensor * tensor = ggml_get_tensor(meta, name);
        const size_t bytes = ggml_nbytes(tensor);
        declared_bytes += bytes;
        declared_end = std::max<uintmax_t>(
            declared_end,
            gguf_get_data_offset(gguf) + gguf_get_tensor_offset(gguf, i) + bytes);
    }
    std::printf("MILESTONE metadata_accepted file_bytes=%ju\n", file_size);
    std::printf("MILESTONE descriptors_accepted count=%lld declared_bytes=%zu declared_end=%ju complete=%s\n",
                static_cast<long long>(n_tensors), declared_bytes, declared_end,
                declared_end <= file_size ? "true" : "false");
    ggml_free(meta);
    gguf_free(gguf);

    progress_state progress;
    clip_context_params params{};
    params.use_gpu = false;
    params.device = nullptr;
    params.flash_attn_type = CLIP_FLASH_ATTN_TYPE_DISABLED;
    params.image_min_tokens = -1;
    params.image_max_tokens = -1;
    params.warmup = false;
    params.no_alloc = false;
    params.progress_callback = record_progress;
    params.progress_callback_user_data = &progress;

    clip_init_result result = clip_init(argv[1], params);
    std::printf("MILESTONE tensor_read_events count=%zu callbacks=%zu final_progress=%.6f\n",
                progress.data_events, progress.callbacks, progress.last);
    if (!result.ctx_v) {
        std::printf("MILESTONE consumer_rejected\n");
        free_result(result);
        return 4;
    }
    std::printf("MILESTONE consumer_constructed modality=vision output_embedding=%d\n",
                clip_n_mmproj_embd(result.ctx_v));
    free_result(result);
    return 0;
}
