"""
智谱/第三方模型兼容性测试脚本

测试你的环境是否支持 Claude Skills 功能
"""
import os
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_sdk_version():
    """测试 1: 检查 SDK 版本"""
    print("=" * 60)
    print("测试 1: 检查 Anthropic SDK 版本")
    print("=" * 60)

    try:
        import anthropic
        version = anthropic.__version__
        print(f"✓ Anthropic SDK 版本: {version}")

        # Skills 需要 0.71.0 或更高版本
        from packaging import version
        if version.parse(version) >= version.parse("0.71.0"):
            print("✓ SDK 版本支持 Skills 功能")
            return True, version
        else:
            print(f"⚠️ SDK 版本过低，需要 >= 0.71.0")
            print("  运行: pip install --upgrade anthropic")
            return False, version
    except ImportError:
        print("❌ 未安装 anthropic 包")
        print("  运行: pip install anthropic")
        return False, None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False, None


def test_api_connection():
    """测试 2: 基本 API 连接"""
    print("\n" + "=" * 60)
    print("测试 2: 基本 API 连接")
    print("=" * 60)

    try:
        from anthropic import Anthropic
        from dotenv import load_dotenv

        # 加载环境变量
        load_dotenv(Path(__file__).parent / ".env")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            print("❌ 未找到 ANTHROPIC_API_KEY")
            print("  请在 .env 文件中配置 API 密钥")
            return False, None

        print(f"✓ API 密钥已加载: {api_key[:10]}...")

        # 测试基本连接
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'API connected'"}]
        )

        print("✓ 基本 API 连接成功")
        print(f"  响应: {response.content[0].text}")
        return True, client

    except Exception as e:
        print(f"❌ API 连接失败: {e}")
        return False, None


def test_beta_api_support(client):
    """测试 3: Beta API 支持（container 参数）"""
    print("\n" + "=" * 60)
    print("测试 3: Beta API 支持 (container 参数)")
    print("=" * 60)

    try:
        # 尝试使用 beta API
        response = client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            container={},  # 空的 container 测试参数支持
            messages=[{"role": "user", "content": "Say 'Beta API works'"}]
        )

        print("✓ Beta API (client.beta.messages) 可用")
        print("✓ container 参数被接受")
        return True

    except AttributeError as e:
        print("❌ client.beta.messages 不存在")
        print("  这意味着 SDK 不支持 Beta API")
        return False
    except TypeError as e:
        if "container" in str(e):
            print("❌ container 参数不被识别")
            print("  这意味着 API 不支持 Skills 功能")
            return False
        else:
            raise
    except Exception as e:
        print(f"⚠️ 其他错误: {e}")
        return False


def test_skills_list(client):
    """测试 4: Skills API 支持"""
    print("\n" + "=" * 60)
    print("测试 4: Skills API (列出技能)")
    print("=" * 60)

    try:
        # 尝试列出可用的技能
        skills = client.beta.skills.list(source="anthropic")

        print(f"✓ Skills API 可用")
        print(f"  找到 {len(skills.data)} 个 Anthropic 管理的技能:")

        for skill in skills.data[:5]:  # 只显示前5个
            print(f"    - {skill.id}: {skill.display_title}")

        return True

    except AttributeError:
        print("❌ client.beta.skills 不存在")
        print("  这意味着 SDK 不支持 Skills API")
        return False
    except Exception as e:
        print(f"⚠️ Skills API 调用失败: {e}")
        print("  可能是因为:")
        print("    1. 智谱 API 不支持 Skills 功能")
        print("    2. 需要特殊的 API 密钥或权限")
        return False


def test_code_execution(client):
    """测试 5: Code Execution 工具支持"""
    print("\n" + "=" * 60)
    print("测试 5: Code Execution 工具")
    print("=" * 60)

    try:
        response = client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
            messages=[{
                "role": "user",
                "content": "用 Python 计算 2+2，然后告诉我结果"
            }]
        )

        print("✓ Code Execution 工具可用")
        return True

    except Exception as e:
        print(f"❌ Code Execution 不可用: {e}")
        return False


