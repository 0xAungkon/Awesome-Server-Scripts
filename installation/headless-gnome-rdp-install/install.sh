#!/bin/bash
"""
This script to install headless rdp gui out of multipass

Usage:
curl -s https://raw.githubusercontent.com/0xAungkon/Awesome-Server-Scripts/refs/heads/main/installation/headless-gnome-rdp-install/install.sh | bash
       
"""

sudo apt update
sudo apt install ubuntu-desktop xrdp
sudo passwd ubuntu
