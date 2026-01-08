"""
新しいアーキテクチャのクイックテスト
"""
import sys
sys.path.insert(0, 'src')

from usd.coordinator import AnalysisCoordinator

# テストケース
test_input = """
ユーザーを削除する機能を作る
"""

print("=" * 60)
print("未定義要素検出器 v2.0 - コンテキスト駆動型テスト")
print("=" * 60)
print()

coordinator = AnalysisCoordinator()
report = coordinator.analyze(test_input)

print("\n" + "=" * 60)
print("✅ テスト完了！")
print("=" * 60)
print(f"\n処理タイプ: {report['action_classification']['action_type'] if report.get('action_classification') else 'N/A'}")
print(f"未定義要素数: {report['undefined_elements']['total']}")
print(f"致命度別:")
if 'by_criticality' in report['undefined_elements']:
    crit = report['undefined_elements']['by_criticality']
    print(f"  🔴 着手不可: {crit.get('must_define', 0)}件")
    print(f"  🟡 要確認: {crit.get('should_confirm', 0)}件")
    print(f"  🟢 後決めOK: {crit.get('can_decide_later', 0)}件")

print(f"\n総合評価: {report['executive_summary']['overall_assessment']}")

# 最初の未定義要素を表示
if report['undefined_elements']['elements']:
    print(f"\n【最初の未定義要素】")
    elem = report['undefined_elements']['elements'][0]
    print(f"タイトル: {elem['title']}")
    if elem.get('criticality'):
        crit = elem['criticality']
        print(f"致命度: {crit.get('level', 'N/A')}")
        print(f"確認先: {crit.get('who_to_ask', 'N/A')}")



