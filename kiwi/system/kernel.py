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
from collections import namedtuple

# project
from ..command import Command

from ..exceptions import KiwiKernelLookupError


class Kernel(object):
    """
    Implementes kernel lookup and extraction from given root tree

    Attributes

    * :attr:`root_dir`
        root directory path name

    * :attr:`kernel_names`
        list of kernel names to search for
        functions.sh::suseStripKernel() provides a normalized
        file so that we do not have to search for many different
        names in this code
    """
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.kernel_names = self._setup_kernel_names_for_lookup()

    def get_kernel(self, raise_on_not_found=False):
        """
        Lookup kernel files and provide filename and version

        :return: tuple with filename, kernelname and version
        :rtype: namedtuple
        """
        for kernel_name in self.kernel_names:
            kernel_file = self.root_dir + '/boot/' + kernel_name
            if os.path.exists(kernel_file):
                version = Command.run(
                    command=['kversion', kernel_file], raise_on_error=False
                ).output
                if not version:
                    version = 'no-version-found'
                version = version.rstrip('\n')
                kernel = namedtuple(
                    'kernel', ['name', 'filename', 'version']
                )
                return kernel(
                    name=os.path.basename(os.path.realpath(kernel_file)),
                    filename=kernel_file,
                    version=version
                )

        if raise_on_not_found:
            raise KiwiKernelLookupError(
                'No kernel found in {0}, searched for {1}'.format(
                    os.sep.join([self.root_dir, 'boot']),
                    ','.join(self.kernel_names)
                )
            )

    def get_xen_hypervisor(self):
        """
        Lookup xen hypervisor and provide filename and hypervisor name

        :return: tuple with filename and hypervisor name
        :rtype: namedtuple
        """
        xen_hypervisor = self.root_dir + '/boot/xen.gz'
        if os.path.exists(xen_hypervisor):
            xen = namedtuple(
                'xen', ['filename', 'name']
            )
            return xen(
                filename=xen_hypervisor,
                name='xen.gz'
            )

    def copy_kernel(self, target_dir, file_name=None):
        """
        Copy kernel to specified target

        If no file_name is given the target filename is set
        as kernel-<kernel.version>.kernel

        :param string target_dir: target path name
        :param string filename: base filename in target
        """
        kernel = self.get_kernel()
        if kernel:
            if not file_name:
                file_name = 'kernel-' + kernel.version + '.kernel'
            target_file = ''.join(
                [target_dir, '/', file_name]
            )
            Command.run(['cp', kernel.filename, target_file])

    def copy_xen_hypervisor(self, target_dir, file_name=None):
        """
        Copy xen hypervisor to specified target

        If no file_name is given the target filename is set
        as hypervisor-<xen.name>

        :param string target_dir: target path name
        :param string filename: base filename in target
        """
        xen = self.get_xen_hypervisor()
        if xen:
            if not file_name:
                file_name = 'hypervisor-' + xen.name
            target_file = ''.join(
                [target_dir, '/', file_name]
            )
            Command.run(['cp', xen.filename, target_file])

    def _setup_kernel_names_for_lookup(self):
        """
        The kernel image name is different per arch and distribution
        This method returns a list of possible kernel image names in
        order to search and find one of them

        :rtype: list
        :return: list of kernel image names
        """
        kernel_names = [
            # lookup for the symlink or functions.sh::suseStripKernel()
            # generated names first
            'vmlinux', 'vmlinuz', 'zImage'
        ]
        kernel_dir = os.listdir(''.join([self.root_dir, '/lib/modules']))
        if kernel_dir:
            # append lookup for the real kernel image names
            # depending on the arch and os they are different
            # in their prefix
            kernel_prefixes = [
                'uImage', 'Image', 'zImage', 'vmlinuz', 'vmlinux', 'image'
            ]
            kernel_name_pattern = '{prefix}-{name}'
            for kernel_prefix in kernel_prefixes:
                kernel_names.append(
                    kernel_name_pattern.format(
                        prefix=kernel_prefix, name=kernel_dir[0]
                    )
                )
        return kernel_names
