from js9 import j



def start_machine(remove=False):

    loginname=j.tools.myconfig.config.data["login_name"]
    if loginname=="":
        raise RuntimeError("please configure your login name, do:\n'js9_config configure -l j.tools.myconfig'")

    cl = j.clients.packetnet.get()  #will get your main connection to packet.net make sure has been configured

    node=cl.startDevice(hostname='%s-nbd'%loginname, plan='baremetal_1', facility='ams1', os='ubuntu_17_10', ipxeUrl=None, wait=True, remove=remove)

    p=node.prefab
    
    p.js9.js9core.install()
    p.runtimes.golang.install()

    #in case you need tarantool & lua
    p.db.tarantool.install()

    return node


node = start_machine(remove=True)
