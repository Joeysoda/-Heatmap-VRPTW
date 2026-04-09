"""
路径验证脚本 - 检查AnyLogic和Python之间的路径配置
"""

import os
import sys

def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60)

def check_path(path, description):
    """检查路径是否存在"""
    exists = os.path.exists(path)
    status = "✓" if exists else "✗"
    print(f"{status} {description}")
    print(f"  路径: {path}")
    if exists:
        print(f"  状态: 存在")
    else:
        print(f"  状态: 不存在 (将自动创建)")
    return exists

def main():
    print_header("AnyLogic-Python 路径验证工具")
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"\n当前脚本目录: {script_dir}")
    
    # 定义路径
    bridge_dir = os.path.join(script_dir, 'anylogic_bridge')
    input_dir = os.path.join(bridge_dir, 'input')
    output_dir = os.path.join(bridge_dir, 'output')
    status_dir = os.path.join(bridge_dir, 'status')
    
    print_header("检查目录结构")
    
    # 检查各个目录
    dirs_to_check = [
        (bridge_dir, "桥接根目录"),
        (input_dir, "输入目录 (AnyLogic → Python)"),
        (output_dir, "输出目录 (Python → AnyLogic)"),
        (status_dir, "状态目录")
    ]
    
    all_exist = True
    for dir_path, description in dirs_to_check:
        exists = check_path(dir_path, description)
        if not exists:
            all_exist = False
            try:
                os.makedirs(dir_path)
                print(f"  → 已创建目录")
            except Exception as e:
                print(f"  → 创建失败: {e}")
    
    print_header("AnyLogic配置信息")
    
    print("\n在AnyLogic的Main agent中，请设置以下变量：")
    print("\n1. inputDir 变量:")
    print(f'   "{input_dir.replace(os.sep, "/") + "/"}"')
    
    print("\n2. outputDir 变量:")
    print(f'   "{output_dir.replace(os.sep, "/") + "/"}"')
    
    print("\n3. pythonBridgePath 变量:")
    print(f'   "{bridge_dir.replace(os.sep, "/")}"')
    
    print_header("检查文件")
    
    # 检查Python脚本
    python_script = os.path.join(script_dir, 'anylogic_file_bridge.py')
    check_path(python_script, "Python桥接脚本")
    
    # 检查启动脚本
    bat_script = os.path.join(script_dir, 'start_python_bridge.bat')
    check_path(bat_script, "启动批处理脚本")
    
    # 检查输出文件
    routes_file = os.path.join(output_dir, 'routes.json')
    if check_path(routes_file, "路线文件 (routes.json)"):
        # 显示文件大小和修改时间
        size = os.path.getsize(routes_file)
        mtime = os.path.getmtime(routes_file)
        from datetime import datetime
        mod_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  大小: {size} 字节")
        print(f"  修改时间: {mod_time}")
    
    print_header("检查输入目录中的订单文件")
    
    if os.path.exists(input_dir):
        order_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
        if order_files:
            print(f"\n找到 {len(order_files)} 个订单文件:")
            for i, filename in enumerate(order_files[:5], 1):  # 只显示前5个
                print(f"  {i}. {filename}")
            if len(order_files) > 5:
                print(f"  ... 还有 {len(order_files) - 5} 个文件")
        else:
            print("\n✓ 输入目录为空 (正常状态)")
    
    print_header("系统信息")
    
    print(f"\nPython版本: {sys.version}")
    print(f"操作系统: {os.name}")
    print(f"当前工作目录: {os.getcwd()}")
    
    print_header("下一步操作")
    
    print("\n1. 确保上述路径在AnyLogic中正确配置")
    print("2. 双击 start_python_bridge.bat 启动Python服务")
    print("3. 在AnyLogic中运行模拟")
    print("4. 观察两个窗口的输出")
    
    print("\n" + "="*60)
    print("验证完成！")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按Enter键退出...")
