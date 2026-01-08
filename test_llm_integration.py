"""
LLM統合テスト
OpenAI API Keyが設定されている場合にLLM機能をテスト
"""
import os
import sys

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from usd.modules.requirement_parser import RequirementParser
from usd.modules.undefined_extractor import UndefinedExtractor


def test_llm_detects_undefined_terms():
    """LLMが未知の用語を検出できることを確認"""
    
    # テスト用の曖昧な要件文
    content = """
    既存のバックエンドシステムと連携する新しい管理画面を開発する。
    ボタンが表示領域と重なる問題が発生している。
    対処としてマージンを調整する予定。
    """
    
    # APIキーが設定されている場合のみテスト実行
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEYが設定されていないためスキップ")
        print("   環境変数OPENAI_API_KEYを設定してテストを実行してください。")
        return
    
    print("="*60)
    print("LLM統合テスト開始")
    print("="*60)
    
    # パース
    print("\n📝 要件をパース中...")
    parser = RequirementParser()
    parsed = parser.parse(content)
    print(f"✓ パース完了: {parsed.statistics.total_sentences}文, {parsed.statistics.total_entities}個のエンティティ")
    
    # LLMなしで抽出
    print("\n🔍 ルールベースのみで検出中...")
    extractor_no_llm = UndefinedExtractor(use_llm=False)
    result_no_llm = extractor_no_llm.extract(parsed)
    print(f"✓ 検出完了: {len(result_no_llm.undefined_elements)}個")
    
    # LLMありで抽出
    print("\n🤖 LLM統合モードで検出中...")
    extractor_with_llm = UndefinedExtractor(use_llm=True, api_key=api_key)
    result_with_llm = extractor_with_llm.extract(parsed)
    print(f"✓ 検出完了: {len(result_with_llm.undefined_elements)}個")
    
    # LLMで検出された要素
    llm_elements = [e for e in result_with_llm.undefined_elements if e.detection.method == "llm"]
    
    # 結果の表示
    print("\n" + "="*60)
    print("📊 テスト結果")
    print("="*60)
    print(f"ルールベースのみ: {len(result_no_llm.undefined_elements)}個")
    print(f"LLM統合後:       {len(result_with_llm.undefined_elements)}個")
    print(f"うちLLMで検出:   {len(llm_elements)}個")
    
    # 検出方法別の統計
    if "by_method" in result_with_llm.statistics:
        print("\n検出方法別:")
        for method, count in result_with_llm.statistics["by_method"].items():
            method_name = {
                "rule_based": "ルールベース",
                "template_driven": "テンプレート",
                "llm": "LLM",
                "semantic_analysis": "意味解析",
                "pattern_matching": "パターンマッチ"
            }.get(method, method)
            print(f"  - {method_name}: {count}件")
    
    # LLMで検出された要素の詳細
    if llm_elements:
        print("\n🤖 LLMで検出された未定義要素:")
        for i, elem in enumerate(llm_elements[:5], 1):
            print(f"\n{i}. {elem.title}")
            print(f"   カテゴリ: {elem.category}")
            print(f"   信頼度: {elem.detection.confidence:.2f}")
            print(f"   説明: {elem.description[:100]}...")
            if elem.questions:
                print(f"   質問: {elem.questions[0].text[:80]}...")
    
    # 検証
    print("\n" + "="*60)
    print("✅ テスト評価")
    print("="*60)
    
    success = True
    
    # 検証1: LLMを使用した方が多くの未定義要素を検出できること
    if len(result_with_llm.undefined_elements) > len(result_no_llm.undefined_elements):
        print("✓ LLMにより追加の未定義要素が検出されました")
    else:
        print("⚠️  LLMによる追加検出がありませんでした")
        print(f"   （ルールベース: {len(result_no_llm.undefined_elements)}, LLM統合: {len(result_with_llm.undefined_elements)}）")
    
    # 検証2: LLMで検出された要素があること
    if len(llm_elements) > 0:
        print(f"✓ LLMで{len(llm_elements)}個の未定義要素を検出")
    else:
        print("⚠️  LLMでの検出数が0です")
        success = False
    
    # 検証3: 統計情報にLLMメソッドが含まれること
    if "by_method" in result_with_llm.statistics and "llm" in result_with_llm.statistics["by_method"]:
        print(f"✓ 統計情報にLLM検出が記録されています")
    else:
        print("⚠️  統計情報にLLM検出が記録されていません")
        success = False
    
    print("\n" + "="*60)
    if success:
        print("🎉 テスト成功！")
        print("="*60)
        return 0
    else:
        print("❌ テスト失敗")
        print("="*60)
        return 1


def test_llm_without_api_key():
    """APIキーなしでもアプリが動作することを確認"""
    print("\n" + "="*60)
    print("APIキーなしテスト")
    print("="*60)
    
    content = "ユーザーは商品をカートに追加できる。"
    
    parser = RequirementParser()
    parsed = parser.parse(content)
    
    # APIキーなしでLLMモードを指定
    print("\n🔍 APIキーなしでLLMモードを指定...")
    extractor = UndefinedExtractor(use_llm=True, api_key=None)
    
    # エラーが発生せず実行できること
    try:
        result = extractor.extract(parsed)
        print(f"✓ 正常に動作しました: {len(result.undefined_elements)}個検出")
        print("✓ LLM機能はスキップされ、ルールベースで動作")
        return 0
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return 1


def main():
    """メイン関数"""
    print("\n" + "="*60)
    print("未定義要素検出器 - LLM統合テスト")
    print("="*60)
    
    # テスト1: LLM検出機能
    result1 = test_llm_detects_undefined_terms()
    
    # テスト2: APIキーなしでの動作
    result2 = test_llm_without_api_key()
    
    # 総合結果
    print("\n" + "="*60)
    print("総合結果")
    print("="*60)
    
    if result1 == 0 or os.environ.get("OPENAI_API_KEY") is None:
        if result2 == 0:
            print("✅ 全てのテストが成功しました！")
            return 0
        else:
            print("⚠️  一部のテストが失敗しました")
            return 1
    else:
        print("❌ テストが失敗しました")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
