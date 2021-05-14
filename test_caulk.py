#!/usr/bin/env python3

import pykube
import logging
import common
import time

logger = logging.getLogger()
sleep_time = 2
depths = [0, 1]


def apply_middleware(name, namespace, depth, sourcerange):
    obj = common.gen_middleware(name, namespace, depth, sourcerange)
    if common.Middleware(api, obj).exists():
        common.Middleware(api, obj).update()
    else:
        common.Middleware(api, obj).create()


def apply_middleglue(name, namespace, depth, mw, sourcemiddlewares=[], ips=[]):
    obj = common.gen_middleglue(name, namespace, depth, mw, sourcemiddlewares, ips)
    if common.MiddleGlue(api, obj).exists():
        common.MiddleGlue(api, obj).update()
    else:
        common.MiddleGlue(api, obj).create()


def delete_middleware(name, namespace):
    ns_obj = common.Middleware.objects(api)
    ns_obj.namespace = namespace
    obj = ns_obj.get(name=name).obj
    common.Middleware(api, obj).delete()


def delete_middleglue(name, namespace):
    ns_obj = common.MiddleGlue.objects(api)
    ns_obj.namespace = namespace
    obj = ns_obj.get(name=name).obj
    common.MiddleGlue(api, obj).delete()


def get_middleware_sourcerange(name, namespace):
    ns_obj = common.Middleware.objects(api)
    ns_obj.namespace = namespace
    obj = ns_obj.get(name=name).obj
    return sorted(obj['spec']['ipWhiteList']['sourceRange'])


def get_middleglue_cidrs(name, namespace):
    cidrs = []

    ns_obj = common.MiddleGlue.objects(api)
    ns_obj.namespace = namespace
    obj = ns_obj.get(name=name).obj
    source_mws = obj['spec']['sourceMiddlewares']
    cidrs.extend(obj['spec']['ips'])

    for source_mw in source_mws:
        if '/' in source_mw:
            source_namespace, source_name = source_mw.split('/')
        else:
            source_name = source_mw
            source_namespace = namespace
        ns_mw = common.Middleware.objects(api)
        ns_mw.namespace = source_namespace
        source_obj = ns_mw.get(name=source_name).obj
        cidrs.extend(source_obj['spec']['ipWhiteList']['sourceRange'])

    return sorted(cidrs)


def check_middleglue(name, namespace):
    ns_obj = common.MiddleGlue.objects(api)
    ns_obj.namespace = namespace
    obj = ns_obj.get(name=name).obj
    middleglue_depth = obj['spec']['depth']
    managed_middleware = obj['spec']['managedMiddleware']
    ns_mw = common.Middleware.objects(api)
    ns_mw.namespace = namespace
    mw_obj = ns_mw.get(name=managed_middleware).obj
    middleware_depth = mw_obj['spec']['ipWhiteList']['ipStrategy']['depth']
    middleware_sourcerange = get_middleware_sourcerange(managed_middleware, namespace)
    middleglue_cidrs = get_middleglue_cidrs(name, namespace)

    return (middleware_sourcerange == middleglue_cidrs) and (middleware_depth == middleglue_depth)


def simple_test(name, namespace, mw, sourcemiddlewares=[], ips=[]):
    for depth in [1, 2]:
        apply_middleglue(name, namespace, depth, mw, ips=ips, sourcemiddlewares=sourcemiddlewares)
        time.sleep(sleep_time)
        assert(check_middleglue(name, namespace))
        delete_middleglue(name, namespace)
        time.sleep(sleep_time)


def test_only_ips():
    simple_test('zoo', 'default', 'panda', ips=ips_zoo)


def test_one_middleware():
    simple_test('zoo', 'default', 'panda', sourcemiddlewares=['koala'])


def test_two_middlewares():
    simple_test('zoo', 'default', 'panda', sourcemiddlewares=['koala', 'bison'])


def test_one_middleware_ips():
    simple_test('zoo', 'default', 'panda', ips=ips_zoo, sourcemiddlewares=['koala'])


def test_two_middlewares_ips():
    simple_test('zoo', 'default', 'panda', ips=ips_zoo, sourcemiddlewares=['koala', 'bison'])


def test_namespace_one_middleware():
    simple_test('zoo', 'default', 'panda', sourcemiddlewares=['kube-system/zebra'])


def test_namespace_one_middleware_ips():
    simple_test('zoo', 'default', 'panda', ips=ips_zoo, sourcemiddlewares=['kube-system/zebra'])


def test_namespace_three_middlewares_ips():
    simple_test('zoo', 'default', 'panda', ips=ips_zoo,
                sourcemiddlewares=['kube-system/zebra', 'koala', 'bison'])


def test_add_ips():
    for depth in depths:
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo, sourcemiddlewares=['koala', 'bison'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo + ['5.5.5.5', '55.55.55.55'],
                         sourcemiddlewares=['koala', 'bison'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        delete_middleglue('zoo', 'default')
        time.sleep(sleep_time)


def test_remove_ips():
    for depth in depths:
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo, sourcemiddlewares=['koala', 'bison'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo[1:], sourcemiddlewares=['koala', 'bison'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        delete_middleglue('zoo', 'default')
        time.sleep(sleep_time)


def test_add_middlewares():
    for depth in depths:
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo, sourcemiddlewares=['koala'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo, sourcemiddlewares=['koala', 'bison'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        delete_middleglue('zoo', 'default')
        time.sleep(sleep_time)


def test_remove_middlewares():
    for depth in depths:
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo, sourcemiddlewares=['koala', 'bison'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo, sourcemiddlewares=['koala'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        delete_middleglue('zoo', 'default')
        time.sleep(sleep_time)


def test_remove_middleglue():
    for depth in depths:
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo, sourcemiddlewares=['koala', 'bison'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        delete_middleglue('zoo', 'default')
        time.sleep(sleep_time)
        ns_obj = common.MiddleGlue.objects(api)
        ns_obj.namespace = 'default'
        try:
            ns_obj.get(name='zoo').obj
            assert(False)
        except pykube.ObjectDoesNotExist:
            pass


def test_namespace_add_middlewares():
    for depth in depths:
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo, sourcemiddlewares=['koala', 'bison'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo,
                         sourcemiddlewares=['kube-system/zebra', 'koala', 'bison'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        delete_middleglue('zoo', 'default')
        time.sleep(sleep_time)


def test_namespace_remove_middlewares():
    for depth in depths:
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo,
                         sourcemiddlewares=['kube-system/zebra', 'koala', 'bison'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        apply_middleglue('zoo', 'default', depth, 'panda', ips=ips_zoo, sourcemiddlewares=['koala', 'bison'])
        time.sleep(sleep_time)
        assert(check_middleglue('zoo', 'default'))
        delete_middleglue('zoo', 'default')
        time.sleep(sleep_time)


api = common.kube_login()

ips_zebra = sorted(['1.1.1.1', '11.11.11.11'])
ips_bison = sorted(['2.2.2.2', '22.22.22.22'])
ips_koala = sorted(['3.3.3.3', '33.33.33.33'])
ips_zoo = sorted(['4.4.4.4', '44.44.44.44'])

apply_middleware('koala', 'default', 0, ips_koala)
apply_middleware('bison', 'default', 2, ips_bison)
apply_middleware('zebra', 'kube-system', 2, ips_zebra)
