import re
import logging
from flowmanager.switch import Switch
from flowmanager.ssh import NoviflowSSH


class Noviflow(Switch):

    """

    Inherits from Switch and Implements Noviflow specific methods 

    """

    def __init__(self, props, expected=False):
        Switch.__init__(self, props, expected)
        self.type = 'noviflow'
        self.ssh = NoviflowSSH(ip=self.ip, user=self.user,
                               port=self.port, password=self.password)

    def reboot(self):
        if self.ssh.execute_command('set status switch reboot', prompt="[all/noentries/nopipeline/none]"):
            if self.ssh.execute_command('noentries', prompt="(y/n)"):
                self.ssh.execute_command('y', prompt=None, eof=True)
                return True

    def break_gateway(self, seconds=0):
        raise Exception(
            'break method is not implemented by this switch {}'.format(self.name))
        # switch = self.switches.get(name)
        # if not switch:
        #     print "ERROR: {} switch does not exists".format(name)
        #     return False
        # seconds = int(seconds)
        # seconds = 0 if not seconds or seconds <=0 else seconds
        # print "INFO: trying to break connectivity to the switch {} switch".format(name)
        # if 'disable_gw' not in switch or len(switch['disable_gw']) <=0 or 'enable_gw' not in switch or len(switch['enable_gw']) <=0:
        #     print "ERROR: enable or disable gw commands not found in switch {} switch".format(name)
        #     return False
        # if switch['type'] == 'noviflow':
        #     if not _execute_commands_in_switch_noviflow(switch['ip'], switch['port'],switch['user'],switch['password'],switch['disable_gw']):
        #         return False
        #     time.sleep(seconds)
        #     return _execute_commands_in_switch_noviflow(switch['ip'], switch['port'],switch['user'],switch['password'],switch['enable_gw'])
        # else:
        #     if not _execute_commands_locally(switch['disable_gw']):
        #         return False
        #     time.sleep(seconds)
        #     return _execute_commands_locally(switch['enable_gw'])

    def break_controller_switch(self, controller_name, seconds=30):
        raise Exception(
            'break method is not implemented by this switch {}'.format(self.name))
        # switch = self
        # if not switch:
        #     print "ERROR: {} switch does not exists".format(sw_name)
        #     return False
        # seconds = int(seconds)
        # seconds = 0 if not seconds or seconds <=0 else seconds
        # print "INFO: trying to break controller {} connection in the switch {} switch".format(controller_name, sw_name)
        # all_ctrl_config = switch.get('controller_config')
        # ctrl_config = all_ctrl_config.get(controller_name) if all_ctrl_config else None
        # if not ctrl_config or 'remove_controller' not in ctrl_config or len(ctrl_config['remove_controller']) <= 0:
        #     print "ERROR: remove controller commands not found in switch {} for controller {}".format(sw_name, controller_name)
        #     return False

    def delete_groups(self):
        if self.ssh.execute_command('del config group groupid all'):
            self.ssh.close()
            return True

    def delete_flows(self):
        if self.ssh.execute_command('del config flow tableid all'):
            self.ssh.close()
            return True

    def get_flows(self):
        logging.debug("NOVIFLOW: %s(%s) getting flows",
                      self.name, self.openflow_name)

        text_flows = self.ssh.execute_command('show status flow tableid all')
        if not text_flows:
            return None

        tableid = re.compile(r'\[TABLE\s+(\d+)\]', re.IGNORECASE)
        flowid = re.compile(r'\[FLOW_ID\s*(\d+)\]', re.IGNORECASE)
        cookies = re.compile(r'Cookie\s*=\s*(\S+)', re.IGNORECASE)
        packetCounts = re.compile(r'Packet_count\s*=\s*(\d+)', re.IGNORECASE)
        byteCounts = re.compile(r'Byte_count\s*=\s*(\d+)', re.IGNORECASE)

        flows = []
        current_flow = None
        current_table = None
        for line in text_flows.splitlines():
            logging.debug("NOVIFLOW: %s(%s) processing line %s",
                          self.name, self.openflow_name, line)
            match = tableid.findall(line)
            if match:
                logging.debug("NOVIFLOW: %s(%s) updating table %s",
                              self.name, self.openflow_name, match[0])
                current_table = match[0]
                current_flow = None
                continue

            match = flowid.findall(line)
            if match:
                logging.debug("NOVIFLOW: %s(%s) creating flow %s",
                              self.name, self.openflow_name, match[0])
                current_flow = {'id': match[0], 'table': current_table}
                flows.append(current_flow)
                continue

            if current_flow is None:
                continue

            match = cookies.findall(line)
            if match:
                current_flow['cookie'] = int('0x{}'.format(match[0]), 16)
                continue

            match = packetCounts.findall(line)
            if match:
                current_flow['packets'] = match[0]
                continue

            match = byteCounts.findall(line)
            if match:
                current_flow['bytes'] = match[0]
                continue

        self.ssh.close()
        # logging.info(flows)
        return flows

    def get_groups(self):
        text_groups = self.ssh.execute_command('show stats group groupid all')
        if not text_groups:
            return None

        groupIdRegex = re.compile(r'Group id:\s*(\d+)', re.IGNORECASE)
        packetCountRegex = re.compile(
            r'Reference count:\s*\d+\s*\S\s+Packet count:\s*(\d+)', re.IGNORECASE)
        byteCountRegex = re.compile(r'Byte count:\s*(\d+)', re.IGNORECASE)

        groups = []
        current_group = None
        for line in text_groups.splitlines():
            match = groupIdRegex.findall(line)
            if match:
                current_group = {'id': match[0]}
                groups.append(current_group)
                continue
            elif current_group is None:
                continue

            match = packetCountRegex.findall(line)
            if match:
                current_group['packets'] = match[0]
                if 'bytes' in current_group:
                    current_group = None
                continue

            match = byteCountRegex.findall(line)
            if match:
                current_group['bytes'] = match[0]
                if 'packets' in current_group:
                    current_group = None
                continue

        self.ssh.close()
        return groups

    def get_controllers_role(self):
        ssh = self.ssh
        if not ssh.create_session():
            return None
        text_groups = self.ssh.execute_command('show status ofchannel')
        if not text_groups:
            return None

        roles = None
        rolesLinesRegex = re.compile(
            r'(Group\s+\S+\s+Role\s+-\s+\S+)', re.IGNORECASE)
        rolesLines = rolesLinesRegex.findall(text_groups)

        if (rolesLines is not None and len(rolesLines) > 0):
            rolesRegex = re.compile(
                r'Group\s+\S+\s+Role\s+-\s+(\S+)', re.IGNORECASE)
            roles = []
            for line in sorted(rolesLines):
                roleList = rolesRegex.findall(line)
                if roleList and len(roleList):
                    roles.append(roleList[0])
        return roles

    def shutdown_port(self, port):
        raise Exception(
            'shutdown port method is not implemented by this switch {}'.format(self.name))

    def start_port(self, port):
        raise Exception(
            'start port method is not implemented by this switch {}'.format(self.name))

    def restart_port(self, port, seconds=0):
        raise Exception(
            'restart port method is not implemented by this switch {}'.format(self.name))

    def get_flow_stats(self, filters=None):
        raise Exception(
            'get_flow_stats method is not implemented by this switch {}'.format(self.name))

    def get_group_stats(self, filters=None):
        raise Exception(
            'get_group_stats method is not implemented by this switch {}'.format(self.name))
