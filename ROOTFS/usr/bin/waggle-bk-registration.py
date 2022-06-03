#!/usr/bin/env python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
import configparser
import json
import logging
import os
import os.path
import re
import subprocess
import sys
import time
from pathlib import Path

import click

software_version = "{{VERSION}}"

formatter = logging.Formatter("%(asctime)s  [%(name)s:%(lineno)d] (%(levelname)s): %(message)s")
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger = logging.getLogger("registration-service")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

client_id_file = "/etc/waggle/node-id"
config_file = "/etc/waggle/config.ini"
client_cert_suffix = "-cert.pub"


def read_file(path):
    return Path(path).read_text()


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Path(path).write_text(content)


def is_file_nonempty(path):
    try:
        return len(read_file(path)) > 0
    except FileNotFoundError:
        return False


def run_registration_command(reg_key, reg_key_cert, cert_user, cert_host, cert_port, command):
    command = [
        "ssh",
        "-vv",
        f"{cert_user}@{cert_host}",
        "-p",
        cert_port,
        "-i",
        reg_key,
        "-o",
        f"CertificateFile={reg_key_cert}",
        command,
    ]

    logger.info(f"executing: {' '.join(command)}")
    return subprocess.check_output(command).decode()


def make_request(command, cert_user, cert_host, cert_port, key, key_cert):
    logger.info("Making request %s to %s.", command, f"{cert_user}@{cert_host}:{cert_port}")

    start_time = time.time()

    while time.time() - start_time < 300:
        try:
            response = run_registration_command(
                key, key_cert, cert_user, cert_host, cert_port, command
            )
            logger.debug("Response for %s:\n%s.", command, response)
            return response
        except subprocess.CalledProcessError:
            logger.exception("Failed to get credentials from %s. Will retry in 30s...", cert_host)
            time.sleep(30)

    raise TimeoutError("Request timed out.")


def request_node_info(node_id, cert_user, cert_host, cert_port, key, key_cert):
    logger.info("Requesting node info from %s.", cert_host)

    response = make_request(
        "register {}".format(node_id), cert_user, cert_host, cert_port, key, key_cert
    )

    if "cert file not found" in response:
        raise ValueError("Certificate not found for {}.".format(node_id))

    return json.loads(response)


def get_certificates(
    node_id,
    cert_user,
    cert_host,
    cert_port,
    key,
    key_cert,
    client_pub_file,
    client_key_file,
    client_cert_file,
):
    logger.info("Getting credentials from %s for node-id [%s].", cert_host, node_id)

    node_info = None
    while True:
        try:
            node_info = request_node_info(node_id, cert_user, cert_host, cert_port, key, key_cert)

            write_file(client_pub_file, node_info["public_key"])
            os.chmod(client_pub_file, 0o600)

            write_file(client_cert_file, node_info["certificate"])
            os.chmod(client_cert_file, 0o600)

            write_file(client_key_file, node_info["private_key"])
            os.chmod(client_key_file, 0o600)

        except Exception as e:
            logger.error(f"(get_certificates) error: {str(e)}")
            time.sleep(30)
            continue

        break

    os.remove(key)
    os.remove(key_cert)
    logger.info("Registration complete")
    return node_info


@click.command()
@click.version_option(version=software_version, message=f"version: %(version)s")
def main():

    if not os.path.exists(config_file):
        sys.exit(f"File {config_file} not found")

    config = configparser.ConfigParser()
    config.read(config_file)

    # load reverse-tunnel specific variables
    if not "reverse-tunnel" in config:
        sys.exit(f"Section 'reverse-tunnel' missing in config file [{config_file}]")

    client_pub_file = config["reverse-tunnel"].get("pubkey")
    client_key_file = config["reverse-tunnel"].get("key", "")
    client_cert_file = f"{client_key_file}{client_cert_suffix}"

    if not client_pub_file:
        sys.exit("variable client_pub_file is not defined")

    if not client_key_file:
        sys.exit("variable client_key_file is not defined")

    # check if registration is needed
    required_files = [
        client_pub_file,
        client_key_file,
        client_cert_file,
    ]

    if all(is_file_nonempty(f) for f in required_files):
        logger.info("Node already has all credentials. Skipping registration.")
        sys.exit(0)

    # load registration specific variables
    if not "registration" in config:
        sys.exit(f"Section 'registration' missing in config file [{config_file}]")

    beekeeper_reg_host = config["registration"].get("host")
    beekeeper_reg_port = config["registration"].get("port")
    beekeeper_reg_user = config["registration"].get("user", "sage_registration")
    beekeeper_reg_privkey = config["registration"].get("key")
    beekeeper_reg_keycert = config["registration"].get("keycert")

    if not beekeeper_reg_host:
        sys.exit("variable beekeeper_reg_host is not defined")

    if not beekeeper_reg_port:
        sys.exit("variable beekeeper_reg_port is not defined")

    if not beekeeper_reg_user:
        sys.exit("variable beekeeper_reg_user is not defined")

    if not beekeeper_reg_privkey:
        sys.exit("variable beekeeper_reg_privkey is not defined")

    if not beekeeper_reg_keycert:
        sys.exit("variable beekeeper_reg_keycert is not defined")

    # get the node ID
    if not os.path.exists(client_id_file):
        sys.exit(f"Client node ID file {client_id_file} missing.")

    node_id = read_file(client_id_file)
    if not node_id:
        sys.exit(f"Client node ID file {client_id_file} empty.")

    # initiate registration
    node_info = get_certificates(
        node_id,
        beekeeper_reg_user,
        beekeeper_reg_host,
        beekeeper_reg_port,
        beekeeper_reg_privkey,
        beekeeper_reg_keycert,
        client_pub_file,
        client_key_file,
        client_cert_file,
    )


if __name__ == "__main__":
    main()
