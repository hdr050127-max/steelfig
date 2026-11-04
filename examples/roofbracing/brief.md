# Figure brief: 屋面交叉支撑(一个支撑开间)

Purpose      说明纵向稳定性靠端开间的屋面交叉支撑把风荷载传到墙支撑;放 D3 报告「稳定性 / 本作业不设计的构件」一节,说明假设
Source       D3 brief Part 1(建筑说明:端开间设屋面支撑);W12L「假定平面外有支撑系统」;AS 4100 Cl 3.3 / 6.6(未核对条款号,标假设)
Subject      交叉拉杆(强调色)
Structure    两榀相邻刚架的西端 0–13 m 段(530UB92.4 haunch 0–6.278,360UB50.7 中段,按 M9 几何),间距 11.315 m;
             Z25019 檩条 @1200 跨两榀;交叉支撑两根 CHS 76.1×3.6(C350)从檐口节点到对面第 5 根檩条位置(约 6 m),
             轴线在椽子顶面下 80 mm 以从檩条下穿过;檐口处一根 CHS 139.7×5.0 压杆(eave strut)连两榀
             assumed: 支撑用 CHS 而非圆钢拉杆;节点板(gusset)尺寸 250×180×10 焊在上翼缘,支撑端部直接搭在节点板上(未画螺栓);
             拉杆轴线低于顶面 80 mm 的做法
Explanation  支撑在平面上的走向;两根拉杆交叉;标支撑开间宽 11.315 m 和支撑长度
Views        (a) 透视从东南上方看整个开间;(b) 平面图(俯视)看交叉形状,标 11.315 m
Labels       1 530UB92.4 haunch 2 360UB50.7 rafter 3 CHS 76.1×3.6 diagonal 4 CHS 139.7×5 eave strut 5 gusset plate 6 purlins
Style        默认;拉杆强调色
Checks       穿模(拉杆 vs 檩条 / 椽子);尺寸;REALISM
Output       fig_roofbracing.tex
Open points  ① 圆钢拉杆还是 CHS?② 要不要画螺栓/节点板细节?(模拟用户:CHS,节点板只示意)
