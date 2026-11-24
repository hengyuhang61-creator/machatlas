# MachAtlas Mach 5 launch material

## English project introduction

**For science-curious readers and CFD reviewers: see where a Mach 5 shock drives air backward, and why one solver release predicts a much longer separated patch.** Open the two real steady solution fields. Switch from Mach number to axial flow near the wall, sweep the axial probe, and locate the friction zero crossings. Then switch from the same-grid release comparison to the wall-temperature control.

The method and input archive gives the mesh and restart hashes, config, wall traces, resource receipts and the frozen convergence gate. The DLR marks are sampled reference brackets. The reported result concerns a controlled computation; uncertainty on the experiment and on the mesh limit a physical validation claim.

[Open the interactive feature](https://hengyuhang61-creator.github.io/machatlas/research.html#discrepancy) · [Methods](research/DISCREPANCY.md) · [Releases](https://github.com/hengyuhang61-creator/machatlas/releases/latest)

## 中文项目介绍

**面向好奇高速流动的读者和 CFD 复核者：看 Mach 5 激波在哪里让近壁气流倒转，以及为什么两个求解器版本给出长度迥异的分离区。** 打开真实的两幅稳态场，在马赫数和近壁轴向速度间切换。拖动轴向探针，读取同一位置的壁摩擦或壁压。也可切换到相同 SU2 版本的壁温对照。

资料包含网格与重启哈希、配置、壁面曲线、资源记录和冻结的收敛门槛。图中 DLR 色带展示零交叉两侧的采样区间。结论限于受控数值计算，实验和网格误差仍限制物理验证。

[打开互动专题](https://hengyuhang61-creator.github.io/machatlas/research.html#discrepancy) · [方法与复算](research/DISCREPANCY.md) · [版本](https://github.com/hengyuhang61-creator/machatlas/releases/latest)

## Third-party community draft

**Draft.** How can two mass-balanced results disagree about where Mach 5 flow reverses? MachAtlas lets you compare two native solutions on the same mesh, switch to wall shear, and read the measured DLR crossing brackets. The release includes the data and solver evidence behind each number. [Explore the comparison](https://hengyuhang61-creator.github.io/machatlas/research.html#discrepancy)
