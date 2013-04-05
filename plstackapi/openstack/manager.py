from plstackapi.planetstack import settings
from django.core import management
management.setup_environ(settings)
from plstackapi.openstack.shell import OpenStackShell


class Manager:

    def __init__(self):
        
        self.shell = OpenStackShell()

    def refresh_nodes(self):
        # collect local nodes
        from plstackapi.core.models import Node
        nodes = Node.objects.all()
        nodes_dict = {}
        for node in nodes:
            nodes_dict[node.name] = node 

        # collect nova nodes:
        compute_nodes = self.shell.nova.hypervisors.list()
        compute_nodes_dict = {}
        for compute_node in compute_nodes:
            compute_nodes_dict[compute_node.hypervisor_hostname] = compute_node

        # add new nodes:
        new_node_names = set(compute_nodes_dict.keys()).difference(nodes_dict.keys())
        for name in new_node_names:
            node = Node(name=compute_nodes_dict[name].hypervisor_hostname)
            node.save()

        # remove old nodes
        old_node_names = set(nodes_dict.keys()).difference(compute_nodes_dict.keys())
        Node.objects.filter(name__in=old_node_names).delete()

    def refresh_flavors(self):
        # collect local flavors
        from plstackapi.core.models import Flavor
        flavors = Flavor.objects.all()
        flavors_dict = {}
        for flavor in flavors:
            flavors_dict[flavor.name] = flavor

        # collect nova falvors
        nova_flavors = self.shell.nova.flavors.list()
        nova_flavors_dict = {}
        for nova_flavor in nova_flavors:
            nova_flavors_dict[nova_flavor.name] = nova_flavor

        # add new flavors 
        new_flavor_names = set(nova_flavors_dict.keys()).difference(flavors_dict.keys())
        for name in new_flavor_names:
             
            flavor = Flavor(flavor_id=nova_flavors_dict[name].id,
                            name=nova_flavors_dict[name].name,
                            memory_mb=nova_flavors_dict[name].ram,
                            disk_gb=nova_flavors_dict[name].disk,   
                            vcpus=nova_flavors_dict[name].vcpus)
            flavor.save()

        # remove old flavors
        old_flavor_names = set(flavors_dict.keys()).difference(nova_flavors_dict.keys())
        Flavor.objects.filter(name__in=old_flavor_names).delete()
            
    def refresh_images(self):
        # collect local images
        from plstackapi.core.models import Image
        images = Image.objects.all()
        images_dict = {}    
        for image in images:
            images_dict[image.name] = image

        # collect glance images
        glance_images = self.shell.glance.get_images()
        glance_images_dict = {}
        for glance_image in glance_images:
            glance_images_dict[glance_image['name']] = glance_image

        # add new images
        new_image_names = set(glance_images_dict.keys()).difference(images_dict.keys())
        for name in new_image_names:
            image = Image(image_id=glance_images_dict[name]['id'],
                          name=glance_images_dict[name]['name'],
                          disk_format=glance_images_dict[name]['disk_format'],
                          container_format=glance_images_dict[name]['container_format'])
            image.save()

        # remove old images
        old_image_names = set(images_dict.keys()).difference(glance_images_dict.keys())
        Image.objects.filter(name__in=old_image_names).delete()
        
     