import pykube
import kopf
import logging
import common

namespace = pykube.all
NAME = 'caulk'
logger = logging.getLogger(NAME)
middleglues = {}
api = common.kube_login()


# Initialize operator and kubernetes objects
def init(namespace):
    for mg in common.MiddleGlue.objects(api).filter(namespace=namespace):
        logger.info(f'[{mg.namespace}/{mg.name}] MiddleGlue found')
        update_middleglue(mg.name, mg.namespace, mg.obj['spec'])
        process_middleglue(mg.name, mg.namespace)


def remove_middleglue(mg, namespace):
    logger.info(f'[{namespace}/{mg}] MiddleGlue deleted')
    mw = middleglues[namespace][mg]['managedMiddleware']
    ns_mw = common.Middleware.objects(api)
    ns_mw.namespace = namespace
    logger.info(f'[{namespace}/{mw}] Managed Middleware deleted')
    obj = ns_mw.get(name=mw).obj
    if not check_middleware_ownership(mg, obj):
        logger.error(f'[{namespace}/{mw}] Managed MiddleWare is not handled by us. Doing nothing')
        return False
    common.Middleware(api, obj).delete()
    del middleglues[namespace][mg]


def update_middleglue(mg, namespace, spec):
    logger.info(f'[{namespace}/{mg}] MiddleGlue updated')
    if namespace not in middleglues:
        middleglues[namespace] = {}
    middleglues[namespace][mg] = spec


def process_middleware(mw, namespace):
    if namespace in middleglues:
        for mg in middleglues[namespace]:
            if mw in middleglues[namespace][mg]['sourceMiddlewares']:
                logger.info(f'[{namespace}/{mw}] Middleware changed, processing MiddleGlue {mg}')
                process_middleglue(mg, namespace)


def deleted_middleware(mw, namespace):
    logger.info(f'[{namespace}/{mw}] Managed Middleware deleted, recreating')
    if namespace in middleglues:
        for mg in middleglues[namespace]:
            logger.info(middleglues[namespace][mg]['managedMiddleware'])
            if mw == middleglues[namespace][mg]['managedMiddleware']:
                logger.info(f'[{namespace}/{mw}] Managed Middleware deleted, recreating')
                process_middleglue(mg, namespace)


def check_middleware_ownership(mg, obj):
    try:
        if obj['metadata']['labels']['app.kubernetes.io/managed-by'] != NAME:
            return False
        if obj['metadata']['labels']['app.kubernetes.io/part-of'] != mg:
            return False
    except KeyError:
        return False
    return True


def process_middleglue(mg, namespace):
    logger.info(f'[{namespace}/{mg}] MiddleGlue processed')
    cidrs = []

    source_mws = middleglues[namespace][mg]['sourceMiddlewares']
    managed_mw = middleglues[namespace][mg]['managedMiddleware']
    depth = middleglues[namespace][mg]['depth']
    cidrs.extend(middleglues[namespace][mg]['ips'])

    for source_mw in source_mws:
        try:
            if '/' in source_mw:
                source_namespace, source_name = source_mw.split('/')
            else:
                source_name = source_mw
                source_namespace = namespace
            ns_mw = common.Middleware.objects(api)
            ns_mw.namespace = source_namespace
            source_obj = ns_mw.get(name=source_name).obj
            cidrs.extend(source_obj['spec']['ipWhiteList']['sourceRange'])
        except pykube.ObjectDoesNotExist:
            logger.error(f'[{source_namespace}/{source_name}] Source Middleware does not exist')

    obj = common.gen_middleware(managed_mw, namespace, depth, cidrs, mg=mg)
    if common.Middleware(api, obj).exists():
        logger.info(f'[{namespace}/{managed_mw}] Updating managed MiddleWare')
        if not check_middleware_ownership(mg, obj):
            logger.error(f'[{namespace}/{managed_mw}] Managed MiddleWare is not handled by us. Not updating')
            raise kopf.PermanentError("Managed MiddleWare is not handled by us. Not updating")
        common.Middleware(api, obj).update()
    else:
        logger.info(f'[{namespace}/{managed_mw}] Creating managed MiddleWare')
        common.Middleware(api, obj).create()


# KOPF watchers
@kopf.on.create('middleglues')
@kopf.on.update('middleglues')
def middleglue_updated(name, namespace, spec, **kwargs):
    update_middleglue(name, namespace, spec)
    process_middleglue(name, namespace)


@kopf.on.delete('middleglues')
def middleglue_deleted(name, namespace, spec, **kwargs):
    remove_middleglue(name, namespace)


@kopf.on.create('middlewares')
@kopf.on.update('middlewares')
def middleware_updated(name, namespace, spec, **kwargs):
    process_middleware(name, namespace)


@kopf.on.delete('middlewares')
def middleware_deleted(name, namespace, spec, **kwargs):
    deleted_middleware(name, namespace)


init(namespace)
