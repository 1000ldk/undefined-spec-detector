"""
処理タイプ分類器
自然言語の作業指示から処理タイプを判定する
"""
import re
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


class ActionType(Enum):
    """処理タイプ"""
    DELETE = "削除系"
    CREATE = "作成系"
    UPDATE = "更新系"
    DISPLAY = "表示系"
    AUTHENTICATION = "認証系"
    EXTERNAL_API = "外部連携系"
    DATA_MIGRATION = "データ移行系"
    BATCH_PROCESS = "バッチ処理系"
    SEARCH = "検索系"
    NOTIFICATION = "通知系"
    IMPORT_EXPORT = "インポート/エクスポート系"
    UNKNOWN = "不明"


@dataclass
class ClassificationResult:
    """分類結果"""
    action_type: ActionType
    confidence: float
    detected_entities: List[str]
    base_severity: str
    matched_keywords: List[str]
    context: str


# 各処理タイプの定義
ACTION_PATTERNS = {
    ActionType.DELETE: {
        "keywords": ["削除", "消す", "除去", "クリア", "消去", "廃棄", "破棄"],
        "critical_concerns": [
            "論理削除 vs 物理削除",
            "復元可能性",
            "カスケード削除の範囲",
            "削除権限",
            "削除ログ"
        ],
        "severity_multiplier": 1.5,
        "base_severity": "HIGH"
    },
    ActionType.CREATE: {
        "keywords": ["作成", "追加", "登録", "新規", "生成", "作る", "増やす"],
        "critical_concerns": [
            "必須項目の定義",
            "バリデーション",
            "重複チェック",
            "初期値設定"
        ],
        "severity_multiplier": 1.0,
        "base_severity": "MEDIUM"
    },
    ActionType.UPDATE: {
        "keywords": ["更新", "変更", "修正", "編集", "書き換え", "直す"],
        "critical_concerns": [
            "更新対象の特定方法",
            "部分更新 vs 全体更新",
            "更新権限",
            "更新履歴の記録"
        ],
        "severity_multiplier": 1.2,
        "base_severity": "MEDIUM"
    },
    ActionType.DISPLAY: {
        "keywords": ["表示", "見る", "確認", "一覧", "詳細", "閲覧", "ビュー", "画面"],
        "critical_concerns": [
            "表示件数の上限",
            "ページネーション",
            "ソート順",
            "0件時の表示"
        ],
        "severity_multiplier": 0.7,
        "base_severity": "LOW"
    },
    ActionType.AUTHENTICATION: {
        "keywords": ["認証", "ログイン", "ログアウト", "サインイン", "パスワード", "トークン"],
        "critical_concerns": [
            "認証方式（JWT, Session, etc）",
            "トークンの有効期限",
            "トークン保存場所",
            "セッション管理"
        ],
        "severity_multiplier": 1.8,
        "base_severity": "CRITICAL"
    },
    ActionType.EXTERNAL_API: {
        "keywords": ["API", "連携", "外部", "LINE", "Slack", "Twitter", "Google", "呼び出し"],
        "critical_concerns": [
            "タイムアウト設定",
            "リトライ戦略",
            "認証情報の管理",
            "エラー時のフォールバック"
        ],
        "severity_multiplier": 1.4,
        "base_severity": "HIGH"
    },
    ActionType.DATA_MIGRATION: {
        "keywords": ["移行", "マイグレーション", "データ移動", "インポート", "変換"],
        "critical_concerns": [
            "データ量の見積もり",
            "ロールバック方法",
            "バリデーション",
            "既存データの扱い"
        ],
        "severity_multiplier": 1.6,
        "base_severity": "HIGH"
    },
    ActionType.BATCH_PROCESS: {
        "keywords": ["バッチ", "定期", "一括", "夜間", "スケジュール"],
        "critical_concerns": [
            "実行タイミング",
            "処理時間の見積もり",
            "エラー時の通知",
            "再実行の方法"
        ],
        "severity_multiplier": 1.3,
        "base_severity": "MEDIUM"
    },
    ActionType.SEARCH: {
        "keywords": ["検索", "探す", "フィルタ", "絞り込み", "サーチ"],
        "critical_concerns": [
            "検索対象フィールド",
            "部分一致 vs 完全一致",
            "検索パフォーマンス",
            "0件時の表示"
        ],
        "severity_multiplier": 0.9,
        "base_severity": "MEDIUM"
    },
    ActionType.NOTIFICATION: {
        "keywords": ["通知", "メール", "アラート", "お知らせ", "送信"],
        "critical_concerns": [
            "通知タイミング",
            "送信失敗時の処理",
            "通知の重複防止",
            "通知設定のON/OFF"
        ],
        "severity_multiplier": 1.1,
        "base_severity": "MEDIUM"
    },
    ActionType.IMPORT_EXPORT: {
        "keywords": ["エクスポート", "ダウンロード", "CSV", "Excel", "インポート", "アップロード"],
        "critical_concerns": [
            "ファイル形式",
            "ファイルサイズ上限",
            "エラー行の扱い",
            "文字コード"
        ],
        "severity_multiplier": 1.2,
        "base_severity": "MEDIUM"
    }
}


