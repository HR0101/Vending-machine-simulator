from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd
from collections import Counter
import json

app = Flask(__name__, template_folder='templates', static_folder='static')

# ===== データ定義 =====
MACHINES = {
    '六号館前': {
        '上段': [
            ('天然水', 120), ('天然水', 120), ('天然水', 120),
            ('やさしい麦茶', 140), ('やさしい麦茶', 140),
            ('京都レモネード', 180), ('京都レモネード', 180),
            ('伊右衛門', 150), ('伊右衛門', 150),
            ('特茶', 190),
            ('ZONe（赤缶エナジー）', 200), ('ZONe（赤缶エナジー）', 200)
        ],
        '中段': [
            ('ミステリー', 240),
            ('クラフトボス フルーツティー', 180),
            ('クラフトボス 贅沢ミルクティー', 180), ('クラフトボス 贅沢ミルクティー', 180),
            ('クラフトボス ラテ', 180), ('クラフトボス ラテ', 180),
            ('クラフトボス ブラック', 180), ('クラフトボス ブラック', 180),
            ('GREENDAKAEAスポドリ', 150),
            ('Wビタミン（ビタミンウォーター）', 170),
            ('Red Bull', 210),
            ('Red Bullノンシュガー', 210)
        ],
        '下段': [
            ('天然水うるTHE果実（オレンジ）', 180), ('天然水うるTHE果実（オレンジ）', 180),
            ('天然水キリッとヨーグルト', 180),
            ('梅ソルティ', 160),
            ('ジンジャーエール', 160),
            ('マスカットサイダー', 160),
            ('飲むヨーグレット', 160),
            ('BOSS WILD', 120), ('BOSS WILD', 120),
            ('NOPE', 120),
            ('Mountain Dew', 140),
            ('デカビタ', 140)
        ]
    },
    '四号館七階': {
        '上段': [
            ('ミステリー', 220),
            ('やさしい麦茶', 140),
            ('クラフトボス 贅沢ミルクティー', 180),
            ('天然水うるTHE果実', 180),
            ('きりっとヨーグルト', 180),
            ('マスカットサイダー', 170),
            ('C.C.レモン', 170), ('C.C.レモン', 170),
            ('ジンジャーエール', 170), ('ジンジャーエール', 170),
            ('天然水', 120), ('天然水', 120)
        ],
        '中段': [
            ('天然水', 110),
            ('Red Bull', 210), ('Red Bull', 210),
            ('ペプシ リフレッシュショット', 140),
            ('デカビタC', 140), ('デカビタC', 140),
            ('NOPE', 120), ('NOPE', 120),
            ('ペプシコーラ〈生〉', 140), ('ペプシコーラ〈生〉', 140),
            ('Mountain Dew', 140), ('Mountain Dew', 140)
        ],
        '下段': [
            ('BOSS 贅沢微糖', 130),
            ('BOSS カフェオレ', 130),
            ('BLACK BOSS（無糖）', 130),
            ('牛乳とバナナ', 140),
            ('BOSS WILD', 120),
            ('いちごミルク', 140),
            ('クラフトボス ラテ', 160),
            ('ライチ＆ヨーグルト', 140), ('ライチ＆ヨーグルト', 140),
            ('スーパービックル', 160),
            ('飲むヨーグレット', 150),
            ('飲むぶどうゼリー', 150)
        ]
    },
    '七号館横': {
        '上段': [
            ('天然水', 120), ('天然水', 120), ('天然水', 120),
            ('キリッと天然水果実', 180),
            ('ピングレソルティ', 150),
            ('やさしい麦茶', 130), ('やさしい麦茶', 130),
            ('緑茶（生茶／伊右衛門）', 150), ('緑茶（生茶／伊右衛門）', 150),
            ('ZONe', 200),
            ('MONSTER', 220),
            ('Red Bull', 210)
        ],
        '中段': [
            ('ミステリー', 240),
            ('ジンジャーエール', 170), ('ジンジャーエール', 170),
            ('マスカットサイダー', 170),
            ('濃いぶどう', 170),
            ('アミノサプリドリンク', 140),
            ('ライムソルト', 160),
            ('クラフトミルクティー', 180),
            ('クラフトフルーツティー', 180), ('クラフトフルーツティー', 180),
            ('FRUIT T-S（フルーツティー）', 170), ('FRUIT T-S（フルーツティー）', 170)
        ],
        '下段': [
            ('カルピスウォーター', 150), ('カルピスウォーター', 150),
            ('フルーツアイスティー白ぶどうとレモン', 170),
            ('MATCH', 160), ('MATCH', 160),
            ('MATCHミニ', 140),
            ('デカビタC', 140), ('デカビタC', 140),
            ('Mountain Dew', 140), ('Mountain Dew', 140),
            ('飲むヨーグレット', 150),
            ('BOSS WILD', 150)
        ]
    }
}


