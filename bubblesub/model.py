import typing as T

from PyQt5 import QtCore

TItem = T.TypeVar('TItem')  # pylint: disable=invalid-name


class classproperty(property):
    def __init__(self, func: T.Callable[[type], TItem]) -> None:
        super().__init__()
        self.func = func

    def __get__(self, cls: object, owner: type) -> TItem:
        return self.func(owner)


class ObservableObject:
    _dirty = False

    def __init__(self) -> None:
        self._setattr_impl = self._setattr_normal

    def __setattr__(self, prop: str, new_value: T.Any) -> None:
        if prop.startswith('_'):
            super().__setattr__(prop, new_value)
        else:
            try:
                old_value = getattr(self, prop)
            except AttributeError:
                super().__setattr__(prop, new_value)
            else:
                if new_value != old_value:
                    self._setattr_impl(prop, new_value)

    def _setattr_normal(self, prop: str, new_value: T.Any) -> None:
        super().__setattr__(prop, new_value)
        self._after_change()

    def _setattr_throttled(self, prop: str, new_value: T.Any) -> None:
        super().__setattr__(prop, new_value)
        self._dirty = True

    def begin_update(self) -> None:
        self._setattr_impl = self._setattr_throttled

    def end_update(self) -> None:
        if self._dirty:
            self._after_change()
        self._setattr_impl = self._setattr_normal
        self._dirty = False

    def _after_change(self) -> None:
        pass


class ObservableListSignals(QtCore.QObject):
    items_inserted = QtCore.pyqtSignal([int, int])
    items_removed = QtCore.pyqtSignal([int, int])
    item_changed = QtCore.pyqtSignal([int])


# alternative to QtCore.QAbstractListModel that simplifies indexing
class ObservableList(T.Generic[TItem]):
    def __init__(self) -> None:
        super().__init__()
        self._signals = ObservableListSignals()
        self._items: T.List[TItem] = []

    @property
    def items_inserted(self) -> QtCore.pyqtSignal:
        return self._signals.items_inserted

    @property
    def items_removed(self) -> QtCore.pyqtSignal:
        return self._signals.items_removed

    @property
    def item_changed(self) -> QtCore.pyqtSignal:
        return self._signals.item_changed

    def __getstate__(self) -> T.Any:
        return self._items

    def __setstate__(self, state: T.Any) -> None:
        self._items = state

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, idx: int) -> TItem:
        return self._items[idx]

    def __setitem__(self, idx: T.Union[slice, int], value: T.Any) -> None:
        if isinstance(idx, slice):
            raise RuntimeError('Slice assignment is not supported')
        else:
            self._items[idx] = value
            self.item_changed.emit(idx)

    def __iter__(self) -> T.Iterator[TItem]:
        yield from self._items

    def get(
            self,
            idx: int,
            default: T.Optional[TItem] = None
    ) -> T.Optional[TItem]:
        if idx < 0 or idx >= len(self):
            return default
        return self._items[idx]

    def index(self, item: TItem) -> T.Optional[int]:
        for idx, other_item in enumerate(self._items):
            if other_item == item:
                return idx
        return None

    def insert(self, idx: int, items: T.List[TItem]) -> None:
        if not items:
            return
        self._items = self._items[:idx] + items + self._items[idx:]
        self.items_inserted.emit(idx, len(items))

    def remove(self, idx: int, count: int) -> None:
        self._items = self._items[:idx] + self._items[idx + count:]
        self.items_removed.emit(idx, count)

    def clear(self) -> None:
        self.remove(0, len(self))

    def move(self, idx: int, new_idx: int) -> None:
        item = self._items[idx]
        self.remove(idx, 1)
        self.insert(new_idx, [item])

    def replace(self, values: T.List[TItem]) -> None:
        old_size = len(self)
        new_size = len(values)
        self._items[:] = []
        self.items_removed.emit(0, old_size)
        self._items[:] = values
        self.items_inserted.emit(0, new_size)