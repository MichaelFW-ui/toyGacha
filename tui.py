import curses
import time
from gacha import GachaSystem, ItemRarity, ItemType

class GachaTUI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.gacha = GachaSystem()
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

    def display_result(self, result, position=None):
        max_y, max_x = self.stdscr.getmaxyx()
        box_width = 16
        box_height = 5  # 增加高度
        
        # 计算起始位置
        start_x = (max_x - box_width * 5) // 2
        start_y = max_y // 2 - 4  # 调整起始位置
        
        # 计算当前物品的位置
        row = position // 5 if position is not None else 0
        col = position % 5 if position is not None else 0
        
        x = start_x + col * box_width
        y = start_y + row * (box_height + 1)
        
        # 绘制方框
        self.draw_box(y, x, box_width, box_height)
        
        # 获取颜色
        color = self.get_color_pair(result)
        
        # 显示结果
        self.stdscr.attron(curses.color_pair(color) | curses.A_BOLD)
        name_text = result.item_name[:10]
        rarity_text = "★" * result.rarity.value
        self.stdscr.addstr(y + 1, x + (box_width - len(name_text)) // 2, name_text)
        self.stdscr.addstr(y + 2, x + (box_width - len(rarity_text)) // 2, rarity_text)
        self.stdscr.attroff(curses.color_pair(color) | curses.A_BOLD)
        
        # 刷新屏幕
        self.stdscr.refresh()

    def draw_frame(self):
        max_y, max_x = self.stdscr.getmaxyx()
        self.stdscr.box()
        title = "★ 豪华抽卡模拟器 ★"
        self.stdscr.addstr(0, (max_x - len(title)) // 2, title)
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
                self.display_result(result)
            elif key == ord('0'):
                self.show_pull_animation()
                results = self.gacha.pull_multi(10)
                self.stdscr.clear()
                self.draw_frame()
                for i, result in enumerate(results):
                    self.display_result(result, i)
            
            time.sleep(0.05)  # 减少延迟

def main(stdscr):
    app = GachaTUI(stdscr)
    app.run()
