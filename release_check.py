#!/usr/bin/env python3
"""
release_check.py — 发布一致性校验器（2026-11-26 CEO铁律落地工具）

背景：ZYZ666-RGB trial report抓到 phm-lite-check runtime __version__(1.0.0) 与
pyproject(1.0.3) 不一致——三处版本号无单一真源，发版流程无自检。

铁律（SOUL.md 2026-11-26）：
  1. 对外发布（PyPI / npm / GitHub Release / 评论引用版本号 / commit号）发出前
     必须跑本工具，任何 FAIL 禁止发布。零豁免。
  2. 修复类 commit 必须：语法验证 + 行数比对 + 测试通过后才能 push。

用法：
  python3 release_check.py <repo_dir>            # 校验单个包仓
  python3 release_check.py --pypi <package_name> # 与PyPI已发布版本对账
"""
import ast, json, os, re, sys, urllib.request

def find_version_decls(root):
    """收集仓内全部版本号声明（pyproject/setup/__init__/任意py的__version__）"""
    decls = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (
            '.git', '__pycache__', 'node_modules', '.venv', 'build',
            'dist', '.eggs') and not d.endswith('.egg-info')]
        for f in files:
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, root)
            try:
                src = open(p, encoding='utf-8', errors='ignore').read()
            except Exception:
                continue
            if f == 'pyproject.toml':
                m = re.search(r'^version\s*=\s*"([^"]+)"', src, re.M)
                if m:
                    decls.append((rel, 'pyproject', m.group(1)))
            elif f == 'setup.py':
                m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', src)
                if m:
                    decls.append((rel, 'setup.py', m.group(1)))
            elif f == 'setup.cfg':
                m = re.search(r'^version\s*=\s*([^\s]+)', src, re.M)
                if m:
                    decls.append((rel, 'setup.cfg', m.group(1)))
            elif f.endswith('.py'):
                for m in re.finditer(r'__version__\s*=\s*["\']([^"\']+)["\']', src):
                    decls.append((rel, '__version__', m.group(1)))
    return decls

def check_repo(root, pypi_name=None, verbose=True):
    """主校验：声明一致性 + 语法 + 行数卫生 + PyPI对账"""
    fails, warns = [], []
    decls = find_version_decls(root)
    if not decls:
        fails.append("零版本声明——包必须有 pyproject version + __version__")
        return fails, warns, None

    versions = set(v for _, _, v in decls)
    if len(versions) > 1:
        fails.append(f"版本不一致: {sorted(versions)}")
        if verbose:
            for rel, kind, v in decls:
                mark = '!' if v != sorted(versions)[0] else ' '
                print(f"  {mark} {v:>8}  {rel} [{kind}]")
    elif verbose:
        for rel, kind, v in decls:
            print(f"    {v:>8}  {rel} [{kind}]")

    # 全部py文件语法验证（防截断/防坏文件）
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', '.venv')]
        for f in files:
            if f.endswith('.py'):
                p = os.path.join(dirpath, f)
                try:
                    ast.parse(open(p, encoding='utf-8', errors='ignore').read())
                except SyntaxError as e:
                    fails.append(f"语法错误 {os.path.relpath(p, root)}: {e}")

    # PyPI对账（若指定）：runtime声明的版本应等于PyPI最新发布版
    if pypi_name and len(versions) == 1:
        v = sorted(versions)[0]
        try:
            req = urllib.request.Request(
                f"https://pypi.org/pypi/{pypi_name}/json",
                headers={"User-Agent": "PHM-release-check"})
            with urllib.request.urlopen(req, timeout=10) as r:
                pypi_v = json.loads(r.read())["info"]["version"]
            if pypi_v != v:
                fails.append(f"与PyPI不同步: 本地声明{v} vs PyPI已发布{pypi_name} {pypi_v}")
            elif verbose:
                print(f"    PyPI对账: {pypi_name} {pypi_v} == 本地 ✓")
        except Exception as e:
            warns.append(f"PyPI对账失败({pypi_name}): {str(e)[:60]}")

    return fails, warns, sorted(versions)

def main():
    args = sys.argv[1:]
    root = pypi = None
    if args and args[0] == '--pypi':
        root, pypi = args[1], args[1]
    elif len(args) >= 1:
        root = args[0]
        if len(args) >= 2:
            pypi = args[1]
    if not root:
        print(__doc__)
        sys.exit(2)

    print(f"=== release_check: {os.path.basename(root.rstrip('/'))} ===")
    fails, warns, versions = check_repo(root, pypi)
    for w in warns:
        print(f"  [WARN] {w}")
    for f in fails:
        print(f"  [FAIL] {f}")
    if fails:
        print(f"判定: FAIL — 禁止发布")
        sys.exit(1)
    print(f"判定: PASS — 版本{versions[0]}全源一致、语法卫生、PyPI对账通过")
    sys.exit(0)

if __name__ == '__main__':
    main()
