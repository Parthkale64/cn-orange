from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.recoco import Timer

log = core.getLogger()

class HostDiscovery(object):
    def __init__(self, connection, blocked_pairs=None, idle_timeout=30,
                 hard_timeout=120, poll_stats=True, stats_period=10):
        self.connection = connection
        connection.addListeners(self)
        self.host_db = {} # The Host Database
        self.mac_to_port = {}
        self.blocked_pairs = blocked_pairs or set()
        self.idle_timeout = int(idle_timeout)
        self.hard_timeout = int(hard_timeout)
        self.poll_stats = _to_bool(poll_stats)

        if self.poll_stats:
            self.stats_timer = Timer(float(stats_period), self._request_stats,
                                     recurring=True)

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            return
        if packet.type == packet.LLDP_TYPE:
            return

        src_mac = str(packet.src)
        dst_mac = str(packet.dst)
        src_key = src_mac.lower()
        dst_key = dst_mac.lower()
        dpid = event.connection.dpid
        in_port = event.port

        self.mac_to_port[src_key] = in_port

        # Check for ARP to get IP Address
        ip_addr = "Unknown"
        if packet.type == packet.ARP_TYPE:
            arp_packet = packet.payload
            if arp_packet:
                ip_addr = str(arp_packet.protosrc)

        # Detect Join/Update Event
        if src_mac not in self.host_db or self.host_db[src_mac]['port'] != in_port:
            self.host_db[src_mac] = {'ip': ip_addr, 'dpid': dpid, 'port': in_port}
            
            # Display Host Database
            log.info("\n=== HOST DATABASE UPDATED ===")
            for mac, details in self.host_db.items():
                log.info("MAC: %s | IP: %s | Switch DPID: %s | Port: %s", 
                         mac, details['ip'], details['dpid'], details['port'])
            log.info("=============================\n")

        # Enforce optional MAC-based blocking policy.
        if (src_key, dst_key) in self.blocked_pairs:
            log.info("Blocked packet %s -> %s on dpid=%s", src_mac, dst_mac, dpid)
            drop = of.ofp_flow_mod()
            drop.priority = 100
            drop.idle_timeout = self.idle_timeout
            drop.hard_timeout = self.hard_timeout
            drop.match.dl_src = packet.src
            drop.match.dl_dst = packet.dst
            self.connection.send(drop)
            return

        out_port = self.mac_to_port.get(dst_key)
        if out_port is None:
            out_port = of.OFPP_FLOOD
        else:
            msg = of.ofp_flow_mod()
            msg.priority = 10
            msg.idle_timeout = self.idle_timeout
            msg.hard_timeout = self.hard_timeout
            msg.match = of.ofp_match.from_packet(packet, in_port)
            msg.actions.append(of.ofp_action_output(port=out_port))
            self.connection.send(msg)

        # Send current packet immediately while controller rule takes effect.
        msg = of.ofp_packet_out()
        msg.actions.append(of.ofp_action_output(port=out_port))
        msg.data = event.ofp
        msg.in_port = in_port
        self.connection.send(msg)

    def _request_stats(self):
        self.connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
        self.connection.send(of.ofp_stats_request(body=of.ofp_port_stats_request()))

    def _handle_FlowStatsReceived(self, event):
        log.info("FlowStats dpid=%s entries=%s", event.connection.dpid, len(event.stats))

    def _handle_PortStatsReceived(self, event):
        for stat in event.stats:
            if stat.port_no < of.OFPP_MAX:
                log.info("PortStats dpid=%s port=%s rx_pkts=%s tx_pkts=%s",
                         event.connection.dpid, stat.port_no,
                         stat.rx_packets, stat.tx_packets)

def _parse_blocked_pairs(raw_pairs):
    blocked = set()
    if not raw_pairs:
        return blocked
    for pair in raw_pairs.split(','):
        pair = pair.strip()
        if not pair:
            continue
        if '>' not in pair:
            continue
        src, dst = pair.split('>', 1)
        blocked.add((src.strip().lower(), dst.strip().lower()))
    return blocked


def _to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def launch(blocked_pairs='', idle_timeout=30, hard_timeout=120,
           poll_stats=True, stats_period=10):
    blocked = _parse_blocked_pairs(blocked_pairs)

    def start_switch(event):
        HostDiscovery(event.connection,
                      blocked_pairs=blocked,
                      idle_timeout=idle_timeout,
                      hard_timeout=hard_timeout,
                      poll_stats=poll_stats,
                      stats_period=stats_period)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