class ActionTypeClassifier:
    """処理タイプ分類器"""
    
    def __init__(self):
        self.patterns = ACTION_PATTERNS
    
    def classify(self, text: str) -> ClassificationResult:
        """
        テキストから処理タイプを分類
        
        Args:
            text: 分類対象のテキスト
            
        Returns:
            ClassificationResult: 分類結果
        """
        # 各タイプのマッチングスコアを計算
        scores = {}
        matched_keywords = {}
        
        for action_type, pattern in self.patterns.items():
            score = 0
            matched = []
            
            for keyword in pattern["keywords"]:
                if keyword in text:
                    score += 1
                    matched.append(keyword)
            
            if score > 0:
                scores[action_type] = score
                matched_keywords[action_type] = matched
        
        # 最もスコアが高いタイプを選択
        if not scores:
            return ClassificationResult(
                action_type=ActionType.UNKNOWN,
                confidence=0.0,
                detected_entities=self._extract_entities(text),
                base_severity="LOW",
                matched_keywords=[],
                context=text
            )
        
        best_type = max(scores.items(), key=lambda x: x[1])[0]
        max_score = scores[best_type]
        
        # 信頼度の計算（マッチしたキーワード数に基づく）
        confidence = min(max_score / 3.0, 1.0)  # 3つ以上で100%
        
        # エンティティ抽出
        entities = self._extract_entities(text)
        
        return ClassificationResult(
            action_type=best_type,
            confidence=confidence,
            detected_entities=entities,
            base_severity=self.patterns[best_type]["base_severity"],
            matched_keywords=matched_keywords[best_type],
            context=text
        )
    
    def _extract_entities(self, text: str) -> List[str]:
        """エンティティを抽出（簡易実装）"""
        entities = []
        
        # よく使われる名詞を抽出
        common_entities = [
            'ユーザー', 'ユーザ', '商品', 'カート', '注文', '決済',
            'アカウント', 'プロフィール', '投稿', 'コメント', '画像',
            'ファイル', 'データ', '情報', 'レコード', 'アイテム'
        ]
        
        for entity in common_entities:
            if entity in text:
                entities.append(entity)
        
        return entities
    
    def get_critical_concerns(self, action_type: ActionType) -> List[str]:
        """
        処理タイプの重要な確認事項を取得
        
        Args:
            action_type: 処理タイプ
            
        Returns:
            重要な確認事項のリスト
        """
        if action_type in self.patterns:
            return self.patterns[action_type]["critical_concerns"]
        return []
    
    def get_severity_multiplier(self, action_type: ActionType) -> float:
        """
        処理タイプの危険度倍率を取得
        
        Args:
            action_type: 処理タイプ
            
        Returns:
            危険度倍率
        """
        if action_type in self.patterns:
            return self.patterns[action_type]["severity_multiplier"]
        return 1.0



