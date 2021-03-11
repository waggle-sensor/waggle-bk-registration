#!/usr/bin/env python3
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
import configparser
import logging
import os
import os.path
import re
import subprocess
import sys
import time
import json
from pathlib import Path
import click

# from kubernetes import client, config

software_version = "{{VERSION}}"

formatter = logging.Formatter(
    "%(asctime)s  [%(name)s:%(lineno)d] (%(levelname)s): %(message)s"
)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
logger = logging.getLogger("registration-service")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

client_pub_file = "/etc/waggle/pubkey.pem"
client_key_file = "/etc/waggle/key.pem"
client_cert_file = "/etc/waggle/key.pem-cert.pub"
client_id_file = "/etc/waggle/node-id"
config_file = "/etc/waggle/config.ini"


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


def run_registration_command(
    registration_key, cert_user, cert_host, cert_port, command
):
    logger.info(
        f"executing: ssh {cert_user}@{cert_host} -p {cert_port} -i {registration_key} {command}"
    )
    return subprocess.check_output(
        [
            "ssh",
            f"{cert_user}@{cert_host}",
            "-p",
            cert_port,
            "-i",
            registration_key,
            command,
        ]
    ).decode()


def make_request(command, cert_user, cert_host, cert_port, key):
    logger.info(
        "Making request %s to %s.", command, f"{cert_user}@{cert_host}:{cert_port}"
    )

    start_time = time.time()

    while time.time() - start_time < 300:
        try:
            response = run_registration_command(
                key, cert_user, cert_host, cert_port, command
            )
            logger.debug("Response for %s:\n%s.", command, response)
            return response
        except subprocess.CalledProcessError:
            logger.exception(
                "Failed to get credentials from %s. Will retry in 30s...", cert_host
            )
            time.sleep(30)

    raise TimeoutError("Request timed out.")


def request_node_info(node_id, cert_user, cert_host, cert_port, key):
    logger.info("Requesting node info from %s.", cert_host)

    response = make_request(
        "register {}".format(node_id), cert_user, cert_host, cert_port, key
    )

    if "cert file not found" in response:
        raise ValueError("Certificate not found for {}.".format(node_id))

    return json.loads(response)


def get_certificates(node_id, cert_user, cert_host, cert_port, key):
    logger.info("Getting credentials from %s for node-id [%s].", cert_host, node_id)

    node_info = None
    while True:
        try:
            node_info = request_node_info(node_id, cert_user, cert_host, cert_port, key)

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

    # os.remove(key) & the cert ? how do know cert name
    logger.info("Registration complete")
    return node_info


@click.command()
@click.version_option(version=software_version, message=f"version: %(version)s")
def main():

    required_files = [
        client_pub_file,
        client_key_file,
        client_cert_file,
    ]

    if not os.path.exists(client_id_file):
        sys.exit(f"File {client_id_file} missing.")

    node_id = read_file(client_id_file)
    if not node_id:
        sys.exit(f"File {client_id_file} empty.")

    if all(is_file_nonempty(f) for f in required_files):
        logger.info("Node already has all credentials. Skipping registration.")
        sys.exit(0)

    if not os.path.exists(config_file):
        sys.exit(f"File {config_file} not found")

    config = configparser.ConfigParser()
    config.read(config_file)

    if not "registration" in config:
        sys.exit(f'Section "registration" missing config file')

    registration_section = config["registration"]

    if "system" in config:
        system_section = config["system"]

    beekeeper_registration_host = registration_section.get("host")
    beekeeper_registration_port = registration_section.get("port")
    beekeeper_registration_user = registration_section.get("user", "sage_registration")
    beekeeper_registration_privkey = registration_section.get("key")

    if not beekeeper_registration_host:
        sys.exit("variable beekeeper-registration-host is not defined")

    if not beekeeper_registration_port:
        sys.exit("variable beekeeper-registration-port is not defined")

    if not beekeeper_registration_user:
        sys.exit("variable beekeeper-registration-user is not defined")

    if not beekeeper_registration_privkey:
        sys.exit("variable beekeeper_registration_privkey is not defined")

    node_info = get_certificates(
        node_id,
        beekeeper_registration_user,
        beekeeper_registration_host,
        beekeeper_registration_port,
        beekeeper_registration_privkey,
    )


if __name__ == "__main__":
    main()
