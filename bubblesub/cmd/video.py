# bubblesub - ASS subtitle editor
# Copyright (C) 2018 Marcin Kurczewski
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Commands related to video and playback."""

import argparse
import typing as T
from pathlib import Path

from PyQt5 import QtWidgets

import bubblesub.api
import bubblesub.ui.util
from bubblesub.api.cmd import BaseCommand
from bubblesub.api.cmd import CommandCanceled
from bubblesub.cmd.common import BooleanOperation
from bubblesub.cmd.common import EventSelection
from bubblesub.cmd.common import RelativePts


class PlaySubtitleCommand(BaseCommand):
    names = ['play-sub', 'play-subtitle']
    help_text = 'Plays given subtitle.'

    @property
    def menu_name(self) -> str:
        return f'&Play {self.args.target.description}'

    @property
    def is_enabled(self) -> bool:
        return self.api.media.is_loaded and self.args.target.makes_sense

    async def run(self) -> None:
        events = await self.args.target.get_subtitles()
        start = min(event.start for event in events)
        end = max(event.end for event in events)
        self.api.media.play(start, end)

    @staticmethod
    def _decorate_parser(
            api: bubblesub.api.Api,
            parser: argparse.ArgumentParser
    ) -> None:
        parser.add_argument(
            '-t', '--target',
            help='subtitle to play',
            type=lambda value: EventSelection(api, value),
            default='selected'
        )


class PlayAudioSelectionCommand(BaseCommand):
    names = [
        'play-audio-sel',
        'play-audio-selection',
        'play-spectrogram-sel',
        'play-spectrogram-selection'
    ]
    help_text = 'Plays a region near the current spectrogram selection.'

    @property
    def menu_name(self) -> str:
        ret = '&Play '
        if self.args.delta_start:
            ret += f'{self.args.delta_start.description} before '
        if self.args.delta_end:
            ret += f'{self.args.delta_end.description} after '
        ret += 'spectrogram selection'
        return ret

    @property
    def is_enabled(self) -> bool:
        return self.api.media.is_loaded \
            and self.api.media.audio.has_selection

    async def run(self) -> None:
        start = self.api.media.audio.selection_start
        end = self.api.media.audio.selection_end

        if self.args.method == 'start':
            end = start
        elif self.args.method == 'end':
            start = end

        if self.args.delta_start:
            start = await self.args.delta_start.apply(start)
        if self.args.delta_end:
            end = await self.args.delta_end.apply(end)

        self.api.media.play(start, end)

    @staticmethod
    def _decorate_parser(
            api: bubblesub.api.Api,
            parser: argparse.ArgumentParser
    ) -> None:
        parser.add_argument(
            '-ds', '--delta-start',
            help='delta relative to the selection start',
            type=lambda value: RelativePts(api, value)
        )
        parser.add_argument(
            '-de', '--delta-end',
            help='delta relative to the selection end',
            type=lambda value: RelativePts(api, value)
        )

        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--start',
            action='store_const',
            dest='method',
            const='start',
            help='play around selection start'
        )
        group.add_argument(
            '--end',
            action='store_const',
            dest='method',
            const='end',
            help='play around selection end'
        )
        group.add_argument(
            '--both',
            action='store_const',
            dest='method',
            const='both',
            help='play around whole selection'
        )


class SeekCommand(BaseCommand):
    names = ['seek']
    help_text = 'Changes the video playback position to desired place.'

    @property
    def menu_name(self) -> str:
        return f'&Seek {self.args.delta.description}'

    @property
    def is_enabled(self) -> bool:
        return self.api.media.is_loaded

    async def run(self) -> None:
        pts = self.api.media.current_pts
        pts = self.api.media.video.align_pts_to_near_frame(pts)
        pts = await self.args.delta.apply(pts)
        pts = self.api.media.video.align_pts_to_near_frame(pts)
        self.api.media.seek(pts, self.args.precise)
        self.api.media.is_paused = True

    @staticmethod
    def _decorate_parser(
            api: bubblesub.api.Api,
            parser: argparse.ArgumentParser
    ) -> None:
        parser.add_argument(
            '-d', '--delta',
            help='amount to shift the selection',
            type=lambda value: RelativePts(api, value),
            required=True,
        )
        parser.add_argument(
            '-p', '--precise',
            help=(
                'whether to use precise seeking at the expense of performance'
            ),
            action='store_true'
        )


class SetPlaybackSpeedCommand(BaseCommand):
    names = ['set-playback-speed']
    help_text = 'Adjusts the video playback speed.'

    @property
    def menu_name(self) -> str:
        return '&Set playback speed to {}'.format(
            self.args.expression.format('current speed')
        )

    async def run(self) -> None:
        new_value = bubblesub.util.eval_expr(
            self.args.expression.format(self.api.media.playback_speed)
        )
        assert isinstance(new_value, type(self.api.media.playback_speed))
        self.api.media.playback_speed = new_value

    @staticmethod
    def _decorate_parser(
            api: bubblesub.api.Api,
            parser: argparse.ArgumentParser
    ) -> None:
        parser.add_argument(
            'expression',
            help='expression to calculate new playback speed',
            type=str
        )


class SetVolumeCommand(BaseCommand):
    names = ['set-volume']
    help_text = 'Adjusts the video volume.'

    @property
    def menu_name(self) -> str:
        return '&Set volume to {}'.format(
            self.args.expression.format('current volume')
        )

    async def run(self) -> None:
        new_value = bubblesub.util.eval_expr(
            self.args.expression.format(self.api.media.volume)
        )
        assert isinstance(new_value, type(self.api.media.volume))
        self.api.media.volume = new_value

    @staticmethod
    def _decorate_parser(
            api: bubblesub.api.Api,
            parser: argparse.ArgumentParser
    ) -> None:
        parser.add_argument(
            'expression',
            help='expression to calculate new volume',
            type=str
        )


class MuteCommand(BaseCommand):
    names = ['mute']
    help_text = 'Mutes or unmutes the video audio.'

    @property
    def menu_name(self) -> str:
        return self.args.operation.get_description(
            'Mute', 'Unmute', 'Toggle mute'
        )

    @property
    def is_enabled(self) -> bool:
        return self.api.media.is_loaded

    async def run(self) -> None:
        self.api.media.mute = self.args.operation.apply(self.api.media.mute)

    @staticmethod
    def _decorate_parser(
            api: bubblesub.api.Api,
            parser: argparse.ArgumentParser
    ) -> None:
        parser.add_argument(
            'operation',
            help='whether to mute the audio',
            type=BooleanOperation
        )


class PauseCommand(BaseCommand):
    names = ['pause']
    help_text = 'Pauses or unpauses the video playback.'

    @property
    def menu_name(self) -> str:
        return self.args.operation.get_description(
            '&Pause playback',
            '&Play until end of the file',
            '&Toggle pause'
        )

    @property
    def is_enabled(self) -> bool:
        return self.api.media.is_loaded

    async def run(self) -> None:
        self.api.media.is_paused = (
            self.args.operation.apply(self.api.media.is_paused)
        )

    @staticmethod
    def _decorate_parser(
            api: bubblesub.api.Api,
            parser: argparse.ArgumentParser
    ) -> None:
        parser.add_argument(
            'operation',
            help='whether to pause the video',
            type=BooleanOperation
        )


class ScreenshotCommand(BaseCommand):
    names = ['video/screenshot']
    help_text = (
        'Makes a screenshot of the current video frame. '
        'Prompts user for the path where to save the screenshot to.'
    )

    @property
    def is_enabled(self) -> bool:
        return self.api.media.is_loaded

    @property
    def menu_name(self) -> str:
        return '&Save screenshot ({} subtitles)'.format(
            'with' if self.args.include_subs else 'without'
        )

    async def run(self) -> None:
        await self.api.gui.exec(self._run_with_gui)

    async def _run_with_gui(self, main_window: QtWidgets.QMainWindow) -> None:
        path = self._show_dialog(main_window)
        if path is None:
            raise CommandCanceled
        self.api.media.video.screenshot(path, self.args.include_subs)
        self.api.log.info(f'saved screenshot to {path}')

    def _show_dialog(
            self,
            main_window: QtWidgets.QMainWindow
    ) -> T.Optional[Path]:
        assert self.api.media.path is not None

        file_name = bubblesub.util.sanitize_file_name(
            'shot-{}-{}.png'.format(
                self.api.media.path.name,
                bubblesub.util.ms_to_str(self.api.media.current_pts)
            )
        )

        return bubblesub.ui.util.save_dialog(
            main_window,
            'Portable Network Graphics (*.png)',
            file_name=file_name
        )

    @staticmethod
    def _decorate_parser(
            api: bubblesub.api.Api,
            parser: argparse.ArgumentParser
    ) -> None:
        parser.add_argument(
            '-i', '--include-subs',
            help='whether to "burn" the subtitles into the screenshot',
            action='store_true'
        )


def register(cmd_api: bubblesub.api.cmd.CommandApi) -> None:
    """
    Register commands in this file into the command API.

    :param cmd_api: command API
    """
    for cls in [
            PlaySubtitleCommand,
            PlayAudioSelectionCommand,
            SeekCommand,
            SetPlaybackSpeedCommand,
            SetVolumeCommand,
            MuteCommand,
            PauseCommand,
            ScreenshotCommand,
    ]:
        cmd_api.register_core_command(T.cast(T.Type[BaseCommand], cls))
