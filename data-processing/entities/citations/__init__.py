from common.commands.compile_tex import make_compile_tex_command
from common.commands.diff_images import make_diff_images_command
from common.commands.locate_hues import make_locate_hues_command
from common.commands.raster_pages import make_raster_pages_command

from .commands.colorize_citations import ColorizeCitations
from .commands.extract_bibitems import ExtractBibitems
from .commands.locate_citations import LocateCitations
from .commands.resolve_bibitems import ResolveBibitems
from .commands.upload_citations import UploadCitations

commands = [
    ExtractBibitems,
    ResolveBibitems,
    ColorizeCitations,
    make_compile_tex_command("citations", "citations"),
    make_raster_pages_command("citations", "citations"),
    make_diff_images_command("citations", "citations"),
    make_locate_hues_command("citations", "citations"),
    LocateCitations,
    UploadCitations,
]