import subprocess
import re
import csv

def get_node_info(node_name):
    try:
        # Execute the scontrol command to get node details
        result = subprocess.run(['scontrol', 'show', 'node', node_name],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Check if the command was successful
        if result.returncode != 0:
            print(f"Error retrieving information for node {node_name}: {result.stderr}")
            return None

        # Initialize a dictionary to store node information
        node_info = {'Node': node_name}

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

        # Extract real memory in MB
        match = re.search(r'RealMemory=(\d+)', result.stdout)
        if match:
            node_info['Real Memory (MB)'] = int(match.group(1))

        # Extract allocated memory in MB
        match = re.search(r'AllocMem=(\d+)', result.stdout)
        if match:
            node_info['Allocated Memory (MB)'] = int(match.group(1))
            # Calculate available memory
            node_info['Available Memory (MB)'] = node_info['Real Memory (MB)'] - node_info['Allocated Memory (MB)']

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

def main():
    # List of node ranges in the free-gpu partition
    node_ranges = [
        'hpc3-gpu-16-[00-07]',
        'hpc3-gpu-17-[02-04]',
        'hpc3-gpu-18-[00-04]',
        'hpc3-gpu-24-[05-08]',
        'hpc3-gpu-k54-[00-05]',
        'hpc3-gpu-l54-[00-09]',
    ]
    # List to store node information
    node_info_list = []
    for node_range in node_ranges:
        nodes = expand_node_range(node_range)
        for node in nodes:
            node_info = get_node_info(node)
            if node_info:
                node_info_list.append(node_info)
        # Print completion message for the current node group
        print(f"{node_range.split('[')[0]} done")
    # Save the node information to a CSV file
    csv_file = 'node_info.csv'
    try:
        with open(csv_file, mode='w', newline='') as file:
            fieldnames = ['Node', 'Total CPUs', 'Allocated CPUs', 'Available CPUs',
                          'Real Memory (MB)', 'Allocated Memory (MB)', 'Available Memory (MB)',
                          'GPU Model', 'Total GPUs', 'Allocated GPUs', 'Available GPUs']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for info in node_info_list:
                writer.writerow(info)
        print(f"Node information saved to {csv_file}")
    except Exception as e:
        print(f"An error occurred while writing to CSV: {e}")

if __name__ == "__main__":
    main()