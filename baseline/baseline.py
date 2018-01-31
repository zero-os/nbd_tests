
from js9 import j
from io import BytesIO
import os
import time

logger = j.logger.logging

ROOT = os.path.dirname(os.path.abspath(__file__))

PACKENTNET_INSTANCE = 'main'
ZEROTIER_INSTANCE = 'main'

FACILITY = 'ams1'
MACHINE_NAME = 'nbd-baseline'
RESET = False
PLAN = 'baremetal_1'

# Flists
FLIST_FIO = 'https://hub.gig.tech/azmy/fio.flist'
FLIST_TARANTOOL = 'https://hub.gig.tech/azmy/nbd-tarantool.flist'
FLIST_NBD = 'https://hub.gig.tech/azmy/nbd-3.16.2.flist'
FLIST_FIO = 'https://hub.gig.tech/azmy/fio.flist'
FLIST_KVM = 'https://hub.gig.tech/azmy/ubuntu-xenial-bootable-sshd.flist'

NBD_SERVER_CONF = 'nbd-server.conf'
FIO_CONF = 'fio.conf'

NBD_CONFIG = {
    'port': 10809,
    'export': '/opt/disk',
    'size': '4G'
}


def make_node(name):
    zt = j.clients.zerotier.get(ZEROTIER_INSTANCE)
    cl = j.clients.packetnet.get(PACKENTNET_INSTANCE)
    zoscl, node, ip = cl.startZeroOS(
        hostname=name, plan=PLAN, facility=FACILITY,
        zerotierAPI=zt.config.data['token_'], zerotierId=zt.config.data['networkID_'],
        remove=RESET, params=['debug']
    )

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
        return container

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
    return container


def stop_base_nbd_client(container):
    tag = 'nbd-client'
    jobs = list(filter(lambda j: j['cmd']['tags'] is not None and tag in j['cmd']['tags'], container.job.list()))
    for job in jobs:
        container.job.kill(job['cmd']['id'])


def run_host_fio_test(cl, device):
    tag = 'fio'

    container = make_container(cl, tag, FLIST_FIO, privileged=True)

    config = j.sal.fs.fileGetContents(j.sal.fs.joinPaths(ROOT, FIO_CONF))
    config = config.format(dev=device)

    dir = '/opt'
    container.filesystem.mkdir(dir)

    buffer = BytesIO(config.encode())
    cfg = j.sal.fs.joinPaths(dir, 'fio.conf')
    container.filesystem.upload(cfg, buffer)

    result = container.system('fio %s' % cfg)

    while result.running:
        logger.info('waiting for fio test to finish')
        try:
            result.get()
        except Exception as e:
            print("error while getting result for fio: %s" % e)

    output = result.get()

    if output.state == 'ERROR':
        raise Exception('fio failed: %s', output.stderr)

    j.sal.fs.writeFile(j.sal.fs.joinPaths(ROOT, 'host-baseline-fio.out'), output.stdout)
    logger.info('Hosts tests written to %s/host-baseline-fio.out' % ROOT)


def make_kvm(cl, name, ssh=2222, media=None):
    vms = cl.kvm.list()
    if name not in [vm['name'] for vm in vms]:
        cl.kvm.create(
            name, media=media,
            flist=FLIST_KVM,
            nics=[{'type': 'default'}], port={2222: 22}
        )

    if not cl.nft.rule_exists(ssh, 'zt0'):
        cl.nft.open_port(ssh, 'zt0')

    authorized = ''
    for key in j.clients.ssh.ssh_keys_list_from_agent():
        pub = j.clients.ssh.SSHKeyGetFromAgentPub(key)
        authorized += pub + '\n'

    buffer = BytesIO(authorized.encode())

    # make sure key is uploaded
    path = j.sal.fs.joinPaths('/mnt', name, 'root', '.ssh')
    cl.filesystem.mkdir(path)
    cl.filesystem.upload(j.sal.fs.joinPaths(path, 'authorized_keys'), buffer)


def run_qemu_fio_test(cl, ip, server):
    # make a kvm node
    ssh = 2222
    make_kvm(cl, 'nbd-test', ssh, media=[
        {'url': 'nbd+tcp://%s:%s/default' % (container_ip(server), NBD_CONFIG['port'])},
    ])

    prefab = j.tools.prefab.getFromSSH(ip, ssh)

    prefab.core.file_write(
        '/etc/apt/sources.list',
        'deb http://archive.ubuntu.com/ubuntu/ xenial main universe multiverse restricted'
    )

    prefab.core.run('apt-get update')
    prefab.core.run('apt-get install -y fio')

    # upload same fio test file
    config = j.sal.fs.fileGetContents(j.sal.fs.joinPaths(ROOT, FIO_CONF))
    config = config.format(dev='vda')

    # upload config
    cfg = j.sal.fs.joinPaths('/tmp', 'config')
    prefab.core.file_write(cfg, config)

    code, out, err = prefab.core.run('fio %s' % cfg)
    if code != 0:
        raise Exception('failed to start nbd-server: %s' % err)

    j.sal.fs.writeFile(j.sal.fs.joinPaths(ROOT, 'guest-baseline-fio.out'), out)
    logger.info('Guest tests written to %s/guest-baseline-fio.out' % ROOT)

    return prefab


DEBUG = False

# Create node on packet.net
if not DEBUG:
    cl, _, ip = make_node(MACHINE_NAME)
    print("IP", ip)
else:
    # local defined node
    cl = j.clients.zero_os.get('main')

cl.timeout = 600
prepare_node(cl)

# 1- start nbd server
server = start_base_nbd_server(cl)

# 2- connect the client
client = start_base_nbd_client(cl, server)

# 3- run fio test
run_host_fio_test(cl, 'nbd0')

# 4- stop the client
stop_base_nbd_client(client)

# 5- make sure server still running
server = start_base_nbd_server(cl)

# 6- run inside a qemu vm
prefab = run_qemu_fio_test(cl, ip, server)
