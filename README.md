# nbd_tests

tests to see maximum performance of NBD

## requirements

- install js93

## configure the clients

### if you have access to despiegk testnodes repo

run the following script:

- https://docs.grid.tf/despiegk/node_tests/src/branch/master/configure.py

### do your own config

- configure your packet.net client (if not done yet)

```bash
js9_config configure -l j.clients.packetnet
```

will need also zerotier config

## configure your machine

```bash
python3 provision.py
```

## to work with configured nodes

try to play with js9_node

```bash
js9_node list
js9_node get -i myname
js9_node ssh -i myname

```

## remarks

- examples how to use clients in https://docs.grid.tf/despiegk/node_tests
