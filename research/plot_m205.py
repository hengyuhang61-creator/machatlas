"""Draw both Mach 2.05 ramp solutions and the resulting wall diagnostics."""
import argparse
from pathlib import Path

from plot_native import COLORS, field, triangles, wall
import matplotlib.pyplot as plt


def render(runs, out):
    fig, ax = plt.subplots(2,2,figsize=(11.5,6.8),layout="constrained")
    fig.suptitle("Mach 2.05 | native 2-D ramp calculations", fontsize=17, weight="bold")
    for pane, (label,path) in zip(ax[0], runs[:2]):
        data = field(path/"flow.vtu")
        chart = pane.tripcolor(triangles(data),data["Mach"],shading="gouraud",
                               cmap="viridis",vmin=0,vmax=2.2)
        pane.axis((-.039,.090,0,.046))
        pane.set_title(label)
        pane.set(xlabel="Axial x [m]",ylabel="Vertical y [m]")
    fig.colorbar(chart,ax=ax[0].tolist(),label="Mach",extend="both")
    for (label,path),color in zip(runs,COLORS):
        x,cf,cp,_ = wall(field(path/"flow.vtu")).T
        ax[1,0].plot(x,cf*1000,color=color,label=label,lw=1.4)
        ax[1,1].plot(x,cp,color=color,lw=1.4)
    ax[1,0].set_ylabel("1,000 × Cf,x")
    ax[1,0].axhline(0,color="#525b5d",lw=.7)
    ax[1,0].legend(fontsize="small",frameon=False)
    ax[1,1].set_ylabel("Cp = (p − p∞) / q∞")
    for pane in ax[1]:
        pane.set_xlim(0,.08)
        pane.set_xlabel("Axial x [m]")
        pane.grid(alpha=.2)
    fig.savefig(out,dpi=145,facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("out",type=Path)
    p.add_argument("--case",nargs=2,metavar=("LABEL","RUN"),action="append",required=True)
    a=p.parse_args()
    render([(label,Path(path)) for label,path in a.case],a.out)
