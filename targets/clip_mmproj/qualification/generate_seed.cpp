#include "ggml.h"
#include "gguf.h"

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct tensor_spec {
    const char * name;
    std::vector<int64_t> dims;
};

const std::vector<tensor_spec> k_tensors = {
    {"v.patch_embd.weight",       {2, 2, 3, 4}},
    {"v.position_embd.weight",    {4, 1}},
    {"v.blk.0.attn_q.weight",     {4, 4}},
    {"v.blk.0.attn_k.weight",     {4, 4}},
    {"v.blk.0.attn_v.weight",     {4, 4}},
    {"v.blk.0.attn_out.weight",   {4, 4}},
    {"v.blk.0.ffn_up.weight",     {4, 8}},
    {"v.blk.0.ffn_down.weight",   {8, 4}},
    {"mm.0.weight",               {4, 4}},
    {"mm.0.bias",                 {4}},
    {"mm.2.weight",               {4, 4}},
    {"mm.2.bias",                 {4}},
};

const std::vector<tensor_spec> k_yi_tensors = {
    {"mm.1.weight",               {4}},
    {"mm.1.bias",                 {4}},
    {"mm.3.weight",               {4, 4}},
    {"mm.3.bias",                 {4}},
    {"mm.4.weight",               {4}},
    {"mm.4.bias",                 {4}},
};

ggml_tensor * make_tensor(ggml_context * ctx, const tensor_spec & spec) {
    ggml_tensor * tensor = ggml_new_tensor(
        ctx, GGML_TYPE_F32, static_cast<int>(spec.dims.size()), spec.dims.data());
    ggml_set_name(tensor, spec.name);
    auto * values = static_cast<float *>(tensor->data);
    for (int64_t i = 0; i < ggml_nelements(tensor); ++i) {
        values[i] = static_cast<float>((i % 17) - 8) / 64.0f;
    }
    return tensor;
}

} // namespace

int main(int argc, char ** argv) {
    if (argc != 3) {
        std::fprintf(stderr,
                     "usage: %s OUTPUT benign|malformed|missing|missing-projector|yi\n",
                     argv[0]);
        return 2;
    }
    const std::string mode = argv[2];
    if (mode != "benign" && mode != "malformed" && mode != "missing" &&
        mode != "missing-projector" && mode != "yi") {
        std::fprintf(stderr, "unknown mode: %s\n", mode.c_str());
        return 2;
    }

    gguf_context * gguf = gguf_init_empty();
    if (!gguf) {
        throw std::runtime_error("gguf_init_empty failed");
    }
    ggml_init_params init = {
        /*.mem_size   =*/ 16u * 1024u * 1024u,
        /*.mem_buffer =*/ nullptr,
        /*.no_alloc   =*/ false,
    };
    ggml_context * data = ggml_init(init);
    if (!data) {
        gguf_free(gguf);
        throw std::runtime_error("ggml_init failed");
    }

    gguf_set_val_str(gguf, "general.architecture", "clip");
    gguf_set_val_str(gguf, "general.name", "mapfuzz-synthetic-clip-mlp");
    gguf_set_val_bool(gguf, "clip.has_vision_encoder", true);
    gguf_set_val_str(gguf, "clip.projector_type",
                     mode == "malformed" ? "mapfuzz-unsupported" : "mlp");
    gguf_set_val_u32(gguf, "clip.vision.embedding_length", 4);
    gguf_set_val_u32(gguf, "clip.vision.block_count", 1);
    gguf_set_val_u32(gguf, "clip.vision.feed_forward_length", 8);
    gguf_set_val_u32(gguf, "clip.vision.attention.head_count", 1);
    gguf_set_val_u32(gguf, "clip.vision.image_size", 2);
    gguf_set_val_u32(gguf, "clip.vision.patch_size", 2);
    gguf_set_val_u32(gguf, "clip.vision.projection_dim", 4);
    gguf_set_val_f32(gguf, "clip.vision.attention.layer_norm_epsilon", 1.0e-5f);
    const float image_mean[3] = {0.5f, 0.5f, 0.5f};
    const float image_std[3] = {0.5f, 0.5f, 0.5f};
    gguf_set_arr_data(gguf, "clip.vision.image_mean", GGUF_TYPE_FLOAT32,
                      image_mean, 3);
    gguf_set_arr_data(gguf, "clip.vision.image_std", GGUF_TYPE_FLOAT32,
                      image_std, 3);

    for (const auto & spec : k_tensors) {
        if (mode == "missing" && std::strcmp(spec.name, "v.blk.0.attn_out.weight") == 0) {
            continue;
        }
        if (mode == "missing-projector" && std::strcmp(spec.name, "mm.2.weight") == 0) {
            continue;
        }
        if (mode == "yi" && std::strncmp(spec.name, "mm.2.", 5) == 0) {
            continue;
        }
        ggml_tensor * tensor = make_tensor(data, spec);
        gguf_add_tensor(gguf, tensor);
        std::printf("tensor name=%s type=F32 bytes=%zu dims=", spec.name,
                    ggml_nbytes(tensor));
        for (size_t i = 0; i < spec.dims.size(); ++i) {
            std::printf("%s%lld", i ? "x" : "", static_cast<long long>(spec.dims[i]));
        }
        std::printf("\n");
    }
    if (mode == "yi") {
        for (const auto & spec : k_yi_tensors) {
            ggml_tensor * tensor = make_tensor(data, spec);
            gguf_add_tensor(gguf, tensor);
            std::printf("tensor name=%s type=F32 bytes=%zu dims=", spec.name,
                        ggml_nbytes(tensor));
            for (size_t i = 0; i < spec.dims.size(); ++i) {
                std::printf("%s%lld", i ? "x" : "",
                            static_cast<long long>(spec.dims[i]));
            }
            std::printf("\n");
        }
    }

    gguf_write_to_file(gguf, argv[1], false);
    ggml_free(data);
    gguf_free(gguf);
    return 0;
}
