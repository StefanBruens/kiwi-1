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
"""
usage: kiwi system create -h | --help
       kiwi system create --root=<directory> --target-dir=<directory>
       kiwi system create help

commands:
    create
        create a system image from the specified root directory
        the root directory is the result of a system prepare
        command
    create help
        show manual page for create command

options:
    --root=<directory>
        the path to the root directory, usually the result of
        a former system prepare call
    --target-dir=<directory>
        the target directory to store the system image file(s)
"""
import os

# project
from .base import CliTask
from ..help import Help
from ..builder import ImageBuilder
from ..system.setup import SystemSetup
from ..privileges import Privileges
from ..path import Path
from ..logger import log


class SystemCreateTask(CliTask):
    """
    Implements creation of system images

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self):
        """
        Create a system image from the specified root directory
        the root directory is the result of a system prepare
        command
        """
        self.manual = Help()
        if self._help():
            return

        Privileges.check_for_root_permissions()

        self.load_xml_description(
            self.command_args['--root']
        )
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            self.command_args['--target-dir']
        )

        log.info('Creating system image')
        if not os.path.exists(self.command_args['--target-dir']):
            Path.create(self.command_args['--target-dir'])

        setup = SystemSetup(
            xml_state=self.xml_state,
            root_dir=self.command_args['--root']
        )
        setup.call_image_script()

        image_builder = ImageBuilder(
            self.xml_state,
            self.command_args['--target-dir'],
            self.command_args['--root']
        )
        result = image_builder.create()
        result.print_results()
        result.dump(
            self.command_args['--target-dir'] + '/kiwi.result'
        )

    def _help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::system::create')
        else:
            return False
        return self.manual
