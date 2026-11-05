"""Evidence-JSON-only sizing check. Does not create a production packet."""
import json
from pathlib import Path

GROUPS = ('repository_code', 'boundary_script', 'assets_and_runtime_targets',
          'store', 'cache', 'venv_configuration', 'venv_installed_environment',
          'base_runtime_root', 'base_runtime_dlls', 'base_standard_library')


def measure(rows):
    unique = {row['path']: row for row in rows}
    files = {'constituent_'+str(i).zfill(5):
             {key:row[key] for key in ('path','sha256','size_bytes')}
             for i,row in enumerate(unique.values())}
    pins = {key:row['sha256'] for key,row in files.items()}
    def size(value):
        return len(json.dumps(value, separators=(',',':')).encode('utf-8'))
    return {'scope':'STRUCTURAL_SIZE_ESTIMATE_ONLY_NOT_EXECUTABLE_PACKET',
            'unique_files':len(files),
            'partial_packet_bytes':size({'declared_files':files,'config':{'pins':list(pins.items())},
                                         'reviewed_context':{'reviewed_pins':pins}}),
            'packet_limit_bytes':8388608,
            'request_pins_only_bytes':size({'protected_pins':pins}),
            'child_request_limit_bytes':1048576,'child_context_limit_bytes':2097152}


if __name__ == '__main__':
    root = Path(r'F:\TERRA -Copy\reports\task3_candidate_packet_20261022_01\inventory')
    rows = [row for name in GROUPS for row in json.loads((root/(name+'.json')).read_bytes())]
    print(json.dumps(measure(rows), indent=2))
