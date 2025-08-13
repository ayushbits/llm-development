## Installation
### Pip Installation
pip install --extra-index-url https://pypi.nvidia.com nemo-curator[cuda12x] # with CUDA

### Docker Installation
- Pull the container
`docker pull nvcr.io/nvidia/nemo-curator:latest`

- Run the container
`docker run --gpus all -it --rm nvcr.io/nvidia/nemo-curator:latest`
- NGC Container - https://catalog.ngc.nvidia.com/orgs/nvidia/containers/nemo-curator


## Nemo Curator
- Github - https://github.com/NVIDIA-NeMo/Curator/
- Docs - https://docs.nvidia.com/nemo/curator/latest/index.html
- Best Practices - https://docs.nvidia.com/nemo-framework/user-guide/latest/datacuration/bestpractices.html 
- Tutorials - https://github.com/NVIDIA-NeMo/Curator/tree/main/tutorials
- Tinystories example - https://github.com/NVIDIA-NeMo/Curator/tree/main/tutorials/tinystories
- Multinode setup guide on slurm - https://docs.nvidia.com/nemo/curator/latest/admin/deployment/slurm/index.html#admin-deployment-slurm