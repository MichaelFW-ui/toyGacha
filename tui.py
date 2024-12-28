import curses
import time
from gacha import GachaSystem, ItemRarity, ItemType

class GachaTUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.gacha = GachaSystem()
        self.character_counts = {}  # 存储角色抽取次数
        self.total_pulls = 0  # 添加总抽数统计
        self.setup_screen()

    def setup_screen(self):
        curses.start_color()
        curses.use_default_colors()
        # 定义更多的颜色对
        curses.init_pair(1, curses.COLOR_YELLOW, -1)      # 五星限定
        curses.init_pair(2, curses.COLOR_RED, -1)         # 五星常驻
        curses.init_pair(3, curses.COLOR_MAGENTA, -1)     # 四星限定
        curses.init_pair(4, curses.COLOR_BLUE, -1)        # 四星常驻
        curses.init_pair(5, curses.COLOR_WHITE, -1)       # 三星
        curses.curs_set(0)
        self.stdscr.clear()

    def draw_box(self, y, x, width, height):
        # 绘制方框
        self.stdscr.addch(y, x, '┌')
        self.stdscr.addch(y, x + width - 1, '┐')
        self.stdscr.addch(y + height - 1, x, '└')
        self.stdscr.addch(y + height - 1, x + width - 1, '┘')
        
        for i in range(1, width - 1):
            self.stdscr.addch(y, x + i, '─')
            self.stdscr.addch(y + height - 1, x + i, '─')
        
        for i in range(1, height - 1):
            self.stdscr.addch(y + i, x, '│')
            self.stdscr.addch(y + i, x + width - 1, '│')

    def get_color_pair(self, result):
        if result.rarity == ItemRarity.FIVE_STAR:
            return 1 if result.item_type == ItemType.LIMITED else 2
        elif result.rarity == ItemRarity.FOUR_STAR:
            return 3 if result.item_type == ItemType.LIMITED else 4
        return 5

    def show_pull_animation(self):
        max_y, max_x = self.stdscr.getmaxyx()
        center_y, center_x = max_y // 2, max_x // 2
        
        animations = ["★", "★ ★", "★ ★ ★"]
        for frame in animations:
            self.stdscr.addstr(center_y, center_x - len(frame)//2, frame)
            self.stdscr.refresh()
            time.sleep(0.1)  # 加快动画速度
            self.stdscr.clear()
            self.draw_frame()

    def get_string_display_width(self, s: str) -> int:
        """计算字符串显示宽度，中文字符计2，ASCII字符计1"""
        width = 0
        for char in s:
            width += 2 if ord(char) > 255 else 1
        return width

    def get_centered_position(self, text: str, space_width: int) -> int:
        """计算文字居中的起始位置"""
        text_width = self.get_string_display_width(text)
        return (space_width - text_width) // 2

    def display_result(self, result, position=None):
        max_y, max_x = self.stdscr.getmaxyx()
        box_width = 18  # 增加宽度到18，确保有足够空间
        box_height = 5
        
        # 计算起始位置
        start_x = (max_x - box_width * 5) // 2
        usable_height = max_y - 10
        total_rows = (10 + 4) // 5
        total_height = total_rows * box_height
        start_y = 2 + (usable_height - total_height) // 2
        
        row = position // 5 if position is not None else 0
        col = position % 5 if position is not None else 0
        
        x = start_x + col * box_width
        y = start_y + row * box_height
        
        # 绘制方框
        self.draw_box(y, x, box_width, box_height)
        
        # 获取颜色
        color = self.get_color_pair(result)
        
        # 显示结果（确保内容不会覆盖边框）
        self.stdscr.attron(curses.color_pair(color) | curses.A_BOLD)
        
        # 处理名称文本，留出更多边距
        name_text = result.item_name
        max_width = box_width - 4  # 两边各留2个字符的空间
        while self.get_string_display_width(name_text) > max_width:
            name_text = name_text[:-1]
        
        name_x = x + self.get_centered_position(name_text, box_width)
        rarity_text = "★" * result.rarity.value
        rarity_x = x + self.get_centered_position(rarity_text, box_width)
        
        # 确保文字不会覆盖边框
        if name_x < x + 1:
            name_x = x + 1
        if rarity_x < x + 1:
            rarity_x = x + 1
            
        self.stdscr.addstr(y + 1, name_x, name_text)
        self.stdscr.addstr(y + 2, rarity_x, rarity_text)
        self.stdscr.attroff(curses.color_pair(color) | curses.A_BOLD)
        
        # 刷新屏幕
        self.stdscr.refresh()

    def get_constellation_text(self, count):
        if count <= 6:
            return f"{count-1}命" if count > 1 else "0命"
        elif count == 7:
            return "满命"
        else:
            return f"满命溢出{count-7}只"

    def update_character_count(self, result):
        if result.rarity in [ItemRarity.FOUR_STAR, ItemRarity.FIVE_STAR]:
            key = (result.item_name, result.rarity, result.item_type)
            self.character_counts[key] = self.character_counts.get(key, 0) + 1

    def get_statistics_text(self):
        limited_5 = {}
        standard_5 = {}
        limited_4 = {}
        standard_4 = {}

        for (name, rarity, item_type), count in self.character_counts.items():
            if rarity == ItemRarity.FIVE_STAR:
                if item_type == ItemType.LIMITED:
                    limited_5[name] = count
                else:
                    standard_5[name] = count
            elif rarity == ItemRarity.FOUR_STAR:
                if item_type == ItemType.LIMITED:
                    limited_4[name] = count
                else:
                    standard_4[name] = count

        lines = []
        if limited_5:
            lines.append("限定五星：" + ", ".join(f"{name}({self.get_constellation_text(count)})" 
                        for name, count in limited_5.items()))
        if standard_5:
            lines.append("常驻五星：" + ", ".join(f"{name}({self.get_constellation_text(count)})" 
                        for name, count in standard_5.items()))
        if limited_4:
            lines.append("限定四星：" + ", ".join(f"{name}({self.get_constellation_text(count)})" 
                        for name, count in limited_4.items()))
        if standard_4:
            lines.append("常驻四星：" + ", ".join(f"{name}({self.get_constellation_text(count)})" 
                        for name, count in standard_4.items()))
        
        lines.append(f"总抽数：{self.total_pulls}")  # 使用 self.total_pulls
        return lines

    def clear_stats_area(self):
        """清除统计信息区域"""
        max_y, max_x = self.stdscr.getmaxyx()
        # 清除从底部往上7行的区域（为统计信息预留更多空间）
        for i in range(2, 9):  # 增加清除的行数
            self.stdscr.move(max_y-i, 1)
            self.stdscr.clrtoeol()

    def draw_frame(self):
        max_y, max_x = self.stdscr.getmaxyx()
        
        # 1. 绘制基础框架
        self.stdscr.box()
        
        # 2. 显示标题
        title = "★ 豪华抽卡模拟器 ★"
        self.stdscr.addstr(0, (max_x - len(title)) // 2, title)
        
        # 3. 清除并显示统计信息（只清除统计信息区域）
        self.clear_stats_area()
        stats = self.get_statistics_text()
        for i, line in enumerate(reversed(stats)):  # 从下往上显示
            if max_y-(i+2) > 1:  # 确保不会覆盖到标题
                self.stdscr.addstr(max_y-(i+2), 2, line[:max_x-4])
        
        # 4. 显示底部帮助信息
        help_text = "按'1'单抽 | 按'0'十连 | 按'q'退出"
        self.stdscr.addstr(max_y-1, (max_x - len(help_text)) // 2, help_text)
        
        self.stdscr.refresh()

    def run(self):
        while True:
            self.draw_frame()
            key = self.stdscr.getch()
            
            if key == ord('q'):
                break
            elif key == ord('1'):
                self.show_pull_animation()
                result = self.gacha.pull()
                self.total_pulls += 1
                self.update_character_count(result)
                self.stdscr.clear()
                self.draw_frame()
                self.display_result(result)
            elif key == ord('0'):
                self.show_pull_animation()
                results = self.gacha.pull_multi(10)
                self.total_pulls += 10
                self.stdscr.clear()
                self.draw_frame()
                for i, result in enumerate(results):
                    self.update_character_count(result)
                    self.display_result(result, i)

def main(stdscr):
    app = GachaTUI(stdscr)
    app.run()
