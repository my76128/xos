import os
import requests
import socket
import sys
import base64
from django.db.models import F, Q
from xos.config import Config
from observer.syncstep import SyncStep
from observer.ansible import run_template_ssh
from core.models import Service
from cord.models import VCPEService, VCPETenant, VBNGTenant, VBNGService
from hpc.models import HpcService, CDNPrefix
from util.logger import Logger, logging

VBNG_API = "http://<vnbg-addr>/onos/virtualbng/privateip/"

# hpclibrary will be in steps/..
parentdir = os.path.join(os.path.dirname(__file__),"..")
sys.path.insert(0,parentdir)

logger = Logger(level=logging.INFO)

class SyncVBNGTenant(SyncStep):
    provides=[VCPETenant]
    observes=VCPETenant
    requested_interval=0

    def __init__(self, **args):
        SyncStep.__init__(self, **args)

    def fetch_pending(self, deleted):
        if (not deleted):
            objs = VBNGTenant.get_tenant_objects().filter(Q(enacted__lt=F('updated')) | Q(enacted=None),Q(lazy_blocked=False))
        else:
            objs = VBNGTenant.get_deleted_tenant_objects()

        return objs

    def defer_sync(self, o, reason):
        o.backend_register="{}"
        o.backend_status = "2 - " + reason
        o.save(update_fields=['enacted','backend_status','backend_register'])
        logger.info("defer object %s due to %s" % (str(o), reason))

    def sync_record(self, o):
        logger.info("sync'ing VBNGTenant %s" % str(o))

        vcpes = VCPETenant.get_tenant_objects().all()
        vcpes = [x for x in vcpes if (x.vbng is not None) and (x.vbng.id == o.id)]
        if not vcpes:
            raise Exception("No vCPE tenant is associated with vBNG %s" % str(o.id))
        if len(vcpes)>1:
            raise Exception("More than one vCPE tenant is associated with vBNG %s" % str(o.id))

        vcpe = vcpes[0]
        sliver = vcpe.sliver

        if not sliver:
            raise Exception("No sliver associated with vBNG %s" % str(o.id))

        external_ns = None
        for ns in sliver.networkslivers.all():
            if (ns.ip) and (ns.network.template.visibility=="private") and (ns.network.template.translation=="none"):
                # need some logic here to find the right network
                external_ns = ns

        if not external_ns:
            self.defer_sync(o, "private network is not filled in yet")
            return

        private_ip = external_ns.ip

        if not o.routeable_subnet:
            print "This is where we would call Pingping's API"
            o.routeable_subnet = "placeholder-from-observer"

            # r = requests.post(VBNG_API + "%s" % private_ip, )
            # public_ip = r.json()
            # o.routeable_subnet = public_ip

        o.save()

    def delete_record(self, m):
        pass

