# Figure brief: 西侧柱柱底(铰接)

Purpose      说明 Option 1 的西侧外柱柱底按铰接建模的构造依据;放 D3 报告 2.1 节「连接假设」(Option 1 = 铰接柱底)
Source       D3 brief Part 2 + TTW 标准图 ST-30xxx 柱底板表(课程图纸 p22);W12L:Option 1 柱底铰接;Ed #87 等不涉及
Subject      柱底板 + 四颗锚栓(强调色给底板)
Structure    610UB113 西柱下段 1.6 m;底板 20 mm 按截面分档 → 32 mm(生成器默认,>620 深度档),灌浆 40 mm,四颗 M30(默认档,假设)锚栓在翼缘内侧 60 mm,混凝土基础 1.3×0.9×0.6 m(示意)
             assumed: 锚栓规格 M24/M30 之间取生成器默认;基础尺寸示意
Explanation  3D 尺寸:锚栓纵向间距(翼缘内 60 mm → 607−120 = 487)、横向间距 120;平面图(俯视正交)再标一次
Views        (a) 透视 3/4 从东南上方,裁到基础;(b) 平面图 look = -z,裁到底板附近,2D 尺寸 487 / 120
Labels       1 610UB113 柱 2 底板 3 锚栓(四颗) 4 灌浆 5 混凝土基础;圆圈自动放
Style        默认;底板强调色
Checks       尺寸文字对模型;无穿模;REALISM 清零
Output       fig_colbase.tex,images/steelfig/,preview PDF
Open points  ① 锚栓用 M24 还是 M30?② 基础尺寸要不要按真实设计?(模拟用户:用默认,基础示意)
