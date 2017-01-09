from mock import call
from mock import patch

import mock

from .test_helper import *

from kiwi.exceptions import *
from kiwi.container.docker import ContainerImageDocker


class TestContainerImageDocker(object):
    def setup(self):
        self.docker = ContainerImageDocker('root_dir')

    def test_init_custom_args(self):
        docker = ContainerImageDocker(
            'root_dir', {'container_name': 'foo', 'entry_command': 'bar'}
        )
        assert docker.container_name == 'foo'
        assert docker.entry_command == 'bar'

    @patch('kiwi.container.docker.Path.wipe')
    def test_del(self, mock_wipe):
        docker = ContainerImageDocker('root_dir')
        docker.docker_dir = 'dir_a'
        docker.docker_root_dir = 'dir_b'
        docker.__del__()
        assert mock_wipe.call_args_list == [
            call('dir_a'), call('dir_b')
        ]

    @patch('kiwi.container.docker.Compress')
    @patch('kiwi.container.docker.Command.run')
    @patch('kiwi.container.docker.DataSync')
    @patch('kiwi.container.docker.mkdtemp')
    @patch('kiwi.container.docker.Path.wipe')
    def test_create(
        self, mock_wipe, mock_mkdtemp, mock_sync, mock_command, mock_compress
    ):
        compressor = mock.Mock()
        mock_compress.return_value = compressor
        docker_root = mock.Mock()
        mock_sync.return_value = docker_root
        tmpdirs = ['kiwi_docker_root_dir', 'kiwi_docker_dir']

        def call_mkdtemp(prefix):
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = call_mkdtemp

        self.docker.create('result.tar.xz')
        assert mock_command.call_args_list == [
            call([
                'umoci', 'init', '--layout',
                'kiwi_docker_dir/umoci_layout'
            ]),
            call([
                'umoci', 'new', '--image',
                'kiwi_docker_dir/umoci_layout:latest'
            ]),
            call([
                'umoci', 'unpack', '--image',
                'kiwi_docker_dir/umoci_layout:latest', 'kiwi_docker_root_dir'
            ]),
            call([
                'umoci', 'repack', '--image',
                'kiwi_docker_dir/umoci_layout:latest', 'kiwi_docker_root_dir'
            ]),
            call([
                'umoci', 'config', '--config.cmd=/bin/bash', '--image',
                'kiwi_docker_dir/umoci_layout:latest'
            ]),
            call([
                'umoci', 'gc', '--layout', 'kiwi_docker_dir/umoci_layout'
            ]),
            call([
                'skopeo', 'copy', 'oci:kiwi_docker_dir/umoci_layout:latest',
                'docker-archive:result.tar:kiwi_docker_dir/umoci_layout:latest'
            ])
        ]
        mock_sync.assert_called_once_with(
            'root_dir', 'kiwi_docker_root_dir/rootfs'
        )
        docker_root.sync_data.assert_called_once_with(
            exclude=['image', '.profile', '.kconfig', 'boot', 'var/cache/kiwi'],
            options=['-a', '-H', '-X', '-A']
        )
        mock_compress.assert_called_once_with('result.tar')
        compressor.xz.assert_called_once_with()
