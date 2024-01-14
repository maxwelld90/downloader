from .direct import DirectLink
from .webpage import Webpage
from .github import GitHub
from .sourceforge import SourceForge

ARTEFACT_MAPPINGS = {
    'direct': DirectLink,
    'webpage': Webpage,
    'github': GitHub,
    'sourceforge': SourceForge,
}