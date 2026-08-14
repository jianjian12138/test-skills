# 移动端自动化测试指南（qa-mobile-autotest）

## 为什么需要清单先行
App 改一个按钮，第二天回归二十条用例集体报红；Android/iOS 各写一套，交接成本高。
**先清单（manifest）后 case**，清单是事实来源，跳过它后面全偏。

## 八步交付闭环
1. 摸底：模拟器 / USB 真机 / 云网格
2. 环境体检：`check_env.py`
3. 清单先行：`scaffold_manifest.py` → screens / flows / risks
4. 生成 Screen / Flow 资产（Page Object 分层）
5. 跨端定位（定位金字塔）
6. 运行 + 失败截图
7. 质量自检：`quality_rubric.py` 五维打分
8. 中文交付摘要（<70 必须补全）

## 定位金字塔
- L1 accessibility id（跨端首选，推动开发加 testID）
- L2 resource-id / name
- L3 iOS predicate / class chain
- L4 Android UiAutomator
- L5 XPath 仅兜底，须注释原因
- 禁止 `Thread.sleep` 与写死坐标。

## 失败诊断
先走 `fault_diagnosis.py` 决策树，一次只改一个变量；混合 App 测完 H5 必须切回 NATIVE_APP。

## 五维 rubric
可运行性25 / 定位健壮性25 / 可维护性20 / 稳定性15 / 覆盖透明度15，满分 100，<70 必须补全。

## 平台注意
- Android：UiAutomator2、需 JDK + SDK，权限动态申请。
- iOS：XCUITest，需 macOS + Xcode + WDA。
- 云真机（SauceLabs/BrowserStack/阿里云/WeTest）可绕过本地设备限制。
