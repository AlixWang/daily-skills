#!/usr/bin/env python3
import sys, argparse

INTENT_WEIGHTS = {'transactional': 1.5, 'commercial': 1.2, 'informational': 0.8, 'navigational': 0.4}

def calculate_kd_roi(keyword, volume, kd, cpc=1.0, intent='transactional', dev_days=1.0):
    intent_mult = INTENT_WEIGHTS.get(intent.lower(), 1.0)
    effective_kd = max(1.0, float(kd))
    effective_days = max(0.5, float(dev_days))
    score = (float(volume) * float(cpc) * intent_mult) / (effective_kd * effective_days)
    if score >= 500:
        tag, rec = 'GOLD', '极高优先级（黄金小词/新词，立即开干）'
    elif score >= 150:
        tag, rec = 'RECOMMENDED', '高性价比（推荐作为 MVP 第一梯队落地页）'
    elif score >= 50:
        tag, rec = 'SECONDARY', '中等性价比（适合程序化 SEO 批量矩阵补充）'
    else:
        tag, rec = 'SKIP', '性价比低（竞争过大或搜索价值低，暂缓）'
    return {'keyword': keyword, 'volume': volume, 'kd': kd, 'cpc': cpc, 'score': round(score, 2), 'tag': tag, 'recommendation': rec}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--keyword', required=True)
    parser.add_argument('-v', '--volume', type=float, required=True)
    parser.add_argument('-d', '--kd', type=float, required=True)
    parser.add_argument('-c', '--cpc', type=float, default=1.0)
    parser.add_argument('-i', '--intent', default='transactional')
    parser.add_argument('-t', '--dev-days', type=float, default=1.0)
    args = parser.parse_args()
    res = calculate_kd_roi(args.keyword, args.volume, args.kd, args.cpc, args.intent, args.dev_days)
    print(res)
