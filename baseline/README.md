# Base line tests for NBD on ZeroOS
The purpose of this test is to set a base line for the nbd performance tests against
our implementations of the nbd servers.

The test will setup an `nbd-server` using the official NBD server implementation then
connect the device to `nbd0` using the official `nbd-client`. After that we run two test

> The tests run on a ZeroOS node, that is hosted on `packet.net Type 1` machine

We use `fio` with this [configuration](fio.conf)

## Host test
The test is performed by running `fio` test against `nbd0` device, directly on the ZOS host machine

Test results
```
randrw-4k: (g=0): rw=randrw, bs=(R) 4096B-4096B, (W) 4096B-4096B, (T) 4096B-4096B, ioengine=libaio, iodepth=16
fio-3.3
Starting 1 process

randrw-4k: (groupid=0, jobs=1): err= 0: pid=20: Wed Jan 31 08:22:54 2018
   read: IOPS=29.7k, BW=116MiB/s (122MB/s)(20.4GiB/180001msec)
    slat (nsec): min=972, max=553883, avg=9800.29, stdev=7228.82
    clat (usec): min=30, max=1813.6k, avg=250.71, stdev=2990.58
     lat (usec): min=44, max=1813.6k, avg=260.71, stdev=2990.61
    clat percentiles (usec):
     |  1.00th=[  157],  5.00th=[  186], 10.00th=[  200], 20.00th=[  217],
     | 30.00th=[  225], 40.00th=[  233], 50.00th=[  241], 60.00th=[  247],
     | 70.00th=[  255], 80.00th=[  265], 90.00th=[  281], 95.00th=[  302],
     | 99.00th=[  371], 99.50th=[  408], 99.90th=[  502], 99.95th=[  586],
     | 99.99th=[ 1237]
   bw (  KiB/s): min=   16, max=127720, per=100.00%, avg=120111.23, stdev=21517.06, samples=355
   iops        : min=    4, max=31930, avg=30027.81, stdev=5379.27, samples=355
  write: IOPS=29.7k, BW=116MiB/s (122MB/s)(20.4GiB/180001msec)
    slat (nsec): min=994, max=809690, avg=12471.65, stdev=9815.49
    clat (usec): min=30, max=1813.5k, avg=262.78, stdev=3994.83
     lat (usec): min=44, max=1813.6k, avg=275.47, stdev=3994.86
    clat percentiles (usec):
     |  1.00th=[  167],  5.00th=[  198], 10.00th=[  210], 20.00th=[  223],
     | 30.00th=[  231], 40.00th=[  239], 50.00th=[  245], 60.00th=[  251],
     | 70.00th=[  260], 80.00th=[  269], 90.00th=[  285], 95.00th=[  302],
     | 99.00th=[  383], 99.50th=[  420], 99.90th=[  515], 99.95th=[  611],
     | 99.99th=[ 1500]
   bw (  KiB/s): min=   16, max=128168, per=100.00%, avg=120045.39, stdev=21487.58, samples=355
   iops        : min=    4, max=32042, avg=30011.34, stdev=5371.89, samples=355
  lat (usec)   : 50=0.01%, 100=0.06%, 250=60.63%, 500=39.19%, 750=0.08%
  lat (usec)   : 1000=0.01%
  lat (msec)   : 2=0.01%, 4=0.01%, 10=0.01%, 20=0.01%, 50=0.01%
  lat (msec)   : 100=0.01%, 250=0.01%, 500=0.01%, 750=0.01%, 1000=0.01%
  lat (msec)   : 2000=0.01%
  cpu          : usr=8.61%, sys=20.66%, ctx=14166502, majf=0, minf=10
  IO depths    : 1=0.1%, 2=0.1%, 4=0.1%, 8=0.1%, 16=100.0%, 32=0.0%, >=64=0.0%
     submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     complete  : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.1%, 32=0.0%, 64=0.0%, >=64=0.0%
     issued rwt: total=5345625,5342702,0, short=0,0,0, dropped=0,0,0
     latency   : target=0, window=0, percentile=100.00%, depth=16

Run status group 0 (all jobs):
   READ: bw=116MiB/s (122MB/s), 116MiB/s-116MiB/s (122MB/s-122MB/s), io=20.4GiB (21.9GB), run=180001-180001msec
  WRITE: bw=116MiB/s (122MB/s), 116MiB/s-116MiB/s (122MB/s-122MB/s), io=20.4GiB (21.9GB), run=180001-180001msec

Disk stats (read/write):
  nbd0: ios=5341641/5338660, merge=0/0, ticks=806290/851266, in_queue=1659137, util=100.00%
```

