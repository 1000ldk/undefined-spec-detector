"""
CLI: コマンドラインインターフェース
"""
import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from usd.coordinator import AnalysisCoordinator


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    未定義要素検出器 (Undefined Spec Detector)
    
    要件や仕様から未定義要素を自動検出します。
    """
    pass


@cli.command()
@click.option('--input', '-i', type=click.Path(exists=True), required=True,
              help='入力ファイル（要件文書）')
@click.option('--output', '-o', type=click.Path(), 
              help='出力ファイル（結果レポート）')
@click.option('--format', '-f', type=click.Choice(['json', 'markdown', 'text']),
              default='text', help='出力形式')
def analyze(input, output, format):
    """要件文書を分析する"""
    
    # ファイルを読み込み
    input_path = Path(input)
    console.print(f"\n📂 入力ファイル: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    console.print(f"📄 文書サイズ: {len(content)}文字\n")
    
    # 分析実行
    coordinator = AnalysisCoordinator()
    
    with console.status("[bold green]分析中...", spinner="dots"):
        report = coordinator.analyze(content)
    
    # 結果の表示
    _display_report(report, format)
    
    # ファイルに出力
    if output:
        output_path = Path(output)
        _save_report(report, output_path, format)
        console.print(f"\n✅ レポートを保存しました: {output_path}")


def _display_report(report: dict, format_type: str):
    """レポートを表示"""
    
    if format_type == 'json':
        console.print_json(data=report)
        return
    
    # テキスト/Markdown形式
    console.print("\n" + "="*60)
    console.print(Panel.fit(
        "[bold cyan]分析レポート[/bold cyan]",
        border_style="cyan"
    ))
    console.print("="*60 + "\n")
    
    # エグゼクティブサマリー
    summary = report['executive_summary']
    console.print("[bold]📊 エグゼクティブサマリー[/bold]")
    console.print(f"  総合評価: [bold]{summary['overall_assessment']}[/bold]")
    console.print(f"  未定義要素: [yellow]{summary['total_undefined']}件[/yellow]")
    if summary['high_risk_count'] > 0:
        console.print(f"  高リスク: [red]{summary['high_risk_count']}件[/red]")
    console.print()
    
    if summary['key_findings']:
        console.print("[bold]🔍 主な発見事項[/bold]")
        for finding in summary['key_findings']:
            console.print(f"  • {finding}")
        console.print()
    
    # 解析結果
    parsing = report['parsing_result']
    console.print("[bold]📝 解析結果[/bold]")
    console.print(f"  文章数: {parsing['sentences']}文")
    console.print(f"  エンティティ: {parsing['entities']}個")
    console.print(f"  アクション: {parsing['actions']}個")
    console.print(f"  完全度スコア: {parsing['statistics']['avg_completeness']:.2f}")
    console.print(f"  曖昧さスコア: {parsing['statistics']['avg_ambiguity']:.2f}")
    console.print()
    
    # 未定義要素
    undefined = report['undefined_elements']
    
    if undefined['by_category']:
        console.print("[bold]📋 カテゴリ別未定義要素[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("カテゴリ", style="cyan")
        table.add_column("件数", justify="right")
        
        for category, count in undefined['by_category'].items():
            table.add_row(category, str(count))
        
        console.print(table)
        console.print()
    
    # 未定義要素の詳細（上位5件）
    if undefined['elements']:
        console.print("[bold]⚠️  未定義要素（上位5件）[/bold]\n")
        
        for i, elem in enumerate(undefined['elements'][:5], 1):
            severity_color = {
                'critical': 'red',
                'high': 'red',
                'medium': 'yellow',
                'low': 'green'
            }.get(elem['severity'], 'white')
            
            console.print(f"[bold]{i}. {elem['title']}[/bold]")
            console.print(f"   カテゴリ: {elem['category']} / {elem['subcategory']}")
            console.print(f"   重要度: [{severity_color}]{elem['severity'].upper()}[/{severity_color}]")
            console.print(f"   説明: {elem['description']}")
            
            if elem['questions']:
                console.print("   質問:")
                for q in elem['questions'][:3]:
                    console.print(f"     • {q}")
            console.print()
    
    # 推奨事項
    meta = report['meta_analysis']
    if meta.get('recommendations'):
        console.print("[bold]💡 推奨事項[/bold]")
        for rec in meta['recommendations']:
            console.print(f"  • {rec}")
        console.print()


def _save_report(report: dict, output_path: Path, format_type: str):
    """レポートをファイルに保存"""
    
    if format_type == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    elif format_type == 'markdown':
        markdown_content = _generate_markdown_report(report)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    else:  # text
        with open(output_path, 'w', encoding='utf-8') as f:
            # 簡易的なテキスト出力
            f.write(f"分析レポート\n")
            f.write(f"生成日時: {report['generated_at']}\n\n")
            f.write(f"未定義要素: {report['executive_summary']['total_undefined']}件\n")


def _generate_markdown_report(report: dict) -> str:
    """Markdown形式のレポートを生成"""
    lines = []
    
    lines.append("# 分析レポート")
    lines.append(f"\n**生成日時**: {report['generated_at']}")
    lines.append(f"**レポートID**: {report['report_id']}\n")
    
    lines.append("## エグゼクティブサマリー\n")
    summary = report['executive_summary']
    lines.append(f"- **総合評価**: {summary['overall_assessment']}")
    lines.append(f"- **未定義要素**: {summary['total_undefined']}件")
    if summary['high_risk_count'] > 0:
        lines.append(f"- **高リスク**: {summary['high_risk_count']}件")
    
    if summary['key_findings']:
        lines.append("\n### 主な発見事項\n")
        for finding in summary['key_findings']:
            lines.append(f"- {finding}")
    
    lines.append("\n## 未定義要素一覧\n")
    for i, elem in enumerate(report['undefined_elements']['elements'], 1):
        lines.append(f"### {i}. {elem['title']}\n")
        lines.append(f"- **カテゴリ**: {elem['category']} / {elem['subcategory']}")
        lines.append(f"- **重要度**: {elem['severity'].upper()}")
        lines.append(f"- **説明**: {elem['description']}")
        
        if elem['questions']:
            lines.append("\n**質問**:")
            for q in elem['questions']:
                lines.append(f"- {q}")
        lines.append("")
    
    meta = report['meta_analysis']
    if meta.get('recommendations'):
        lines.append("\n## 推奨事項\n")
        for rec in meta['recommendations']:
            lines.append(f"- {rec}")
    
    return "\n".join(lines)


def main():
    """CLIのエントリーポイント"""
    cli()


if __name__ == '__main__':
    main()

