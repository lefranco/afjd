#!/bin/bash

# sudo apt install xdotool

# Time (in seconds) between simulated movements.
# Use a value less than your screen-lock/suspend idle time (e.g., 60 seconds).
INTERVAL=30

echo "Starting 'stay awake' script. Press Ctrl+C to stop."

while true; do
    # 1. Move mouse 1 pixel right
    xdotool mousemove_relative 1 0

    # 2. Move mouse 1 pixel left (to return it to the original position)
    xdotool mousemove_relative -- -1 0

    # 3. Wait for the set interval
    sleep $INTERVAL
done
