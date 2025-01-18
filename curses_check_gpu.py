import subprocess
import re
import csv
import curses
import time

def get_node_info(node_name):
    try:
        # Execute the scontrol command to get node details
        result = subprocess.run(['scontrol', 'show', 'node', node_name],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Check if the command was successful
        if result.returncode != 0:
            print(f"Error retrieving information for node {node_name}: {result.stderr}")
            return None

        # Initialize a dictionary to store node information with default values
        node_info = {
            'Node': node_name,
            'Total CPUs': 0,
            'Allocated CPUs': 0,
            'Available CPUs': 0,
            'Real Memory (GB)': 0.0,
            'Allocated Memory (GB)': 0.0,
            'Available Memory (GB)': 0.0,
            'GPU Model': 'None',
            'Total GPUs': 0,
            'Allocated GPUs': 0,
            'Available GPUs': 0
        }

        # Extract total CPUs
        match = re.search(r'CPUTot=(\d+)', result.stdout)
        if match:
            node_info['Total CPUs'] = int(match.group(1))

        # Extract allocated CPUs
        match = re.search(r'CPUAlloc=(\d+)', result.stdout)
        if match:
            node_info['Allocated CPUs'] = int(match.group(1))
        # Calculate available CPUs
        node_info['Available CPUs'] = node_info['Total CPUs'] - node_info['Allocated CPUs']

        # Extract real memory in MB and convert to GB
        match = re.search(r'RealMemory=(\d+)', result.stdout)
        if match:
            real_memory_mb = int(match.group(1))
            node_info['Real Memory (GB)'] = real_memory_mb / 1024

        # Extract allocated memory in MB and convert to GB
        match = re.search(r'AllocMem=(\d+)', result.stdout)
        if match:
            alloc_memory_mb = int(match.group(1))
            node_info['Allocated Memory (GB)'] = alloc_memory_mb / 1024
        # Calculate available memory in GB
        node_info['Available Memory (GB)'] = node_info['Real Memory (GB)'] - node_info['Allocated Memory (GB)']

        # Extract GPU information
        match = re.search(r'Gres=gpu:(\w+):(\d+)', result.stdout)
        if match:
            node_info['GPU Model'] = match.group(1)
            node_info['Total GPUs'] = int(match.group(2))

        # Extract allocated GPUs
        match = re.search(r'AllocTRES=.*gres/gpu=(\d+)', result.stdout)
        if match:
            node_info['Allocated GPUs'] = int(match.group(1))
        # Calculate available GPUs
        node_info['Available GPUs'] = node_info['Total GPUs'] - node_info['Allocated GPUs']

        return node_info

    except Exception as e:
        print(f"An error occurred while processing node {node_name}: {e}")
        return None

def expand_node_range(node_range):
    # Example input: 'hpc3-gpu-16-[00,02-07]'
    prefix = node_range.split('[')[0]
    range_part = node_range.split('[')[1].strip(']')
    nodes = []
    for part in range_part.split(','):
        if '-' in part:
            start, end = part.split('-')
            for i in range(int(start), int(end) + 1):
                nodes.append(f"{prefix}{i:02}")
        else:
            nodes.append(f"{prefix}{int(part):02}")
    return nodes

def display_results_curses(node_ranges):
    def draw_menu(stdscr):
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(True)  # Make getch() non-blocking
        while True:
            # Refresh node info list
            node_info_list = []
            for node_range in node_ranges:
                nodes = expand_node_range(node_range)
                for node in nodes:
                    node_info = get_node_info(node)
                    if node_info:
                        node_info_list.append(node_info)

            # Sort by GPU Model
            node_info_list.sort(key=lambda x: x['GPU Model'])

            # Get terminal dimensions
            max_y, max_x = stdscr.getmaxyx()
            stdscr.clear()
            stdscr.addstr(0, 0, "Node Resource Availability (Live View - Sorted by GPU Model) - Press 'q' to quit")
            stdscr.addstr(1, 0, "Warning: Extend the terminal window size to view all information properly.")
            stdscr.addstr(2, 0, "-" * (max_x - 1))
            stdscr.addstr(3, 0, f"{'Node':<20} | {'Available CPUs':<15} | {'Available Memory (GB)':<20} | {'Available GPUs':<15} | {'GPU Model':<15}")
            stdscr.addstr(4, 0, "-" * (max_x - 1))  # Line separating the headers from data

            for idx, node_info in enumerate(node_info_list, start=5):  # Start at line 5
                if idx >= max_y - 1:  # Ensure we don’t write outside terminal height
                    break
                line = f"{node_info['Node']:<20} | {node_info['Available CPUs']:<15} | {node_info['Available Memory (GB)']:<20.2f} | {node_info['Available GPUs']:<15} | {node_info['GPU Model']:<15}"
                stdscr.addstr(idx, 0, line[:max_x - 1])

            stdscr.refresh()
            key = stdscr.getch()

            if key == ord('q'):  # Quit on 'q'
                break
            
            time.sleep(60)  # Refresh every 60 seconds

    curses.wrapper(draw_menu)

def main():
    node_ranges = [
        'hpc3-gpu-16-[00-07]',
        'hpc3-gpu-17-[02-04]',
        'hpc3-gpu-18-[00-04]',
        'hpc3-gpu-24-[05-08]',
        'hpc3-gpu-k54-[00-05]',
        'hpc3-gpu-l54-[00-09]',
    ]

    # Save the full information to a CSV file
    csv_file = 'node_info.csv'
    node_info_list = []
    for node_range in node_ranges:
        nodes = expand_node_range(node_range)
        for node in nodes:
            node_info = get_node_info(node)
            if node_info:
                node_info_list.append(node_info)
    try:
        with open(csv_file, mode='w', newline='') as file:
            fieldnames = ['Node', 'Total CPUs', 'Allocated CPUs', 'Available CPUs',
                          'Real Memory (GB)', 'Allocated Memory (GB)', 'Available Memory (GB)',
                          'GPU Model', 'Total GPUs', 'Allocated GPUs', 'Available GPUs']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for info in node_info_list:
                writer.writerow(info)
        print(f"Node information saved to {csv_file}")
    except Exception as e:
        print(f"An error occurred while writing to CSV: {e}")

    # Display live results in terminal
    display_results_curses(node_ranges)

if __name__ == "__main__":
    main()