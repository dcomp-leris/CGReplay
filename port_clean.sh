#!/bin/bash

# List of UDP ports to check and kill processes
ports=("5000" "5501" "5555" "5508")  # Add more ports as needed

for port in "${ports[@]}"; do
  # Find the process using the current UDP port
  pid=$(sudo lsof -t -i UDP:$port)

  # Check if a process was found for the port
  if [ -z "$pid" ]; then
    echo "No process found using UDP port $port."
  else
    # Kill the process by PID
    sudo kill -9 $pid
    echo "Process $pid using UDP port $port has been killed."
  fi
done