## Guest test
Once the host tests are complete, we disconnect the client, and respwan the server (with exact config). Then we
start qemu VM that is connected to the exported nbd device. Then we install fio on the VM and rerun the same
exact fio tests

Results
```
randrw-4k: (g=0): rw=randrw, bs=4K-4K/4K-4K/4K-4K, ioengine=libaio, iodepth=16
fio-2.2.10
Starting 1 process

randrw-4k: (groupid=0, jobs=1): err= 0: pid=980: Wed Jan 31 08:40:25 2018
  read : io=20440MB, bw=116279KB/s, iops=29069, runt=180001msec
    slat (usec): min=1, max=460, avg= 3.70, stdev= 2.38
    clat (usec): min=40, max=859315, avg=264.80, stdev=1226.38
     lat (usec): min=88, max=859321, avg=268.68, stdev=1226.38
    clat percentiles (usec):
     |  1.00th=[  173],  5.00th=[  197], 10.00th=[  211], 20.00th=[  229],
     | 30.00th=[  239], 40.00th=[  249], 50.00th=[  258], 60.00th=[  266],
     | 70.00th=[  278], 80.00th=[  294], 90.00th=[  318], 95.00th=[  342],
     | 99.00th=[  398], 99.50th=[  422], 99.90th=[  494], 99.95th=[  540],
     | 99.99th=[  788]
    bw (KB  /s): min=   14, max=123384, per=100.00%, avg=116276.58, stdev=11484.90
  write: io=20408MB, bw=116099KB/s, iops=29024, runt=180001msec
    slat (usec): min=1, max=315, avg= 4.57, stdev= 2.60
    clat (usec): min=46, max=859454, avg=275.20, stdev=1647.71
     lat (usec): min=67, max=859457, avg=279.95, stdev=1647.70
    clat percentiles (usec):
     |  1.00th=[  191],  5.00th=[  211], 10.00th=[  223], 20.00th=[  239],
     | 30.00th=[  247], 40.00th=[  258], 50.00th=[  266], 60.00th=[  274],
     | 70.00th=[  286], 80.00th=[  298], 90.00th=[  326], 95.00th=[  354],
     | 99.00th=[  406], 99.50th=[  430], 99.90th=[  502], 99.95th=[  548],
     | 99.99th=[  892]
    bw (KB  /s): min=    7, max=123408, per=100.00%, avg=116208.08, stdev=11459.87
    lat (usec) : 50=0.01%, 100=0.01%, 250=36.60%, 500=63.30%, 750=0.08%
    lat (usec) : 1000=0.01%
    lat (msec) : 2=0.01%, 4=0.01%, 10=0.01%, 20=0.01%, 50=0.01%
    lat (msec) : 100=0.01%, 250=0.01%, 500=0.01%, 750=0.01%, 1000=0.01%
  cpu          : usr=10.22%, sys=35.63%, ctx=6072216, majf=0, minf=11
  IO depths    : 1=0.1%, 2=0.1%, 4=0.1%, 8=0.1%, 16=100.0%, 32=0.0%, >=64=0.0%
     submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     complete  : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.1%, 32=0.0%, 64=0.0%, >=64=0.0%
     issued    : total=r=5232605/w=5224504/d=0, short=r=0/w=0/d=0, drop=r=0/w=0/d=0
     latency   : target=0, window=0, percentile=100.00%, depth=16

Run status group 0 (all jobs):
   READ: io=20440MB, aggrb=116279KB/s, minb=116279KB/s, maxb=116279KB/s, mint=180001msec, maxt=180001msec
  WRITE: io=20408MB, aggrb=116099KB/s, minb=116099KB/s, maxb=116099KB/s, mint=180001msec, maxt=180001msec

Disk stats (read/write):
  vda: ios=5233546/5223729, merge=0/0, ticks=1360636/1410452, in_queue=2770908, util=100.00%%
```