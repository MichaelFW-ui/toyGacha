import random
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class ItemRarity(Enum):
    THREE_STAR = 3
    FOUR_STAR = 4
    FIVE_STAR = 5

class ItemType(Enum):
    LIMITED = "limited"
    STANDARD = "standard"

@dataclass
class GachaResult:
    rarity: ItemRarity
    item_type: ItemType
    item_name: str

class GachaSystem:
    def __init__(self):
        self.since_last_five_star = 0
        self.since_last_four_star = 0
        self.last_limited_five_star = 1
        
        self.base_five_star_prob = 0.006
        self.base_four_star_prob = 0.051
        self.step_up = 73
        self.step_end = 90
        
        # 加载物品池
        self.load_items()
    
    def load_items(self):
        items_path = Path(__file__).parent / 'items.json'
        with open(items_path, 'r', encoding='utf-8') as f:
            self.items = json.load(f)

    def _get_random_item(self, rarity: ItemRarity, item_type: ItemType) -> str:
        if rarity == ItemRarity.FIVE_STAR:
            pool = self.items['limited_five_star' if item_type == ItemType.LIMITED else 'five_star']
        elif rarity == ItemRarity.FOUR_STAR:
            pool = self.items['limited_four_star' if item_type == ItemType.LIMITED else 'four_star']
        else:
            pool = self.items['three_star']
        return random.choice(pool)

    def _calculate_five_star_prob(self):
        if self.since_last_five_star < self.step_up:
            return self.base_five_star_prob
        
        if self.since_last_five_star >= self.step_end:
            return 1.0
            
        progress = (self.since_last_five_star - self.step_up) / (self.step_end - self.step_up)
        return self.base_five_star_prob + (1 - self.base_five_star_prob) * progress

    def _get_adjusted_probabilities(self):
        p5 = self._calculate_five_star_prob()
        
        # 先判断是否到达四星保底
        if self.since_last_four_star >= 10:
            p4 = 1 - p5  # 如果不是五星就必定是四星
        else:
            # 正常情况下四星概率会被五星挤压
            p4 = max(min(1 - p5, self.base_four_star_prob), 0)
        
        # 三星概率为剩余概率
        p3 = max(1 - p5 - p4, 0)
        return p3, p4, p5

    def pull(self) -> GachaResult:
        # 先更新计数器，再进行概率判断
        self.since_last_five_star += 1
        self.since_last_four_star += 1
        
        p3, p4, p5 = self._get_adjusted_probabilities()
        
        rand = random.random()
        if rand < p5:
            # 抽中五星，重置五星计数器
            self.since_last_five_star = 0
            
            if self.last_limited_five_star == 0:
                # 大保底，必定限定
                self.last_limited_five_star = 1
                item_type = ItemType.LIMITED
            else:
                # 小保底，50/50
                is_limited = random.random() < 0.5
                self.last_limited_five_star = 1 if is_limited else 0
                item_type = ItemType.LIMITED if is_limited else ItemType.STANDARD
            
            return GachaResult(
                ItemRarity.FIVE_STAR,
                item_type,
                self._get_random_item(ItemRarity.FIVE_STAR, item_type)
            )
                
        elif rand < p5 + p4:
            # 抽中四星，重置四星计数器
            self.since_last_four_star = 0
            # 四星50/50，无保底
            item_type = ItemType.LIMITED if random.random() < 0.5 else ItemType.STANDARD
            return GachaResult(
                ItemRarity.FOUR_STAR,
                item_type,
                self._get_random_item(ItemRarity.FOUR_STAR, item_type)
            )
        else:
            # 抽中三星
            return GachaResult(ItemRarity.THREE_STAR, ItemType.STANDARD, "三星物品")

    def pull_multi(self, times=10):
        return [self.pull() for _ in range(times)]
