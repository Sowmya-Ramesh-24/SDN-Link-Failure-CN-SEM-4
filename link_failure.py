from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *

log = core.getLogger()


class LinkFailureController(EventMixin):

    def __init__(self):
        self.listenTo(core.openflow)
        self.listenTo(core.openflow_discovery)

        self.mac_to_port = {}
        self.switches = {}
        self.adj = {}
        self.link_states = {}

        log.info("=== Link Failure Controller Started ===")

    # --------------------------------------------------
    # Switch Connected
    # --------------------------------------------------
    def _handle_ConnectionUp(self, event):
        dpid = event.dpid
        self.switches[dpid] = event.connection
        self.mac_to_port.setdefault(dpid, {})
        self.adj.setdefault(dpid, {})

        log.info("[UP] Switch s%s connected", dpid)

        # Table-miss: flood unknown packets
        msg = of.ofp_flow_mod()
        msg.priority = 0
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        event.connection.send(msg)

    # --------------------------------------------------
    # Switch Disconnected
    # --------------------------------------------------
    def _handle_ConnectionDown(self, event):
        dpid = event.dpid
        log.warning("[DOWN] Switch s%s disconnected", dpid)

        if dpid in self.switches:
            del self.switches[dpid]

    # --------------------------------------------------
    # Link Events (Fixed Stable Version)
    # --------------------------------------------------
    def _handle_LinkEvent(self, event):
        link = event.link
        dpid1 = link.dpid1
        dpid2 = link.dpid2
        port1 = link.port1
        port2 = link.port2

        # Ignore bogus self-links
        if dpid1 == dpid2:
            return

        if event.added:
            self.adj.setdefault(dpid1, {})[dpid2] = port1
            self.adj.setdefault(dpid2, {})[dpid1] = port2

            self.link_states[(dpid1, dpid2)] = True
            self.link_states[(dpid2, dpid1)] = True

            log.info("[LINK UP] s%s port%s <-> s%s port%s",
                     dpid1, port1, dpid2, port2)

        elif event.removed:
            # Ignore fake repeated removals
            if (dpid1, dpid2) not in self.link_states:
                return

            if self.link_states[(dpid1, dpid2)] is False:
                return

            self.link_states[(dpid1, dpid2)] = False
            self.link_states[(dpid2, dpid1)] = False

            if dpid2 in self.adj.get(dpid1, {}):
                del self.adj[dpid1][dpid2]

            if dpid1 in self.adj.get(dpid2, {}):
                del self.adj[dpid2][dpid1]

            log.warning("[FAILURE DETECTED] Link DOWN: s%s <-> s%s",
                        dpid1, dpid2)

            log.warning("[RECOVERY] Clearing flows, rerouting via backup path...")
            self._clear_all_flows()

    # --------------------------------------------------
    # Clear Flow Tables
    # --------------------------------------------------
    def _clear_all_flows(self):
        for dpid, conn in self.switches.items():
            # Delete all existing flows
            msg = of.ofp_flow_mod(command=of.OFPFC_DELETE)
            conn.send(msg)

            # Re-add table-miss flood rule
            msg2 = of.ofp_flow_mod()
            msg2.priority = 0
            msg2.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            conn.send(msg2)

        log.info("[REROUTE] Flow tables cleared - paths rebuilding...")

    # --------------------------------------------------
    # Packet Processing
    # --------------------------------------------------
    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            return

        dpid = event.dpid
        in_port = event.port

        # Learn source MAC
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][packet.src] = in_port

        if packet.dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][packet.dst]

            # Install flow rule
            msg = of.ofp_flow_mod()
            msg.match.in_port = in_port
            msg.match.dl_src = packet.src
            msg.match.dl_dst = packet.dst
            msg.priority = 10
            msg.idle_timeout = 30
            msg.hard_timeout = 60
            msg.actions.append(of.ofp_action_output(port=out_port))
            event.connection.send(msg)

            #log.info("[FLOW INSTALLED] s%s: %s -> %s out_port=%s",
                     #dpid, packet.src, packet.dst, out_port)
        else:
            out_port = of.OFPP_FLOOD

        # Forward current packet
        msg = of.ofp_packet_out()
        msg.buffer_id = event.ofp.buffer_id
        msg.in_port = in_port
        msg.actions.append(of.ofp_action_output(port=out_port))

        if event.ofp.buffer_id == of.NO_BUFFER:
            msg.data = event.ofp.data

        event.connection.send(msg)


# --------------------------------------------------
# Launch Controller
# --------------------------------------------------
def launch():
    from pox.openflow.discovery import launch as discovery_launch
    discovery_launch()
    core.registerNew(LinkFailureController)
    log.info("Link Failure Controller Loaded Successfully")
