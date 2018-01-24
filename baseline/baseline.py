from js9 import j
import os


PACKENTNET_INSTANCE = 'main'
MACHINE_NAME = 'nbd-baseline'
REMOVE_MACHINE = False
OS = 'ubuntu_16_04'
PLAN = 'baremetal_1'

ROOT = os.path.dirname(os.path.abspath(__file__))

NBD_SERVER_CONF = 'nbd-server.conf'
FIO_CONF = 'fio.conf'

NBD_CONFIG = {
    'port': 6666,
    'export': '/tmp/baseline.disk',
    'size': '4G'
}

# ITSYOUONLINE_APP_ID = 'JNSnQnn-frYqg-8N6IsCQRdY5Hec'
# ITSYOUONLINE_APP_SECRET = 'Kw7lkYMoQbQH1NWQSujW___X-Lsv'
# curr_path = abspath(__file__).split(os.sep)
# home_dir = os.sep.join(curr_path[:curr_path.index('test_zos_vdisk')+1])


def init():
    cl = j.clients.packetnet.get(PACKENTNET_INSTANCE)

    _, prefab = cl.startDevice(
        MACHINE_NAME,
        plan=PLAN,
        remove=REMOVE_MACHINE,
        os=OS
    )
    return prefab


def prepare(machine):
    '''
    Install required packages.
    '''
    machine.system.package.ensure('nbd-server')
    machine.system.package.ensure('nbd-client')
    machine.system.package.ensure('fio')


def ensure_nbd_server(machine):
    ps = machine.system.process.find('nbd-server')
    if len(ps) >= 1:
        return

    config = j.sal.fs.fileGetContents(j.sal.fs.joinPaths(ROOT, NBD_SERVER_CONF))
    config = config.format(**NBD_CONFIG)

    # upload config
    dir = '/opt/nbd-server'
    machine.core.dir_ensure(dir)
    cfg = j.sal.fs.joinPaths(dir, 'config')
    machine.core.file_write(cfg, config)

    code, _, err = machine.core.run('nbd-server -C %s' % cfg)
    if code != 0:
        raise Exception('failed to start nbd-server: %s' % err)


def ensure_nbd_client(machine):
    ps = machine.system.process.find('nbd-client')
    if len(ps) > 0:
        return

    code, _, err = machine.core.run('modprobe nbd')
    if code != 0:
        raise Exception('failed to load nbd module: %s' % err)

    # we will always use nbd0
    code, _, err = machine.core.run('nbd-client localhost %s --name default /dev/nbd0' % NBD_CONFIG['port'])
    if code != 0:
        raise Exception('failed to start nbd-server: %s' % err)


def run_fio_host(machine):
    # upload fio.conf
    config = j.sal.fs.fileGetContents(j.sal.fs.joinPaths(ROOT, FIO_CONF))
    config = config.format(dev='nbd0')

    # upload config
    cfg = j.sal.fs.joinPaths('/tmp', 'config')
    machine.core.file_write(cfg, config)

    code, out, err = machine.core.run('fio %s' % cfg)
    if code != 0:
        raise Exception('failed to start nbd-server: %s' % err)

    j.sal.fs.writeFile(j.sal.fs.joinPaths(ROOT, 'host-fio.out'), out)


machine = init()
prepare(machine)

# start nbd server
ensure_nbd_server(machine)

# connect the client
ensure_nbd_client(machine)

# run fio host
run_fio_host(machine)

