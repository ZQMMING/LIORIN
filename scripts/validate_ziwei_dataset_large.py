"""紫微斗数数据集验证工具 v7 - 运行更大规模验证"""

import json
import os
import subprocess
from pathlib import Path


DATASET_PATH = Path(r'E:\顺天资料\紫薇案例\ziwei-doushu-dataset\ziwei-samples-toolkit\sample-preview')


def load_sample(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_filename(filepath):
    basename = os.path.basename(filepath).replace('.json', '')
    parts = basename.split('-')
    return {
        'year': int(parts[0]),
        'month': int(parts[1]),
        'day': int(parts[2]),
        'hour': int(parts[3][1:]),
        'gender': parts[4],
    }


def extract_reference(sample):
    chart = sample['chart']
    raw_palaces = chart.get('palaces', [])
    if isinstance(raw_palaces, list):
        palaces_dict = {p.get('name', ''): p for p in raw_palaces}
    else:
        palaces_dict = raw_palaces or {}
    
    return {
        'wuxing_ju_name': chart.get('wuxingJuName', ''),
        'ming_gong_branch': chart.get('mingGongBranch', -1),
        'shen_gong_branch': chart.get('shenGongBranch', -1),
        'palaces': palaces_dict,
    }


def get_iztro_result(year, month, day, hour, gender):
    gender_js = '男' if gender == 'male' else '女'
    script = f'''
    const {{ bySolar }} = require('iztro').astro;
    const a = bySolar('{year}-{month}-{day}', {hour}, '{gender_js}', true, 'zh-CN');
    console.log(JSON.stringify({{
        soul: a.earthlyBranchOfSoulPalace,
        body: a.earthlyBranchOfBodyPalace,
        wuxing: a.fiveElementsClass,
    }}));
    '''
    proc = subprocess.run(['node', '-e', script], capture_output=True, text=True, encoding='utf-8')
    return json.loads(proc.stdout)


BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']


def validate_one(reference, result):
    checks = {}
    all_pass = True
    
    # 五行局
    ref_wx = reference['wuxing_ju_name']
    eng_wx = result['wuxing']
    wx_ok = ref_wx == eng_wx
    checks['wuxing'] = {'ref': ref_wx, 'engine': eng_wx, 'pass': wx_ok}
    if not wx_ok: all_pass = False
    
    # 命宫
    ref_ming = BRANCHES[reference['ming_gong_branch']] if 0 <= reference['ming_gong_branch'] < 12 else ''
    eng_ming = result['soul']
    ming_ok = ref_ming == eng_ming
    checks['ming'] = {'ref': ref_ming, 'engine': eng_ming, 'pass': ming_ok}
    if not ming_ok: all_pass = False
    
    # 身宫
    ref_shen = BRANCHES[reference['shen_gong_branch']] if 0 <= reference['shen_gong_branch'] < 12 else ''
    eng_shen = result['body']
    shen_ok = ref_shen == eng_shen
    checks['shen'] = {'ref': ref_shen, 'engine': eng_shen, 'pass': shen_ok}
    if not shen_ok: all_pass = False
    
    return all_pass, checks


def main():
    sample_files = sorted(DATASET_PATH.glob('**/*.json'))
    print(f'Total samples: {len(sample_files)}')
    
    # 随机抽样 100 个
    import random
    random.seed(42)
    samples = random.sample(sample_files, min(100, len(sample_files)))
    
    passed = 0
    failed = 0
    errors = []
    
    for i, filepath in enumerate(samples):
        try:
            sample = load_sample(str(filepath))
            reference = extract_reference(sample)
            time_info = parse_filename(str(filepath))
            
            result = get_iztro_result(
                time_info['year'], time_info['month'], time_info['day'],
                time_info['hour'], time_info['gender']
            )
            
            ok, checks = validate_one(reference, result)
            
            if ok:
                passed += 1
            else:
                failed += 1
                errors.append({
                    'file': filepath.name,
                    'checks': {k: v for k, v in checks.items() if not v['pass']},
                })
            
            if (i + 1) % 20 == 0:
                print(f'Progress: {i+1}/{len(samples)} ({passed} passed, {failed} failed)')
        
        except Exception as e:
            failed += 1
            errors.append({'file': filepath.name, 'error': str(e)})
    
    print(f'\n=== 验证结果 (100 samples) ===')
    print(f'总计: {len(samples)}')
    print(f'通过: {passed}')
    print(f'失败: {failed}')
    print(f'通过率: {passed/len(samples)*100:.1f}%')
    
    if errors:
        print(f'\n失败示例 (前10个):')
        for err in errors[:10]:
            print(f'  - {err["file"]}')
            if 'checks' in err:
                for check, detail in err['checks'].items():
                    print(f'    {check}: ref={detail["ref"]}, engine={detail["engine"]}')
            elif 'error' in err:
                print(f'    Error: {err["error"]}')


if __name__ == '__main__':
    main()
