#!/usr/bin/env python3
import json
import sys

def update_config(measurements):
    # Load current config
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Update energy and cycles
    for op, data in measurements.items():
        if op in config['energy']:
            if data['energy_J'] is not None:
                config['energy'][op] = data['energy_J']
        if op in config.get('cycles', {}):
            if data['cycles'] is not None:
                config['cycles'][op] = data['cycles']

    # Save back
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

    # Also update src/crz/config.py defaults
    with open('src/crz/config.py', 'r') as f:
        lines = f.readlines()

    # Find energy dict
    in_energy = False
    in_cycles = False
    new_lines = []
    for line in lines:
        if '"energy": {' in line:
            in_energy = True
        elif in_energy and '},' in line and '"thermal"' in line:
            in_energy = False
        elif in_energy:
            for op, data in measurements.items():
                if f'"{op}":' in line and data['energy_J'] is not None:
                    line = f'                "{op}": {data["energy_J"]},  # Updated\n'
                    break
        elif '"cycles": {' in line:
            in_cycles = True
        elif in_cycles and '},' in line and '"cores"' in line:
            in_cycles = False
        elif in_cycles:
            for op, data in measurements.items():
                if f'"{op}":' in line and data['cycles'] is not None:
                    line = f'                "{op}": {data["cycles"]},\n'
                    break
        new_lines.append(line)

    with open('src/crz/config.py', 'w') as f:
        f.writelines(new_lines)

    print("Config updated with measurements.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("usage: apply_measurements.py <measurements.json>")
        sys.exit(1)
    with open(sys.argv[1], 'r') as f:
        measurements = json.load(f)
    update_config(measurements)
