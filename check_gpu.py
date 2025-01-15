import subprocess
import re
import csv

def get_gpu_info(node_name):
    try:
        # Execute the scontrol command to get node details
        result = subprocess.run(['scontrol', 'show', 'node', node_name],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Check if the command was successful
        if result.returncode != 0:
            print(f"Error retrieving information for node {node_name}: {result.stderr}")
            return None
        # Search for the Gres field in the output
        match = re.search(r'Gres=gpu:(\w+):\d+', result.stdout)
        if match:
            gpu_type = match.group(1)
            return gpu_type
        else:
            print(f"No GPU information found for node {node_name}.")
            return None
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
    # List to store GPU information per node
    node_gpu_info = []
    for node_range in node_ranges:
        nodes = expand_node_range(node_range)
        for node in nodes:
            gpu_type = get_gpu_info(node)
            if gpu_type:
                node_gpu_info.append({'Node': node, 'GPU': gpu_type})
        # Print completion message for the current node group
        print(f"{node_range.split('[')[0]} done")
    # Save the GPU information to a CSV file
    csv_file = 'node_gpu_info.csv'
    try:
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['Node', 'GPU'])
            writer.writeheader()
            for info in node_gpu_info:
                writer.writerow(info)
        print(f"GPU information saved to {csv_file}")
    except Exception as e:
        print(f"An error occurred while writing to CSV: {e}")

if __name__ == "__main__":
    main()