# ===== ユーティリティ関数 =====
def get_all_products(machine_name):
    """指定された自販機の全商品を取得（ミステリー除外）"""
    products = []
    for shelf in MACHINES[machine_name].values():
        for item in shelf:
            if item[0] != 'ミステリー':
                products.append(item)
    return products


def get_mystery_price(machine_name):
    """指定された自販機のミステリー価格を取得"""
    for shelf in MACHINES[machine_name].values():
        for item in shelf:
            if item[0] == 'ミステリー':
                return item[1]
    return None


def build_layout(machine_name):
    """指定された自販機の実機配置（上段・中段・下段／左→右）を構造化して返す"""
    layout = {}
    for shelf_name, items in MACHINES[machine_name].items():
        layout[shelf_name] = [
            {'name': name, 'price': int(price), 'is_mystery': name == 'ミステリー'}
            for name, price in items
        ]
    return layout


def simulate_once(machine_name):
    """1回のミステリー実行シミュレーション"""
    products = get_all_products(machine_name)
    selected = np.random.choice(len(products), 2, replace=True)
    item1, item2 = products[selected[0]], products[selected[1]]
    mystery_price = get_mystery_price(machine_name)
    total_value = item1[1] + item2[1]
    profit = total_value - mystery_price

    return {
        'item1': item1[0],
        'price1': int(item1[1]),
        'item2': item2[0],
        'price2': int(item2[1]),
        'total': int(total_value),
        'profit': int(profit),
        'roi': round(profit / mystery_price * 100, 2)
    }


def run_simulation(machine_name, num_trials):
    """複数回のシミュレーション実行"""
    products = get_all_products(machine_name)
    mystery_price = get_mystery_price(machine_name)
    results = []

    for _ in range(num_trials):
        selected = np.random.choice(len(products), 2, replace=True)
        item1, item2 = products[selected[0]], products[selected[1]]
        total_value = item1[1] + item2[1]
        profit = total_value - mystery_price

        results.append({
            'item1': item1[0],
            'price1': int(item1[1]),
            'item2': item2[0],
            'price2': int(item2[1]),
            'total': int(total_value),
            'profit': int(profit),
            'roi': round(profit / mystery_price * 100, 2)
        })

    return results


def calculate_statistics(results):
    """統計情報の計算"""
    if not results:
        return {}

    profits = [r['profit'] for r in results]
    totals = [r['total'] for r in results]
    rois = [r['roi'] for r in results]

    return {
        'avg_total': round(np.mean(totals), 2),
        'avg_profit': round(np.mean(profits), 2),
        'avg_roi': round(np.mean(rois), 2),
        'max_profit': int(np.max(profits)),
        'min_profit': int(np.min(profits)),
        'std_dev': round(np.std(profits), 2),
        'loss_rate': round(sum(1 for p in profits if p < 0) / len(profits) * 100, 2)
    }


def get_profit_distribution(results, bins=10):
    """利益分布のヒストグラムデータ"""
    profits = [r['profit'] for r in results]
    hist, bin_edges = np.histogram(profits, bins=bins)
    return {
        'labels': [f'{int(bin_edges[i])}-{int(bin_edges[i+1])}' for i in range(len(bin_edges)-1)],
        'data': hist.tolist()
    }


def get_top_combinations(results, top_n=10):
    """最も出現しやすい組み合わせトップN"""
    combinations = []
    for r in results:
        combo = tuple(sorted([r['item1'], r['item2']]))
        combinations.append(combo)

    counter = Counter(combinations)
    top_combos = counter.most_common(top_n)

    return {
        'labels': [f"{c[0][0]}\n+\n{c[0][1]}" for c in top_combos],
        'data': [c[1] for c in top_combos],
        'full_labels': [f"{c[0][0]} + {c[0][1]}" for c in top_combos]
    }


def get_product_appearance_rate(results, top_n=15):
    """各商品の出現確率"""
    all_products = []
    for r in results:
        all_products.append(r['item1'])
        all_products.append(r['item2'])

    counter = Counter(all_products)
    top_products = counter.most_common(top_n)

    return {
        'labels': [p[0] for p in top_products],
        'data': [round(p[1] / len(all_products) * 100, 2) for p in top_products],
        'counts': [p[1] for p in top_products]
    }


