"""..."""

from pcq.modules.cloc import Cloc
from pcq.modules.radon import RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw
from pcq.modules.ruff import Ruff

MODULES = {
    "cloc": [Cloc],
    "radon": [RadonCc, RadonHal, RadonHalFunction, RadonMi, RadonRaw],
    "ruff": [Ruff],
}
