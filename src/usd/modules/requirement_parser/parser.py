"""
Module 1: Requirement Parser
要件文書を解析して構造化する
"""
import re
from typing import List, Dict, Any
from datetime import datetime
import uuid

from usd.schema import (
    ParsedRequirement,
    Sentence,
    Entity,
    Action,
    Requirement,
    Statistics,
    Attribute,
    Mention,
    Condition,
    ErrorHandling,
    Priority,
    InputDocument,
)


class RequirementParser:
    """要件文書を解析するメインクラス"""
    
    def __init__(self):
        """初期化"""
        self.version = "1.0.0"
        # 簡易的な実装: spacyは後で追加可能
        
    def parse(self, input_doc: InputDocument) -> ParsedRequirement:
        """
        要件文書を解析する
        
        Args:
            input_doc: 入力文書
        
        Returns:
            解析結果（構造化データ）
        """
        document_id = self._generate_id()
        content = input_doc.content
        
        # 1. 文章分割
        sentences = self._extract_sentences(content)
        
        # 2. エンティティ抽出（簡易実装）
        entities = self._extract_entities(content, sentences)
        
        # 3. アクション抽出
        actions = self._extract_actions(content, sentences, entities)
        
        # 4. 要件の評価
        requirements = self._evaluate_requirements(sentences, entities, actions)
        
        # 5. 統計情報の計算
        statistics = self._calculate_statistics(sentences, entities, actions, requirements)
        
        return ParsedRequirement(
            document_id=document_id,
            parsed_at=datetime.now(),
            parser_version=self.version,
            original_content=content,
            metadata=input_doc.metadata,
            sentences=sentences,
            entities=entities,
            actions=actions,
            requirements=requirements,
            statistics=statistics
        )
    
    def _generate_id(self) -> str:
        """ID生成"""
        return f"DOC-{uuid.uuid4().hex[:8].upper()}"
    
    def _extract_sentences(self, content: str) -> List[Sentence]:
        """文章を分割"""
        sentences = []
        lines = content.split('\n')
        
        char_pos = 0
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                char_pos += len(line) + 1
                continue
            
            # 簡易的な文分割（。で分割）
            sub_sentences = [s.strip() for s in line.split('。') if s.strip()]
            
            for sub_sent in sub_sentences:
                sent_id = f"S-{len(sentences) + 1:03d}"
                sentence = Sentence(
                    id=sent_id,
                    text=sub_sent,
                    line_number=line_num,
                    start_char=char_pos,
                    end_char=char_pos + len(sub_sent),
                    type=self._classify_sentence_type(sub_sent),
                    importance=Priority.MEDIUM
                )
                sentences.append(sentence)
                char_pos += len(sub_sent) + 1
        
        return sentences
    
    def _classify_sentence_type(self, text: str) -> str:
        """文の種類を分類"""
        if any(word in text for word in ['できる', '可能', 'する']):
            return "requirement"
        elif any(word in text for word in ['とする', 'こと', '必要']):
            return "constraint"
        elif any(word in text for word in ['例えば', 'など']):
            return "example"
        else:
            return "explanation"
    
    def _extract_entities(self, content: str, sentences: List[Sentence]) -> List[Entity]:
        """エンティティを抽出（簡易実装）"""
        entities_dict: Dict[str, Entity] = {}
        
        # よく出現する名詞をエンティティとして抽出
        # 簡易的なパターンマッチング
        common_nouns = [
            'ユーザー', 'ユーザ', '利用者', '商品', '製品', 'アイテム',
            'カート', 'データ', '情報', '価格', '金額', '在庫',
            '注文', 'オーダー', '決済', '購入', 'システム', 'サービス',
            'パスワード', 'メール', 'アカウント', 'ログイン'
        ]
        
        entity_counter = 0
        for noun in common_nouns:
            if noun in content:
                entity_counter += 1
                entity_id = f"E-{entity_counter:03d}"
                
                # メンションを探す
                mentions = []
                for sent in sentences:
                    if noun in sent.text:
                        pos = sent.text.find(noun)
                        mentions.append(Mention(
                            sentence_id=sent.id,
                            text=noun,
                            position=pos
                        ))
                
                # エンティティタイプの推定
                entity_type = self._infer_entity_type(noun)
                
                entity = Entity(
                    id=entity_id,
                    name=noun,
                    type=entity_type,
                    mentions=mentions,
                    definition_status="undefined",  # デフォルトは未定義
                    ambiguity_score=0.7  # デフォルトスコア
                )
                
                entities_dict[noun] = entity
        
        return list(entities_dict.values())
    
    def _infer_entity_type(self, noun: str) -> str:
        """エンティティタイプを推定"""
        actor_keywords = ['ユーザー', 'ユーザ', '利用者', '管理者', 'オペレーター']
        object_keywords = ['商品', '製品', 'アイテム', 'カート', '注文']
        data_keywords = ['データ', '情報', '価格', '金額', '在庫']
        system_keywords = ['システム', 'サービス', 'アプリ']
        
        if noun in actor_keywords:
            return "actor"
        elif noun in object_keywords:
            return "object"
        elif noun in data_keywords:
            return "data"
        elif noun in system_keywords:
            return "system"
        else:
            return "object"
    
    def _extract_actions(
        self, 
        content: str, 
        sentences: List[Sentence],
        entities: List[Entity]
    ) -> List[Action]:
        """アクションを抽出"""
        actions = []
        
        # 動詞のパターン
        action_patterns = [
            (r'(.+?)は(.+?)を(.+?)できる', 3),  # 主語-目的語-動詞
            (r'(.+?)を(.+?)する', 2),  # 目的語-動詞
        ]
        
        action_counter = 0
        for sent in sentences:
            text = sent.text
            
            # パターンマッチング
            for pattern, _ in action_patterns:
                match = re.search(pattern, text)
                if match:
                    action_counter += 1
                    action_id = f"A-{action_counter:03d}"
                    
                    # 簡易的な動詞抽出
                    verb = self._extract_verb(text)
                    subject_entity = self._find_entity(match.group(1) if match.lastindex >= 1 else "", entities)
                    object_entity = self._find_entity(match.group(2) if match.lastindex >= 2 else "", entities)
                    
                    # 条件の抽出
                    preconditions = self._extract_conditions(text)
                    
                    # エラーハンドリングの有無
                    has_error_handling = any(word in text for word in ['エラー', '失敗', 'できない', '不可'])
                    
                    action = Action(
                        id=action_id,
                        verb=verb,
                        subject=subject_entity if subject_entity else "UNKNOWN",
                        object=object_entity,
                        preconditions=preconditions,
                        error_handling=ErrorHandling(
                            mentioned=has_error_handling,
                            defined=False  # 簡易実装では常にFalse
                        )
                    )
                    actions.append(action)
                    break
        
        return actions
    
    def _extract_verb(self, text: str) -> str:
        """動詞を抽出"""
        verb_patterns = ['追加', '削除', '変更', '確認', '表示', '登録', '更新', '取得', '送信', '実行']
        for verb in verb_patterns:
            if verb in text:
                return verb
        return "処理"
    
    def _find_entity(self, text: str, entities: List[Entity]) -> str:
        """テキストからエンティティを見つける"""
        for entity in entities:
            if entity.name in text:
                return entity.id
        return None
    
    def _extract_conditions(self, text: str) -> List[Condition]:
        """条件を抽出"""
        conditions = []
        
        # 「〜場合」「〜とき」などのパターン
        condition_patterns = [
            r'(.+?)場合',
            r'(.+?)とき',
            r'(.+?)際',
        ]
        
        for pattern in condition_patterns:
            match = re.search(pattern, text)
            if match:
                cond_text = match.group(1).strip()
                condition = Condition(
                    description=cond_text,
                    type="precondition",
                    defined=False,  # 具体的な判定方法が不明
                    ambiguous=True,  # デフォルトで曖昧と判定
                    entities=[]
                )
                conditions.append(condition)
        
        return conditions
    
    def _evaluate_requirements(
        self,
        sentences: List[Sentence],
        entities: List[Entity],
        actions: List[Action]
    ) -> List[Requirement]:
        """要件を評価"""
        requirements = []
        
        req_counter = 0
        for sent in sentences:
            if sent.type == "requirement":
                req_counter += 1
                req_id = f"REQ-{req_counter:03d}"
                
                # 完全度スコアの計算（簡易）
                completeness = self._calculate_completeness(sent.text, entities, actions)
                
                # 曖昧さスコアの計算
                ambiguity = self._calculate_ambiguity(sent.text)
                
                # 欠けている要素
                missing = self._identify_missing_elements(sent.text)
                
                requirement = Requirement(
                    id=req_id,
                    text=sent.text,
                    type="functional",  # 簡易実装
                    completeness_score=completeness,
                    ambiguity_score=ambiguity,
                    missing_elements=missing
                )
                requirements.append(requirement)
        
        return requirements
    
    def _calculate_completeness(
        self,
        text: str,
        entities: List[Entity],
        actions: List[Action]
    ) -> float:
        """完全度スコアを計算"""
        score = 0.0
        checks = 0
        
        # エンティティが定義されているか
        has_entity = any(e.name in text for e in entities)
        if has_entity:
            score += 0.3
        checks += 1
        
        # 動詞があるか
        has_verb = any(v in text for v in ['できる', 'する', '表示', '追加'])
        if has_verb:
            score += 0.3
        checks += 1
        
        # 条件が明確か
        has_condition = '場合' in text or 'とき' in text
        if has_condition:
            # 条件があるが詳細不明な場合は低スコア
            score += 0.1
        checks += 1
        
        # エラーハンドリングの言及
        has_error = any(w in text for w in ['エラー', '失敗', 'できない'])
        if has_error:
            score += 0.2
        checks += 1
        
        return min(score, 1.0)
    
    def _calculate_ambiguity(self, text: str) -> float:
        """曖昧さスコアを計算"""
        score = 0.0
        
        # 曖昧な形容詞
        vague_adjectives = ['速い', '遅い', '高速', '大きい', '小さい', '多い', '少ない', '適切', '十分']
        for adj in vague_adjectives:
            if adj in text:
                score += 0.2
        
        # 曖昧な副詞
        vague_adverbs = ['すぐに', '速やかに', '適宜', '随時', '定期的']
        for adv in vague_adverbs:
            if adv in text:
                score += 0.2
        
        # 条件が曖昧
        if ('場合' in text or 'とき' in text) and not any(w in text for w in ['=', '>', '<', '以上', '以下']):
            score += 0.3
        
        return min(score, 1.0)
    
    def _identify_missing_elements(self, text: str) -> List[str]:
        """欠けている要素を特定"""
        missing = []
        
        if 'できる' in text and 'できない' not in text and 'エラー' not in text:
            missing.append("エラー時の挙動")
        
        if any(w in text for w in ['追加', '登録', '保存']) and '削除' not in text:
            missing.append("削除機能の有無")
        
        if any(w in text for w in ['データ', '情報', '値']) and not any(w in text for w in ['型', 'フォーマット', '形式']):
            missing.append("データ型・形式")
        
        return missing
    
    def _calculate_statistics(
        self,
        sentences: List[Sentence],
        entities: List[Entity],
        actions: List[Action],
        requirements: List[Requirement]
    ) -> Statistics:
        """統計情報を計算"""
        avg_completeness = 0.0
        avg_ambiguity = 0.0
        
        if requirements:
            avg_completeness = sum(r.completeness_score for r in requirements) / len(requirements)
            avg_ambiguity = sum(r.ambiguity_score for r in requirements) / len(requirements)
        
        return Statistics(
            total_sentences=len(sentences),
            total_entities=len(entities),
            total_relationships=0,  # 簡易実装では0
            total_actions=len(actions),
            avg_completeness_score=round(avg_completeness, 2),
            avg_ambiguity_score=round(avg_ambiguity, 2)
        )