def get_profit_bracket_distribution(results):
    """利益帯別の確率分布"""
    brackets = {
        '大赤字 (-∞～-200)': sum(1 for r in results if r['profit'] < -200),
        '赤字 (-200～-1)': sum(1 for r in results if -200 <= r['profit'] < 0),
        'ほぼ等価 (-1～50)': sum(1 for r in results if 0 <= r['profit'] < 50),
        '黒字 (50～200)': sum(1 for r in results if 50 <= r['profit'] < 200),
        '大黒字 (200～)': sum(1 for r in results if r['profit'] >= 200)
    }

    total = len(results)
    return {
        'labels': list(brackets.keys()),
        'data': [round(v / total * 100, 2) for v in brackets.values()],
        'counts': list(brackets.values())
    }


# ===== Flask ルート =====
@app.route('/')
def index():
    machines = list(MACHINES.keys())
    return render_template('index.html', machines=machines)


@app.route('/api/machines')
def get_machines():
    """自販機一覧"""
    return jsonify({
        'machines': list(MACHINES.keys()),
        'prices': {name: get_mystery_price(name) for name in MACHINES.keys()}
    })


@app.route('/api/layout', methods=['POST'])
def api_layout():
    """指定された自販機の実機配置を返す"""
    data = request.json
    machine_name = data.get('machine')

    if machine_name not in MACHINES:
        return jsonify({'error': 'Invalid machine'}), 400

    return jsonify({
        'machine': machine_name,
        'mystery_price': get_mystery_price(machine_name),
        'layout': build_layout(machine_name)
    })


@app.route('/api/simulate-once', methods=['POST'])
def api_simulate_once():
    """1回のシミュレーション"""
    data = request.json
    machine_name = data.get('machine')

    if machine_name not in MACHINES:
        return jsonify({'error': 'Invalid machine'}), 400

    result = simulate_once(machine_name)
    return jsonify(result)


@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    """大規模シミュレーション"""
    data = request.json
    machine_name = data.get('machine')
    num_trials = int(data.get('trials', 10000))

    if machine_name not in MACHINES:
        return jsonify({'error': 'Invalid machine'}), 400

    if num_trials < 100 or num_trials > 100000:
        return jsonify({'error': 'Trials must be between 100 and 100000'}), 400

    results = run_simulation(machine_name, num_trials)
    stats = calculate_statistics(results)
    profit_dist = get_profit_distribution(results, bins=20)
    top_combos = get_top_combinations(results, top_n=10)
    product_rate = get_product_appearance_rate(results, top_n=15)
    bracket_dist = get_profit_bracket_distribution(results)

    return jsonify({
        'machine': machine_name,
        'mystery_price': get_mystery_price(machine_name),
        'num_trials': num_trials,
        'statistics': stats,
        'profit_distribution': profit_dist,
        'top_combinations': top_combos,
        'product_appearance': product_rate,
        'bracket_distribution': bracket_dist
    })


@app.route('/api/comparison', methods=['POST'])
def api_comparison():
    """複数自販機の比較（各自販機の全分析を含む）"""
    data = request.json
    num_trials = int(data.get('trials', 5000))

    if num_trials < 100 or num_trials > 100000:
        return jsonify({'error': 'Trials must be between 100 and 100000'}), 400

    comparison = []   # サマリー比較表用
    machines = []     # 各自販機の詳細分析用

    for machine_name in MACHINES.keys():
        results = run_simulation(machine_name, num_trials)
        stats = calculate_statistics(results)

        # サマリー比較表用のデータ
        comparison.append({
            'machine': machine_name,
            'mystery_price': get_mystery_price(machine_name),
            **stats
        })

        # 各自販機の詳細分析データ（単機シミュレーションと同じ項目＋実機配置）
        machines.append({
            'machine': machine_name,
            'mystery_price': get_mystery_price(machine_name),
            'statistics': stats,
            'layout': build_layout(machine_name),
            'profit_distribution': get_profit_distribution(results, bins=20),
            'top_combinations': get_top_combinations(results, top_n=10),
            'product_appearance': get_product_appearance_rate(results, top_n=15),
            'bracket_distribution': get_profit_bracket_distribution(results)
        })

    return jsonify({
        'comparison': comparison,
        'machines': machines,
        'num_trials': num_trials
    })


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='127.0.0.1')
