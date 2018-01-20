
# different tests

## requirements

- install js93 (development branch !!!)
- use node on packet.net use provisioning script in root 'provision.py'

## nbd servers

goal is to test impact tof nbd not of the backend implementation itself

### lua

- tarantool lua nbd server
- data in mem or redis (something as non blocking as possible)

### golang

- golang nbd server
- data in mem or redis (something as non blocking as possible)


## result of test

- document result of test, want to see MB/sec & iops (r/w/random)
- needs to be easy to understand result

## how to do

- use prefab to do all setup & execute tests
- all needs to be reproducable
- need separate scripts for each test

## reference tests

### test 1: raw test, lua, non buffered

- is lua nbd
- mount raw device
- do test make sure buffering is turned off

### test 2: raw test, lua, buffered (std)

- is lua nbd
- mount raw device
- fs buffer/cache is used

### test 3: raw test, lua, buffered (std), bcache

- is lua nbd
- mount raw device
- fs buffer/cache is used
- use bcache in between

### test 4,5,6 same as 1,2,3 but with golang


## vm tests

choose lua or golang whatever had best results above to do all further tests

### test 7: qemu nbd layer

- use nbd layer of qemu (check what are most optimal results)
- non buffered in OS

### test 7: qemu to raw device

- mount nbd volume and mount that one under qemu
- non buffered in OS

### test 8: qemu to nbd raw device on top of bcache

- mount nbd volume and mount that one under qemu
- bcache is used to speedup the raw device
- non buffered in OS

### test 9: qemu to qcow2, which is put on xfs which is put on raw ndb device

- mount nbd volume and mount
- put xfs on top
- put qcow2 image on top
- non buffered in OS in VM

### test 10: qemu to qcow2, which is put on xfs which is put on raw ndb device and using bcache

- mount nbd volume and mount
- put xfs on top
- put qcow2 image on top
- bcache is used to speedup the raw device
- non buffered in OS in VM



