"""紫微斗数数据集验证工具 v6 - 正确解析小时

关键修正：文件名中的 hHH 直接对应 birthInfo.hour，不需要转换。
- h00 -> hour=0
- h03 -> hour=3 (数据集实际存储值)
- h06 -> hour=6
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


DATASET_PATH = Path(r'E:\顺天资料\紫薇案例\ziwei-doushu-dataset\ziwei-samples-toolkit\sample-preview')


def load_sample(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_filename(filepath: str) -> dict:
    basename = os.path.basename(filepath).replace('.json', '')
    parts = basename.split('-')
    
    year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2])
    
    # hHH 直接对应小时（不是时辰索引）
    # h00 -> 0, h03 -> 3, h06 -> 6, ...
    hour = int(parts[3][1:])
    
    gender = parts[4]
    
    return {'year': year, 'month': month, 'day': day, 'hour': hour, 'gender': gender}


def extract_reference(sample: dict) -> dict:
    chart = sample['chart']
    
    raw_palaces = chart.get('palaces', [])
    if isinstance(raw_palaces, list):
        palaces_dict = {p.get('name', ''): p for p in raw_palaces}
    else:
        palaces_dict = raw_palaces or {}
    
    return {
        'wuxing_ju': chart.get('wuxingJu'),
        'wuxing_ju_name': chart.get('wuxingJuName', ''),
        'ming_gong_branch': chart.get('mingGongBranch', -1),
        'shen_gong_branch': chart.get('shenGongBranch', -1),
        'palaces': palaces_dict,
    }


def get_iztro_by_solar(year: int, month: int, day: int, hour: int, gender: str) -> dict:
    gender_js = '男' if gender == 'male' else '女'
    
    script = f'''
    const {{ bySolar }} = require('iztro').astro;
    const a = bySolar('{year}-{month}-{day}', {hour}, '{gender_js}', true, 'zh-CN');
    console.log(JSON.stringify({{
        soul: a.earthlyBranchOfSoulPalace,
        body: a.earthlyBranchOfBodyPalace,
        wuxing: a.fiveElementsClass,
        palaces: a.palaces.map(p => ({{
            name: p.name,
            branch: p.earthlyBranch,
            major: (p.majorStars||[]).map(s=>s.name),
            minor: (p.minorStars||[]).map(s=>s.name),
        }}))
    }}));
    '''
    
    proc = subprocess.run(['node', '-e', script], capture_output=True, text=True, encoding='utf-8')
    return json.loads(proc.stdout)


BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']


def validate_sample(reference: dict, iztro_result: dict) -> dict:
    results = {'pass': True, 'checks': {}}
    
    # 1. 五行局
    ref_wx = reference.get('wuxing_ju_name', '')
    eng_wx = iztro_result.get('wuxing', '')
    wx_ok = ref_wx == eng_wx
    results['checks']['wuxing_ju'] = {'ref': ref_wx, 'engine': eng_wx, 'pass': wx_ok}
    if not wx_ok: results['pass'] = False
    
    # 2. 命宫地支
    ref_ming_idx = reference.get('ming_gong_branch', -1)
    ref_ming = BRANCHES[ref_ming_idx] if 0 <= ref_ming_idx < 12 else ''
    eng_ming = iztro_result.get('soul', '')
    ming_ok = ref_ming == eng_ming
    results['checks']['ming_gong'] = {'ref': ref_ming, 'engine': eng_ming, 'pass': ming_ok}
    if not ming_ok: results['pass'] = False
    
    # 3. 身宫地支
    ref_shen_idx = reference.get('shen_gong_branch', -1)
    ref_shen = BRANCHES[ref_shen_idx] if 0 <= ref_shen_idx < 12 else ''
    eng_shen = iztro_result.get('body', '')
    shen_ok = ref_shen == eng_shen
    results['checks']['shen_gong'] = {'ref': ref_shen, 'engine': eng_shen, 'pass': shen_ok}
    if not shen_ok: results['pass'] = False
    
    # 4. 命宫主星
    ref_ming_p = reference.get('palaces', {}).get('命宫', {})
    if isinstance(ref_ming_p, dict):
        ref_stars = [s.get('name', '') for s in ref_ming_p.get('stars', []) if s.get('type') == 'major']
        eng_palace = None
        for p in iztro_result.get('palaces', []):
            if p.get('name') == '命宫':
                eng_palace = p
                break
        if eng_palace:
            eng_stars = eng_palace.get('major', [])
            stars_ok = ref_stars[:3] == eng_stars[:3]
            results['checks']['ming_stars'] = {'ref': ref_stars[:3], 'engine': eng_stars[:3], 'pass': stars_ok}
            if not stars_ok: results['pass'] = False
    
    return results


def run_validation(sample_count: int = 50):
    sample_files = sorted(DATASET_PATH.glob('**/*.json'))[:sample_count]
    
    passed = 0
    failed = 0
    errors = []
    
    for i, filepath in enumerate(sample_files):
        try:
            sample = load_sample(str(filepath))
            reference = extract_reference(sample)
            time_info = parse_filename(str(filepath))
            
            iztro_result = get_iztro_by_solar(
                time_info['year'],
                time_info['month'],
                time_info['day'],
                time_info['hour'],
                time_info['gender'],
            )
            
            result = validate_sample(reference, iztro_result)
            
            if result['pass']:
                passed += 1
            else:
                failed += 1
                errors.append({
                    'index': i,
                    'filepath': filepath.name,
                    'failures': {k: v for k, v in result['checks'].items() if not v['pass']},
                })
            
            if (i + 1) % 10 == 0:
                print(f'Progress: {i+1}/{len(sample_files)} ({passed} passed, {failed} failed)')
        
        except Exception as e:
            failed += 1
            errors.append({
                'index': i,
                'filepath': filepath.name,
                'error': str(e),
            })
    
    return {
        'total': len(sample_files),
        'passed': passed,
        'failed': failed,
        'pass_rate': passed / len(sample_files) if sample_files else 0,
        'errors': errors,
    }


if __name__ == '__main__':
    result = run_validation(50)
    print(f'\n=== 验证结果 ===')
    print(f'总计: {result["total"]}')
    print(f'通过: {result["passed"]}')
    print(f'失败: {result["failed"]}')
    print(f'通过率: {result["pass_rate"]:.1%}')
    
    if result['errors']:
        print(f'\n失败示例 (前5个):')
        for err in result['errors'][:5]:
            print(f'  - {err["filepath"]}')
            if 'failures' in err:
                for check, detail in err['failures'].items():
                    print(f'    {check}: ref={detail["ref"]}, engine={detail["engine"]}')
            elif 'error' in err:
                print(f'    Error: {err["error"]}')
