import cyclopts

import y2
from y2 import clean
from y2 import hig
from y2 import pv
from y2 import xcode

app = cyclopts.App(
    name="y2",
    help="Why have two when one will do?",
    version=y2.__version__,
)
app.command(hig.app)
app.command(xcode.app)
app.command(clean.clean)
app.command(pv.pv)


if __name__ == "__main__":
    app()
