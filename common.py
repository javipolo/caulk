import pykube
import logging

logger = logging.getLogger()
NAME = 'caulk'


# CRD helpers
class Middleware(pykube.objects.NamespacedAPIObject):
    version = 'traefik.containo.us/v1alpha1'
    endpoint = 'middlewares'
    kind = 'Middleware'


class MiddleGlue(pykube.objects.NamespacedAPIObject):
    version = 'kodify.io/v1alpha1'
    endpoint = 'middleglues'
    kind = 'MiddleGlue'


def kube_login():
    try:
        config = pykube.KubeConfig.from_service_account()
        logger.debug("Pykube is configured in cluster with service account.")
    except FileNotFoundError:
        config = pykube.KubeConfig.from_file()
        logger.debug("Pykube is configured via kubeconfig file.")
    return pykube.HTTPClient(config)


def gen_middleware(name, namespace, depth, sourcerange, mg=""):
    obj = {
        'apiVersion': 'traefik.containo.us/v1alpha1',
        'kind': 'Middleware',
        'metadata': {
            'name': name,
            'namespace': namespace,
            'labels': {
                'app.kubernetes.io/managed-by': NAME,
                'app.kubernetes.io/part-of': mg,
                },
            },
        'spec': {
            'ipWhiteList': {
                'ipStrategy': {'depth': depth},
                'sourceRange': sourcerange,
            },
          },
        }
    return obj


def gen_middleglue(name, namespace, depth, mw, sourcemiddlewares=[], ips=[]):
    obj = {
        'apiVersion': 'kodify.io/v1alpha1',
        'kind': 'MiddleGlue',
        'metadata': {
            'name': name,
            'namespace': namespace,
            },
        'spec': {
            'managedMiddleware': mw,
            'sourceMiddlewares': sourcemiddlewares,
            'ips': ips,
            'depth': depth,
          },
        }
    return obj
