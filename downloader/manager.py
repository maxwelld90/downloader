import os
import sys
import time
import json
import shutil
from .artefacts import ARTEFACT_MAPPINGS

class DownloadManager(object):

    def __init__(self, args):
        self.__config = self.__create_config_object(args)
        self.__state = self.__create_state_object()
        
        self.__is_dry_run = self.__config['args'].dryrun
        self.__artfact_mappings = ARTEFACT_MAPPINGS
    
    def __create_config_object(self, args):
        try:
            with open(args.config_path, 'r') as f:
                config_object = json.load(f)
                config_object['args'] = args

                config_object['temp_directories'] = {}

                for platform in config_object['platforms']:
                    config_object['platforms'][platform]['temporary_directory'] = os.path.join(config_object['platforms'][platform]['directory'], 'temp')
                
                return config_object

        except FileNotFoundError:
            print("The specified file could not be found")
            sys.exit(1)

        except json.decoder.JSONDecodeError:
            print("Bad JSON formatting")
            sys.exit(1)
    
    def __create_state_object(self):
        def create_new_state_object():
            return {
                'last_run': int(time.time()),
                'inventory': {},
                'changes': {}
            }

        try:
            with open(self.__config['stateFile'], 'r') as f:
                state_object = json.load(f)
                state_object['last_run'] = int(time.time())
                state_object['changes'] = {}

                return state_object
        
        except FileNotFoundError:
            return create_new_state_object()
        
        except json.decoder.JSONDecodeError:
            return create_new_state_object()

    def run(self):
        artefacts = []

        for platform in self.__config['platforms']:
            platform_config = self.__config['platforms'][platform]
            platform_config['name'] = platform

            for artefact_config in self.__config['artefacts'][platform]:
                artefact = self.__create_artefact_object(platform_config, artefact_config)

                if any(existing.identifier == artefact.identifier for existing in artefacts):
                    print('You have a duplicate!')
                    sys.exit(1)

                if not artefact.does_url_exist():
                    print("Does not exist/http error")
                    sys.exit(1)
                
                artefacts.append(artefact)
        
        self.__download_artefacts(artefacts)

        # Archive check - extract archive.
        # Move files from temp folders.

        self.__report_changes()
    
    def __create_artefact_object(self, platform_config: dict, artefact_config: dict):
        if artefact_config['src']['from'] not in self.__artfact_mappings.keys():
            print('Unknown artefact type')
            sys.exit(1)
        
        return self.__artfact_mappings[artefact_config['src']['from']](platform_config, artefact_config)
        
    def __download_artefacts(self, artefacts: list):
        if self.__is_dry_run:
            return
        
        for platform in self.__config['platforms']:
            #shutil.rmtree(self.__config['platforms'][platform]['directory'])
            os.makedirs(self.__config['platforms'][platform]['temporary_directory'], exist_ok=True)

        for artefact in artefacts:
            artefact.download()
            artefact.update_state(self.__state)

            if artefact.is_archive():
                artefact.extract_archive()
        
        self.__save_state(artefacts)
    
    def __report_changes(self):
        if len(self.__state['changes'].keys()) == 0:
            print('No changes.')
            return
        
        for item in self.__state['changes'].values():
            print(f"CHANGE: {item['platform']}/{item['name']}/{item['architecture']}")
    
    def __save_state(self, artefacts: list):
        current_artefact_identifiers = set(artefact.identifier for artefact in artefacts)
        self.__state['inventory'] = {key: value for key, value in self.__state['inventory'].items() if key in current_artefact_identifiers}

        with open(self.__config['stateFile'], 'w') as output_file:
            json.dump(self.__state, output_file)