import subprocess
import json
import re


class Batman(object):
    """
    Bindings for B.A.T.M.A.N. advanced (v15 compat) batctl tool
    """

    def __init__(self, mesh_interface="bat0"):
        self.mesh_interface = mesh_interface

    def batadv_vis(self):
        """
        Parse "batadv-vis -i <mesh_interface> -f json"
        into an array of dictionaries.
        """
        output = subprocess.check_output(
            ["batadv-vis", "-i", self.mesh_interface, "-f", "json"])
        lines = output.decode('utf-8').splitlines()
        return [json.loads(line) for line in lines]

    def gateways(self):
        """
        Parse "batctl -m <mesh_interface> gwl -n"
        into an array of dictionaries.
        """
        output = subprocess.check_output(
            ["batctl", "-m", self.mesh_interface, "gwl", "-n"])
        lines = output.decode("utf-8").splitlines()

        # pattern to find mac addresses with colon delimiter
        mac_addr = re.compile(r'(([a-z0-9]{2}:){5}[a-z0-9]{2})')

        gateway_list = []

        # check if the local server is a gateway
        if self.gw_mode() == 'server':
            local_mac_addr = mac_addr.search(lines[0]).group(0)
            gateway_list.append(local_mac_addr)

        # find non-local gateways
        for line in lines:
            match = mac_addr.search(line)
            if match:
                gateway_list.append(match.group(0))

        return gateway_list

    def gw_mode(self):
        """
        Parse "batctl -m <mesh_interface> gw_mode"
        """
        output = subprocess.check_output(
            ["batctl", "-m", self.mesh_interface, "gw"])
        elements = output.decode("utf-8").split()
        return elements[0]
