# **NCCL Setup**

[https://github.com/NVIDIA/nccl-tests](https://github.com/NVIDIA/nccl-tests)

1.1. What is NCCL?  
The NVIDIA Collective Communications Library (NCCL, pronounced “Nickel”) is a library for inter-GPU communication. \[[Doc](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/overview.html)\]

1.2. What is NCCL test?  
It's an [open-source software](https://github.com/NVIDIA/nccl-tests/tree/master) to benchmark inter-GPU communication speed.

1.3. Why/When do I care about NCCL test?  
When you run deep learning across multiple GPUs, you care about the communication speed among those GPUs.  
By running NCCL tests with various configs, you can check if your hardware can reach the designed performance for each config setting.


# **Basic Understanding**

Read this performance metric documentation before starting with the below instructions \- [https://github.com/NVIDIA/nccl-tests/blob/v2.13.11/doc/PERFORMANCE.md](https://github.com/NVIDIA/nccl-tests/blob/v2.13.11/doc/PERFORMANCE.md)

* This explains how NCCL (NVIDIA Collective Communications Library) performance tests report and interpret their results.   
* Operation Time \- NCCL tests report the average time (in milliseconds) it takes to complete a collective operation  
* Algorithm Bandwidth (algbw) \- How much data (in GB) is being processed per second by the algorithm. For point-to-point operations (like Send/Receive), this is meaningful and directly reflects throughput.  
* Bus Bandwidth (busbw) \- It adjusts the algorithm bandwidth to reflect the actual hardware bottleneck (e.g., NVLink, PCIe, network), making it possible to compare results regardless of the number of ranks.

# 

# **Setup Instructions**

We run nccl\_tests for AllReduce, ReduceScatter and AllGather on a large cluster of NVL8 nodes with the following configurations. \[[See this](https://github.com/NVIDIA/nccl-tests/tree/master?tab=readme-ov-file#running-multiple-operations-in-parallel) to set these parameters\]

* **NCCL\_TESTS\_SPLIT=MOD8** (Corresponds to NCCL\_TESTS\_SPLIT=MOD72 on NVL72 domain or NCCL\_TESTS\_SPLIT=MOD64 on NVL64 domain): This flag configures each collective group to incorporate a single GPU within an NVL domain. (See note on **NCCL\_TESTS\_SPLIT\_MASK** and **NCCL\_TESTS\_SPLIT** below).  
* **NCCL\_ALGO=Ring**: Fixed the NCCL algorithm to Ring to ensure that bus bandwidth remains unaffected by the auto-selection of different algorithms in NCCL.  
* **NCCL\_PROTO=Simple**: Fixed the NCCL protocol to Simple to ensure that bus bandwidth remains unaffected by the auto-selection of different protocols in NCCL.

We deliberately choose the Ring/Simple configuration for acceptance testing based on our experiments with 8 nodes (as shown in the figures below). The Ring/Simple offers the best balance between performance across message sizes and the smoothness of the S-curve.

Below are the steps we used to run the NCCL Test on a H100 NVL8 cluster. The same performance should be attained using either NCCL\_TESTS\_SPLIT \= MOD72 or NCCL\_TESTS\_SPLIT \= MOD64 within the respective NVL domain.

**Tools to be used for the test**: Slurm 24.05.4 (including pmix and pyxis plugins), NCCL 2.23.4, NCCL test 2.14, CUDA 12.6.

**Setup Steps using SLURM**:

1. Set up the container and install NCCL Test w/ MPI.

| \> srun \--pty \--container-image nvcr.io\\\#nvidia/pytorch:24.10-py3 \--container-save=${WORK\_DIR}/nvidia\_pytorch\_24.10.sqsh bash \-i\> git clone \-b v2.22.3-1 [https://github.com/NVIDIA/nccl.git](https://github.com/NVIDIA/nccl.git) \> cd nccl \> make \-j src.build \> cd ..\> git clone \-b v2.14.0 https://github.com/NVIDIA/nccl-tests.git\> cd nccl-tests\> make MPI=1 MPI\_HOME=/usr/local/mpi \-j 32\> exit *\# srun* |
| :---- |

2. Create a Slurm script acceptance\_nccl\_tests\_ring\_simple.sh for running the NCCL test.

| *\#\! /bin/bash \#SBATCH \--exclusive             \# exclusive node access \#SBATCH \--mem=0                 \# all mem avail \#SBATCH \--gpus-per-node=8 \#SBATCH \--ntasks-per-node=8**\#SBATCH \--output=%x\_%j.out**\#SBATCH \--overcommit**\#SBATCH \--comment=sysctl-sys.kernel.numa\_balancing=0,transparent\_hugepage\_defrag=never,transparent\_hugepage=never**\#SBATCH \-t 2:00:00             \# wall time* set \-xset \-e \-o pipefailNODES\=$SLURM\_JOB\_NUM\_NODESGPUS\_PER\_NODE\=${SLURM\_NTASKS\_PER\_NODE}  MAIN\_LOG\_DIR\=acceptance\_ring\_simpleWORKDIR\=$PWDLOGDIR\=$WORKDIR/$MAIN\_LOG\_DIRmkdir \-p ${LOGDIR}export NCCL\_BUILD\_PATH\=/workspace/nccl/buildexport LD\_LIBRARY\_PATH\=$NCCL\_BUILD\_PATH/lib:$LD\_LIBRARY\_PATHexport NCCL\_TEST\_PATH\=/workspace/nccl-tests/build*\#PARAMS for sweep*NCCL\_PARAMS\=" env LD\_LIBRARY\_PATH=/workspace/nccl/build/lib env NCCL\_BUFFSIZE= env NCCL\_DEBUG=INFO env NCCL\_ALGO=Ring env NCCL\_PROTO=Simple env NCCL\_TESTS\_SPLIT=MOD8 env NCCL\_P2P\_NET\_CHUNKSIZE=131072 "TESTS=(    "alltoall\_perf"    "all\_reduce\_perf"    "all\_gather\_perf"    "reduce\_scatter\_perf")TEST\_PARAMS\="-dfloat \-b8 \-e16G \-f2 \-g1"TEST\_PARAMS\_A2A\="-duint8 \-b8 \-e8G \-f2 \-g1"srun \-t5 \-N 1 \--ntasks-per-node 1 \--mpi\=pmix \--container-image\=${CONTAINER\_NAME} ${NCCL\_PARAMS} ls \-lrt ${NCCL\_TEST\_PATH}srun \-t5 \-N 1 \--ntasks-per-node 1 \--mpi\=pmix \--container-image\=${CONTAINER\_NAME} ${NCCL\_PARAMS} ldd ${NCCL\_TEST\_PATH}/all\_reduce\_perfecho XXXX STARTING SWEEP on ${NODES} nodesfor TEST in ${TESTS\[@\]};do   echo XXXX RUNNING Iteration $ITER $TEST w/ $ALGO,$PROTO on ${NODES} nodes ${GPUS} GPUs   LOGFILE\=LOG\_${TEST}\_N${NODES}n${GPUS\_PER\_NODE}\_ITER-${ITER}.txt   if \[\[ "${TEST}" \== "alltoall\_perf" \]\]; then      NCCL\_TEST\_PARAMS=$TEST\_PARAMS\_A2A   else      NCCL\_TEST\_PARAMS=$TEST\_PARAMS   fi   srun \-N ${NODES} \--ntasks-per-node ${GPUS\_PER\_NODE} \--mpi\=pmix \--container-image\=${CONTAINER\_NAME} ${NCCL\_PARAMS} ${NCCL\_TEST\_PATH}/${TEST} ${NCCL\_TEST\_PARAMS} | tee ${LOGDIR}/${LOGFILE}done |
| :---- |

**NOTE**: If you specify \-b8 in alltoall\_perf, all\_gather\_perf, reduce\_scatter\_perf, then the measured message size starts from (8 \* 2 \* num\_nodes)

3. Launch the NCCL tests with the following commands/scripts.

| *\#\! /bin/bash* for ITER in {1..5} ;do   CONTAINER\_NAME\=${WORK\_DIR}/nvidia\_pytorch\_24.10.sqsh ITER\=$ITER sbatch \-N 192 acceptance\_nccl\_tests\_ring\_simple.shdone |
| :---- |

4. You can use the following command to display the results for each run. The "size" column represents the message size in bytes, while the "out-of-place/busbw" column indicates the corresponding bus bandwidth.

| \> grep \-h \-v \-E 'NCCL|Rank' acceptance\_ring\_simple/\* |
| :---- |

**Setup Steps using mpirun**:

`LD_LIBRARY_PATH=nccl/build/lib/:$LD_LIBRARY_PATH` (Add absolute path to nccl)
`mpirun -x LD_LIBRARY_PATH  -np <num_gpus> --host <optional hosts> -x NCCL_ALGO=<ring/tree> -x NCCL_IB_HCA=<infiniband interfaces> ./build/all_reduce_perf -b 1G -e 8G -f 2 -g 1`
- -mca pml ucx -x UCX_NET_DEVICES - mpi specific flag
- Consult [nccl-test github](https://github.com/NVIDIA/nccl-tests) for arguments details


# Performance Comparison
- Check datasheet of corresponding GPUs to get theoretical peak performance of GPUs.