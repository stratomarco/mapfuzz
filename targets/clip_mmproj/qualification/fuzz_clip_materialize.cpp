#include "clip.h"

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <unistd.h>

namespace {

std::atomic<unsigned long long> attempted{0};
std::atomic<unsigned long long> accepted{0};
std::atomic<unsigned long long> materialized{0};

struct progress_state {
    bool saw_data = false;
    float last = 0.0f;
};

bool record_progress(float progress, void * opaque) {
    auto * state = static_cast<progress_state *>(opaque);
    if (progress > state->last) {
        state->saw_data = true;
        state->last = progress;
    }
    return true;
}

void print_metrics() {
    std::fprintf(stderr,
                 "MAPFUZZ_METRICS attempted=%llu accepted=%llu materialized=%llu\n",
                 attempted.load(), accepted.load(), materialized.load());
}

struct register_metrics {
    register_metrics() {
        std::atexit(print_metrics);
    }
} register_metrics_once;

struct temp_file {
    char path[32] = "/tmp/mapfuzz_clip_XXXXXX";
    int fd = -1;

    temp_file() : fd(mkstemp(path)) {}
    ~temp_file() {
        if (fd >= 0) {
            close(fd);
        }
        unlink(path);
    }
};

} // namespace

extern "C" int LLVMFuzzerTestOneInput(const uint8_t * data, size_t size) {
    ++attempted;
    if (size == 0 || size > (1u << 20)) {
        return 0;
    }

    temp_file file;
    if (file.fd < 0) {
        return 0;
    }
    size_t written = 0;
    while (written < size) {
        const ssize_t n = write(file.fd, data + written, size - written);
        if (n <= 0) {
            return 0;
        }
        written += static_cast<size_t>(n);
    }
    close(file.fd);
    file.fd = -1;

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

    clip_init_result result = clip_init(file.path, params);
    if (progress.saw_data) {
        ++materialized;
    }
    if (result.ctx_v) {
        ++accepted;
        clip_free(result.ctx_v);
    }
    if (result.ctx_a) {
        clip_free(result.ctx_a);
    }
    if (result.ctx_gen_a) {
        clip_free(result.ctx_gen_a);
    }
    return 0;
}
