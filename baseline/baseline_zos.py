
from js9 import j
from io import BytesIO
import os
import time

logger = j.logger.logging

ROOT = os.path.dirname(os.path.abspath(__file__))

PACKENTNET_INSTANCE = 'main'
MACHINE_NAME = 'nbd-baseline'
RESET = False
PLAN = 'baremetal_1'

ZT_TOKEN = 'q7sh7dPnbuwN4525YDnjwfGUjAcXCCnW'
ZTID = '93afae5963f3ebd8'

VM_FLIST = 'https://hub.gig.tech/gig-official-apps/ubuntu-xenial-bootable.flist'

# Flists
FLIST_FIO = 'https://hub.gig.tech/azmy/fio.flist'
FLIST_TARANTOOL = 'https://hub.gig.tech/azmy/nbd-tarantool.flist'
FLIST_NBD = 'https://hub.gig.tech/azmy/nbd-3.16.2.flist'
# FLIST_NBD = 'https://hub.gig.tech/azmy/nbd-3.13.flist'

NBD_SERVER_CONF = 'nbd-server.conf'
FIO_CONF = 'fio.conf'

NBD_CONFIG = {
    'port': 10809,
    'export': '/opt/disk',
    'size': '4G'
}


def make_node(name):
    cl = j.clients.packetnet.get(PACKENTNET_INSTANCE)
    zoscl, node, ip = cl.startZeroOS(hostname=name, plan=PLAN, zerotierAPI=ZT_TOKEN, zerotierId=ZTID, remove=RESET)
    return zoscl, node, ip  # expanded for self documentation


def prepare_node(cl):
    disk = list(filter(lambda d: d['mountpoint'] == '/var/cache', cl.info.disk()))
    if len(disk):
        # disk is mounted
        return

    devices = list(filter(
        lambda device: 'children' not in device and device['mountpoint'] is None,
        cl.disk.list()['blockdevices']
    ))

    if len(devices) == 0:
        raise Exception('No cache devices found')

    device = j.sal.fs.joinPaths('/dev', devices[-1]['name'])
    found = False
    for fs in cl.btrfs.list():
        for dev in fs['devices']:
            if dev['path'] == device:
                found = True
                break

    if not found:
        cl.btrfs.create('cache', [device], overwrite=True)

    cl.disk.mount(device, '/var/cache')
    cl.system('modprobe nbd').get()


def make_container(cl, name, flist, privileged=False, host_network=False):
    matches = cl.container.find(name)
    container = None
    if len(matches) > 1:
        raise Exception('found multiple conainers of name: %s' % name)
    elif len(matches) == 1:
        container = cl.container.client(list(matches.keys())[0])
    else:
        srcmnt = '/var/cache/%s' % name
        cl.filesystem.mkdir(srcmnt)
        cid = cl.container.create(
            flist, tags=[name], host_network=host_network,
            privileged=privileged, mount={srcmnt: '/opt'}).get()

        container = cl.container.client(cid)

    return container


def container_ip(container):
    nics = container.info.nic()
    phys = [nic for nic in nics if 'loopback' not in nic['flags']]
    if len(phys) == 1:
        return phys[0]['addrs'][0]['addr'][:-3]

    raise Exception('more than one nic found')


def start_base_nbd_server(cl):
    tag = 'nbd-server'
    container = make_container(cl, tag, FLIST_NBD)

    # find the nbd-server job
    job = list(filter(lambda j: j['cmd']['tags'] is not None and tag in j['cmd']['tags'], container.job.list()))
    if len(job) == 1:
        return container

    container.system('truncate -s %s %s' % (NBD_CONFIG['size'], NBD_CONFIG['export']))

    config = j.sal.fs.fileGetContents(j.sal.fs.joinPaths(ROOT, NBD_SERVER_CONF))
    config = config.format(**NBD_CONFIG)

    # upload config
    dir = '/opt'
    container.filesystem.mkdir(dir)

    buffer = BytesIO(config.encode())
    cfg = j.sal.fs.joinPaths(dir, 'disk.config')
    container.filesystem.upload(cfg, buffer)

    result = container.system('nbd-server -d -C %s' % cfg, tags=[tag])
    # make sure the job will remain running
    for i in range(3):
        if not result.running:
            print(result.get())
            raise Exception('job exited')
        time.sleep(1)

    logger.info('NBD-SERVER JOB ID: %s', result.id)
    return container


def start_base_nbd_client(cl, server):
    tag = 'nbd-client'

    container = make_container(cl, tag, FLIST_NBD, privileged=True)

    # find the nbd-server job
    job = list(filter(lambda j: j['cmd']['tags'] is not None and tag in j['cmd']['tags'], container.job.list()))
    if len(job) == 1:
        return

    # we always use nbd0
    result = container.system(
        'nbd-client %s %s /dev/nbd0 -n -name default -b 4096' % (container_ip(server), NBD_CONFIG['port']),
        tags=[tag]
    )

    for i in range(3):
        if not result.running:
            print(result.get())
            raise Exception('job exited')
        time.sleep(1)

    logger.info('NBD-CLIENT JOB ID: %s', result.id)


cl, node, ip = make_node(MACHINE_NAME)

prepare_node(cl)

# start nbd server
server = start_base_nbd_server(cl)
client = start_base_nbd_client(cl, server)
