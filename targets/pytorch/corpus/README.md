# pytorch seed corpus

seed_state_dict.pkl is a minimal weights_only-loadable pickle. To enrich, add
varied checkpoints saved with torch.save on a machine with torch: different dtype
tensors, nested dict/list state, meta tensors, multiple storages. Each seed must
load via torch.load(weights_only=True). Keep seeds small.
