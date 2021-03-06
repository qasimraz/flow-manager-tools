import json
import logging

cache = {}


def get_from_cache_object(ctrl, url):
    if ctrl.name in cache:
        return cache[ctrl.name].get(url)


def add_to_cache_object(ctrl, url):
    if ctrl.name in cache:
        return cache[ctrl.name].get(url)


def get_from_api(ctrl, url, use_cache=True):
    data = get_from_cache_object(ctrl, url) if use_cache else None
    if not use_cache or not data:
        resp = ctrl.http_get(url)
        if resp is None or resp.status_code != 200 or resp.content is None:
            logging.debug("OPENFLOW: data not found for %s", url)
            return None
        data = json.loads(resp.content)
        add_to_cache_object(ctrl, data)

    return data


def get_topology(ctrl, topology_name, config=False, use_cache=True):
    url = (ctrl.get_config_url() if config else ctrl.get_operational_url()) + \
        '/network-topology:network-topology/topology/{}'.format(topology_name)
    data = get_from_api(ctrl, url, use_cache)
    if data:
        topology = data.get('topology')
        if topology is not None and len(topology) <= 0:
            return None
        return topology[0]


def get_openflow(ctrl, config=True, use_cache=True):
    url = (ctrl.get_config_url() if config else ctrl.get_operational_url()
           ) + '/opendaylight-inventory:nodes'
    return get_from_api(ctrl, url, use_cache)


def get_config_openflow(ctrl, use_cache=True):
    return get_openflow(ctrl=ctrl, config=True, use_cache=use_cache)


def get_operational_openflow(ctrl, use_cache=True):
    return get_openflow(ctrl=ctrl, config=False, use_cache=use_cache)


def get_fm_openflow(ctrl, use_cache=True):
    url = ctrl.get_operational_fm_url('openflow:nodes')
    return get_from_api(ctrl, url, use_cache)


def get_topology_nodes(ctrl, topology_name, filter_hosts=True, filter_anycast=True, use_cache=True):
    topology = get_topology(ctrl, topology_name,
                            config=False, use_cache=use_cache)
    if topology is None:
        return None

    nodes = topology.get('node')
    if nodes is None or len(nodes) <= 0:
        return None

    result = []
    for node in nodes:
        if filter_hosts and unicode(node['node-id']).startswith(unicode('host:')):
            continue
        if filter_anycast and unicode(node['node-id']).startswith(unicode('anycast:')):
            continue
        result.append(node['node-id'])

    return result if len(result) > 0 else None


def get_topology_links(ctrl, topology_name, filter_hosts=True, use_cache=True):
    topology = get_topology(ctrl, topology_name,
                            config=False, use_cache=use_cache)
    if topology is None:
        return None

    links = topology.get('link')
    if links is None or len(links) <= 0:
        return None

    result = {}
    for link in links:
        if filter_hosts and link['source']['source-node'].startswith('host:'):
            continue
        if filter_hosts and link['destination']['dest-node'].startswith('host:'):
            continue
        result[link['link-id']] = link

    return result if len(result) > 0 else None


def get_openflow_connected_nodes(ctrl, use_cache=True):
    data = get_operational_openflow(ctrl, use_cache)
    if data is None or 'nodes' not in data or 'node' not in data['nodes']:
        logging.debug("OPENFLOW: connected nodes not found")
        return None

    nodes = {}
    for node in data['nodes']['node']:
        name = node['id']
        if not name.startswith('openflow:'):
            continue
        nodes[name] = node

    return nodes if len(nodes) > 0 else None


def get_paths(ctrl, config=False, use_cache=True):
    url = ctrl.get_config_fm_url(
        'path:paths') if config else ctrl.get_operational_fm_url('path:paths')
    paths = get_from_api(ctrl, url, use_cache)
    if paths and 'paths' in paths and 'path' in paths['paths']:
        return paths['paths']['path']


def get_elines(ctrl, config=False, use_cache=True):
    url = ctrl.get_config_fm_url(
        'eline:elines') if config else ctrl.get_operational_fm_url('eline:elines')
    elines = get_from_api(ctrl, url, use_cache)
    if elines and 'elines' in elines and 'eline' in elines['elines']:
        return elines['elines']['eline']


def get_treepaths(ctrl, config=False, use_cache=True):
    url = ctrl.get_config_fm_url(
        'tree-path:treepaths') if config else ctrl.get_operational_fm_url('tree-path:treepaths')
    paths = get_from_api(ctrl, url, use_cache)
    if paths and 'treepaths' in paths and 'treepath' in paths['treepaths']:
        return paths['treepaths']['treepath']


def get_etrees(ctrl, config=False, use_cache=True):
    url = ctrl.get_config_fm_url(
        'etree:etrees') if config else ctrl.get_operational_fm_url('etree:etrees')
    etrees = get_from_api(ctrl, url, use_cache)
    if etrees and 'etrees' in etrees and 'etree' in etrees['etrees']:
        return etrees['etrees']['etree']


def get_path_mpls_nodes(ctrl, config=False, use_cache=True):
    url = ctrl.get_config_fm_url(
        'path-mpls:mpls-nodes') if config else ctrl.get_operational_fm_url('path-mpls:mpls-nodes')
    nodes = get_from_api(ctrl, url, use_cache)
    if nodes and 'mpls-nodes' in nodes:
        return nodes['mpls-nodes']


def get_eline_mpls_nodes(ctrl, config=False, use_cache=True):
    url = ctrl.get_config_fm_url(
        'eline-mpls:eline-nodes') if config else ctrl.get_operational_fm_url('eline-mpls:eline-nodes')
    nodes = get_from_api(ctrl, url, use_cache)
    if nodes and 'eline-nodes' in nodes:
        return nodes['eline-nodes']


def get_etree_sr_nodes(ctrl, config=False, use_cache=True):
    url = ctrl.get_config_fm_url(
        'etree-sr:etree-nodes') if config else ctrl.get_operational_fm_url('etree-sr:etree-nodes')
    nodes = get_from_api(ctrl, url, use_cache)
    if nodes and 'etree-nodes' in nodes:
        return nodes['etree-nodes']
