import torch
print(torch.cuda.is_available())  # Should print True
print(torch.cuda.device_count()) # Should print the number of GPUs you have