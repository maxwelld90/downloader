from .base import ArtefactBase, ArtefactStatus

class DirectLink(ArtefactBase):

    def __init__(self, platform_config: dict, artefact_config: dict):
        super().__init__(platform_config, artefact_config)
    
    @classmethod
    def get_type(cls):
        return 'direct'

    def _setup(self):
        self._download_url = self._artefact_config['src']['url']
        self._version = self._artefact_config['src']['version']

        self._status = ArtefactStatus.READY_TO_DOWNLOAD
    
    def _get_request(self):
        pass