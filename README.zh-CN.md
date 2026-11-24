# MachAtlas

**看见同一 Mach 5 工况下，求解器怎样预测激波后的近壁气流倒转。**

[打开 Mach 5 互动专题](https://hengyuhang61-creator.github.io/machatlas/research.html#discrepancy) · [公开图鉴](https://hengyuhang61-creator.github.io/machatlas/) · [版本发布](https://github.com/hengyuhang61-creator/machatlas/releases/latest) · [English](README.md)

同一网格、初值与绝热配置下，SU2 8.6.0 和 7.4.0 预测的分离泡分别约为 23.57 mm 和 7.92 mm。并排看真实的马赫数和近壁轴向速度场，拖动探针读取壁摩擦或压力。切换到 300 K 对照，就能在固定 SU2 版本下查看壁温带来的变化。DLR 参考标记同时给出壁摩擦零交叉的采样区间。

[研究结论与复算](research/DISCREPANCY.md)公开输入、观测量、重启链和误差边界。研究对照支持数值归因，完整物理验证仍待完成。

## 其他风洞案例

- **Mach 2.05 斜坡**。Stanford PIV 与公开 SU2 对照，在相同测点切换误差指标。另有 2-D 原生求解和入口剖面核验。
- **Mach 2.5 轴对称锥**。NASA PIV 与公开 RANS 对照。移动同宽的径向窗口便可看到 FUN3D 模型比较变化。
- **Mach 3 HMVE**。两组 NASA PIV 实验，在 21 个对齐测站比较两个径向带的速度均值。

前三个图鉴案例的离线复算使用已归档的数据。研究工作流可执行原生 SU2，发布包包含完整研究求解的证据。CI 另运行 20 步的 SU2 冒烟用例来验收执行入口。实验支持范围、数据许可和复算命令见[英文说明](README.md)与[来源](SOURCES.md)。
