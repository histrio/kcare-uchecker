#!/usr/bin/env python

import os
import sys
import csv
import time
import subprocess
import tempfile
import shutil

import logging
logging.basicConfig(filename='fetch.log', level=logging.DEBUG)

from uchecker import get_dist, check_output, get_build_id, NotAnELFException, BuildIDParsingException

REPOS_PARAMS = ["--enablerepo=*", "--disablerepo=*media*"]


def get_all_versions_rpm(package, latest=False):
    cmd = ["yum", "list", "available", package + ".x86_64"]
    if not latest:
        cmd += ["--showduplicates", ]
    cmd += REPOS_PARAMS
    for line in check_output(cmd).split('\n'):
        if line.startswith(package):
            # TODO: use repo also
            _, version, repo = line.split()
            if ":" in version:
                _, version = version.split(":", 1)
            yield repo, version


def get_all_versions_deb(package, latest=False):
    cmd = ["apt-cache", "madison", package]
    for line in check_output(cmd).split('\n'):
        if line.strip().startswith(package):
            _, version, repo = [it.strip() for it in line.split('|')]
            yield repo, version


def download_and_unpack_deb(package, version, dest):
    cmd = ["apt", "download",  package + '=' + version]
    subprocess.check_call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dest)
    version = version.replace(":", "%3a")
    pkg_path = os.path.join(dest,  '{0}_{1}_amd64.deb'.format(package, version))
    cmd = ["dpkg", "-x", pkg_path, dest]
    subprocess.check_call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=dest)
    return dest


def download_and_unpack_rpm(package, version, dest):
    package = package + '-' + version
    cmd = ["yumdownloader", "-x", "*i686", "--archlist=x86_64", "--nogpgcheck", "--destdir=" + dest]
    cmd += REPOS_PARAMS
    cmd.append(package)
    subprocess.check_call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pkg_path = os.path.join(dest, package + '.x86_64.rpm')
    rpm2cpio = subprocess.Popen(["rpm2cpio", pkg_path], stdout=subprocess.PIPE)
    cpio = subprocess.Popen(["cpio", "-idv"], stdin=rpm2cpio.stdout, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, cwd=dest)
    rpm2cpio.stdout.close()
    cpio.communicate()
    return dest


def iter_shared_libs(src):
    for root, _, files in os.walk(src):
        for fname in files:
            fpath = os.path.join(root, fname)
            if ".build-id" in fpath:
                continue
            try:
                with open(fpath, 'rb') as fd:
                    build_id = get_build_id(fd)
                yield fpath, build_id
            except (NotAnELFException, BuildIDParsingException, IOError) as err:
                logging.error("Can't read build_id of '%s': %s", fpath, err)


def fetch(package_name, latest):
    for dist in ('rpm', 'deb'):
        download_and_unpack = globals()['download_and_unpack_' + dist]
        get_all_versions = globals()['get_all_versions_' + dist]
        for repo, version in get_all_versions(package_name, latest):
            src = tempfile.mkdtemp('-fetch')
            logging.info('Fetch %s-%s to %s (%s)', 
                        package_name, version, src, dist)
            download_and_unpack(package_name, version, src)
            for slib, build_id in iter_shared_libs(src):
                libname = os.path.basename(slib)
                yield package_name, repo, version, libname, build_id
            shutil.rmtree(src)


def main(packages):
    dist = get_dist()
    latest = 'FETCH_ALL' not in os.environ
    logging.info("Dist: %s", dist)
    ts = int(time.time())
    tsv_writer = csv.writer(sys.stdout, delimiter='\t', lineterminator='\n')
    for package in packages:
        for rec in fetch(package, latest):
            tsv_writer.writerow((ts, dist, ) + rec)

if __name__ == "__main__":
    main(sys.argv[1:])
