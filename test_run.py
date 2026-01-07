"""
簡易テスト: サンプルデータでの動作確認
"""
from usd.schema import InputDocument
from usd.coordinator import AnalysisCoordinator


def test_sample_ec_cart():
    """ECサイトカート機能のサンプルで動作確認"""
    
    sample_content = """
# ECサイト カート機能の要件

## 機能要件

### カートへの追加
ユーザーは商品をカートに追加できる。
在庫がある場合のみ追加可能。

### カートの表示
ユーザーはカート内の商品一覧を確認できる。
商品名、価格、数量を表示する。

### 購入処理
ユーザーはカート内の商品を購入できる。
決済完了後、在庫から減算する。

## 非機能要件
- 高速に動作すること
- 安全に処理すること
"""
    
    print("="*60)
    print("未定義要素検出器 - 動作確認テスト")
    print("="*60)
    print()
    
    # 分析実行
    coordinator = AnalysisCoordinator()
    report = coordinator.analyze(sample_content)
    
    print("\n" + "="*60)
    print("テスト完了")
    print("="*60)
    print()
    print(f"✓ 未定義要素: {report['undefined_elements']['total']}個検出")
    print(f"✓ エンティティ: {report['parsing_result']['entities']}個抽出")
    print(f"✓ アクション: {report['parsing_result']['actions']}個抽出")
    print()
    
    # 結果の一部を表示
    print("検出された未定義要素（一部）:")
    for i, elem in enumerate(report['undefined_elements']['elements'][:3], 1):
        print(f"{i}. {elem['title']}")
        print(f"   カテゴリ: {elem['category']}")
        print(f"   質問数: {len(elem['questions'])}")
        print()
    
    return report


if __name__ == '__main__':
    test_sample_ec_cart()

