# simple toy gacha

测试Copilot的能力。

## 使用方法

```bash
python main.py
```
进行抽卡模拟

```bash
python analysis.py
```

检查抽卡模型是否符合概率计算。

items.json的格式为：
```json
{
    "limited_five_star": [
        "AAAAA"
    ],
    "five_star": [
        "BBBB",
        "CCCC",
        "DDDD"
    ],
    "limited_four_star": [
        "EEEE",
        "FFFF",
        "GGGG"
    ],
    "four_star": [
        "HHH",
        "III",
        "JJJ"
    ],
    "three_star": [
        "KKK",
        "LLL",
        "MMM"
    ]
}
```