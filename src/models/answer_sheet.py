"""
解答用紙に関するデータモデル
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class Region:
    """座標領域を表すクラス"""
    tag: str
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    
    @property
    def width(self) -> int:
        """領域の幅を返します"""
        return abs(self.end_x - self.start_x)
    
    @property
    def height(self) -> int:
        """領域の高さを返します"""
        return abs(self.end_y - self.start_y)
    
    @property
    def center(self) -> Tuple[int, int]:
        """領域の中心座標を返します"""
        return (
            int(self.start_x + (self.end_x - self.start_x) / 2),
            int(self.start_y + (self.end_y - self.start_y) / 2)
        )


@dataclass
class AnswerSheet:
    """解答用紙のデータモデル"""
    filename: str
    regions: Dict[str, Region] = field(default_factory=dict)
    
    def add_region(self, region: Region) -> None:
        """領域を追加します"""
        self.regions[region.tag] = region
    
    def get_region(self, tag: str) -> Optional[Region]:
        """タグで指定した領域を取得します"""
        return self.regions.get(tag)
    
    def has_region(self, tag: str) -> bool:
        """指定したタグの領域が存在するか確認します"""
        return tag in self.regions