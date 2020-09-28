#!/usr/bin/env python3
__author__ = 'Sean R. Lynch'
__copyright__ = '(c) 2020 Sean R. Lynch'
__email__ = 'seanl@literati.org'

"""Controller main module."""

import argparse
from collections import defaultdict
import logging
import os
import time

import digitalocean
from kubernetes import client, config, watch


ANNOTATION_PREFIX = 'do-pod-dns-controller.literati.org/'
TTL = 30
INTERVAL = 10


def split_hostname(domains, hostname):
    """
    Find the longest matching domain and strip it off the end of the
    hostname.

    """

    match = None
    match_domain = None
    for domain in domains:
        if hostname.endswith(domain):
            if len(hostname) == len(domain):
                # Same length, can't be a longer match
                match = ''
                match_domain = domain
                break

            if hostname[-len(domain)-1] != '.':
                # False match: not separated by dot
                logging.debug('False match: {!r} {!r}'.format(hostname, domain))
                break

            m = hostname[:-len(domain)-1]
            # Shorter hostname means longer matching domain
            if match is None or len(m) < len(match):
                match = m
                match_domain = domain

    return match, match_domain


def update_dns(host, domain, ips):
    """Do the actual DNS update."""

    logging.debug(f'Setting {host!r} {domain!r} to {ips!r}.')
    d = digitalocean.Domain(token=DIGITALOCEAN_TOKEN, name=domain)
    records = d.get_records()
    # Make a copy since we mutate it
    needed_ips = set(ips)
    records_to_delete = []
    for r in records:
        if r.name == host and r.type == 'A':
            if r.data in needed_ips:
                if r.ttl != TTL:
                    logging.info('Updating TTL for {host!r} {domain!r} {r.data!r} from {r.ttl!r} to {TTL}.')
                    r.ttl = TTL
                    r.save()
                needed_ips.remove(r.data)
            else:
                # Make sure we remove duplicates
                records_to_delete.append(r)

    for ip in needed_ips:
        # If we have any records to delete, update some instead
        if records_to_delete:
            r = records_to_delete.pop()
            logging.info(f'Updating {host!r} in {domain!r} from {r.data!r} to {ip!r}.')
            r.data = ip
            r.ttl = TTL
            r.save()
        else:
            logging.info(f'Creating new record mapping {host!r} in {domain!r} to {ip!r}.')
            r.create_new_domain_record(
                type='A',
                name=host,
                ttl=TTL,
                data=ip)

    # Delete any remaining unwanted records
    for r in records_to_delete:
        logging.info(f'Deleting {r.name!r} {domain!r} {r.type!r} {r.data!r}.')
        r.destroy()


def loop(domains):
    try:
        config.load_kube_config()
    except Exception:
        logging.info('Using in-cluster config.')
        config.load_incluster_config()

    v1 = client.CoreV1Api()
    while True:
        node_external_ips = {}
        hostnames = defaultdict(set)
        for node in v1.list_node().items:
            node_name = node.metadata.name
            for address in node.status.addresses:
                if address.type == 'ExternalIP':
                    node_external_ips[node.metadata.name] = address.address
                    break
            else:
                logging.warning('Node {!r} has no ExternalIP.'.format(node_name))

        for pod in v1.list_pod_for_all_namespaces(watch=False).items:
            annotations = pod.metadata.annotations
            if pod.status.phase != 'Running' or annotations is None:
                continue

            annotations = {
                k[len(ANNOTATION_PREFIX):]: v for k, v in pod.metadata.annotations.items() if k.startswith(ANNOTATION_PREFIX)
            }

            if not annotations:
                continue

            name = '{}/{}'.format(pod.metadata.namespace, pod.metadata.name)
            if 'hostname' not in annotations:
                logging.warnig('Annotated pod without hostname: {!r}'.format(name))
                continue

            for k in annotations.keys():
                if k != 'hostname':
                    logging.warning('Unrecognized annotation on pod {!r}: {!r}'.format(name, k))

            node_name = pod.spec.node_name
            if node_name not in node_external_ips:
                logging.warning('Pod {!r} is on unknown node {!r}. Probably a new node.'.format(name, node_name))
                continue

            hostnames[annotations['hostname']].add(node_external_ips[node_name])

        for hostname, ips in hostnames.items():
            host, domain = split_hostname(domains, hostname)
            if domain is None:
                logging.debug('Non-matching hostname: {!r} {!r}'.format(hostname, domains))
            else:
                update_dns(host, domain, ips)

        time.sleep(10)


def main():
    global DIGITALOCEAN_TOKEN
    parser = argparse.ArgumentParser()
    parser.add_argument('--domain', action='append')
    parser.add_argument('--log-level', default='info')
    args = parser.parse_args()

    if not args.domain:
        print('At least one domain is required.')
        parser.print_usage()
        return 1

    if args.log_level:
        logging.getLogger().setLevel(args.log_level.upper())

    DIGITALOCEAN_TOKEN = os.environ['DIGITALOCEAN_TOKEN']
    loop(args.domain)


if __name__ == '__main__':
    main()
