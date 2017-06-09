DESCRIPTOR_ATTR_NAME = '_dofu_descriptors'
PASS_SVC_DESCRIPTOR = '_pass_svc'


def register_descriptor(fn, descriptor):
    if not hasattr(fn, DESCRIPTOR_ATTR_NAME):
        setattr(fn, DESCRIPTOR_ATTR_NAME, set())
    getattr(fn, DESCRIPTOR_ATTR_NAME).add(descriptor)


def has_descriptor(fn, descriptor):
    if hasattr(fn, DESCRIPTOR_ATTR_NAME) and descriptor in getattr(fn, DESCRIPTOR_ATTR_NAME):
        return True
    return False
