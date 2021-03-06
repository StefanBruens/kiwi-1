# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
# project
from .archive import ArchiveBuilder
from .filesystem import FileSystemBuilder
from .container import ContainerBuilder
from .disk import DiskBuilder
from .live import LiveImageBuilder
from .pxe import PxeBuilder
from ..defaults import Defaults

from ..exceptions import (
    KiwiRequestedTypeError
)


class ImageBuilder(object):
    """
        image builder factory
    """
    def __new__(self, xml_state, target_dir, root_dir):
        requested_image_type = xml_state.get_build_type_name()
        if requested_image_type in Defaults.get_filesystem_image_types():
            return FileSystemBuilder(
                xml_state, target_dir, root_dir
            )
        elif requested_image_type in Defaults.get_disk_image_types():
            return DiskBuilder(
                xml_state, target_dir, root_dir
            )
        elif requested_image_type in Defaults.get_live_image_types():
            return LiveImageBuilder(
                xml_state, target_dir, root_dir
            )
        elif requested_image_type in Defaults.get_network_image_types():
            return PxeBuilder(
                xml_state, target_dir, root_dir
            )
        elif requested_image_type in Defaults.get_archive_image_types():
            return ArchiveBuilder(
                xml_state, target_dir, root_dir
            )
        elif requested_image_type in Defaults.get_container_image_types():
            return ContainerBuilder(
                xml_state, target_dir, root_dir
            )
        else:
            raise KiwiRequestedTypeError(
                'requested image type %s not supported' % requested_image_type
            )
