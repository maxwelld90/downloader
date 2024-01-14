import re
import requests
from .base import ArtefactBase, ArtefactStatus

class GitHub(ArtefactBase):

    def __init__(self, platform_config: dict, artefact_config: dict):
        super().__init__(platform_config, artefact_config)
    
    @classmethod
    def get_type(cls):
        return 'github'

    def _setup(self):
        if 'tag' not in self._artefact_config['src'].keys() or self._artefact_config['src']['tag'] == '' or self._artefact_config['src']['tag'].lower() == 'latest':
            self.__api_url = f"https://api.github.com/repos/{self._artefact_config['src']['owner']}/{self._artefact_config['src']['repository']}/releases/latest"
        else:
            self.__api_url = f"https://api.github.com/repos/{self._artefact_config['src']['owner']}/{self._artefact_config['src']['repository']}/releases/tags/{self._artefact_config['src']['tag']}"
    
    def _get_request(self):
        response = requests.get(self.__api_url)
        data = response.json()
        urls = []
        pattern = re.compile(self._artefact_config['src']['regex'])

        for asset in data['assets']:
            urls.append(asset['browser_download_url'])
        
        for url in urls:
            match = re.search(pattern, url)

            if match:
                self._download_url = url
                self._version = match.group(1)  # url.split('/')[-2]
                break
        
        if self._download_url is None or self._version is None:
            raise ValueError("Couldn't find a URL or version.")
        
        self._status = ArtefactStatus.READY_TO_DOWNLOAD