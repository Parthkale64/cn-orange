# Host Discovery Service (POX + Mininet)
Automatically detect and maintain a list of hosts in the SDN network.

## Project Expectation:
- Detect host join events
- Maintain host database; Display host details        
- Update dynamically

## 1. Problem Statement and Objective

The objective is to build and validate a POX-based SDN controller over a Mininet topology that demonstrates:
- Host discovery and controller visibility.
- L2 learning-switch forwarding behavior.
- Policy-based blocking/filtering.
- Monitoring and logging through controller and switch statistics.
- Basic performance observation using ping and iperf.

## 2. Topology and Design Choice

- Topology file: `topology.py`
- Controller module: `pox/ext/host_discovery.py`
- Mininet design: one OpenFlow switch (`s1`) connected to three hosts (`h1`, `h2`, `h3`).

Why this design:
- Simple enough for clear packet flow analysis.
- Sufficient to demonstrate forwarding, blocking policy, and performance changes.
- Easy to validate flow table updates on a single switch.

## 3. Setup and Run

Prerequisites:
- Mininet installed.
- Open vSwitch installed.
- Python 3 available.

Terminal 1: Start POX controller from project root.

```bash
cd pox
./pox.py log.level --DEBUG openflow.of_01 host_discovery \
  '--blocked_pairs=00:00:00:00:00:01>00:00:00:00:00:03' \
  --idle_timeout=30 --hard_timeout=120 --poll_stats=True --stats_period=10
```

Terminal 2: Start topology.

```bash
sudo python3 topology.py
```

## 4. Functional Demo Commands (Mininet CLI)

### A. Forwarding (Learning Switch)

```bash
pingall
```

Expected:
- First packets trigger `packet_in`.
- Controller learns MAC-to-port mapping.
- Subsequent traffic is forwarded with installed flow rules.

### B. Blocking and Filtering

Blocking policy used above:
- `h1 -> h3` is blocked (`00:...:01 > 00:...:03`).

Validation:

```bash
h1 ping -c 3 h3
h1 ping -c 3 h2
```

Expected:
- `h1 -> h3` fails or is dropped.
- `h1 -> h2` succeeds.

### C. Monitoring and Logging

Controller logs should show:
- Host database updates.
- Blocked flow messages.
- FlowStats and PortStats at configured interval.

### D. Routing or QoS Behavior

This project focuses on L2 forwarding + ACL-style filtering + monitoring.
If required by your instructor, QoS can be added with OVS queue configuration as an extension.

## 5. Performance Observation and Analysis

## Latency (ping)

```bash
h1 ping -c 10 h2
h1 ping -c 10 h3
```

Record:
- min/avg/max RTT before and after policy application.

## Throughput (iperf)

Run iperf server on one host:

```bash
h2 iperf -s &
```

Run client from another host:

```bash
h1 iperf -c h2 -t 10
```

Optional UDP test:

```bash
h1 iperf -u -c h2 -b 10M -t 10
```

Record:
- TCP throughput (Mbits/sec).
- UDP throughput/loss if applicable.

## Flow Table Changes

From host OS terminal:

```bash
sudo ovs-ofctl dump-flows s1
```

Record:
- Learned match fields.
- Rule priorities and timeout values.

## Packet and Port Statistics

```bash
sudo ovs-ofctl dump-ports s1
```

Record:
- RX/TX packets and bytes per port.
- Compare with controller-side PortStats logs.

## 6. Validation and Regression Checks

Suggested checks:
1. Baseline forwarding works (`pingall`).
2. Block rule blocks only targeted source-destination MAC pair.
3. Non-targeted traffic remains unaffected.
4. Flow entries appear and expire according to configured timeout.
5. Throughput and latency values are captured and explained.
