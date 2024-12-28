import math
import random
from typing import List, Tuple
import numpy as np
from scipy import stats
from scipy.special import binom  # 添加这一行
from gacha import GachaSystem, ItemType, ItemRarity

class GachaAnalysis:
    def __init__(self):
        self.base_five_star_prob = 0.006
        self.base_four_star_prob = 0.051
        self.step_up = 73
        self.step_end = 90

    def _calc_single_prob(self, pull_count: int) -> float:
        """计算单抽概率"""
        if pull_count < self.step_up:
            return self.base_five_star_prob
        elif pull_count >= self.step_end:
            return 1.0
        else:
            progress = (pull_count - self.step_up) / (self.step_end - self.step_up)
            return self.base_five_star_prob + (1 - self.base_five_star_prob) * progress

    def calculate_multi_pull_probs_theory(self) -> dict:
        """理论计算十连抽的概率分布（不考虑概率提升）"""
        p = self.base_five_star_prob
        q = 1 - p
        
        # 无五星概率：所有抽都不是五星
        p_none = q ** 10
        
        # 一个五星概率：选择1个位置是五星，其他都不是
        p_one = binom(10, 1) * p * (q ** 9)
        
        # 两个五星概率：选择2个位置是五星，其他都不是
        p_two = binom(10, 2) * (p ** 2) * (q ** 8)
        
        # 三个及以上五星概率
        p_more = 1 - p_none - p_one - p_two
        
        return {
            "无五星": p_none,
            "一个五星": p_one,
            "两个五星": p_two,
            "三个及以上五星": p_more
        }

    def _calculate_pity_sequence(self, total_pulls: int) -> List[float]:
        """计算考虑保底的概率序列"""
        probs = []
        for i in range(1, total_pulls + 1):
            if i < self.step_up:
                probs.append(self.base_five_star_prob)
            elif i >= self.step_end:
                probs.append(1.0)
            else:
                progress = (i - self.step_up) / (self.step_end - self.step_up)
                prob = self.base_five_star_prob + (1 - self.base_five_star_prob) * progress
                probs.append(prob)
        return probs

    def prob_before_pity(self) -> dict:
        """计算在概率提升前出金的概率"""
        prob_not_get = 1
        total_prob = 0
        
        for i in range(1, self.step_up):
            prob_get = prob_not_get * self.base_five_star_prob
            total_prob += prob_get
            prob_not_get *= (1 - self.base_five_star_prob)
        
        return {
            "概率提升前出金": total_prob,
            "到达概率提升": prob_not_get
        }

    def limited_prob_for_pulls(self, max_pulls: int = 170) -> dict:
        """计算不同抽数获得限定五星的概率（考虑多金）"""
        results = {}
        for pulls in range(10, max_pulls + 1, 10):
            # 使用动态规划计算概率
            prob = self._calculate_limited_dp(pulls)
            results[pulls] = prob
        return results

    def _calculate_limited_dp(self, total_pulls: int) -> float:
        """使用动态规划计算获得限定的概率"""
        # dp[i][j][k][l] 表示：
        # i: 当前抽数
        # j: 获得的限定数量
        # k: 当前是否在大保底(0:小保底, 1:大保底)
        # l: 距离上次五星的抽数(0-89)
        dp = [[[[0.0 for _ in range(90)] for _ in range(2)] 
               for _ in range(total_pulls + 1)] for _ in range(total_pulls + 1)]
        
        # 初始状态：0抽，0个限定，小保底，0抽距离
        dp[0][0][0][0] = 1.0
        
        for i in range(total_pulls):
            for j in range(i + 1):
                for k in range(2):
                    for l in range(90):
                        if dp[i][j][k][l] == 0:
                            continue
                            
                        # 计算当前抽的五星概率
                        current_prob = self._calc_single_prob(l + 1)
                        
                        # 没抽到五星：距离+1
                        if l + 1 < 90:  # 除非到达90抽保底
                            dp[i+1][j][k][l+1] += dp[i][j][k][l] * (1 - current_prob)
                        
                        # 抽到五星：距离重置为0
                        if k == 0:  # 小保底
                            # 抽到限定：限定数+1，保持小保底
                            dp[i+1][j+1][0][0] += dp[i][j][k][l] * current_prob * 0.5
                            # 抽到常驻：进入大保底
                            dp[i+1][j][1][0] += dp[i][j][k][l] * current_prob * 0.5
                        else:  # 大保底
                            # 必定是限定：限定数+1，回到小保底
                            dp[i+1][j+1][0][0] += dp[i][j][k][l] * current_prob
        
        # 统计所有抽到至少一个限定的概率
        total_prob = 0
        for j in range(1, total_pulls + 1):
            for k in range(2):
                for l in range(90):
                    total_prob += dp[total_pulls][j][k][l]
        
        return total_prob

    def expected_pulls_theory(self) -> float:
        """理论计算期望抽数（考虑保底）"""
        # 计算73抽之前的期望
        exp_before_pity = 0
        prob_not_get = 1
        for i in range(1, self.step_up):
            prob_get = prob_not_get * self.base_five_star_prob
            exp_before_pity += i * prob_get
            prob_not_get *= (1 - self.base_five_star_prob)
        
        # 计算73-90抽的期望
        exp_during_pity = 0
        for i in range(self.step_up, self.step_end + 1):
            current_prob = self._calc_single_prob(i)
            prob_get = prob_not_get * current_prob
            exp_during_pity += i * prob_get
            prob_not_get *= (1 - current_prob)
        
        # 计算限定角色的期望（考虑大小保底）
        basic_exp = exp_before_pity + exp_during_pity
        return basic_exp * 1.5  # 考虑50/50的影响
    
    def prob_distribution_by_pulls(self) -> dict:
        """计算不同抽数获得限定五星的理论概率"""
        results = {}
        for pulls in range(10, 171, 10):
            prob = self._calculate_limited_dp(pulls)  # 直接使用动态规划方法
            results[pulls] = prob
        return results
    
    # 删除 _calculate_limited_prob_theory 函数，因为它的功能已经被 _calculate_limited_dp 完全替代

    def experimental_verification(self, num_trials: int = 1000000) -> dict:
        """使用实际抽卡系统进行实验验证"""
        gacha = GachaSystem()
        results = {
            'total_pulls': 0,
            'five_star_count': 0,
            'five_star_positions': [],  # 记录每个五星出现的位置
            'four_star_count': 0,
            'limited_five_star_count': 0
        }
        
        for _ in range(num_trials):
            result = gacha.pull()
            results['total_pulls'] += 1
            
            if result.rarity == ItemRarity.FIVE_STAR:
                results['five_star_count'] += 1
                results['five_star_positions'].append(results['total_pulls'])
                if result.item_type == ItemType.LIMITED:
                    results['limited_five_star_count'] += 1
            elif result.rarity == ItemRarity.FOUR_STAR:
                results['four_star_count'] += 1
        
        return results

    def compare_theory_and_practice(self, experimental_data: dict) -> dict:
        """比较理论值和实验值"""
        total_pulls = experimental_data['total_pulls']
        
        # 计算实验概率
        actual_five_star_rate = experimental_data['five_star_count'] / total_pulls
        actual_four_star_rate = experimental_data['four_star_count'] / total_pulls
        actual_limited_rate = experimental_data['limited_five_star_count'] / total_pulls
        
        # 计算理论概率
        theory_five_star_rate = self.base_five_star_prob
        theory_four_star_rate = self.base_four_star_prob
        theory_limited_rate = self.base_five_star_prob * 0.75  # 考虑大小保底的综合概率
        
        return {
            '实验五星率': actual_five_star_rate,
            '理论五星率': theory_five_star_rate,
            '实验四星率': actual_four_star_rate,
            '理论四星率': theory_four_star_rate,
            '实验限定率': actual_limited_rate,
            '理论限定率': theory_limited_rate,
            '五星误差': abs(actual_five_star_rate - theory_five_star_rate) / theory_five_star_rate,
            '四星误差': abs(actual_four_star_rate - theory_four_star_rate) / theory_four_star_rate,
            '限定误差': abs(actual_limited_rate - theory_limited_rate) / theory_limited_rate
        }

if __name__ == "__main__":
    analyzer = GachaAnalysis()
    
    print("\n=== 理论概率分析 ===")
    print("十连抽概率分布：")
    theory_probs = analyzer.calculate_multi_pull_probs_theory()
    for result, prob in theory_probs.items():
        print(f"{result}: {prob:.2%}")
    
    print("\n期望抽数（考虑保底）：")
    expected = analyzer.expected_pulls_theory()
    print(f"抽出限定五星的理论期望抽数: {expected:.2f}")
    
    print("\n不同抽数获得限定的理论概率：")
    prob_dist = analyzer.prob_distribution_by_pulls()
    for pulls, prob in prob_dist.items():
        print(f"{pulls}抽: {prob:.2%}")
    
    print("\n=== 实验验证 ===")
    experimental_data = analyzer.experimental_verification(1000000)
    comparison = analyzer.compare_theory_and_practice(experimental_data)
    
    print("\n理论与实验对比：")
    for metric, value in comparison.items():
        print(f"{metric}: {value:.4%}")
