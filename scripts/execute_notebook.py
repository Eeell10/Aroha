"""Execute with a Jupyter kernel, or explicitly validate cells in-process when sockets are unavailable."""
from pathlib import Path
import argparse
import base64
import io
import nbformat
from nbclient import NotebookClient

root=Path(__file__).resolve().parents[1]
path=root/'notebooks/01_conceptual_design.ipynb'
nb=nbformat.read(path,as_version=4)
parser=argparse.ArgumentParser(); parser.add_argument('--in-process',action='store_true'); args=parser.parse_args()
if args.in_process:
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    import matplotlib.pyplot as plt
    shell=InteractiveShell.instance(); count=0
    for cell in nb.cells:
        if cell.cell_type!='code': continue
        count+=1; cell.execution_count=count; cell.outputs=[]
        with capture_output() as captured:
            result=shell.run_cell(cell.source,store_history=False)
        if result.error_before_exec or result.error_in_exec:
            raise RuntimeError(f'Notebook cell {count} failed') from (result.error_before_exec or result.error_in_exec)
        for name,text in [('stdout',captured.stdout),('stderr',captured.stderr)]:
            if text: cell.outputs.append(nbformat.v4.new_output('stream',name=name,text=text))
        for rich in captured.outputs:
            cell.outputs.append(nbformat.v4.new_output('display_data',data=rich.data,metadata=rich.metadata))
        for number in plt.get_fignums():
            fig=plt.figure(number); buffer=io.BytesIO(); fig.savefig(buffer,format='png',bbox_inches='tight')
            cell.outputs.append(nbformat.v4.new_output('display_data',data={'image/png':base64.b64encode(buffer.getvalue()).decode()}))
            plt.close(fig)
    nb.metadata['execution_note']='Cells executed in-process with IPython; live Jupyter kernel/server was not validated because workspace sockets are prohibited.'
else:
    NotebookClient(nb,timeout=180,kernel_name='aroha',resources={'metadata':{'path':str(root)}}).execute()
out=root/'reports/runs/01_conceptual_design.executed.ipynb'; out.parent.mkdir(parents=True,exist_ok=True)
nbformat.write(nb,out)
print(out)
