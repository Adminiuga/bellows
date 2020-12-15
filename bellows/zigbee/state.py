"""Classes to implement status of the application controller."""

from dataclasses import InitVar, dataclass, field
import functools
from typing import Any, Dict, Iterable, List, Optional

import zigpy.types as t
import zigpy.zdo.types as zdo_t


@dataclass
class NodeInfo:
    """Controller Application network Node information."""

    nwk: t.NWK = t.NWK(0xFFFE)
    ieee: Optional[t.EUI64] = None
    logical_type: Optional[zdo_t.LogicalType] = None

    def __post_init__(self) -> None:
        """Initialize instance."""
        if self.ieee is None:
            self.ieee = t.EUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff")
        if self.logical_type is None:
            self.logical_type = zdo_t.LogicalType.Reserved7


@dataclass
class NetworkInformation:
    """Network information."""

    extended_pan_id: Optional[t.ExtendedPanId] = field(default_factory=t.ExtendedPanId)
    pan_id: Optional[t.PanId] = 0xFFFE
    nwk_update_id: Optional[t.uint8_t] = 0x00
    nwk_manager_id: Optional[t.NWK] = t.NWK(0xFFFE)
    channel: Optional[t.uint8_t] = None


@dataclass
class Counter:
    """Ever increasing Counter representation."""

    name: str
    initial_value: InitVar[int] = 0
    _raw_value: int = field(init=False, default=0)
    reset_count: int = field(init=False, default=0)
    _last_reset_value: int = field(init=False, default=0)

    def __eq__(self, other) -> bool:
        """Compare two counters."""
        if isinstance(other, self.__class__):
            return self.value == other.value

        return self.value == other

    def __int__(self) -> int:
        """Return int of the current value."""
        return self.value

    def __post_init__(self, initial_value) -> None:
        """Initialize instance."""
        self._raw_value = initial_value

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} = {self.value}"

    @property
    def value(self) -> int:
        """Current value of the counter."""

        return self._last_reset_value + self._raw_value

    def update(self, new_value: int) -> None:
        """Update counter value."""

        if new_value == self._raw_value:
            return

        diff = new_value - self._raw_value
        if diff < 0:  # Roll over or reset
            self.reset_and_update(new_value)
            return

        self._raw_value = new_value

    def increment(self, increment: int = 1) -> None:
        """Increment current value by increment."""

        assert increment >= 0
        self._raw_value += increment

    def reset_and_update(self, value: int) -> None:
        """Clear (rollover event) and optionally update."""

        self._last_reset_value = self.value
        self._raw_value = value
        self.reset_count += 1

    reset = functools.partialmethod(reset_and_update, 0)


class Counters:
    """Named collection of counters."""

    def __init__(self, collection_name: str, names: Optional[Iterable[str]]) -> None:
        """Initialize instance."""

        self._name = collection_name
        self._counters: Dict[Any, Counter] = {name: Counter(name) for name in names}

    def __contains__(self, item: Any) -> bool:
        """Is the "counter id/name" in the list."""
        return item in self._counters

    def __iter__(self) -> Iterable[Counter]:
        """Return an iterable of the counters"""
        return (counter for counter in self._counters.values())

    def __str__(self) -> str:
        """String magic method."""
        counters = [str(counter) for counter in self]
        return f"{self.name}: [{', '.join(counters)}]"

    def __repr__(self) -> str:
        """Representation magic method."""
        counters = (
            f"{counter.__class__.__name__}('{counter.name}', {int(counter)})"
            for counter in self
        )
        counters = ", ".join(counters)
        return f"{self.__class__.__name__}('{self.name}', {{{counters}}})"

    @property
    def name(self) -> str:
        """Return counter collection name."""
        return self._name

    @property
    def list(self) -> List[Counter]:
        """Return list of counters."""

        return [counter for counter in self._counters.values()]

    def reset(self) -> None:
        """Clear and rollover counters."""

        for counter in self._counters.values():
            counter.reset()

    def __getitem__(self, counter_id: Any) -> Counter:
        """Get a counter."""

        return self._counters[counter_id]

    def __setitem__(self, counter_id: Any, value: int) -> None:
        """Update specific counter to new value."""

        self._counters[counter_id].update(value)

    def add_counter(self, name: str, value: int = 0) -> Counter:
        """Add a new counter."""

        if name in self._counters:
            return self[name]

        counter = Counter(name, initial_value=value)
        self._counters[counter.name] = counter
        return counter


@dataclass
class State:
    node_information: NodeInfo
    network_information: NetworkInformation
    counters: Optional[Dict[str, Counters]] = None

    def __post_init__(self) -> None:
        """Initialize default counters."""
        if self.counters is None:
            self.counters = {}
