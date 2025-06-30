#!/bin/bash

"""
This script to kill process by port

Usage:
curl -s https://raw.githubusercontent.com/0xAungkon/Awesome-Server-Scripts/refs/heads/main/utils/port-killer.sh | bash - 8000
       
"""

port_kill() {
    if [ -z "$1" ]; then
        echo "Usage: port_kill PORT_NUMBER"
        return 1
    fi

    PIDs=$(lsof -t -i :"$1" 2>/dev/null)
    if [ -n "$PIDs" ]; then
        kill -9 $PIDs 2>/dev/null
        echo "✓ Successfully killed process(es) running on port $1"
        return 0
    else
        echo "No process running on port $1"
        return 1
    fi
}
alias force-kill='port_kill'
