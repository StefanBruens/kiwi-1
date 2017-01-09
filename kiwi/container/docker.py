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
import os

# project
from ..defaults import Defaults
from ..path import Path
from ..command import Command
from tempfile import mkdtemp
from ..utils.sync import DataSync
from ..utils.compress import Compress


class ContainerImageDocker(object):
    """
    Create docker container from a root directory

    Attributes

    * :attr:`root_dir`
        root directory path name

    * :attr:`custom_args`
        custom argument hash:
        - container_name: tag name of the container, default: latest
        - entry_command: default command to run, default: bin/bash
    """
    def __init__(self, root_dir, custom_args=None):
        self.root_dir = root_dir
        self.docker_dir = None
        self.docker_root_dir = None

        if custom_args and 'container_name' in custom_args:
            self.container_name = custom_args['container_name']
        else:
            self.container_name = 'latest'

        if custom_args and 'entry_command' in custom_args:
            self.entry_command = custom_args['entry_command']
        else:
            self.entry_command = '/bin/bash'

    def create(self, filename):
        """
        Create compressed docker system container tar archive

        :param string filename: archive file name
        """
        exclude_list = [
            'image', '.profile', '.kconfig', 'boot',
            Defaults.get_shared_cache_location()
        ]

        self.docker_dir = mkdtemp(prefix='kiwi_docker_dir.')
        self.docker_root_dir = mkdtemp(prefix='kiwi_docker_root_dir.')

        container_dir = os.sep.join(
            [self.docker_dir, 'umoci_layout']
        )
        container_tag = ':'.join(
            [container_dir, self.container_name]
        )

        Command.run(
            ['umoci', 'init', '--layout', container_dir]
        )
        Command.run(
            ['umoci', 'new', '--image', container_tag]
        )
        Command.run(
            ['umoci', 'unpack', '--image', container_tag, self.docker_root_dir]
        )
        docker_root = DataSync(
            self.root_dir, os.sep.join([self.docker_root_dir, 'rootfs'])
        )
        docker_root.sync_data(
            options=['-a', '-H', '-X', '-A'], exclude=exclude_list
        )
        Command.run(
            ['umoci', 'repack', '--image', container_tag, self.docker_root_dir]
        )
        Command.run(
            [
                'umoci', 'config',
                '='.join(['--config.cmd', self.entry_command]),
                '--image', container_tag
            ]
        )
        Command.run(
            ['umoci', 'gc', '--layout', container_dir]
        )

        docker_tarfile = filename.replace('.xz', '')
        Command.run(
            [
                'skopeo', 'copy', 'oci:{0}'.format(
                    container_tag
                ),
                'docker-archive:{0}:{1}'.format(
                    docker_tarfile, container_tag
                )
            ]
        )
        compressor = Compress(docker_tarfile)
        compressor.xz()

    def __del__(self):
        if self.docker_dir:
            Path.wipe(self.docker_dir)
        if self.docker_root_dir:
            Path.wipe(self.docker_root_dir)
