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
from bubblesub.cmd.common import RelativePts
from bubblesub.util import ShiftTarget


def _fmt_shift_target(shift_target: ShiftTarget) -> str:
    return {
        ShiftTarget.Start: 'selection start',
        ShiftTarget.End: 'selection end',
        ShiftTarget.Both: 'selection'
    }[shift_target]


class PlayCurrentSubtitleCommand(BaseCommand):
    names = ['video/play-current-sub']
    menu_name = '&Play current subtitle'
    help_text = 'Plays the currently selected subtitle.'

    @property
    def is_enabled(self) -> bool:
        return self.api.media.is_loaded and self.api.subs.has_selection

    async def run(self) -> None:
        sub = self.api.subs.selected_events[0]
        self.api.media.play(sub.start, sub.end)


class PlayAroundSpectrogramSelectionCommand(BaseCommand):
    names = ['video/play-around-sel']
    help_text = 'Plays a region near the current spectrogram selection.'

    @property
    def menu_name(self) -> str:
        ret = '&Play '
        if self.args.delta_start < 0 and self.args.delta_end == 0:
            ret += f'{-self.args.delta_start} ms before '
        elif self.args.delta_start == 0 and self.args.delta_end > 0:
            ret += '{self.args.delta_end} ms after '
        elif self.args.delta_start != 0 or self.args.delta_end != 0:
            ret += (
                '{self.args.delta_start:+} ms / '
                '{self.args.delta_end:+} ms around '
            )
        ret += _fmt_shift_target(self.args.target)
        return ret

    @property
    def is_enabled(self) -> bool:
        return self.api.media.is_loaded \
            and self.api.media.audio.has_selection

    async def run(self) -> None:
        if self.args.target == ShiftTarget.Start:
            self.api.media.play(
                self.api.media.audio.selection_start + self.args.delta_start,
                self.api.media.audio.selection_start + self.args.delta_end
            )
        elif self.args.target == ShiftTarget.End:
            self.api.media.play(
                self.api.media.audio.selection_end + self.args.delta_start,
                self.api.media.audio.selection_end + self.args.delta_end
            )
        elif self.args.target == ShiftTarget.Both:
            self.api.media.play(
                self.api.media.audio.selection_start + self.args.delta_start,
                self.api.media.audio.selection_end + self.args.delta_end
            )

    @staticmethod
    def _decorate_parser(
            api: bubblesub.api.Api,
            parser: argparse.ArgumentParser
    ) -> None:
        parser.add_argument(
            '-t', '--target',
            help='part of selection to play around',
            type=ShiftTarget.from_string,
            choices=list(ShiftTarget),
            default=ShiftTarget.Both
        )
        parser.add_argument(
            '-ds', '--delta-start',
            help='delta relative to the selection start in milliseconds',
            type=int,
            default=0
        )
        parser.add_argument(
            '-de', '--delta-end',
            help='delta relative to the selection end in milliseconds',
            type=int,
            default=0
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
            PlayCurrentSubtitleCommand,
            PlayAroundSpectrogramSelectionCommand,
            SeekCommand,
            SetPlaybackSpeedCommand,
            SetVolumeCommand,
            MuteCommand,
            PauseCommand,
            ScreenshotCommand,
    ]:
        cmd_api.register_core_command(T.cast(T.Type[BaseCommand], cls))
