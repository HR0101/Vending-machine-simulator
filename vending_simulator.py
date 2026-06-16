import streamlit as st
import pandas as pd
import numpy as np
from itertools import combinations_with_replacement
from collections import Counter
import matplotlib.pyplot as plt
import japanize_matplotlib

# 日本語フォント対応
plt.rcParams['font.sans-serif'] = ['Hiragino Kaku Gothic ProN', 'Yu Gothic', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

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


def simulate_mystery(machine_name):
    """1回のミステリー実行シミュレーション"""
    products = get_all_products(machine_name)
    selected = np.random.choice(len(products), 2, replace=True)
    item1, item2 = products[selected[0]], products[selected[1]]
    return item1, item2


def run_simulation(machine_name, num_trials):
    """複数回のシミュレーション実行"""
    results = []
    products = get_all_products(machine_name)
    mystery_price = get_mystery_price(machine_name)

    for _ in range(num_trials):
        selected = np.random.choice(len(products), 2, replace=True)
        item1, item2 = products[selected[0]], products[selected[1]]
        total_value = item1[1] + item2[1]
        profit = total_value - mystery_price

        results.append({
            '商品1': item1[0],
            '価格1': item1[1],
            '商品2': item2[0],
            '価格2': item2[1],
            '合計価格': total_value,
            '利益': profit,
            'ROI': (profit / mystery_price * 100)
        })

    return pd.DataFrame(results)


def calculate_statistics(df):
    """統計情報の計算"""
    mystery_price = df['合計価格'].mean() - df['利益'].mean()

    stats = {
        'ミステリー代金': mystery_price,
        '平均獲得価格': df['合計価格'].mean(),
        '平均利益': df['利益'].mean(),
        '平均ROI': df['ROI'].mean(),
        '最高利益': df['利益'].max(),
        '最低利益': df['利益'].min(),
        '標準偏差': df['利益'].std(),
        '赤字確率': (df['利益'] < 0).sum() / len(df) * 100
    }
    return stats


def get_top_combinations(df, top_n=10):
    """最も出現しやすい組み合わせトップN"""
    df['組み合わせ'] = df.apply(
        lambda x: f"{x['商品1']} + {x['商品2']}"
        if x['商品1'] <= x['商品2']
        else f"{x['商品2']} + {x['商品1']}",
        axis=1
    )
    return df['組み合わせ'].value_counts().head(top_n)


def get_product_appearance_rate(df):
    """各商品の出現確率"""
    all_products = list(df['商品1']) + list(df['商品2'])
    return pd.Series(all_products).value_counts(normalize=True).head(15)


# ===== Streamlit UI =====
st.set_page_config(page_title='自販機ミステリーシミュレーター', layout='wide', initial_sidebar_state='expanded')
st.title('🥤 自販機ミステリーシミュレーター')

# サイドバー設定
st.sidebar.markdown('## ⚙️ シミュレーション設定')
machine_name = st.sidebar.selectbox('自販機を選択', list(MACHINES.keys()))
num_trials = st.sidebar.slider('試行回数', 100, 100000, 10000, step=100)

# ===== メインコンテンツ =====
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown(f'### 選択中: {machine_name}')
    mystery_price = get_mystery_price(machine_name)
    st.info(f'ミステリー代金: **{mystery_price}円**')

    if st.button('🎲 1回シミュレーション実行', use_container_width=True, key='single'):
        item1, item2 = simulate_mystery(machine_name)
        total_value = item1[1] + item2[1]
        profit = total_value - mystery_price

        st.success('✅ 出ました!')
        st.markdown(f'''
        **商品1:** {item1[0]} ({item1[1]}円)
        **商品2:** {item2[0]} ({item2[1]}円)
        ---
        **合計価格:** {total_value}円
        **利益:** {profit:+}円 ({profit/mystery_price*100:+.1f}%)
        ''')

# ===== 大規模シミュレーション =====
st.markdown('---')
st.markdown('## 📊 大規模シミュレーション結果')

if st.button('🚀 シミュレーション開始', use_container_width=True, key='simulation'):
    with st.spinner(f'{num_trials:,}回のシミュレーション中...'):
        df = run_simulation(machine_name, num_trials)

    st.success(f'✅ {num_trials:,}回のシミュレーション完了!')

    # 統計情報
    st.markdown('### 📈 統計情報')
    stats = calculate_statistics(df)

    metric_col = st.columns(4)
    metric_col[0].metric('平均獲得価格', f"{stats['平均獲得価格']:.1f}円")
    metric_col[1].metric('平均利益', f"{stats['平均利益']:+.1f}円")
    metric_col[2].metric('平均ROI', f"{stats['平均ROI']:+.1f}%")
    metric_col[3].metric('赤字確率', f"{stats['赤字確率']:.1f}%")

    st.metric('利益の標準偏差', f"{stats['標準偏差']:.1f}円")

    # 分布グラフ
    st.markdown('### 📉 利益分布')
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(df['利益'], bins=50, color='#2b6cb0', alpha=0.7, edgecolor='black')
    ax.axvline(df['利益'].mean(), color='red', linestyle='--', linewidth=2, label=f'平均: {df["利益"].mean():.1f}円')
    ax.axvline(0, color='orange', linestyle='--', linewidth=2, label='損益分岐点')
    ax.set_xlabel('利益（円）')
    ax.set_ylabel('出現回数')
    ax.set_title(f'{machine_name} - 利益分布 ({num_trials:,}回)')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    st.pyplot(fig, use_container_width=True)

    # 最も出現しやすい組み合わせ
    st.markdown('### 🏆 最も出現しやすい組み合わせ TOP 10')
    top_combos = get_top_combinations(df)

    fig, ax = plt.subplots(figsize=(10, 6))
    top_combos.plot(kind='barh', ax=ax, color='#c53030')
    ax.set_xlabel('出現回数')
    ax.set_title('組み合わせ出現ランキング')
    ax.grid(axis='x', alpha=0.3)
    st.pyplot(fig, use_container_width=True)

    # 各商品の出現確率
    st.markdown('### 📦 各商品の出現確率 TOP 15')
    product_rate = get_product_appearance_rate(df)

    fig, ax = plt.subplots(figsize=(10, 6))
    product_rate.plot(kind='barh', ax=ax, color='#38a169')
    ax.set_xlabel('出現確率 (%)')
    ax.set_title('商品出現確率ランキング')
    ax.grid(axis='x', alpha=0.3)
    for i, v in enumerate(product_rate * 100):
        ax.text(v + 0.5, i, f'{v:.1f}%', va='center', fontsize=9)
    st.pyplot(fig, use_container_width=True)

    # 利益帯別の確率
    st.markdown('### 💰 利益帯別の確率分布')
    profit_bins = [-500, -200, 0, 100, 200, 500, 1000]
    profit_distribution = pd.cut(df['利益'], bins=profit_bins).value_counts(normalize=True).sort_index() * 100

    fig, ax = plt.subplots(figsize=(10, 4))
    profit_distribution.plot(kind='bar', ax=ax, color='#9f7aea')
    ax.set_xlabel('利益帯（円）')
    ax.set_ylabel('確率 (%)')
    ax.set_title('利益帯別の出現確率')
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    st.pyplot(fig, use_container_width=True)

    # 複数自販機の比較
    st.markdown('### 🔄 複数自販機の比較分析')
    if st.checkbox('他の自販機との比較を表示'):
        comparison_data = []
        for mname in MACHINES.keys():
            mdf = run_simulation(mname, 5000)
            mstats = calculate_statistics(mdf)
            comparison_data.append({
                '自販機': mname,
                'ミステリー価格': mstats['ミステリー代金'],
                '平均利益': mstats['平均利益'],
                'ROI': mstats['平均ROI'],
                '赤字確率': mstats['赤字確率']
            })

        comp_df = pd.DataFrame(comparison_data)
        st.dataframe(comp_df, use_container_width=True)

        fig, ax = plt.subplots(figsize=(10, 4))
        comp_df.set_index('自販機')['平均利益'].plot(kind='bar', ax=ax, color=['#2b6cb0', '#c53030', '#38a169'])
        ax.set_ylabel('平均利益（円）')
        ax.set_title('自販機別の平均利益比較')
        ax.grid(axis='y', alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig, use_container_width=True)

    # 詳細データのダウンロード
    st.markdown('### 📥 詳細データ')
    st.dataframe(df.head(20), use_container_width=True)

    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label='📊 CSVでダウンロード',
        data=csv_data,
        file_name=f'{machine_name}_simulation_{num_trials}.csv',
        mime='text/csv'
    )

st.markdown('---')
st.caption('Created with Streamlit | 自販機ミステリーシミュレーター')
