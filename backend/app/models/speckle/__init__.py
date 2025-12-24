"""Speckle BuiltElements Models for OpenTruss

本模块包含所有 Speckle BuiltElements 的 Pydantic 模型定义，用于数据摄入 API。

所有模型继承自 SpeckleBuiltElementBase，包含 OpenTruss 特定的字段扩展。
"""

from .base import (
    Geometry2D,
    SpeckleBuiltElementBase,
)

from .architectural import (
    Wall,
    Floor,
    Ceiling,
    Roof,
    Column,
)

from .structural import (
    Beam,
    Brace,
    Structure,
    Rebar,
)

from .mep import (
    Duct,
    Pipe,
    CableTray,
    Conduit,
    Wire,
)

from .spatial import (
    Level,
    Room,
    Space,
    Zone,
    Area,
)

from .other import (
    Opening,
    Topography,
    GridLine,
    Profile,
    Network,
    View,
    Alignment,
    Baseline,
    Featureline,
    Station,
)

# 所有 Speckle 元素类型的 Union
from typing import Union

SpeckleBuiltElement = Union[
    # Architectural
    Wall, Floor, Ceiling, Roof, Column,
    # Structural
    Beam, Brace, Structure, Rebar,
    # MEP
    Duct, Pipe, CableTray, Conduit, Wire,
    # Spatial
    Level, Room, Space, Zone, Area,
    # Other
    Opening, Topography, GridLine, Profile, Network, View,
    Alignment, Baseline, Featureline, Station,
]

__all__ = [
    # Base
    "Geometry2D",
    "SpeckleBuiltElementBase",
    "SpeckleBuiltElement",
    # Architectural
    "Wall",
    "Floor",
    "Ceiling",
    "Roof",
    "Column",
    # Structural
    "Beam",
    "Brace",
    "Structure",
    "Rebar",
    # MEP
    "Duct",
    "Pipe",
    "CableTray",
    "Conduit",
    "Wire",
    # Spatial
    "Level",
    "Room",
    "Space",
    "Zone",
    "Area",
    # Other
    "Opening",
    "Topography",
    "GridLine",
    "Profile",
    "Network",
    "View",
    "Alignment",
    "Baseline",
    "Featureline",
    "Station",
]

