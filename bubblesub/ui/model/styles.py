import enum
import typing as T

from PyQt5 import QtCore
from PyQt5 import QtGui

import bubblesub.api
import bubblesub.cache
import bubblesub.model
from bubblesub.ass.style import Color
from bubblesub.ui.model.proxy import ObservableListTableAdapter


def _serialize_color(color: Color) -> QtGui.QColor:
    return QtGui.QColor(color. red, color.green, color.blue, color.alpha)


def _deserialize_color(color: QtGui.QColor) -> Color:
    return Color(color.red(), color.green(), color.blue(), color.alpha())


class StylesModelColumn(enum.IntEnum):
    Name = 0
    FontName = 1
    FontSize = 2
    Bold = 3
    Italic = 4
    Underline = 5
    StrikeOut = 6
    PrimaryColor = 7
    SecondaryColor = 8
    BackColor = 9
    OutlineColor = 10
    ShadowWidth = 11
    OutlineWidth = 12
    ScaleX = 13
    ScaleY = 14
    Angle = 15
    Spacing = 16
    MarginLeft = 17
    MarginRight = 18
    MarginVertical = 19
    Alignment = 20


def _getattr_proxy(
        prop_name: str,
        wrapper: T.Callable[[T.Any], T.Any]
) -> T.Callable[[bubblesub.ass.style.Style], T.Any]:
    def func(style: bubblesub.ass.style.Style) -> T.Any:
        return wrapper(getattr(style, prop_name))

    return func


def _setattr_proxy(
        prop_name: str,
        wrapper: T.Callable[[T.Any], T.Any]
) -> T.Callable[[bubblesub.ass.style.Style, T.Any], None]:
    def func(style: bubblesub.ass.style.Style, value: T.Any) -> None:
        setattr(style, prop_name, wrapper(value))

    return func


_READER_MAP = {
    StylesModelColumn.Name: _getattr_proxy('name', str),
    StylesModelColumn.FontName: _getattr_proxy('font_name', str),
    StylesModelColumn.FontSize: _getattr_proxy('font_size', int),
    StylesModelColumn.Bold: _getattr_proxy('bold', bool),
    StylesModelColumn.Italic: _getattr_proxy('italic', bool),
    StylesModelColumn.Underline: _getattr_proxy('underline', bool),
    StylesModelColumn.StrikeOut: _getattr_proxy('strike_out', bool),
    StylesModelColumn.ShadowWidth: _getattr_proxy('shadow', float),
    StylesModelColumn.OutlineWidth: _getattr_proxy('outline', float),
    StylesModelColumn.ScaleX: _getattr_proxy('scale_x', float),
    StylesModelColumn.ScaleY: _getattr_proxy('scale_y', float),
    StylesModelColumn.Angle: _getattr_proxy('angle', float),
    StylesModelColumn.Spacing: _getattr_proxy('spacing', float),
    StylesModelColumn.Alignment: _getattr_proxy('alignment', int),
    StylesModelColumn.MarginLeft: _getattr_proxy('margin_left', int),
    StylesModelColumn.MarginRight: _getattr_proxy('margin_right', int),
    StylesModelColumn.MarginVertical: _getattr_proxy('margin_vertical', int),
    StylesModelColumn.PrimaryColor:
        _getattr_proxy('primary_color', _serialize_color),
    StylesModelColumn.SecondaryColor:
        _getattr_proxy('secondary_color', _serialize_color),
    StylesModelColumn.BackColor:
        _getattr_proxy('back_color', _serialize_color),
    StylesModelColumn.OutlineColor:
        _getattr_proxy('outline_color', _serialize_color),
}

_WRITER_MAP = {
    StylesModelColumn.Name: _setattr_proxy('name', str),
    StylesModelColumn.FontName: _setattr_proxy('font_name', str),
    StylesModelColumn.FontSize: _setattr_proxy('font_size', int),
    StylesModelColumn.Bold: _setattr_proxy('bold', bool),
    StylesModelColumn.Italic: _setattr_proxy('italic', bool),
    StylesModelColumn.Underline: _setattr_proxy('underline', bool),
    StylesModelColumn.StrikeOut: _setattr_proxy('strike_out', bool),
    StylesModelColumn.ShadowWidth: _setattr_proxy('shadow', float),
    StylesModelColumn.OutlineWidth: _setattr_proxy('outline', float),
    StylesModelColumn.ScaleX: _setattr_proxy('scale_x', float),
    StylesModelColumn.ScaleY: _setattr_proxy('scale_y', float),
    StylesModelColumn.Angle: _setattr_proxy('angle', float),
    StylesModelColumn.Spacing: _setattr_proxy('spacing', float),
    StylesModelColumn.Alignment: _setattr_proxy('alignment', int),
    StylesModelColumn.MarginLeft: _setattr_proxy('margin_left', int),
    StylesModelColumn.MarginRight: _setattr_proxy('margin_right', int),
    StylesModelColumn.MarginVertical: _setattr_proxy('margin_vertical', int),
    StylesModelColumn.PrimaryColor:
        _setattr_proxy('primary_color', _deserialize_color),
    StylesModelColumn.SecondaryColor:
        _setattr_proxy('secondary_color', _deserialize_color),
    StylesModelColumn.BackColor:
        _setattr_proxy('back_color', _deserialize_color),
    StylesModelColumn.OutlineColor:
        _setattr_proxy('outline_color', _deserialize_color),
}


class StylesModel(ObservableListTableAdapter):
    def flags(self, index: QtCore.QModelIndex) -> int:
        if index.column() == StylesModelColumn.Name:
            return T.cast(
                int,
                QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
            )
        return T.cast(
            int,
            QtCore.Qt.ItemIsEnabled |
            QtCore.Qt.ItemIsSelectable |
            QtCore.Qt.ItemIsEditable
        )

    @property
    def _column_count(self) -> int:
        return len(StylesModelColumn)

    @bubblesub.cache.Memoize
    def _get_data(self, row_idx: int, col_idx: int, role: int) -> T.Any:
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            style = self._list[row_idx]
            return _READER_MAP[StylesModelColumn(col_idx)](style)
        return QtCore.QVariant()

    def _set_data(
            self, row_idx: int, col_idx: int, role: int, new_value: T.Any
    ) -> bool:
        style = self._list[row_idx]
        try:
            _WRITER_MAP[StylesModelColumn(col_idx)](style, new_value)
        except KeyError:
            return False
        return True