def test_simple_skill(client):
    """测试 6: 简单 Skill 使用（完整流程）"""
    print("\n" + "=" * 60)
    print("测试 6: 完整 Skills 流程")
    print("=" * 60)

    try:
        # 尝试使用一个简单的技能
        response = client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            container={
                "skills": [
                    {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
                ]
            },
            tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
            messages=[{
                "role": "user",
                "content": "创建一个简单的 Excel 文件，包含一个单元格 A1 值为 'Hello'"
            }],
            betas=[
                "code-execution-2025-08-25",
                "files-api-2025-04-14",
                "skills-2025-10-02"
            ]
        )

        print("✓ Skills 请求成功")
        print(f"  输入 tokens: {response.usage.input_tokens}")
        print(f"  输出 tokens: {response.usage.output_tokens}")

        # 检查是否返回了 file_id
        file_ids = []
        for block in response.content:
            if hasattr(block, 'type') and block.type == "tool_result":
                # 检查是否有 file_id
                content_str = str(block)
                if 'file_id' in content_str.lower():
                    print("✓ 检测到文件创建（file_id 在响应中）")
                    file_ids.append("found")
                    break

        if file_ids:
            print("✓ Skills 功能完整可用！")
            return True
        else:
            print("⚠️ Skills API 调用成功，但未检测到文件创建")
            print("  可能的原因:")
            print("    1. 技能加载成功但未执行")
            print("    2. 文件创建失败但未报错")
            return False

    except Exception as e:
        print(f"❌ Skills 调用失败: {e}")
        print("\n  可能的原因:")
        print("    1. 智谱 API 不支持 Anthropic 的技能")
        print("    2. API 端点不同，需要特殊配置")
        print("    3. 需要使用智谱自己的技能系统")
        return False


def main():
    """运行所有测试"""
    print("\n" + "🔍" * 30)
    print("Claude Skills 兼容性测试")
    print("适用于: 智谱 AI / 第三方 Claude API")
    print("🔍" * 30 + "\n")

    results = {}

    # 测试 1: SDK 版本
    results['sdk_version'], sdk_version = test_sdk_version()

    if not results['sdk_version']:
        print("\n❌ SDK 版本过低或未安装，无法继续测试")
        print("请先安装/升级: pip install anthropic>=0.71.0")
        return

    # 测试 2: API 连接
    results['api_connection'], client = test_api_connection()

    if not results['api_connection']:
        print("\n❌ API 连接失败，无法继续测试")
        print("请检查 .env 文件中的 API 密钥配置")
        return

    # 测试 3: Beta API
    results['beta_api'] = test_beta_api_support(client) if client else False

    # 测试 4: Skills API
    results['skills_api'] = test_skills_list(client) if client else False

    # 测试 5: Code Execution
    results['code_execution'] = test_code_execution(client) if client else False

    # 测试 6: 完整流程
    if all([results.get('beta_api'), results.get('code_execution')]):
        results['full_skills'] = test_simple_skill(client)
    else:
        results['full_skills'] = False
        print("\n⚠️ 跳过完整流程测试（前置条件未满足）")

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {test_name}")

    # 判断兼容性
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"\n通过率: {passed_count}/{total_count}")

    if results.get('full_skills'):
        print("\n🎉 恭喜！你的环境完全支持 Claude Skills 功能！")
        print("   你可以直接使用 skills/ 目录下的教程笔记本")
    elif results.get('api_connection') and not results.get('beta_api'):
        print("\n⚠️ 检测到问题: API 连接正常，但 Beta API 不可用")
        print("\n可能的解决方案:")
        print("  1. 如果你使用的是智谱 AI:")
        print("     - 智谱可能不支持 Anthropic 的 Skills 功能")
        print("     - 需要使用智谱自己的工具/插件系统")
        print("  2. 如果你使用的是其他第三方 API:")
        print("     - 确认该服务是否兼容 Anthropic API")
        print("     - 查看官方文档关于 Skills/Tools 的说明")
        print("  3. 要使用完整 Skills 功能:")
        print("     - 需要使用 Anthropic 官方 API")
        print("     - 注册账号: https://console.anthropic.com/")
    elif results.get('beta_api') and not results.get('skills_api'):
        print("\n⚠️ 检测到问题: Beta API 可用，但 Skills API 不可用")
        print("\n可能的原因:")
        print("  - 第三方 API 不支持 Skills 列表功能")
        print("  - 但可能仍支持使用技能（尝试运行完整流程测试）")
    else:
        print("\n❌ 你的环境当前不支持 Claude Skills 功能")
        print("\n建议:")
        print("  1. 使用 Anthropic 官方 API: https://console.anthropic.com/")
        print("  2. 或者询问智谱 AI 是否有类似的工具/插件功能")


if __name__ == "__main__":
    main()
