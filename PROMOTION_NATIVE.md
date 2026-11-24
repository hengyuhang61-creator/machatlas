# MachAtlas v0.2.0 launch material

## English

**What moves when a Mach 5 shock meets a wall?** New native SU2 simulations compare grid refinement, two turbulence closures and a matched thermal-wall change. Inspect the real Mach, velocity, wall pressure and skin-friction fields. One branch passed the mass screen while its separation point was still moving.

[Open the new research page](https://hengyuhang61-creator.github.io/machatlas/research.html) · [Release](https://github.com/hengyuhang61-creator/machatlas/releases/tag/v0.2.0) · [Replay](research/REPRODUCE.md) · [Captured demo](media/native-study-demo.gif)

## 中文

**当 Mach 5 激波撞上边界层，哪些结果会变？** 新的 SU2 原生仿真比较了三层网格、两种湍流闭合及一个同起点壁温对照。可以切换真实 Mach 数、速度、壁面压力和摩擦系数。一条分支的质量误差已很低，分离位置却还在移动。

[打开研究页](https://hengyuhang61-creator.github.io/machatlas/research.html) · [正式发布](https://github.com/hengyuhang61-creator/machatlas/releases/tag/v0.2.0) · [复算入口](research/REPRODUCE.md)

## Community draft

We ran the Mach 5 Schülein benchmark in SU2 8.6 across three grid levels. In one late continuation, both saves had less than 0.004% mass imbalance, but the separation point moved 7.20 mm. The new release includes the terminal fields, a matched wall-temperature contrast, the Mach 2.05 inlet qualification, exact run fingerprints and repairable limits. This is a numerical sensitivity study; experimental validation remains open. [Study](https://hengyuhang61-creator.github.io/machatlas/research.html)
