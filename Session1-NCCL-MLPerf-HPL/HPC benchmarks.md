# HPC benchmarks

This guide documents how to run the HPC benchmarks on a Slurm cluster provisioned by the BCM/Slurm on Azure MVP. The container image is at [https://catalog.ngc.nvidia.com/orgs/nvidia/containers/hpc-benchmarks](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/hpc-benchmarks) and the A100 reference performance is at [https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/nvidia-a100-datasheet-us-nvidia-1758950-r4-web.pdf](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/nvidia-a100-datasheet-us-nvidia-1758950-r4-web.pdf)

# Single Node Benchmark

## Get an interactive session on a GPU node.

With enroot configured properly you can now get an interactive shell on a node via the srun command. Don’t try to ssh to a compute node, let Slurm allocate a node for you. In a separate shell if you check the queue you will see that your interactive session is running as a normal slurm job.

```
srun --nodes=1 --gpus-per-node=8 --container-image=nvcr.io#nvidia/hpc-benchmarks:24.03 --container-mounts="/home/user:/workspace/test" --pty /bin/bash
```

enroot should have download the container image and you should get a shell on a GPU node

```
$ srun --nodes=1 --gpus-per-node=8 --container-image=nvcr.io#nvidia/hpc-benchmarks:24.03 --container-mounts="/home/user:/workspace/test" --pty /bin/bash
pyxis: importing docker image: nvcr.io#nvidia/hpc-benchmarks:24.03
pyxis: imported docker image: nvcr.io#nvidia/hpc-benchmarks:24.03
bash: /usr/bin/tclsh: No such file or directory
```

The workspace directory in the container contains sample slurm scripts and benchmark configuration files. For a x86\_64 architecture, start by looking at the HPL directory. You can copy sample dat and slurm files to your mounted directory so that you have them on your local file system. Considering the mount made, copy the files to \`/workspace/test\`

```
user@gpu001:/workspace$ ls -l hpl-linux-x86_64/
total 55364
-rw-r--r-- 1 user user     3177 Mar  4 16:38 COPYRIGHT-HPL-2.1
-rw-r--r-- 1 user user     1104 Mar  4 16:38 README
-rw-r--r-- 1 user user     1372 Mar  4 16:38 RUNNING
-rw-r--r-- 1 user user    16846 Mar  4 16:38 TUNING
-rwxr-xr-x 1 user user     6233 Mar  4 16:38 hpl.sh
drwxr-xr-x 2 user user     4096 Mar  4 16:38 sample-dat
drwxr-xr-x 2 user user     4096 Mar  4 16:38 sample-slurm
-rwxr-xr-x 1 user user 56642280 Mar  4 16:38 xhpl
```

An example of copying the file is shown below. It is useful if you want to keep a permanent copy of the input files instead of starting from scratch every time you run the container.

```
user@gpu001:/workspace$ cp hpl-linux-x86_64/sample-dat/HPL-1GPU.dat /workspace/test
```

## Running your first Benchmark

You will need to run the \`hpl.sh\` script and provide an input file that describes the operations that you want to perform. The basis is that HPL runs linear algebra operations on Matrices.

```
user@gpu001:/workspace$ .ƒcu/hpl.sh --dat ./hpl-linux-x86_64/sample-dat/HPL-1GPU.dat 
[gpu001:438533] PMIX ERROR: ERROR in file gds_ds12_lock_pthread.c at line 168
================================================================================
HPL-NVIDIA 24.3.0  -- NVIDIA accelerated HPL benchmark -- NVIDIA
================================================================================
```

After the run is complete you can see the performance that you obtained. HPL gives you the performance for FP64 precision. The output below shows that you obtained 16.98 TFlops. WIthout tuning the parameters this is already quite close to the theoretical 19.5 TFlops in FP64 of a A100.

```
================================================================================
T/V                N    NB     P     Q         Time          Gflops (   per GPU)
--------------------------------------------------------------------------------
WC0            92160  1024     1     1        30.73       1.698e+04 ( 1.698e+04)
HPL_pdgesv() start time Tue Mar 12 04:52:03 2024
HPL_pdgesv() end time   Tue Mar 12 04:52:34 2024
--------------------------------------------------------------------------------
||Ax-b||_oo/(eps*(||A||_oo*||x||_oo+||b||_oo)*N)=   0.000320172243 ...... PASSED
||Ax-b||_oo  . . . . . . . . . . . . . . . . . = 0.0000000009839921
||A||_oo . . . . . . . . . . . . . . . . . . . = 23224.8618729176305351
||x||_oo . . . . . . . . . . . . . . . . . . . = 12.9330625765687746
||b||_oo . . . . . . . . . . . . . . . . . . . = 0.4999958145935574
================================================================================
```

## Tuning the benchmark

If you want to push the envelope you can modify the parameters in your “dat” file, the biggest impact comes from the matrix size and the block size. An A100 has 80GB of GPU memory, it can fit a matrix of roughly 100,00 x 100,000. 

For instance the following snippet shows the content of the HPL dat file for a run with a Matrix of size 92800 and for 4 block sizes of 128,256,512 and 1024\. You will see that optimizing the matrix size for the available memory leads to better results, increasing the block size too much deteriorates the results.

```
HPLinpack benchmark input file
Innovative Computing Laboratory, University of Tennessee
HPL.out      output file name (if any)
6            device out (6=stdout,7=stderr,file)
1            # of problems sizes (N)
92800   Ns
4            # of NBs
128 256 512 1024         NBs
```

Getting 80% of the theoretical performance of the A100 is relatively easy but any additional gain afterwards is hard. Getting higher will require further optimization and digging deep into the system. However 17 TFlops 88% of max is not bad in such a short time, the snippet below shows the result with a matrix of size N=96256

```
================================================================================
T/V                N    NB     P     Q         Time          Gflops (   per GPU)
--------------------------------------------------------------------------------
WC0            96256  1024     1     1        34.92       1.703e+04 ( 1.703e+04)
```

# Running the Benchmark via Slurm

Within the container file system you will find a sample Slurm script to submit your benchmark runs to the scheduler. The container “runtime” is enroot, copy a sample and adapt it to your needs/environment. Here is where you find the samples

```
user@gpu001:/workspace$ ls -l hpl-linux-x86_64/sample-slurm/
total 16
-rw-r--r-- 1 user user 581 Mar  4 16:38 hpl-enroot-1N.sub
-rw-r--r-- 1 user user 581 Mar  4 16:38 hpl-enroot-8N.sub
```

The slurm script is simple and re-use the srun syntax that you used to get an interactive session. Do note the number of nodes and the \`gpus-per-node\` request.

```
user@slogin001:~$ more hpl-enroot-1N.sub 
#!/bin/bash
#SBATCH --nodes 1
#SBATCH --gpus-per-node=8
#SBATCH --job-name "test-hpl.1N"
#SBATCH --time=40:00
#SBATCH --output=enroot-%x.%J.%N.out
DATESTRING=`date "+%Y-%m-%dT%H:%M:%S"`
CONT='nvcr.io#nvidia/hpc-benchmarks:24.03'
MOUNT="/home/user:/workspace/test"
echo "Running on hosts: $(echo $(scontrol show hostname))"
echo "$DATESTRING"
srun --container-image="${CONT}" --container-mounts="${MOUNT}" ./hpl.sh --dat /workspace/test/HPL-1GPU.dat
echo "Done"
echo "$DATESTRING"
```

Back on the login node, submit a slurm job with the \`sbatch\` command and check that you are in the queue and running on a GPU node

```
user@slogin001:~$ sbatch hpl-enroot-1N.sub 
Submitted batch job 271
user@slogin001:~$ squeue
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
               271      defq test-hpl   user  R       0:03      1 gpu001
```

Once the job is finished you will have the result of your HPL benchmark in a file

```
$ ls -l | grep enroot-test-hpl.1N.271.gpu001.out 
-rw-rw-r-- 1 user user 21554 Mar 12 05:49 enroot-test-hpl.1N.271.gpu001.out
```

# Running MXP benchmark

FP8 precision is not available on A100, only on H100.

FP16 sloppy\_type \=2  
FP8 sloppy\_type \=1

Set the following environment variables

export MELLANOX\_VISIBLE\_DEVICES=all  
export PMIX\_MCA\_gds=hash  
export UCX\_NET\_DEVICES=eth0

```
srun -N1 --gpus-per-node=8 --ntasks-per-node=8 --cpu-bind=none --mem-bind=none --container-image="nvcr.io#nvidia/hpc-benchmarks:24.03" --mpi=pmix       ./hpl-mxp.sh       --gpu-affinity 0:1:2:3:4:5:6:7 --mem-affinity 1:1:0:0:3:3:2:2       --cpu-affinity 24-47:24-47:0-23:0-23:72-95:72-95:48-71:48-71 --ucx-affinity mlx5_0:mlx5_1:mlx5_2:mlx5_3:mlx5_4:mlx5_5:mlx5_6:mlx5_7       --n 380000 --nb 4096 --nprow 4 --npcol 2 --nporder row       --preset-gemm-kernel 0 --u-panel-chunk-nbs 8 --use-mpi-panel-broadcast 50 --sloppy-type 2       --call-dgemv-with-multiple-threads 0 --Anq-device 0 --mpi-use-mpi 1 --prioritize-trsm 0 --prioritize-factorization 1
```

FP16

```
 ****** HPL MxP Result    ****** 
    EPS           . . . . . . . . . . . . . . . . .          =    2.000000E-16
    Threshold     . . . . . . . . . . . . . . . . .          =    1.600000E+01
  ||Ax-b||_oo     . . . . . . . . . . . . . . . . .          =    1.026956E-13
  ||A   ||_oo     . . . . . . . . . . . . . . . . .          =    3.816733E+05
  ||x   ||_oo     . . . . . . . . . . . . . . . . .          =    5.287836E-06
  ||b   ||_oo     . . . . . . . . . . . . . . . . .          =    9.999958E-01
  ||Ax-b||_oo / (EPS * (||A||_oo * ||x||_oo + ||b||_oo) * N) =    4.477002E-04 ...... PASSED
    N = 380000, NB = 4096, NPROW = 4, NPCOL = 2, SLOPPY-TYPE = 2
       GFLOPS = 8.7877e+05, per GPU =  109846.77
    LU GFLOPS = 1.7273e+06, per GPU =  215914.71
 ****** HPL MxP Result    ****** 
```

That’s 215 TFlops per GPU for the LU solver which scales linearly to 1.73 PetaFlops for 8 GPUs.

## Running STREAM Memory Bandwidth Benchmark

```
./stream-gpu-test.sh --d 6
Command line: /workspace/stream-gpu-linux-x86_64/stream_test -d6 
======================================================================================
NVIDIA-STREAM 24.3.0  -- NVIDIA accelerated STREAM benchmark -- NVIDIA
======================================================================================
usage: ./stream_test
	-n<elements>    [Number of elements on array]
	-d<device>      [Device for testing]
There are 8 devices supporting CUDA
Device 0: "NVIDIA A100-SXM4-80GB" 	 108 SMs(8.0)	Memory: 1593MHz x 5120-bit = 2039.0 GB/s PEAK	 ECC is ON
Device 1: "NVIDIA A100-SXM4-80GB" 	 108 SMs(8.0)	Memory: 1593MHz x 5120-bit = 2039.0 GB/s PEAK	 ECC is ON
Device 2: "NVIDIA A100-SXM4-80GB" 	 108 SMs(8.0)	Memory: 1593MHz x 5120-bit = 2039.0 GB/s PEAK	 ECC is ON
Device 3: "NVIDIA A100-SXM4-80GB" 	 108 SMs(8.0)	Memory: 1593MHz x 5120-bit = 2039.0 GB/s PEAK	 ECC is ON
Device 4: "NVIDIA A100-SXM4-80GB" 	 108 SMs(8.0)	Memory: 1593MHz x 5120-bit = 2039.0 GB/s PEAK	 ECC is ON
Device 5: "NVIDIA A100-SXM4-80GB" 	 108 SMs(8.0)	Memory: 1593MHz x 5120-bit = 2039.0 GB/s PEAK	 ECC is ON
Device 6: "NVIDIA A100-SXM4-80GB" 	 108 SMs(8.0)	Memory: 1593MHz x 5120-bit = 2039.0 GB/s PEAK	 ECC is ON
Device 7: "NVIDIA A100-SXM4-80GB" 	 108 SMs(8.0)	Memory: 1593MHz x 5120-bit = 2039.0 GB/s PEAK	 ECC is ON
Device Selected 6: "NVIDIA A100-SXM4-80GB"
 STREAM Benchmark implementation in CUDA
 Array size (double)=67108864*8*8 (4096 MB)
Optimizing...
 [|||||||||||||||||||||||||||||||||||||||||||||||||\] 100.0% 
Function      Rate (MB/s)   Avg time     Min time     Max time
Copy:      1774334.0593       0.0006       0.0006       0.0006
Scale:     1765000.8783       0.0006       0.0006       0.0006
Add:       1784367.2629       0.0009       0.0009       0.0009
Triad:     1790970.6722       0.0009       0.0009       0.0009
```

That’s 1.7 TB/s out of theoretical 2TB/s

# Running on Multiple Nodes

Since there are multiple GPU nodes in the BCM/Slurm cluster, we can run a benchmark that will use MPI (i.e Message Passing Interface) to perform linear algebra operations across nodes. If the infiniband fabric is well configured, that the MPI library is also well built for the infrastructure we should also get good performance. Maybe close to 68 TFlops.

```
#/bin/bash
export OMPI_MCA_coll_hcoll_enable=0
export UCX_TLS=tcp
export UCX_NET_DEVICES=eth0
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export NCCL_SOCKET_IFNAME=eth0
export NCCL_IB_PCI_RELAXED_ORDERING=1
export NCCL_TOPO_FILE=/cm/shared/etc/ndv4-topo.xml
export NCCL_DEBUG=INFO
export NCCL_PROTO=LL,LL128,Simple
export NCCL_ALGO=Tree,Ring,CollnetDirect,CollnetChain,NVLS
export MELLANOX_VISIBLE_DEVICES=all
export PMIX_MCA_gds=hash
export PMIX_MCA_psec=native
#srun -N2 --exclusive --gpus-per-node 8 --mpi=pmix --container-mounts=/cm/shared/etc:/cm/shared/etc --container-image="nvcr.io#nvidia/pytorch:23.12-py3" -p defq all_reduce_perf_mpi -b 1G -e 4G 
-f 2 -g 8
srun --nodes 2 --gpus-per-node=8 --container-image="${CONT}" --container-mounts="${MOUNT}" --container-mounts=/cm/shared/etc:/cm/shared/etc --cpu-bind=none --mpi=pmix ./hpl.sh --dat /workspace/
hpl-linux-x86_64/sample-dat/HPL-dgx-1N-2.dat
```

Gives 33TFlops for two nodes, which is roughly twice the 17TFlops performance of one node.

```
================================================================================
T/V                N    NB     P     Q         Time          Gflops (   per GPU)
--------------------------------------------------------------------------------
WC0           136192  1024     2     1        50.86       3.311e+04 ( 1.656e+04)
HPL_pdgesv() start time Fri Mar 22 10:24:41 2024
HPL_pdgesv() end time   Fri Mar 22 10:25:32 2024
gpu001:407892:407892 [0] NCCL INFO comm 0x5555bc5462a0 rank 0 nranks 2 cudaDev 0 busId 100000 - Destroy COMPLETE
gpu001:407892:407892 [0] NCCL INFO comm 0x5555bfd50f10 rank 0 nranks 1 cudaDev 0 busId 100000 - Destroy COMPLETE
--------------------------------------------------------------------------------
||Ax-b||_oo/(eps*(||A||_oo*||x||_oo+||b||_oo)*N)=   0.000342665054 ...... PASSED
||Ax-b||_oo  . . . . . . . . . . . . . . . . . = 0.0000000005540878
||A||_oo . . . . . . . . . . . . . . . . . . . = 34324.2656301951064961
||x||_oo . . . . . . . . . . . . . . . . . . . = 3.1156139542548562
||b||_oo . . . . . . . . . . . . . . . . . . . = 0.4999973716258063
================================================================================
```

