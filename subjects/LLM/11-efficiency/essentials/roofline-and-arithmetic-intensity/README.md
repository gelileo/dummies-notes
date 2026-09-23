# Essential · The roofline and arithmetic intensity

**Needed for:** *"decode is memory-bound"*, *"FLOPs per byte"*, and every batching argument in
[chapter 11](../../README.md) and [chapter 10](../../../10-inference-and-decoding/).

## Two speed limits

```
   arithmetic: 9.90e+14 FLOP/s      memory: 3.35e+12 bytes/s
   ridge point = arithmetic / memory = 296 FLOPs per byte
   an operation doing fewer FLOPs per byte it moves is waiting on memory (memory-bound).
   more, and it is waiting on arithmetic (compute-bound). the roofline is min(peak, BW x intensity).
```

A chip can do arithmetic at one rate and fetch data at another, and they are wildly different:
an H100 performs about 300 floating-point operations in the time it takes to move one byte from
memory. Any computation is limited by whichever it runs out of first. The **roofline** is the
plot of that: throughput rises with FLOPs-per-byte until it hits the arithmetic ceiling.

## Arithmetic intensity of a matrix multiply

```
   FLOPs = 2*B*d*n.  bytes = 2*(B*d + d*n + B*n) in bf16.  for large d,n the weight term d*n dominates:
   intensity ~ 2*B*d*n / (2*d*n) = B.   each row of the batch reuses the same weights once more.
        B       FLOPs       bytes  FLOPs/byte  time (ms)   bound
        1     1.2e+08     1.2e+08           1      0.035   memory
        4     4.7e+08     1.2e+08           4      0.035   memory
       16     1.9e+09     1.2e+08          16      0.035   memory
       64     7.5e+09     1.2e+08          63      0.036   memory
      256     3.0e+10     1.3e+08         237      0.038   memory
     1024     1.2e+11     1.6e+08         775      0.121   compute
     4096     4.8e+11     2.7e+08        1792      0.486   compute
   below the ridge, doubling B is nearly free -- the time is the weight read either way.
```

For `[B, d] @ [d, n]` the weight matrix dominates the bytes and gets reused once per row of the
batch — so **intensity ≈ B**. At `B = 1` the chip fetches a weight and uses it once: hopelessly
memory-bound. Time barely moves as `B` grows, because you were waiting on the same weight read
either way. Only past the ridge does more batch cost more time.

## The same fact as utilisation

```
   B=1     achieved       3 TFLOP/s =    0% of peak
   B=16    achieved      53 TFLOP/s =    5% of peak
   B=256   achieved     794 TFLOP/s =   80% of peak
   B=1024  achieved     990 TFLOP/s =  100% of peak
   at B=1 the chip is ~0.3% utilised. this is why single-user decode is so wasteful and why
   serving systems batch requests together.
```

Single-user decode uses a fraction of a percent of the chip. That number is why inference
providers batch requests together and why a chatbot's per-token price falls with load.

## It is not only matmuls

```
   elementwise add      ~  0.17 FLOPs/byte -> memory-bound
   softmax (approx)     ~  1.25 FLOPs/byte -> memory-bound
   layernorm (approx)   ~  2.00 FLOPs/byte -> memory-bound
   matmul B=256         ~256.00 FLOPs/byte -> memory-bound
   almost everything except a big matmul is memory-bound. kernel fusion exists to avoid
   writing an intermediate to memory and reading it straight back.
```

Elementwise ops, softmax and normalisation do a handful of FLOPs per element and read and write
that element — all memory-bound. **Kernel fusion** exists to avoid writing an intermediate result
to memory and reading it straight back; FlashAttention is this idea applied to attention.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **roofline** | Achievable throughput = min(peak FLOP/s, bandwidth × intensity). |
| **arithmetic intensity** | FLOPs per byte moved. The x-axis of the roofline. |
| **ridge point** | Peak ÷ bandwidth: the intensity where memory stops being the limit. |
| **memory-bound** | Intensity below the ridge. Waiting on data. |
| **compute-bound** | Intensity above the ridge. Waiting on arithmetic. |
| **HBM bandwidth** | Bytes per second from GPU main memory. ~3.35 TB/s on an H100. |
| **kernel fusion** | Combining operations to avoid a round trip through memory. |
