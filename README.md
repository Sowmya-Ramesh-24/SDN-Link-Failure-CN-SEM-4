# SDN Link Failure Detection using POX and Mininet

This project implements Software Defined Networking (SDN)-based link failure detection and dynamic rerouting using the POX controller and Mininet.

The system detects link failures in real time and automatically reroutes traffic through backup paths using OpenFlow flow rules.

---

## Problem Statement

In traditional networks, rerouting after link failure is slow and decentralized.

This project demonstrates how SDN enables centralized failure detection and dynamic rerouting through a controller-based architecture.

---

## Features

- Real-time link failure detection
- Automatic rerouting through backup path
- OpenFlow-based flow rule installation
- Dynamic flow table clearing and rebuilding
- Centralized SDN control using POX

---

## Technologies Used

- Python 3
- POX SDN Controller
- Mininet
- Open vSwitch
- OpenFlow Protocol
- Ubuntu Linux

---

## Network Topology

Triangle redundant topology:

``` 
        h1
         |
         s1
        /  \
       /    \
      s2----s3
      |      |
      h3     h2
```

Primary Path: h1 sends packet to h2
```
s1 → s2 → s3
```
Backup Path:
```
s1 → s3
```
This redundancy allows rerouting when a link fails.

--- 

### Requirements

To run this project, install:
- Ubuntu Linux VM (Ubuntu 20.04 / 22.04 preferred)
- Python 3
- Mininet
- POX Controller
- Open vSwitch
  
1. Install Mininet
```
sudo apt update
sudo apt install mininet -y
```
2. Install Open vSwitch
```
sudo apt install openvswitch-switch -y
```
3. Clone POX
```
git clone https://github.com/noxrepo/pox.git
```
4. Verify Installation
```
sudo mn --test pingall
cd ~/pox
python3 pox.py --help
```
---
### Project Files
- link_failure.py         → POX controller logic
- link_failure_topo.py    → Mininet topology definition
---

### How to Run
Step 1: Start POX Controller
```
cd ~/pox
python3 pox.py link_failure
```
Step 2: Start Mininet Topology in a seperate terminal
```
cd ~/pox/sdn_project
sudo python3 link_failure_topo.py
```
3.Testing the Project
  - Test Normal Connectivity in mininet terminal
    ```
    pingall
    pingall
    ```
  - Simulate Link Failure
    ```
    link s1 s2 down
    ```
  - Test Recovery After Failure
    ```
    h1 ping -c 10 h2
    ```
---
### Expected result:
After pingall
0% packet loss
Traffic is automatically rerouted through backup path.

Restore Link
link s1 s2 up
---
### Controller Logic Summary

The POX controller performs:
- Detect switch connections
- Learn MAC addresses dynamically
- Install OpenFlow forwarding rules
- Detect link failures using LLDP discovery events
- Remove stale flow entries
- Rebuild routing paths dynamically
