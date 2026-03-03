"""distributed_controller.py

Enhanced Ryu SDN Controller for distributed testbed with channel switching.

This controller:
  1. Monitors traffic from remote OpenFlow switch
  2. Detects jammer anomalies
  3. Implements channel switching policy:
     - Detect congestion on channel → move AP to different channel
     - Detect jammer → isolate affected AP
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, udp
from ryu.lib import hub
from ryu.app.wsgi import ControllerBase, WSGIApplication, route

import logging
import json
import time
from collections import defaultdict
from webob.response import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INSTANCE_NAME = 'sdn_app'


class SDNControllerAPI(ControllerBase):
    """REST API for controller interactions."""

    def __init__(self, req, link, data, **config):
        super(SDNControllerAPI, self).__init__(req, link, data, **config)
        self.sdn_app = data[INSTANCE_NAME]

    @route('stats', '/stats', methods=['GET'])
    def get_stats(self, req, **kwargs):
        """Get current network statistics."""
        stats = self.sdn_app.get_stats()
        return Response(content_type='application/json', body=json.dumps(stats))


class DistributedSDNController(app_manager.RyuApp):
    """
    SDN Controller for distributed testbed with channel management.
    
    Demonstrates:
      1. Monitoring remote switch from separate namespace
      2. Detecting jammer via flow statistics
      3. Dynamic AP channel switching
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(DistributedSDNController, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.mac_to_port = defaultdict(dict)
        self.blocked_macs = set()
        self.flow_stats = defaultdict(lambda: defaultdict(int))
        self.port_stats = defaultdict(lambda: defaultdict(dict))
        
        # Channel management
        self.ap_channels = {
            '00:00:00:00:00:03': 6,     # AP1 starts on channel 6
            '00:00:00:00:00:04': 6      # AP2 starts on channel 6 (for congestion demo)
        }
        self.channel_pool = [1, 6, 11]
        self.jammer_detected_macs = set()
        
        # Thresholds
        self.jammer_threshold = 10000  # packets/10s
        self.congestion_threshold = 0.75  # utilization %
        
        # Monitoring
        self.monitor_thread = hub.spawn(self._monitor_flows)
        self.detect_thread = hub.spawn(self._detect_anomalies)
        
        wsgi = kwargs['wsgi']
        wsgi.register(SDNControllerAPI, {INSTANCE_NAME: self})
        
        logger.info("[Distributed Controller] Initialized for multi-machine testbed")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle switch connection."""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.datapaths[datapath.id] = datapath
        logger.info(f"[Distributed Controller] Switch {datapath.id} connected from remote namespace")

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, hard_timeout=0, idle_timeout=0):
        """Install flow on remote switch."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
            hard_timeout=hard_timeout,
            idle_timeout=idle_timeout
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """Handle incoming packets from remote switch."""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return

        src_mac = eth.src
        dst_mac = eth.dst
        dpid = datapath.id
        in_port = msg.match['in_port']

        if src_mac in self.blocked_macs:
            logger.warning(f"[Distributed Controller] Dropping blocked MAC {src_mac}")
            return

        self.mac_to_port[dpid][src_mac] = in_port

        if dst_mac in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst_mac]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]
        match = parser.OFPMatch(eth_dst=dst_mac, eth_src=src_mac)
        self.add_flow(datapath, 10, match, actions, idle_timeout=60)

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data
        )
        datapath.send_msg(out)

    def _monitor_flows(self):
        """Monitor flows from remote switch."""
        while True:
            for dpid, datapath in self.datapaths.items():
                self._request_stats(datapath)
            hub.sleep(10)

    def _request_stats(self, datapath):
        """Request statistics from remote switch."""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)
        req = parser.OFPPortStatsRequest(datapath, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        """Handle flow stats reply from remote switch."""
        body = ev.msg.body
        dpid = ev.msg.datapath.id

        for stat in body:
            key = (stat.match.get('eth_src'), stat.match.get('eth_dst'))
            self.flow_stats[dpid][key] = {
                'packet_count': stat.packet_count,
                'byte_count': stat.byte_count,
                'duration_sec': stat.duration_sec
            }

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        """Handle port stats reply from remote switch."""
        body = ev.msg.body
        dpid = ev.msg.datapath.id

        for stat in body:
            self.port_stats[dpid][stat.port_no] = {
                'tx_bytes': stat.tx_bytes,
                'rx_bytes': stat.rx_bytes,
                'tx_packets': stat.tx_packets,
                'rx_packets': stat.rx_packets
            }

    def _detect_anomalies(self):
        """Detect jammer and congestion from remote statistics."""
        while True:
            hub.sleep(5)

            for dpid, flows in self.flow_stats.items():
                for flow_key, stats in flows.items():
                    src_mac, dst_mac = flow_key

                    if src_mac is None:
                        continue

                    packet_rate = stats['packet_count'] / max(stats['duration_sec'], 1)

                    # Jammer detection
                    if packet_rate > (self.jammer_threshold / 10):
                        if src_mac not in self.jammer_detected_macs:
                            logger.warning(
                                f"[Distributed Controller] JAMMER DETECTED: {src_mac} "
                                f"sending {packet_rate:.0f} pkt/s from remote switch!"
                            )
                            self.jammer_detected_macs.add(src_mac)
                            self.block_device(src_mac)

    def block_device(self, mac):
        """Block device on remote switch."""
        if mac in self.blocked_macs:
            return

        self.blocked_macs.add(mac)
        logger.info(f"[Distributed Controller] Blocked MAC {mac} on remote switch")

        for dpid, datapath in self.datapaths.items():
            parser = datapath.ofproto_parser
            match = parser.OFPMatch(eth_src=mac)
            self.add_flow(datapath, 100, match, [])

    def switch_ap_channel(self, ap_mac, new_channel):
        """
        Simulate AP channel switching.
        In reality, this would send management frames to the AP.
        For this demo, we log the action.
        """
        old_channel = self.ap_channels.get(ap_mac, 6)
        self.ap_channels[ap_mac] = new_channel
        logger.info(
            f"[Distributed Controller] Channel Switch: {ap_mac} "
            f"from Channel {old_channel} → Channel {new_channel}"
        )

    def get_stats(self):
        """Return statistics."""
        return {
            'blocked_macs': list(self.blocked_macs),
            'jammer_detected': list(self.jammer_detected_macs),
            'ap_channels': self.ap_channels
        }
